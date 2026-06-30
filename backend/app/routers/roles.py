from fastapi import APIRouter

from app.core.audit import write_audit_log
from app.core.auth import AdminOrLeaderUser, AdminUser
from app.core.db import BASIC_ROLE_CODES, ROLE_SELECT, require_role, response_single
from app.core.errors import conflict
from app.schemas.common import RoleRead
from app.schemas.roles import RoleCreate, RoleUpdate
from app.supabase_client import supabase

router = APIRouter(prefix="/roles", tags=["roles"])


def _referenced_user_count(role_id: int) -> int:
    users = supabase.table("app_users").select("id").eq("role_id", role_id).execute().data or []
    return len(users)


def _ensure_unique_role_code(code: str, exclude_id: int | None = None) -> None:
    existing = (
        supabase.table("app_roles")
        .select("id")
        .eq("code", code)
        .maybe_single()
        .execute()
        .data
    )
    if existing and existing.get("id") != exclude_id:
        raise conflict("Role code already exists")


@router.get("", response_model=list[RoleRead])
def read_roles(_: AdminOrLeaderUser) -> list[dict]:
    return (
        supabase.table("app_roles")
        .select(ROLE_SELECT)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


@router.get("/{role_id}", response_model=RoleRead)
def read_role(role_id: int, _: AdminOrLeaderUser) -> dict:
    return require_role(role_id)


@router.post("", response_model=RoleRead, status_code=201)
def create_role(payload: RoleCreate, current_user: AdminUser) -> dict:
    _ensure_unique_role_code(payload.code)
    created = response_single(
        supabase.table("app_roles")
        .insert(payload.model_dump(mode="json"))
        .select(ROLE_SELECT)
        .single()
        .execute(),
        "Role was created but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_roles",
        target_id=str(created["id"]),
        action="create",
        before=None,
        after=created,
    )
    return created


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: int, payload: RoleUpdate, current_user: AdminUser) -> dict:
    before = require_role(role_id)
    updates = payload.model_dump(mode="json", exclude_unset=True)
    if not updates:
        return before

    new_code = updates.get("code")
    if before.get("code") in BASIC_ROLE_CODES and new_code and new_code != before.get("code"):
        raise conflict("Basic role code cannot be changed")

    if new_code:
        _ensure_unique_role_code(new_code, exclude_id=role_id_str)

    after = response_single(
        supabase.table("app_roles")
        .update(updates)
        .eq("id", role_id)
        .select(ROLE_SELECT)
        .single()
        .execute(),
        "Role was updated but could not be read",
    )
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_roles",
        target_id=str(role_id),
        action="update",
        before=before,
        after=after,
    )
    return after


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: int, current_user: AdminUser) -> None:
    before = require_role(role_id)

    if before.get("code") in BASIC_ROLE_CODES:
        raise conflict("Basic roles cannot be deleted")

    if _referenced_user_count(role_id) > 0:
        raise conflict("Role is referenced by app_users")

    supabase.table("app_roles").delete().eq("id", role_id).execute()
    write_audit_log(
        actor_user_id=current_user.auth_user_id,
        target_table="app_roles",
        target_id=str(role_id),
        action="delete",
        before=before,
        after=None,
    )
