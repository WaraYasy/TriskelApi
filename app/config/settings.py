"""
Configuración global de la aplicación

Gestiona variables de entorno y configuración de la aplicación.
Migrado desde app/config.py
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno"""

    # ==================== Aplicación ====================
    # Nombre de la aplicación (hardcodeado, no configurable)
    app_name: str = "Triskel-API"

    # Detección automática del entorno
    # Railway establece RAILWAY_ENVIRONMENT=production
    # Heroku establece DYNO
    environment: str = (
        "production"
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("DYNO")
        else "development"
    )

    # Puerto (Railway/Heroku lo proporcionan automáticamente con $PORT)
    port: int = int(os.getenv("PORT", "8000"))

    # Debug (automático: solo activo en desarrollo)
    @property
    def debug(self) -> bool:
        return self.environment == "development"

    # ==================== Firebase ====================
    # Path local para desarrollo (solo usado si no hay credenciales en base64)
    firebase_credentials_path: str = "config/firebase-credentials.json"

    # Base64 encoded credentials (RECOMENDADO para Railway/Producción)
    # Para generar: cat config/firebase-credentials.json | base64
    firebase_credentials_base64: Optional[str] = None

    # JSON crudo como string (alternativa, puede tener problemas con saltos de línea)
    firebase_credentials_json: Optional[str] = None

    # ==================== Base de Datos SQL ====================
    # Variables genéricas compatibles con PostgreSQL, MySQL, MariaDB
    db_host: Optional[str] = None
    db_port: int = 5432  # Puerto por defecto de PostgreSQL (MySQL usa 3306)
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None

    # ==================== Seguridad ====================
    # OBLIGATORIAS en producción - no tienen valor por defecto
    secret_key: str
    api_key: str

    # ==================== JWT (Auth de Administradores) ====================
    jwt_secret_key: (
        str  # Secret para firmar JWT tokens (DEBE ser diferente de SECRET_KEY)
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60  # 1 hora
    jwt_refresh_token_expire_days: int = 7  # 7 días

    # ==================== Password Hashing ====================
    bcrypt_rounds: int = (
        12  # Número de rounds para bcrypt (más rounds = más seguro pero más lento)
    )

    # ==================== CORS ====================
    # Orígenes permitidos (separados por comas)
    # En desarrollo: permite todo (*)
    # En producción: debe especificarse explícitamente
    @property
    def cors_origins(self) -> str:
        env_origins = os.getenv("CORS_ORIGINS", "")
        if self.environment == "production" and env_origins:
            return env_origins
        elif self.environment == "development":
            return "*"
        else:
            # Producción sin CORS_ORIGINS definido - modo restrictivo
            return ""

    # ==================== Logging ====================
    # Nivel de logs configurables por entorno
    @property
    def log_level(self) -> str:
        env_log_level = os.getenv("LOG_LEVEL", "")
        if env_log_level:
            return env_log_level.upper()
        # Defaults por entorno
        return "DEBUG" if self.environment == "development" else "INFO"

    # Directorio donde se guardarán los logs
    log_directory: str = "logs"

    # Formato de logs: "json" para producción, "text" para desarrollo
    @property
    def log_format(self) -> str:
        env_format = os.getenv("LOG_FORMAT", "")
        if env_format:
            return env_format.lower()
        # JSON en producción, texto en desarrollo
        return "json" if self.environment == "production" else "text"

    # Rotación por tamaño: tamaño máximo de cada archivo de log (en MB)
    log_max_file_size_mb: int = 10

    # Número de archivos de backup a mantener
    log_backup_count: int = 5

    # Rotación por tiempo: días antes de rotar el archivo
    log_rotation_days: int = 7

    # Activar logs a archivo (además de consola)
    @property
    def log_to_file(self) -> bool:
        return os.getenv("LOG_TO_FILE", "true").lower() == "true"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validación de seguridad en producción
        if self.environment == "production":
            if not self.secret_key or self.secret_key == "":
                raise ValueError("SECRET_KEY es obligatoria en producción")
            if not self.api_key or self.api_key == "":
                raise ValueError("API_KEY es obligatoria en producción")
            if not self.jwt_secret_key or self.jwt_secret_key == "":
                raise ValueError("JWT_SECRET_KEY es obligatoria en producción")
            if (
                not self.firebase_credentials_base64
                and not self.firebase_credentials_json
            ):
                raise ValueError(
                    "FIREBASE_CREDENTIALS_BASE64 o FIREBASE_CREDENTIALS_JSON "
                    "son obligatorias en producción"
                )


# Instancia global de configuración
settings = Settings()
