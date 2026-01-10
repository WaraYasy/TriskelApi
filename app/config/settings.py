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
    environment: str = "production" if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("DYNO") else "development"

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

    # ==================== Base de Datos (MariaDB - Futuro) ====================
    mariadb_host: Optional[str] = None
    mariadb_port: int = 3306
    mariadb_database: Optional[str] = None
    mariadb_user: Optional[str] = None
    mariadb_password: Optional[str] = None

    # ==================== Seguridad ====================
    # OBLIGATORIAS en producción - no tienen valor por defecto
    secret_key: str
    api_key: str

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
            if not self.firebase_credentials_base64 and not self.firebase_credentials_json:
                raise ValueError(
                    "FIREBASE_CREDENTIALS_BASE64 o FIREBASE_CREDENTIALS_JSON "
                    "son obligatorias en producción"
                )


# Instancia global de configuración
settings = Settings()
