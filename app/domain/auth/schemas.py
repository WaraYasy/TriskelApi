from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime

from .validators import PasswordValidator


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def trim_username(cls, v: str) -> str:
        return v.strip()


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    role: str = Field(default="admin", pattern="^(admin|support|viewer)$")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return PasswordValidator.validate(v)

    @field_validator("username")
    @classmethod
    def trim_username(cls, v: str) -> str:
        return v.strip()


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|support|viewer)$")
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str, info) -> str:
        validated = PasswordValidator.validate(v)
        if info.data.get("old_password") == validated:
            raise ValueError("El nuevo password debe ser diferente del actual")
        return validated


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[str]

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int
