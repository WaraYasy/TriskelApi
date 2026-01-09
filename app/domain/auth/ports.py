"""
Ports (Interfaces) para Auth

TODO: Definir interfaz para repositorio de autenticación.

Este dominio usa arquitectura HEXAGONAL porque:
- Usa MariaDB (diferente a Firestore)
- Podrías cambiar a PostgreSQL o OAuth externo
- Testing con mocks es crítico para seguridad

Interfaz sugerida:
class IAuthRepository(ABC):
    @abstractmethod
    def create_user(username, email, password_hash) -> AdminUser

    @abstractmethod
    def get_user_by_username(username) -> Optional[AdminUser]

    @abstractmethod
    def validate_credentials(username, password) -> Optional[AdminUser]

    @abstractmethod
    def create_audit_log(user_id, action, ip) -> AuditLog

    @abstractmethod
    def get_audit_logs(filters) -> List[AuditLog]
"""
pass
