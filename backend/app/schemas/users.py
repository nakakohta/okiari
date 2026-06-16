from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    display_name: str | None = Field(default=None, max_length=255)
    email: EmailStr
    role_id: UUID
    is_active: bool = True


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: UUID


class UserStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool
