from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
from jose import JWTError, jwt

from app.config.settings import settings

from .ports import IAuthRepository
from .schemas import AdminUserCreate, AdminUserUpdate
from .validators import PasswordValidator


class AuthService:
    """Servicio de dominio para autenticación y usuarios.

    Maneja la lógica de negocio de:
    - Login y generación de JWT.
    - Refresh tokens.
    - CRUD de administradores.
    - Auditoría.
    """

    ROLE_PERMISSIONS = {
        "admin": [
            "view_players",
            "edit_players",
            "delete_players",
            "view_games",
            "edit_games",
            "delete_games",
            "view_events",
            "edit_events",
            "delete_events",
            "view_admins",
            "create_admins",
            "edit_admins",
            "delete_admins",
            "view_audit_logs",
        ],
        "support": [
            "view_players",
            "edit_players",
            "view_games",
            "edit_games",
            "view_events",
            "edit_events",
            "view_audit_logs",
        ],
        "viewer": [
            "view_players",
            "view_games",
            "view_events",
        ],
    }

    def __init__(self, repository: IAuthRepository):
        """Inicializa el servicio.

        Args:
            repository (IAuthRepository): Repositorio inyectado.
        """
        self.repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de contraseña usando bcrypt.

        Args:
            password (str): Contraseña plana.

        Returns:
            str: Hash bcrypt.

        Raises:
            ValueError: Si la contraseña excede longitud máxima.
        """
        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError(f"Password no puede exceder {PasswordValidator.MAX_LENGTH} caracteres")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña contra su hash.

        Args:
            plain_password (str): Contraseña plana.
            hashed_password (str): Hash bcrypt.

        Returns:
            bool: True si coinciden.
        """
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, user_id: int, username: str, role: str) -> str:
        """Crea un JWT de acceso.

        Args:
            user_id (int): ID del usuario.
            username (str): Nombre de usuario.
            role (str): Rol del usuario.

        Returns:
            str: Token JWT codificado.
        """
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "type": "access",
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def create_refresh_token(self, user_id: int, username: str) -> str:
        """Crea un JWT de refresco (larga duración).

        Args:
            user_id (int): ID del usuario.
            username (str): Nombre de usuario.

        Returns:
            str: Token JWT codificado.
        """
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        payload = {
            "type": "refresh",
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Decodifica y valida un JWT.

        Args:
            token (str): El token JWT.
            token_type (str): Tipo esperado ("access" o "refresh").

        Returns:
            Dict[str, Any]: Payload del token.

        Raises:
            JWTError: Si el token es inválido o expirado.
        """
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != token_type:
            raise JWTError(f"Token tipo '{payload.get('type')}', esperado '{token_type}'")
        return payload

    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Autentica un usuario y genera tokens.

        Args:
            username (str): Nombre de usuario.
            password (str): Contraseña.
            ip_address (Optional[str]): IP del cliente.
            user_agent (Optional[str]): User Agent del cliente.

        Returns:
            Dict[str, Any]: Dict con tokens y datos del usuario.

        Raises:
            ValueError: Si las credenciales son inválidas o usuario inactivo.
        """
        username = username.strip()

        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError("Password inválido")

        user = self.repository.get_user_by_username(username)
        if not user:
            raise ValueError("Credenciales inválidas")

        if not self.verify_password(password, user["password_hash"]):
            raise ValueError("Credenciales inválidas")

        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        self.repository.update_last_login(user["id"])

        access_token = self.create_access_token(user["id"], user["username"], user["role"])
        refresh_token = self.create_refresh_token(user["id"], user["username"])

        self.repository.create_audit_log(
            user_id=user["id"],
            username=username,
            action="login_success",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            },
        }

    def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Renueva el token de acceso usando un refresh token.

        Args:
            refresh_token (str): Token de refresco.
            ip_address (Optional[str]): IP del cliente.
            user_agent (Optional[str]): User Agent.

        Returns:
            Dict[str, Any]: Nuevos tokens.

        Raises:
            ValueError: Si usuario no existe o inactivo.
        """
        payload = self.verify_token(refresh_token, token_type="refresh")
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")
        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        new_access_token = self.create_access_token(user["id"], user["username"], user["role"])
        new_refresh_token = self.create_refresh_token(user["id"], user["username"])

        # Registrar renovación de token en audit log
        self.repository.create_audit_log(
            user_id=user["id"],
            username=user["username"],
            action="token_refresh",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    def get_current_user(self, token: str) -> Dict[str, Any]:
        """Obtiene el usuario actual desde un token de acceso.

        Args:
            token (str): Access token.

        Returns:
            Dict[str, Any]: Datos del usuario con permisos.

        Raises:
            ValueError: Si usuario no existe o inactivo.
        """
        payload = self.verify_token(token, token_type="access")
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")
        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "last_login": user["last_login"],
            "permissions": self.get_role_permissions(user["role"]),
        }

    def create_admin(self, admin_data: AdminUserCreate) -> Dict[str, Any]:
        """Crea un nuevo administrador (hash password primero).

        Args:
            admin_data (AdminUserCreate): Datos del nuevo admin.

        Returns:
            Dict[str, Any]: Usuario creado.
        """
        password_hash = self.hash_password(admin_data.password)
        return self.repository.create_admin_user(
            username=admin_data.username,
            email=admin_data.email,
            password_hash=password_hash,
            role=admin_data.role,
        )

    def update_admin(self, user_id: int, admin_update: AdminUserUpdate) -> Optional[Dict[str, Any]]:
        """Actualiza un administrador existente.

        Args:
            user_id (int): ID del usuario.
            admin_update (AdminUserUpdate): Datos a actualizar.

        Returns:
            Optional[Dict[str, Any]]: Usuario actualizado o None.
        """
        return self.repository.update_user(
            user_id=user_id,
            email=admin_update.email,
            role=admin_update.role,
            is_active=admin_update.is_active,
        )

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Cambia la contraseña de un usuario.

        Args:
            user_id (int): ID del usuario.
            old_password (str): Contraseña actual.
            new_password (str): Nueva contraseña.
            ip_address (Optional[str]): IP para auditoría.

        Returns:
            bool: True si tuvo éxito.
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("Usuario no existe")

        if not self.verify_password(old_password, user["password_hash"]):
            return False

        new_password_hash = self.hash_password(new_password)
        success = self.repository.update_password(user_id, new_password_hash)

        if success:
            self.repository.create_audit_log(
                user_id=user_id,
                username=user["username"],
                action="change_password",
                ip_address=ip_address,
                success=True,
            )

        return success

    def list_admins(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Lista usuarios administradores.

        Args:
            role (Optional[str]): Filtro por rol.
            is_active (Optional[bool]): Filtro por estado.
            limit (int): Límite de resultados.

        Returns:
            List[Dict[str, Any]]: Lista de usuarios.
        """
        return self.repository.list_users(role=role, is_active=is_active, limit=limit)

    def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene un administrador por ID (sin hash de password).

        Args:
            user_id (int): ID del usuario.

        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None.
        """
        user = self.repository.get_user_by_id(user_id)
        if not user:
            return None
        user_copy = user.copy()
        user_copy.pop("password_hash", None)
        return user_copy

    @classmethod
    def get_role_permissions(cls, role: str) -> List[str]:
        """Obtiene lista de permisos para un rol.

        Args:
            role (str): Rol del usuario.

        Returns:
            List[str]: Lista de permisos (strings).
        """
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        """Verifica si un rol tiene un permiso específico.

        Args:
            role (str): Rol del usuario.
            permission (str): Permiso a verificar.

        Returns:
            bool: True si tiene permiso.
        """
        return permission in cls.get_role_permissions(role)

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Obtiene logs de auditoría con paginación.

        Args:
            user_id (Optional[int]): Filtro por usuario.
            action (Optional[str]): Filtro por acción.
            start_date (Optional[datetime]): Inicio rango fecha.
            end_date (Optional[datetime]): Fin rango fecha.
            success (Optional[bool]): Filtro por éxito.
            limit (int): Límite.
            offset (int): Desplazamiento.

        Returns:
            Dict[str, Any]: {logs: [], total: int}.
        """
        logs = self.repository.get_audit_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            success=success,
            limit=limit,
            offset=offset,
        )
        total = self.repository.count_audit_logs(
            user_id=user_id, action=action, start_date=start_date, end_date=end_date
        )
        return {"logs": logs, "total": total, "limit": limit, "offset": offset}
