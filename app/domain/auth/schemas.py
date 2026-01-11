"""
Schemas (DTOs) para la API de Auth

Estos son los modelos de ENTRADA y SALIDA de la API REST.
Define qué datos acepta y retorna cada endpoint de autenticación.
"""
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List
from datetime import datetime
import re


# ==================== Request Schemas ====================

class LoginRequest(BaseModel):
    """
    Datos necesarios para login de administrador.
    """
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "Admin123!"
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Datos necesarios para renovar access token.
    """
    refresh_token: str = Field(..., description="Refresh token obtenido del login")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class AdminUserCreate(BaseModel):
    """
    Datos necesarios para crear un nuevo administrador.

    Password debe cumplir:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos un número
    """
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer", pattern="^(admin|support|viewer)$")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Valida que el password cumpla con requisitos de seguridad.
        """
        if len(v) < 8:
            raise ValueError("Password debe tener al menos 8 caracteres")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password debe tener al menos una mayúscula")

        if not re.search(r"[0-9]", v):
            raise ValueError("Password debe tener al menos un número")

        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Valida que el username solo contenga caracteres alfanuméricos y guiones.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username solo puede contener letras, números, guiones y guiones bajos")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "support_user",
                "email": "support@triskel.local",
                "password": "Support123!",
                "role": "support"
            }
        }


class AdminUserUpdate(BaseModel):
    """
    Datos que se pueden actualizar de un administrador.

    Todos los campos son opcionales (solo se actualizan los enviados).
    """
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|support|viewer)$")
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "new_email@triskel.local",
                "role": "admin",
                "is_active": True
            }
        }


class ChangePasswordRequest(BaseModel):
    """
    Datos necesarios para cambiar password de usuario actual.
    """
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Valida que el nuevo password cumpla con requisitos de seguridad.
        """
        if len(v) < 8:
            raise ValueError("Password debe tener al menos 8 caracteres")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password debe tener al menos una mayúscula")

        if not re.search(r"[0-9]", v):
            raise ValueError("Password debe tener al menos un número")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword456!"
            }
        }


# ==================== Response Schemas ====================

class TokenResponse(BaseModel):
    """
    Respuesta al login o refresh token exitoso.

    El cliente debe:
    1. Guardar access_token para requests autenticados
    2. Guardar refresh_token para renovar cuando expire el access
    3. Incluir access_token en header: Authorization: Bearer <token>
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Segundos hasta expiración del access_token")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class AdminUserResponse(BaseModel):
    """
    Respuesta con datos de un administrador.

    NUNCA incluye password_hash por seguridad.
    """
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
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@triskel.local",
                "role": "admin",
                "is_active": True,
                "created_at": "2026-01-10T10:00:00Z",
                "updated_at": "2026-01-10T10:00:00Z",
                "last_login": "2026-01-11T15:30:00Z"
            }
        }


class CurrentUserResponse(BaseModel):
    """
    Respuesta con datos del usuario actual (endpoint /auth/me).

    Incluye permisos calculados según su rol.
    """
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    permissions: List[str] = Field(
        ...,
        description="Lista de permisos basados en el rol del usuario"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "admin",
                "email": "admin@triskel.local",
                "role": "admin",
                "is_active": True,
                "created_at": "2026-01-10T10:00:00Z",
                "updated_at": "2026-01-10T10:00:00Z",
                "last_login": "2026-01-11T15:30:00Z",
                "permissions": [
                    "view_players",
                    "edit_players",
                    "delete_players",
                    "view_games",
                    "edit_games",
                    "delete_games",
                    "view_admins",
                    "create_admins",
                    "edit_admins",
                    "delete_admins",
                    "view_audit_logs"
                ]
            }
        }


class AuditLogResponse(BaseModel):
    """
    Respuesta con datos de un log de auditoría.
    """
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
        json_schema_extra = {
            "example": {
                "id": 42,
                "user_id": 1,
                "username": "admin",
                "action": "export_players_csv",
                "resource_type": "player",
                "resource_id": None,
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "details": '{"count": 150, "filters": {}}',
                "timestamp": "2026-01-11T15:30:00Z",
                "success": True,
                "error_message": None
            }
        }


class AuditLogListResponse(BaseModel):
    """
    Respuesta con lista paginada de logs de auditoría.
    """
    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int

    class Config:
        json_schema_extra = {
            "example": {
                "logs": [
                    {
                        "id": 42,
                        "user_id": 1,
                        "username": "admin",
                        "action": "login_success",
                        "timestamp": "2026-01-11T15:30:00Z",
                        "success": True
                    }
                ],
                "total": 150,
                "limit": 10,
                "offset": 0
            }
        }
