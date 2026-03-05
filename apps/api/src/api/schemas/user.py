import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from api.models.user import Role


class UserInviteCreate(BaseModel):
    email: EmailStr
    role: Role

    @field_validator("role")
    @classmethod
    def role_not_admin(cls, v: Role) -> Role:
        if v == Role.admin:
            raise ValueError("Cannot invite a user with admin role")
        return v


class UserInviteResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    invite_url: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    role: Role | None = None
    is_active: bool | None = None


class UserAdminOut(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
