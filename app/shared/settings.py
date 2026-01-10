"""
Configuración global de la aplicación

Gestiona variables de entorno y configuración de la aplicación.
Migrado desde app/config.py
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno"""

    # Aplicación
    app_name: str = "Triskel-API"
    debug: bool = True
    port: int = 8000
    environment: str = "development"  # development|staging|production

    # Firebase
    firebase_credentials_path: str = "config/firebase-credentials.json"
    firebase_credentials_json: Optional[str] = None  # Para Railway/Producción

    # MariaDB (preparado para futuro uso)
    mariadb_host: Optional[str] = None
    mariadb_port: int = 3306
    mariadb_database: Optional[str] = None
    mariadb_user: Optional[str] = None
    mariadb_password: Optional[str] = None

    # Seguridad
    secret_key: Optional[str] = None
    api_key: Optional[str] = None

    # CORS
    cors_origins: str = "*"  # Cambiar en producción

    # Logging
    log_level: str = "INFO"  # DEBUG|INFO|WARNING|ERROR|CRITICAL

    class Config:
        env_file = ".env"
        case_sensitive = False


# Instancia global de configuración
settings = Settings()
