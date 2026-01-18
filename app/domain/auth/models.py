"""
Modelos SQLAlchemy para Auth

Define las tablas SQL para:
- AdminUser: Usuarios administradores del sistema
- AuditLog: Logs de auditoría de acciones administrativas

Compatible con PostgreSQL, MySQL, MariaDB.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.infrastructure.database.sql_client import Base


class AdminUser(Base):
    """
    Usuario administrador del sistema.

    Tabla: admin_users

    Roles disponibles:
    - admin: Control total del sistema (CRUD admins, exports, etc.)
    - support: Acceso a jugadores/partidas para soporte (sin CRUD admins)
    - viewer: Solo lectura (analytics, sin modificaciones)
    """

    __tablename__ = "admin_users"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Credenciales
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # bcrypt hash

    # Autorización
    role = Column(
        String(20), nullable=False, default="viewer", index=True
    )  # admin | support | viewer

    # Estado
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}', role='{self.role}', active={self.is_active})>"


class AuditLog(Base):
    """
    Registro de auditoría de acciones administrativas.

    Tabla: audit_logs

    Registra específicamente:
    - Autenticación: login_success, login_failed, logout, token_refresh, change_password
    - Exportaciones: export_players_csv, export_games_csv, export_events_csv, etc.

    NO registra acciones de CRUD normales (view_player, edit_player, etc.)
    según especificación del usuario.
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Usuario que realiza la acción (nullable para acciones del sistema)
    user_id = Column(
        Integer,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    username = Column(String(50), nullable=True)  # Denormalizado para queries rápidas

    # Acción realizada
    action = Column(String(100), nullable=False, index=True)
    # Ejemplos: login_success, login_failed, logout, export_players_csv, etc.

    # Recurso afectado (opcional)
    resource_type = Column(String(50), nullable=True)  # player, game, event, admin_user
    resource_id = Column(String(100), nullable=True)  # ID del recurso

    # Contexto de la petición
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Detalles adicionales (JSON serializado como string)
    details = Column(Text, nullable=True)
    # Ejemplo: {"count": 150, "filters": {}, "format": "csv"}

    # Timestamp
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Resultado
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user='{self.username}', timestamp={self.timestamp})>"
