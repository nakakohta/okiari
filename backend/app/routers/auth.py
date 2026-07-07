from fastapi import APIRouter

from app.core.auth import AuthenticatedUser
from app.schemas.common import MeResponse

router = APIRouter(tags=["auth"])


def build_me_response(current_user: AuthenticatedUser) -> MeResponse:
    role = current_user.role
    return MeResponse(user=current_user.profile, role=role, store_assignments=[])


@router.get("/auth/me", response_model=MeResponse)
def get_auth_me(current_user: AuthenticatedUser) -> MeResponse:
    return build_me_response(current_user)


@router.get("/me", response_model=MeResponse, include_in_schema=False)
def get_me_alias(current_user: AuthenticatedUser) -> MeResponse:
    return build_me_response(current_user)
