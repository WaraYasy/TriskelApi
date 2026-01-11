"""
Ports (Interfaces) del dominio Auth

Define el CONTRATO que debe cumplir cualquier repositorio de Auth.
El Service solo conoce esta interfaz, no la implementación concreta.

Este dominio usa arquitectura HEXAGONAL porque:
- Usa MySQL (diferente a Firestore usado en Players/Games)
- Podrías cambiar a PostgreSQL, OAuth externo, o LDAP
- Testing con mocks es crítico para seguridad
- Desacopla lógica de negocio de persistencia
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime


class IAuthRepository(ABC):
    """
    Interfaz que define las operaciones de persistencia para Auth.

    Cualquier implementación (MySQL, PostgreSQL, Mock) debe
    implementar todos estos métodos.
    """

    # ==================== Admin User Management ====================

    @abstractmethod
    def create_admin_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: str = "viewer"
    ) -> Dict[str, Any]:
        """
        Crea y guarda un nuevo usuario administrador.

        Args:
            username: Nombre de usuario único
            email: Email único del administrador
            password_hash: Hash bcrypt del password (NUNCA password plano)
            role: Rol del admin (admin | support | viewer)

        Returns:
            Dict con datos del usuario creado (sin password_hash)

        Raises:
            ValueError: Si username o email ya existen
        """
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su ID.

        Args:
            user_id: ID único del administrador

        Returns:
            Dict con datos del usuario (con password_hash) si existe, None si no
        """
        pass

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su username.

        Args:
            username: Username del administrador

        Returns:
            Dict con datos del usuario (con password_hash) si existe, None si no
        """
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Busca un admin por su email.

        Args:
            email: Email del administrador

        Returns:
            Dict con datos del usuario (con password_hash) si existe, None si no
        """
        pass

    @abstractmethod
    def update_last_login(self, user_id: int) -> None:
        """
        Actualiza el timestamp de último login.

        Args:
            user_id: ID del usuario que acaba de hacer login
        """
        pass

    @abstractmethod
    def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza campos de un usuario administrador.

        Args:
            user_id: ID del usuario a actualizar
            email: Nuevo email (opcional)
            role: Nuevo rol (opcional)
            is_active: Nuevo estado (opcional)

        Returns:
            Dict con datos actualizados si existe, None si no
        """
        pass

    @abstractmethod
    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        """
        Actualiza el password hash de un usuario.

        Args:
            user_id: ID del usuario
            new_password_hash: Nuevo hash bcrypt del password

        Returns:
            True si se actualizó, False si el usuario no existe
        """
        pass

    @abstractmethod
    def deactivate_user(self, user_id: int) -> bool:
        """
        Desactiva un usuario (soft delete).

        Args:
            user_id: ID del usuario a desactivar

        Returns:
            True si se desactivó, False si no existía
        """
        pass

    @abstractmethod
    def list_users(
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
        pass

    # ==================== Audit Log Management ====================

    @abstractmethod
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
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea un registro de auditoría.

        Args:
            user_id: ID del usuario que realizó la acción (None para sistema)
            username: Username del usuario (denormalizado)
            action: Acción realizada (login_success, export_players_csv, etc.)
            resource_type: Tipo de recurso afectado (player, game, etc.)
            resource_id: ID del recurso afectado
            ip_address: IP desde donde se realizó la acción
            user_agent: User agent del cliente
            details: JSON string con detalles adicionales
            success: Si la acción fue exitosa
            error_message: Mensaje de error si falló

        Returns:
            Dict con datos del log creado
        """
        pass

    @abstractmethod
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtiene logs de auditoría con filtros opcionales.

        Args:
            user_id: Filtrar por usuario (opcional)
            action: Filtrar por tipo de acción (opcional)
            start_date: Fecha inicio del rango (opcional)
            end_date: Fecha fin del rango (opcional)
            success: Filtrar por resultado (opcional)
            limit: Número máximo de logs a retornar
            offset: Número de logs a saltar (paginación)

        Returns:
            Lista de dicts con datos de logs
        """
        pass

    @abstractmethod
    def count_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Cuenta logs de auditoría con filtros opcionales.

        Args:
            user_id: Filtrar por usuario (opcional)
            action: Filtrar por tipo de acción (opcional)
            start_date: Fecha inicio del rango (opcional)
            end_date: Fecha fin del rango (opcional)

        Returns:
            Número total de logs que cumplen los filtros
        """
        pass
