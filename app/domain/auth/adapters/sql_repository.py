"""
Adaptador SQL para Auth

Implementación CONCRETA del repositorio usando SQLAlchemy + Base de Datos SQL.
Soporta PostgreSQL, MySQL, MariaDB, etc.
Implementa la interfaz IAuthRepository.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logger import logger

from ..models import AdminUser, AuditLog
from ..ports import IAuthRepository


class SQLAuthRepository(IAuthRepository):
    """
    Repositorio de Auth usando Base de Datos SQL con SQLAlchemy.

    Esta es la implementación real que habla con la base de datos.
    Soporta PostgreSQL, MySQL, MariaDB, etc.
    Implementa todos los métodos definidos en IAuthRepository.
    """

    def __init__(self, session: Session):
        """
        Inicializa el repositorio.

        Args:
            session: Sesión de SQLAlchemy para transacciones
        """
        self.session = session

    # ==================== Helper Methods ====================

    def _user_to_dict(self, user: AdminUser, include_password: bool = False) -> Dict[str, Any]:
        """
        Convierte un AdminUser ORM model a dict.

        Args:
            user: Modelo SQLAlchemy de AdminUser
            include_password: Si incluir password_hash (solo para autenticación interna)

        Returns:
            Dict con datos del usuario
        """
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "last_login": user.last_login,
        }

        if include_password:
            data["password_hash"] = user.password_hash

        return data

    def _log_to_dict(self, log: AuditLog) -> Dict[str, Any]:
        """
        Convierte un AuditLog ORM model a dict.

        Args:
            log: Modelo SQLAlchemy de AuditLog

        Returns:
            Dict con datos del log
        """
        return {
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "details": log.details,
            "timestamp": log.timestamp,
            "success": log.success,
            "error_message": log.error_message,
        }

    # ==================== Admin User Management ====================

    def create_admin_user(
        self, username: str, email: str, password_hash: str, role: str = "viewer"
    ) -> Dict[str, Any]:
        """
        Crea un nuevo usuario administrador.
        """
        try:
            user = AdminUser(
                username=username,
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True,
            )

            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)

            logger.info(f"Admin creado: {user.username} (role: {user.role})")
            return self._user_to_dict(user, include_password=False)

        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error creando admin (username/email duplicado): {e}")
            raise ValueError("Username o email ya existe")

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su ID.
        """
        user = self.session.query(AdminUser).filter_by(id=user_id).first()

        if not user:
            return None

        return self._user_to_dict(user, include_password=True)

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su username.
        """
        user = self.session.query(AdminUser).filter_by(username=username).first()

        if not user:
            return None

        return self._user_to_dict(user, include_password=True)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su email.
        """
        user = self.session.query(AdminUser).filter_by(email=email).first()

        if not user:
            return None

        return self._user_to_dict(user, include_password=True)

    def update_last_login(self, user_id: int) -> None:
        """
        Actualiza el timestamp de último login.
        """
        user = self.session.query(AdminUser).filter_by(id=user_id).first()

        if user:
            user.last_login = datetime.utcnow()
            self.session.commit()
            logger.debug(f"Last login actualizado para user {user_id}")

    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza campos de un usuario administrador.
        """
        user = self.session.query(AdminUser).filter_by(id=user_id).first()

        if not user:
            return None

        try:
            if email is not None:
                user.email = email
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active

            self.session.commit()
            self.session.refresh(user)

            logger.info(f"Admin actualizado: {user.username}")
            return self._user_to_dict(user, include_password=False)

        except IntegrityError as e:
            self.session.rollback()
            logger.error(f"Error actualizando admin (email duplicado): {e}")
            raise ValueError("Email ya existe")

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Actualiza el password hash de un usuario.
        """
        user = self.session.query(AdminUser).filter_by(id=user_id).first()

        if not user:
            return False

        user.password_hash = new_password_hash
        self.session.commit()

        logger.info(f"Password actualizado para user {user_id}")
        return True

    def deactivate_user(self, user_id: int) -> bool:
        """
        Desactiva un usuario (soft delete).
        """
        user = self.session.query(AdminUser).filter_by(id=user_id).first()

        if not user:
            return False

        user.is_active = False
        self.session.commit()

        logger.info(f"Admin desactivado: {user.username}")
        return True

    def list_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Lista usuarios administradores con filtros opcionales.
        """
        query = self.session.query(AdminUser)

        if role is not None:
            query = query.filter_by(role=role)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        users = query.limit(limit).all()

        return [self._user_to_dict(user, include_password=False) for user in users]

    # ==================== Audit Log Management ====================

    def create_audit_log(
        self,
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Crea un registro de auditoría.
        """
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            success=success,
            error_message=error_message,
        )

        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)

        logger.debug(f"Audit log creado: {action} por {username}")
        return self._log_to_dict(log)

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene logs de auditoría con filtros opcionales.
        """
        query = self.session.query(AuditLog)

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        if action is not None:
            query = query.filter_by(action=action)

        if start_date is not None:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.timestamp <= end_date)

        if success is not None:
            query = query.filter_by(success=success)

        # Ordenar por timestamp descendente (más recientes primero)
        query = query.order_by(AuditLog.timestamp.desc())

        # Paginación
        logs = query.limit(limit).offset(offset).all()

        return [self._log_to_dict(log) for log in logs]

    def count_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Cuenta logs de auditoría con filtros opcionales.
        """
        query = self.session.query(AuditLog)

        if user_id is not None:
            query = query.filter_by(user_id=user_id)

        if action is not None:
            query = query.filter_by(action=action)

        if start_date is not None:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date is not None:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.count()
