"""
Entorno de Alembic para migraciones de base de datos.

Conecta Alembic con la configuración de SQLAlchemy del proyecto.
Soporta modo online (conexión directa) y offline (genera SQL).
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Añadir el directorio raíz al path para importar módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config.settings import settings

# Importar modelos para que Alembic los detecte
from app.domain.auth.models import AdminUser, AuditLog  # noqa: F401
from app.infrastructure.database.sql_client import Base

# Configuración de Alembic
config = context.config

# Configurar logging desde alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de SQLAlchemy para autogenerate
target_metadata = Base.metadata


def get_database_url() -> str:
    """Construye la URL de conexión desde variables de entorno."""
    if not settings.db_host:
        raise ValueError(
            "Base de datos SQL no configurada. "
            "Define DB_HOST, DB_USER, DB_PASSWORD, DB_NAME en .env"
        )

    return (
        f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    )


def run_migrations_offline() -> None:
    """
    Ejecuta migraciones en modo 'offline'.

    Genera SQL sin conexión directa a la base de datos.
    Útil para revisar los cambios antes de aplicarlos.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Ejecuta migraciones en modo 'online'.

    Conecta directamente a la base de datos y aplica los cambios.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
