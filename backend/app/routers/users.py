from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter

from app.core.audit import write_audit_log
from app.core.auth import AdminOrLeaderUser, AdminUser, AuthenticatedUser
from app.core.db import (
    USER_SELECT,
    active_admin_count,
    get_role,
    get_user_profile,
    require_role,
    require_user_profile,
    response_single,
)
from app.core.errors import conflict, forbidden, not_found
from app.schemas.common import UserRead
from app.schemas.users import UserCreate, UserRoleUpdate, UserStatusUpdate, UserUpdate
from app.supabase_client import supabase

router = APIRouter(prefix="/users", tags=["users"])


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _auth_user_exists(user_id: str) -> bool:
    try:
        response = supabase.auth.admin.get_user_by_id(user_id)
    except Exception:
        return False
    return getattr(response, "user", None) is not None


def _ensure_unique_user(id_value: str, email: str, exclude_id: str | None = None) -> None:
    existing_id = get_user_profile(id_value)
    if existing_id and existing_id.get("id") != exclude_id:
        raise conflict("User id already exists")

    existing_email = (
        supabase.table("app_users")
        .select("id")
        .eq("email", email)
        .maybe_single()
        .execute()
        .data
    )
    if existing_email and existing_email.get("id") != exclude_id:
        raise conflict("User email already exists")


def _would_remove_last_active_admin(user: dict, new_role_id: str | None = None, new_is_active: bool | None = None) -> bool:
    role = user.get("role") or {}
    is_admin = role.get("code") == "admin"
    is_active = user.get("is_active") is True
    if not (is_admin and is_active):
        return False

    if new_role_id:
        new_role = require_role(new_role_id)
        if new_role.get("code") == "admin":
            return False

    if new_is_active is not None and new_is_active is True:
        return False

    return active_admin_count() <= 1


@router.get("", response_model=list[UserRead])
def read_users(_: AdminOrLeaderUser) -> list[dict]:
    return (
        supabase.table("app_users")
        .select(USER_SELECT)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: UUID, current_user: AuthenticatedUser) -> dict:
    user_id_str = str(user_id)
    if current_user.role_code not in {"admin", "leader"} and current_user.auth_user_id != user_id_str:
        raise forbidden()
    return require_user_profile(user_id_str)


@router.post("", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, current_user: AdminUser) -> dict:
    user_id = str(payload.id)
    if not _auth_user_exists(user_id):
        raise not_found("Auth user not found")

    _ensure_unique_user(user_id, str(payload.email))
    require_role(str(payload.role_id))

    insert_payload = payload.model_dump(mode="json")
    created = response_single(
        supabase.table("app_users")
        .insert(insert_payload)
        .select(USER_SELECT)
        .single()
        .execute(),
        "User was created but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_users",
        target_id=user_id,
        action="create",
        before=None,
        after=created,
    )
    return created


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, payload: UserUpdate, current_user: AdminUser) -> dict:
    user_id_str = str(user_id)
    before = require_user_profile(user_id_str)
    updates = payload.model_dump(mode="json", exclude_unset=True)
    if not updates:
        return before

    if "email" in updates:
        _ensure_unique_user(user_id_str, updates["email"], exclude_id=user_id_str)

    updates["updated_at"] = _now()
    after = response_single(
        supabase.table("app_users")
        .update(updates)
        .eq("id", user_id_str)
        .select(USER_SELECT)
        .single()
        .execute(),
        "User was updated but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_users",
        target_id=user_id_str,
        action="update",
        before=before,
        after=after,
    )
    return after


@router.patch("/{user_id}/role", response_model=UserRead)
def update_user_role(user_id: UUID, payload: UserRoleUpdate, current_user: AdminUser) -> dict:
    user_id_str = str(user_id)
    before = require_user_profile(user_id_str)
    new_role_id = str(payload.role_id)
    require_role(new_role_id)

    if _would_remove_last_active_admin(before, new_role_id=new_role_id):
        raise conflict("Cannot remove the last active admin user")

    after = response_single(
        supabase.table("app_users")
        .update({"role_id": new_role_id, "updated_at": _now()})
        .eq("id", user_id_str)
        .select(USER_SELECT)
        .single()
        .execute(),
        "User role was updated but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_users",
        target_id=user_id_str,
        action="change_role",
        before=before,
        after=after,
    )
    return after


@router.patch("/{user_id}/status", response_model=UserRead)
def update_user_status(user_id: UUID, payload: UserStatusUpdate, current_user: AdminUser) -> dict:
    user_id_str = str(user_id)
    before = require_user_profile(user_id_str)

    if _would_remove_last_active_admin(before, new_is_active=payload.is_active):
        raise conflict("Cannot deactivate the last active admin user")

    after = response_single(
        supabase.table("app_users")
        .update({"is_active": payload.is_active, "updated_at": _now()})
        .eq("id", user_id_str)
        .select(USER_SELECT)
        .single()
        .execute(),
        "User status was updated but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_users",
        target_id=user_id_str,
        action="change_status",
        before=before,
        after=after,
    )
    return after
