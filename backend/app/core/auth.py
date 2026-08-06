from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase_auth.errors import AuthApiError, AuthInvalidJwtError, AuthRetryableError

from app.core.db import get_user_profile
from app.core.errors import forbidden, unauthorized
from app.supabase_client import verify_access_token

bearer_scheme = HTTPBearer(auto_error=False)
PROFILE_CACHE_TTL_SECONDS = 10.0
_profile_cache: dict[str, tuple[float, dict]] = {}
_profile_cache_lock = RLock()


@dataclass(frozen=True)
class CurrentUser:
    auth_user_id: str
    profile: dict
    role: dict

    @property
    def role_code(self) -> str:
        return self.role.get("code", "")


def invalidate_user_profile_cache(user_id: str | None = None) -> None:
    with _profile_cache_lock:
        if user_id is None:
            _profile_cache.clear()
        else:
            _profile_cache.pop(user_id, None)


def _cached_user_profile(user_id: str) -> dict | None:
    now = monotonic()
    with _profile_cache_lock:
        cached = _profile_cache.get(user_id)
        if cached and now - cached[0] < PROFILE_CACHE_TTL_SECONDS:
            return cached[1]

    profile = get_user_profile(user_id)
    with _profile_cache_lock:
        if profile:
            _profile_cache[user_id] = (now, profile)
        else:
            _profile_cache.pop(user_id, None)
        return profile


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()

    try:
        claims_response = verify_access_token(credentials.credentials)
    except AuthInvalidJwtError as exc:
        raise unauthorized() from exc
    except AuthApiError as exc:
        if exc.status in {400, 401, 403}:
            raise unauthorized() from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc
    except (AuthRetryableError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication verification failed temporarily",
        ) from exc

    claims = getattr(claims_response, "claims", None) or {}
    auth_user_id = claims.get("sub")
    if not auth_user_id:
        raise unauthorized()

    profile = _cached_user_profile(str(auth_user_id))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user is not registered in app_users",
        )

    if profile.get("is_active") is False:
        raise forbidden("Inactive user")

    role = profile.get("role") or {}
    if not role.get("code"):
        raise forbidden("User role is not configured")

    return CurrentUser(auth_user_id=str(auth_user_id), profile=profile, role=role)


def require_roles(*allowed_codes: str):
    def dependency(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if current_user.role_code not in allowed_codes:
            raise forbidden()
        return current_user

    return dependency


AdminUser = Annotated[CurrentUser, Depends(require_roles("admin"))]
AdminOrLeaderUser = Annotated[CurrentUser, Depends(require_roles("admin", "leader"))]
BusinessEditorUser = Annotated[CurrentUser, Depends(require_roles("admin", "leader", "sub_leader"))]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
