from typing import Any

from fastapi import HTTPException, status

from app.core.errors import not_found
from app.supabase_client import supabase


USER_SELECT = (
    "id,display_name,email,role_id,is_active,created_at,updated_at,"
    "role:app_roles(id,code,name,description,created_at)"
)

ROLE_SELECT = "id,code,name,description,created_at"

BASIC_ROLE_CODES = {"admin", "leader", "sub_leader", "viewer"}


def _data(response: Any) -> Any:
    return getattr(response, "data", None)


def list_users() -> list[dict[str, Any]]:
    return _data(supabase.table("app_users").select(USER_SELECT).order("created_at", desc=True).execute()) or []


def get_user_profile(user_id: str) -> dict[str, Any] | None:
    data = (
        _data(
            supabase.table("app_users")
            .select(USER_SELECT)
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        or None
    )
    return data


def require_user_profile(user_id: str) -> dict[str, Any]:
    user = get_user_profile(user_id)
    if not user:
        raise not_found("User not found")
    return user


def list_roles() -> list[dict[str, Any]]:
    return _data(supabase.table("app_roles").select(ROLE_SELECT).order("created_at", desc=True).execute()) or []


def get_role(role_id: str) -> dict[str, Any] | None:
    return (
        _data(
            supabase.table("app_roles")
            .select(ROLE_SELECT)
            .eq("id", role_id)
            .maybe_single()
            .execute()
        )
        or None
    )


def get_role_by_code(code: str) -> dict[str, Any] | None:
    return (
        _data(
            supabase.table("app_roles")
            .select(ROLE_SELECT)
            .eq("code", code)
            .maybe_single()
            .execute()
        )
        or None
    )


def require_role(role_id: str) -> dict[str, Any]:
    role = get_role(role_id)
    if not role:
        raise not_found("Role not found")
    return role


def active_admin_count() -> int:
    admin_role = get_role_by_code("admin")
    if not admin_role:
        return 0

    users = (
        _data(
            supabase.table("app_users")
            .select("id")
            .eq("role_id", admin_role["id"])
            .eq("is_active", True)
            .execute()
        )
        or []
    )
    return len(users)


def response_single(response: Any, detail: str) -> dict[str, Any]:
    data = _data(response)
    if isinstance(data, list):
        if not data:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
        return data[0]
    if not data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
    return data
