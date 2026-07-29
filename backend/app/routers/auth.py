from fastapi import APIRouter

from app.core.auth import AuthenticatedUser
from app.schemas.common import MeResponse
from app.supabase_client import supabase

router = APIRouter(tags=["auth"])


def build_me_response(current_user: AuthenticatedUser) -> MeResponse:
    role = current_user.role
    assignments = (
        supabase.table("user_store_assignments")
        .select("store_id,can_view,can_edit")
        .eq("user_id", current_user.auth_user_id)
        .execute()
        .data
        or []
    )
    return MeResponse(user=current_user.profile, role=role, store_assignments=assignments)


@router.get("/auth/me", response_model=MeResponse)
def get_auth_me(current_user: AuthenticatedUser) -> MeResponse:
    return build_me_response(current_user)


@router.get("/me", response_model=MeResponse, include_in_schema=False)
def get_me_alias(current_user: AuthenticatedUser) -> MeResponse:
    return build_me_response(current_user)
