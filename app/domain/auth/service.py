"""
Service Layer para Auth - Lógica de negocio de autenticación

Contiene todas las reglas de negocio de autenticación y autorización.
Depende de la INTERFAZ IAuthRepository, no de una implementación concreta.

Responsabilidades:
- Password hashing/verification con bcrypt
- JWT token generation/validation
- User authentication (login, refresh)
- User management (CRUD)
- Authorization (role-based permissions)
- Audit logging

Seguridad crítica:
- NUNCA retornar password_hash al cliente
- SIEMPRE hashear passwords con bcrypt
- Validar tokens en cada petición protegida
- Registrar intentos de login fallidos
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

# JWT and password hashing
from jose import JWTError, jwt
from passlib.context import CryptContext

from .ports import IAuthRepository
from .schemas import AdminUserCreate, AdminUserUpdate
from app.config.settings import settings
from app.core.logger import logger


# Configurar bcrypt para hashing de passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Servicio de lógica de negocio para autenticación.

    IMPORTANTE: Recibe el repository por Dependency Injection.
    No sabe si es MySQL, PostgreSQL o un Mock - solo usa la interfaz.
    """

    # Definición de permisos por rol
    ROLE_PERMISSIONS = {
        "admin": [
            # Players
            "view_players",
            "edit_players",
            "delete_players",
            # Games
            "view_games",
            "edit_games",
            "delete_games",
            # Events
            "view_events",
            "edit_events",
            "delete_events",
            # Admins
            "view_admins",
            "create_admins",
            "edit_admins",
            "delete_admins",
            # Audit
            "view_audit_logs",
        ],
        "support": [
            # Players
            "view_players",
            "edit_players",
            # Games
            "view_games",
            "edit_games",
            # Events
            "view_events",
            "edit_events",
            # Audit (solo sus propios logs)
            "view_audit_logs",
        ],
        "viewer": [
            # Solo lectura
            "view_players",
            "view_games",
            "view_events",
        ],
    }

    def __init__(self, repository: IAuthRepository):
        """
        Inicializa el servicio con un repositorio.

        Args:
            repository: Implementación de IAuthRepository (inyectada)
        """
        self.repository = repository

    # ==================== Password Hashing ====================

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashea un password usando bcrypt.

        Args:
            password: Password en texto plano

        Returns:
            Hash bcrypt del password
        """
        return pwd_context.hash(password, rounds=settings.bcrypt_rounds)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica que un password coincida con su hash.

        Args:
            plain_password: Password en texto plano
            hashed_password: Hash bcrypt del password

        Returns:
            True si coinciden, False si no
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ==================== JWT Token Management ====================

    def create_access_token(self, user_id: int, username: str, role: str) -> str:
        """
        Crea un JWT access token.

        Args:
            user_id: ID del usuario
            username: Username del usuario
            role: Rol del usuario

        Returns:
            JWT token firmado
        """
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )

        payload = {
            "type": "access",
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return token

    def create_refresh_token(self, user_id: int, username: str) -> str:
        """
        Crea un JWT refresh token.

        Args:
            user_id: ID del usuario
            username: Username del usuario

        Returns:
            JWT refresh token firmado
        """
        expire = datetime.utcnow() + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )

        payload = {
            "type": "refresh",
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )

        return token

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verifica y decodifica un JWT token.

        Args:
            token: JWT token a verificar
            token_type: Tipo esperado ("access" o "refresh")

        Returns:
            Payload del token si es válido

        Raises:
            JWTError: Si el token es inválido, expiró, o es del tipo incorrecto
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )

            # Verificar que sea del tipo correcto
            if payload.get("type") != token_type:
                raise JWTError(f"Token tipo '{payload.get('type')}', esperado '{token_type}'")

            return payload

        except JWTError as e:
            logger.warning(f"Token inválido: {e}")
            raise

    # ==================== Authentication ====================

    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Autentica un usuario con username y password.

        Args:
            username: Username del administrador
            password: Password en texto plano
            ip_address: IP del cliente (para audit log)
            user_agent: User agent del cliente (para audit log)

        Returns:
            Dict con access_token, refresh_token y datos del usuario

        Raises:
            ValueError: Si las credenciales son inválidas o el usuario está desactivado
        """
        # Buscar usuario
        user = self.repository.get_user_by_username(username)

        if not user:
            # Registrar intento fallido
            self.repository.create_audit_log(
                user_id=None,
                username=username,
                action="login_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Usuario no existe"
            )
            raise ValueError("Credenciales inválidas")

        # Verificar password
        if not self.verify_password(password, user["password_hash"]):
            # Registrar intento fallido
            self.repository.create_audit_log(
                user_id=user["id"],
                username=username,
                action="login_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Password incorrecto"
            )
            raise ValueError("Credenciales inválidas")

        # Verificar que el usuario esté activo
        if not user["is_active"]:
            # Registrar intento fallido
            self.repository.create_audit_log(
                user_id=user["id"],
                username=username,
                action="login_failed",
                ip_address=ip_address,
                user_agent=user_agent,
                success=False,
                error_message="Usuario desactivado"
            )
            raise ValueError("Usuario desactivado")

        # Actualizar último login
        self.repository.update_last_login(user["id"])

        # Generar tokens
        access_token = self.create_access_token(
            user["id"],
            user["username"],
            user["role"]
        )
        refresh_token = self.create_refresh_token(
            user["id"],
            user["username"]
        )

        # Registrar login exitoso
        self.repository.create_audit_log(
            user_id=user["id"],
            username=username,
            action="login_success",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        logger.info(f"Login exitoso: {username}")

        # Retornar tokens y datos del usuario (sin password_hash)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,  # en segundos
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            }
        }

    def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Renueva un access token usando un refresh token.

        Args:
            refresh_token: Refresh token válido
            ip_address: IP del cliente (para audit log)
            user_agent: User agent del cliente (para audit log)

        Returns:
            Dict con nuevo access_token y refresh_token

        Raises:
            JWTError: Si el refresh token es inválido
            ValueError: Si el usuario no existe o está desactivado
        """
        # Verificar refresh token
        payload = self.verify_token(refresh_token, token_type="refresh")

        # Obtener usuario
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")

        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        # Generar nuevos tokens
        new_access_token = self.create_access_token(
            user["id"],
            user["username"],
            user["role"]
        )
        new_refresh_token = self.create_refresh_token(
            user["id"],
            user["username"]
        )

        # Registrar renovación de token
        self.repository.create_audit_log(
            user_id=user["id"],
            username=user["username"],
            action="token_refresh",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        logger.debug(f"Token renovado: {user['username']}")

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    def get_current_user(self, token: str) -> Dict[str, Any]:
        """
        Obtiene el usuario actual desde un access token.

        Args:
            token: Access token JWT

        Returns:
            Dict con datos del usuario y sus permisos

        Raises:
            JWTError: Si el token es inválido
            ValueError: Si el usuario no existe o está desactivado
        """
        # Verificar access token
        payload = self.verify_token(token, token_type="access")

        # Obtener usuario actualizado de la BD
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")

        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        # Añadir permisos
        permissions = self.get_role_permissions(user["role"])

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "last_login": user["last_login"],
            "permissions": permissions,
        }

    # ==================== User Management ====================

    def create_admin(
        self,
        admin_data: AdminUserCreate,
        created_by_user_id: Optional[int] = None,
        created_by_username: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un nuevo usuario administrador.

        Args:
            admin_data: Datos del admin a crear
            created_by_user_id: ID del admin que crea (para audit)
            created_by_username: Username del admin que crea (para audit)
            ip_address: IP del cliente (para audit log)

        Returns:
            Dict con datos del admin creado (sin password_hash)

        Raises:
            ValueError: Si username o email ya existen
        """
        # Hashear password
        password_hash = self.hash_password(admin_data.password)

        # Crear usuario
        user = self.repository.create_admin_user(
            username=admin_data.username,
            email=admin_data.email,
            password_hash=password_hash,
            role=admin_data.role
        )

        # Registrar en audit log
        self.repository.create_audit_log(
            user_id=created_by_user_id,
            username=created_by_username,
            action="create_admin_user",
            resource_type="admin_user",
            resource_id=str(user["id"]),
            ip_address=ip_address,
            details=json.dumps({"new_username": user["username"], "role": user["role"]}),
            success=True
        )

        logger.info(f"Admin creado: {user['username']} por {created_by_username}")
        return user

    def update_admin(
        self,
        user_id: int,
        admin_update: AdminUserUpdate,
        updated_by_user_id: Optional[int] = None,
        updated_by_username: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un usuario administrador.

        Args:
            user_id: ID del usuario a actualizar
            admin_update: Campos a actualizar
            updated_by_user_id: ID del admin que actualiza (para audit)
            updated_by_username: Username del admin que actualiza (para audit)
            ip_address: IP del cliente (para audit log)

        Returns:
            Dict con datos actualizados si existe, None si no

        Raises:
            ValueError: Si el email ya existe
        """
        user = self.repository.update_user(
            user_id=user_id,
            email=admin_update.email,
            role=admin_update.role,
            is_active=admin_update.is_active
        )

        if user:
            # Registrar en audit log
            self.repository.create_audit_log(
                user_id=updated_by_user_id,
                username=updated_by_username,
                action="update_admin_user",
                resource_type="admin_user",
                resource_id=str(user_id),
                ip_address=ip_address,
                details=json.dumps(admin_update.model_dump(exclude_none=True)),
                success=True
            )

            logger.info(f"Admin actualizado: ID {user_id} por {updated_by_username}")

        return user

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Cambia el password de un usuario.

        Args:
            user_id: ID del usuario
            old_password: Password actual en texto plano
            new_password: Nuevo password en texto plano
            ip_address: IP del cliente (para audit log)

        Returns:
            True si se cambió, False si el old_password es incorrecto

        Raises:
            ValueError: Si el usuario no existe
        """
        # Obtener usuario
        user = self.repository.get_user_by_id(user_id)

        if not user:
            raise ValueError("Usuario no existe")

        # Verificar old_password
        if not self.verify_password(old_password, user["password_hash"]):
            # Registrar intento fallido
            self.repository.create_audit_log(
                user_id=user_id,
                username=user["username"],
                action="change_password",
                ip_address=ip_address,
                success=False,
                error_message="Password actual incorrecto"
            )
            return False

        # Hashear nuevo password
        new_password_hash = self.hash_password(new_password)

        # Actualizar
        success = self.repository.update_password(user_id, new_password_hash)

        if success:
            # Registrar cambio exitoso
            self.repository.create_audit_log(
                user_id=user_id,
                username=user["username"],
                action="change_password",
                ip_address=ip_address,
                success=True
            )

            logger.info(f"Password cambiado: {user['username']}")

        return success

    def list_admins(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Lista usuarios administradores con filtros opcionales.

        Args:
            role: Filtrar por rol (opcional)
            is_active: Filtrar por estado activo (opcional)
            limit: Número máximo de usuarios a retornar

        Returns:
            Lista de dicts con datos de usuarios (sin password_hash)
        """
        return self.repository.list_users(role=role, is_active=is_active, limit=limit)

    def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un admin por ID (sin password_hash).

        Args:
            user_id: ID del usuario

        Returns:
            Dict con datos del usuario si existe, None si no
        """
        user = self.repository.get_user_by_id(user_id)

        if not user:
            return None

        # Remover password_hash antes de retornar
        user_copy = user.copy()
        user_copy.pop("password_hash", None)

        return user_copy

    # ==================== Authorization ====================

    @classmethod
    def get_role_permissions(cls, role: str) -> List[str]:
        """
        Obtiene los permisos de un rol.

        Args:
            role: Rol del usuario (admin | support | viewer)

        Returns:
            Lista de permisos permitidos para ese rol
        """
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        """
        Verifica si un rol tiene un permiso específico.

        Args:
            role: Rol del usuario
            permission: Permiso a verificar

        Returns:
            True si el rol tiene el permiso, False si no
        """
        role_permissions = cls.get_role_permissions(role)
        return permission in role_permissions

    # ==================== Audit Logging ====================

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Obtiene logs de auditoría con filtros y paginación.

        Args:
            user_id: Filtrar por usuario (opcional)
            action: Filtrar por acción (opcional)
            start_date: Fecha inicio del rango (opcional)
            end_date: Fecha fin del rango (opcional)
            success: Filtrar por resultado (opcional)
            limit: Número máximo de logs a retornar
            offset: Número de logs a saltar (paginación)

        Returns:
            Dict con logs, total, limit y offset
        """
        logs = self.repository.get_audit_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            success=success,
            limit=limit,
            offset=offset
        )

        total = self.repository.count_audit_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def audit_log(
        self,
        user_id: int,
        username: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un registro de auditoría.

        Helper method para crear audit logs desde el código.

        Args:
            user_id: ID del usuario
            username: Username del usuario
            action: Acción realizada
            resource_type: Tipo de recurso (opcional)
            resource_id: ID del recurso (opcional)
            ip_address: IP del cliente (opcional)
            user_agent: User agent del cliente (opcional)
            details: Detalles adicionales como dict (opcional)
            success: Si la acción fue exitosa
            error_message: Mensaje de error si falló (opcional)

        Returns:
            Dict con datos del log creado
        """
        # Serializar details a JSON
        details_json = json.dumps(details) if details else None

        return self.repository.create_audit_log(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details_json,
            success=success,
            error_message=error_message
        )
