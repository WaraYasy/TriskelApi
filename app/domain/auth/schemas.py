from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .validators import PasswordValidator


class LoginRequest(BaseModel):
    """Esquema para la petición de login.

    Attributes:
        username (str): Nombre de usuario (3-50 caracteres).
        password (str): Contraseña (8-72 caracteres).
    """

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("username")
    @classmethod
    def trim_username(cls, v: str) -> str:
        """Elimina espacios en blanco del nombre de usuario."""
        return v.strip()


class RefreshTokenRequest(BaseModel):
    """Esquema para la petición de renovación de token.

    Attributes:
        refresh_token (str): Token de refresco válido.
    """

    refresh_token: str


class AdminUserCreate(BaseModel):
    """Esquema para la creación de un usuario administrador.

    Attributes:
        username (str): Nombre de usuario.
        email (EmailStr): Correo electrónico válido.
        password (str): Contraseña segura.
        role (str): Rol del usuario (admin, support, viewer).
    """

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    role: str = Field(default="admin", pattern="^(admin|support|viewer)$")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Valida que la contraseña cumpla con los requisitos de seguridad."""
        return PasswordValidator.validate(v)

    @field_validator("username")
    @classmethod
    def trim_username(cls, v: str) -> str:
        """Elimina espacios en blanco del nombre de usuario."""
        return v.strip()


class AdminUserUpdate(BaseModel):
    """Esquema para la actualización de un usuario administrador.

    Attributes:
        email (Optional[EmailStr]): Nuevo correo electrónico.
        role (Optional[str]): Nuevo rol.
        is_active (Optional[bool]): Estado de activación.
    """

    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|support|viewer)$")
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    """Esquema para el cambio de contraseña.

    Attributes:
        old_password (str): Contraseña actual.
        new_password (str): Nueva contraseña.
    """

    old_password: str = Field(..., min_length=8, max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str, info) -> str:
        """Valida la nueva contraseña y asegura que sea diferente a la anterior."""
        validated = PasswordValidator.validate(v)
        if info.data.get("old_password") == validated:
            raise ValueError("El nuevo password debe ser diferente del actual")
        return validated


class TokenResponse(BaseModel):
    """Esquema de respuesta con tokens de acceso.

    Attributes:
        access_token (str): Token de acceso JWT.
        refresh_token (str): Token de refresco.
        token_type (str): Tipo de token (bearer).
        expires_in (int): Tiempo de expiración en segundos.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminUserResponse(BaseModel):
    """Esquema de respuesta con datos de un usuario administrador.

    Attributes:
        id (int): ID del usuario.
        username (str): Nombre de usuario.
        email (str): Correo electrónico.
        role (str): Rol del usuario.
        is_active (bool): Estado de activación.
        created_at (datetime): Fecha de creación.
        updated_at (datetime): Fecha de última actualización.
        last_login (Optional[datetime]): Fecha del último inicio de sesión.
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


class CurrentUserResponse(BaseModel):
    """Esquema de respuesta para el usuario actual autenticado.

    Incluye permisos además de los datos básicos.

    Attributes:
        id (int): ID del usuario.
        username (str): Nombre de usuario.
        email (str): Correo electrónico.
        role (str): Rol del usuario.
        is_active (bool): Estado de activación.
        created_at (datetime): Fecha de creación.
        updated_at (datetime): Fecha de última actualización.
        last_login (Optional[datetime]): Fecha del último inicio de sesión.
        permissions (List[str]): Lista de permisos asignados.
    """

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
    """Esquema de respuesta para un log de auditoría.

    Attributes:
        id (int): ID del log.
        user_id (Optional[int]): ID del usuario (si aplica).
        username (Optional[str]): Nombre de usuario (si aplica).
        action (str): Acción realizada.
        resource_type (Optional[str]): Tipo de recurso afectado.
        resource_id (Optional[str]): ID del recurso afectado.
        ip_address (Optional[str]): Dirección IP.
        user_agent (Optional[str]): User Agent.
        details (Optional[str]): Detalles adicionales.
        timestamp (datetime): Fecha y hora del evento.
        success (bool): Si la acción fue exitosa.
        error_message (Optional[str]): Mensaje de error (si falló).
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


class AuditLogListResponse(BaseModel):
    """Esquema de respuesta para una lista paginada de logs.

    Attributes:
        logs (List[AuditLogResponse]): Lista de logs.
        total (int): Total de registros encontrados.
        limit (int): Límite de paginación usado.
        offset (int): Offset de paginación usado.
    """

    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int
