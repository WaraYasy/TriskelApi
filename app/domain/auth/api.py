"""
API REST para Auth

Endpoints de FastAPI para autenticación y gestión de administradores.
Usa Dependency Injection para desacoplar de implementaciones concretas.

Reglas de acceso:
- POST /v1/auth/login: Público (autenticación)
- POST /v1/auth/refresh: Público (renovar token)
- POST /v1/auth/logout: Requiere JWT (logout con audit log)
- GET /v1/auth/me: Requiere JWT (info usuario actual)
- POST /v1/auth/change-password: Requiere JWT (cambiar password propio)
- POST /v1/auth/admin/users: Requiere JWT + permiso create_admins
- GET /v1/auth/admin/users: Requiere JWT + permiso view_admins
- PATCH /v1/auth/admin/users/{id}: Requiere JWT + permiso edit_admins
- GET /v1/auth/admin/audit: Requiere JWT + permiso view_audit_logs
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from typing import List, Optional
from datetime import datetime
from jose import JWTError

from .ports import IAuthRepository
from .service import AuthService
from .schemas import (
    LoginRequest,
    RefreshTokenRequest,
    AdminUserCreate,
    AdminUserUpdate,
    ChangePasswordRequest,
    TokenResponse,
    AdminUserResponse,
    CurrentUserResponse,
    AuditLogResponse,
    AuditLogListResponse,
)
from .adapters.sql_repository import SQLAuthRepository
from app.infrastructure.database.sql_client import get_db_session
from sqlalchemy.orm import Session


# Router de FastAPI
router = APIRouter(prefix="/v1/auth", tags=["Auth"])


# ==================== DEPENDENCY INJECTION ====================

def get_auth_repository(db: Session = Depends(get_db_session)) -> IAuthRepository:
    """
    Dependency que provee el repositorio de Auth.

    Retorna la implementación concreta (SQL genérico).
    Si queremos cambiar a otra BD, solo cambiamos las credenciales.

    Args:
        db: Sesión de SQLAlchemy inyectada

    Returns:
        IAuthRepository: Implementación del repositorio
    """
    return SQLAuthRepository(session=db)


def get_auth_service(
    repository: IAuthRepository = Depends(get_auth_repository)
) -> AuthService:
    """
    Dependency que provee el servicio de Auth.

    Recibe el repository por inyección automática.

    Args:
        repository: Repositorio inyectado por FastAPI

    Returns:
        AuthService: Servicio configurado
    """
    return AuthService(repository=repository)


def get_current_admin(
    authorization: str = Header(..., description="Bearer token"),
    service: AuthService = Depends(get_auth_service)
) -> dict:
    """
    Dependency que extrae y valida el usuario actual desde el JWT.

    Args:
        authorization: Header Authorization con formato "Bearer <token>"
        service: Servicio de autenticación

    Returns:
        Dict con datos del usuario actual + permisos

    Raises:
        HTTPException 401: Si el token es inválido o falta
        HTTPException 403: Si el usuario está desactivado
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token inválido. Formato: 'Bearer <token>'"
        )

    token = authorization.replace("Bearer ", "")

    try:
        user = service.get_current_user(token)
        return user
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=403,
            detail=str(e)
        )


def require_permission(permission: str):
    """
    Factory que crea un dependency para verificar permisos específicos.

    Args:
        permission: Permiso requerido (ej: "create_admins")

    Returns:
        Dependency function que valida el permiso
    """
    def check_permission(current_user: dict = Depends(get_current_admin)) -> dict:
        """
        Verifica que el usuario actual tenga el permiso requerido.

        Args:
            current_user: Usuario actual inyectado

        Returns:
            Usuario actual si tiene permiso

        Raises:
            HTTPException 403: Si no tiene el permiso
        """
        if permission not in current_user.get("permissions", []):
            raise HTTPException(
                status_code=403,
                detail=f"Permiso '{permission}' requerido"
            )
        return current_user

    return check_permission


