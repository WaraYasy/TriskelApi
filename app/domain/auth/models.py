"""
Modelos de dominio para Auth

TODO: Implementar modelos de autenticación de administradores.

Estos modelos se guardarán en MariaDB (base de datos SQL).
Son para el equipo de soporte, no para jugadores.

Modelos sugeridos:
class AdminUser(Base):  # SQLAlchemy model
    __tablename__ = "admin_users"
    id: int
    username: str
    email: str
    password_hash: str  # NUNCA guardar password plano
    role: str  # "admin" | "support" | "viewer"
    created_at: datetime
    is_active: bool

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: int
    user_id: int
    action: str  # "login", "view_player", "delete_game", etc.
    timestamp: datetime
    ip_address: str
    details: str  # JSON con info adicional
"""
pass
