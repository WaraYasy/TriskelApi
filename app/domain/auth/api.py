from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from jose import JWTError
from sqlalchemy.orm import Session

from app.infrastructure.database.sql_client import get_db_session

from .adapters.sql_repository import SQLAuthRepository
from .ports import IAuthRepository
from .schemas import (
    AdminUserCreate,
    AdminUserResponse,
    AdminUserUpdate,
    AuditLogListResponse,
    AuditLogResponse,
    ChangePasswordRequest,
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from .service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


def get_auth_repository(db: Session = Depends(get_db_session)) -> IAuthRepository:
    """Inyecta el repositorio SQLAuthRepository.

    Args:
        db (Session): Sesión de base de datos.

    Returns:
        IAuthRepository: Repositorio instanciado.
    """
    return SQLAuthRepository(session=db)


def get_auth_service(
    repository: IAuthRepository = Depends(get_auth_repository),
) -> AuthService:
    """Inyecta el servicio AuthService.

    Args:
        repository (IAuthRepository): Repositorio inyectado.

    Returns:
        AuthService: Servicio instanciado.
    """
    return AuthService(repository=repository)


def get_current_admin(
    authorization: str = Header(...), service: AuthService = Depends(get_auth_service)
) -> dict:
    """Obtiene el administrador actual desde el token Bearer.

    Args:
        authorization (str): Header Authorization.
        service (AuthService): Servicio de autenticación.

    Returns:
        dict: Datos del usuario actual.

    Raises:
        HTTPException: Si el token es inválido, expirado o faltante.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")
    try:
        return service.get_current_user(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))


def require_permission(permission: str):
    """Dependencia para requerir un permiso específico.

    Args:
        permission (str): Permiso requerido.

    Returns:
        function: Función de dependencia.
    """

    def check_permission(current_user: dict = Depends(get_current_admin)) -> dict:
        if permission not in current_user.get("permissions", []):
            raise HTTPException(status_code=403, detail=f"Permiso '{permission}' requerido")
        return current_user

    return check_permission


def get_client_info(request: Request) -> tuple:
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    ip_address, user_agent = get_client_info(request)
    try:
        result = service.login(login_data.username, login_data.password, ip_address, user_agent)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )
    except ValueError as e:
        error_msg = str(e)
        if "72 caracteres" in error_msg:
            raise HTTPException(status_code=400, detail="Password excede longitud máxima")
        elif "Credenciales inválidas" in error_msg or "Password inválido" in error_msg:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        elif "desactivado" in error_msg.lower():
            raise HTTPException(status_code=403, detail="Usuario desactivado")
        else:
            raise HTTPException(status_code=400, detail=error_msg)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    ip_address, user_agent = get_client_info(request)
    try:
        result = service.refresh_access_token(refresh_data.refresh_token, ip_address, user_agent)
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            token_type=result["token_type"],
            expires_in=result["expires_in"],
        )
    except (JWTError, ValueError) as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(
    request: Request,
    current_user: dict = Depends(get_current_admin),
    service: AuthService = Depends(get_auth_service),
):
    ip_address, user_agent = get_client_info(request)
    service.repository.create_audit_log(
        user_id=current_user["id"],
        username=current_user["username"],
        action="logout",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
    )
    return {"message": "Logout exitoso"}


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_admin)):
    return CurrentUserResponse(**current_user)


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_admin),
    service: AuthService = Depends(get_auth_service),
):
    ip_address, _ = get_client_info(request)
    success = service.change_password(
        current_user["id"],
        password_data.old_password,
        password_data.new_password,
        ip_address,
    )
    if not success:
        raise HTTPException(status_code=400, detail="Password actual incorrecto")
    return {"message": "Password cambiado exitosamente"}


@router.post("/admin/users", response_model=AdminUserResponse, status_code=201)
def create_admin_user(
    admin_data: AdminUserCreate,
    current_user: dict = Depends(require_permission("create_admins")),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = service.create_admin(admin_data)
        return AdminUserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/users", response_model=List[AdminUserResponse])
def list_admin_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    current_user: dict = Depends(require_permission("view_admins")),
    service: AuthService = Depends(get_auth_service),
):
    users = service.list_admins(role=role, is_active=is_active, limit=limit)
    return [AdminUserResponse(**user) for user in users]


@router.get("/admin/users/{user_id}", response_model=AdminUserResponse)
def get_admin_user(
    user_id: int,
    current_user: dict = Depends(require_permission("view_admins")),
    service: AuthService = Depends(get_auth_service),
):
    user = service.get_admin(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return AdminUserResponse(**user)


@router.patch("/admin/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(
    user_id: int,
    admin_update: AdminUserUpdate,
    current_user: dict = Depends(require_permission("edit_admins")),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = service.update_admin(user_id, admin_update)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return AdminUserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    service: AuthService = Depends(get_auth_service),
):
    result = service.get_audit_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        success=success,
        limit=limit,
        offset=offset,
    )
    return AuditLogListResponse(
        logs=[AuditLogResponse(**log) for log in result["logs"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )
