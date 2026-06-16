from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.db import get_user_profile
from app.core.errors import forbidden, unauthorized
from app.supabase_client import supabase

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    auth_user_id: str
    profile: dict
    role: dict

    @property
    def role_code(self) -> str:
        return self.role.get("code", "")


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()

    try:
        auth_response = supabase.auth.get_user(credentials.credentials)
    except Exception as exc:
        raise unauthorized() from exc

    auth_user = getattr(auth_response, "user", None)
    auth_user_id = getattr(auth_user, "id", None)
    if not auth_user_id:
        raise unauthorized()

    profile = get_user_profile(str(auth_user_id))
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
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