# ==================== HELPER FUNCTIONS ====================

def get_client_info(request: Request) -> tuple:
    """
    Extrae información del cliente para audit logs.

    Args:
        request: Request de FastAPI

    Returns:
        Tuple con (ip_address, user_agent)
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


# ==================== PUBLIC ENDPOINTS ====================

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """
    Login de administrador con username y password.

    Retorna access token (1 hora) y refresh token (7 días).

    Args:
        login_data: Credenciales (username + password)
        request: Request para extraer IP y user agent
        service: Servicio inyectado automáticamente

    Returns:
        TokenResponse: Tokens JWT + info del usuario

    Raises:
        HTTPException 401: Si las credenciales son inválidas
    """
    ip_address, user_agent = get_client_info(request)

    try:
        result = service.login(
            username=login_data.username,
            password=login_data.password,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"]
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service)
):
    """
    Renueva el access token usando un refresh token válido.

    Args:
        refresh_data: Refresh token
        request: Request para extraer IP y user agent
        service: Servicio inyectado automáticamente

    Returns:
        TokenResponse: Nuevos tokens JWT

    Raises:
        HTTPException 401: Si el refresh token es inválido
    """
    ip_address, user_agent = get_client_info(request)

    try:
        result = service.refresh_access_token(
            refresh_token=refresh_data.refresh_token,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"]
        )

    except (JWTError, ValueError) as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


# ==================== PROTECTED ENDPOINTS (Require JWT) ====================

@router.post("/logout")
def logout(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    service: AuthService = Depends(get_auth_service)
):
    """
    Logout del usuario actual.

    Registra el logout en audit log.
    Nota: Los tokens JWT son stateless, así que el logout solo crea un audit log.
    El cliente debe eliminar los tokens almacenados.

    Args:
        request: Request para extraer IP y user agent
        current_user: Usuario actual inyectado
        service: Servicio inyectado automáticamente

    Returns:
        Dict con mensaje de éxito
    """
    ip_address, user_agent = get_client_info(request)

    # Registrar logout en audit log
    service.audit_log(
        user_id=current_user["id"],
        username=current_user["username"],
        action="logout",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True
    )

    return {"message": "Logout exitoso"}


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(
    current_user: dict = Depends(get_current_admin)
):
    """
    Obtiene información del usuario actualmente autenticado.

    Incluye permisos basados en su rol.

    Args:
        current_user: Usuario actual inyectado

    Returns:
        CurrentUserResponse: Datos del usuario + permisos
    """
    return CurrentUserResponse(**current_user)


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_admin),
    service: AuthService = Depends(get_auth_service)
):
    """
    Cambia el password del usuario actual.

    Requiere password actual para seguridad.

    Args:
        password_data: Password actual y nuevo password
        request: Request para extraer IP
        current_user: Usuario actual inyectado
        service: Servicio inyectado automáticamente

    Returns:
        Dict con mensaje de éxito

    Raises:
        HTTPException 400: Si el password actual es incorrecto
    """
    ip_address, _ = get_client_info(request)

    success = service.change_password(
        user_id=current_user["id"],
        old_password=password_data.old_password,
        new_password=password_data.new_password,
        ip_address=ip_address
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Password actual incorrecto"
        )

    return {"message": "Password cambiado exitosamente"}


# ==================== ADMIN ENDPOINTS (Require Specific Permissions) ====================

@router.post("/admin/users", response_model=AdminUserResponse, status_code=201)
def create_admin_user(
    admin_data: AdminUserCreate,
    request: Request,
    current_user: dict = Depends(require_permission("create_admins")),
    service: AuthService = Depends(get_auth_service)
):
    """
    Crea un nuevo usuario administrador.

    Requiere permiso: create_admins (solo rol admin)

    Args:
        admin_data: Datos del nuevo admin
        request: Request para extraer IP
        current_user: Usuario actual (con permiso validado)
        service: Servicio inyectado automáticamente

    Returns:
        AdminUserResponse: Datos del admin creado

    Raises:
        HTTPException 400: Si username o email ya existen
        HTTPException 403: Si no tiene permiso
    """
    ip_address, _ = get_client_info(request)

    try:
        user = service.create_admin(
            admin_data=admin_data,
            created_by_user_id=current_user["id"],
            created_by_username=current_user["username"],
            ip_address=ip_address
        )

        return AdminUserResponse(**user)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/admin/users", response_model=List[AdminUserResponse])
def list_admin_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    current_user: dict = Depends(require_permission("view_admins")),
    service: AuthService = Depends(get_auth_service)
):
    """
    Lista usuarios administradores con filtros opcionales.

    Requiere permiso: view_admins (solo rol admin)

    Args:
        role: Filtrar por rol (opcional)
        is_active: Filtrar por estado activo (opcional)
        limit: Máximo número de usuarios a retornar
        current_user: Usuario actual (con permiso validado)
        service: Servicio inyectado automáticamente

    Returns:
        Lista de AdminUserResponse
    """
    users = service.list_admins(role=role, is_active=is_active, limit=limit)
    return [AdminUserResponse(**user) for user in users]


@router.get("/admin/users/{user_id}", response_model=AdminUserResponse)
def get_admin_user(
    user_id: int,
    current_user: dict = Depends(require_permission("view_admins")),
    service: AuthService = Depends(get_auth_service)
):
    """
    Obtiene un usuario administrador por ID.

    Requiere permiso: view_admins (solo rol admin)

    Args:
        user_id: ID del usuario a obtener
        current_user: Usuario actual (con permiso validado)
        service: Servicio inyectado automáticamente

    Returns:
        AdminUserResponse: Datos del admin

    Raises:
        HTTPException 404: Si el usuario no existe
    """
    user = service.get_admin(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return AdminUserResponse(**user)


@router.patch("/admin/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    admin_update: AdminUserUpdate,
    request: Request,
    current_user: dict = Depends(require_permission("edit_admins")),
    service: AuthService = Depends(get_auth_service)
):
    """
    Actualiza un usuario administrador.

    Requiere permiso: edit_admins (solo rol admin)

    Args:
        user_id: ID del usuario a actualizar
        admin_update: Campos a actualizar
        request: Request para extraer IP
        current_user: Usuario actual (con permiso validado)
        service: Servicio inyectado automáticamente

    Returns:
        AdminUserResponse: Datos actualizados

    Raises:
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si el email ya existe
    """
    ip_address, _ = get_client_info(request)

    try:
        user = service.update_admin(
            user_id=user_id,
            admin_update=admin_update,
            updated_by_user_id=current_user["id"],
            updated_by_username=current_user["username"],
            ip_address=ip_address
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )

        return AdminUserResponse(**user)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/admin/audit", response_model=AuditLogListResponse)
def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    success: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(require_permission("view_audit_logs")),
    service: AuthService = Depends(get_auth_service)
):
    """
    Obtiene logs de auditoría con filtros y paginación.

    Requiere permiso: view_audit_logs (admin y support)

    Args:
        user_id: Filtrar por usuario (opcional)
        action: Filtrar por acción (opcional)
        start_date: Fecha inicio del rango (opcional)
        end_date: Fecha fin del rango (opcional)
        success: Filtrar por resultado (opcional)
        limit: Número máximo de logs a retornar
        offset: Número de logs a saltar (paginación)
        current_user: Usuario actual (con permiso validado)
        service: Servicio inyectado automáticamente

    Returns:
        AuditLogListResponse: Logs paginados + total
    """
    result = service.get_audit_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        success=success,
        limit=limit,
        offset=offset
    )

    return AuditLogListResponse(
        logs=[AuditLogResponse(**log) for log in result["logs"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"]
    )
