from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None
    created_at: datetime | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str | None = None
    email: str
    role_id: int
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    role: RoleRead | None = None


class MeResponse(BaseModel):
    user: UserRead
    role: RoleRead
    store_assignments: list[dict] = Field(default_factory=list)
