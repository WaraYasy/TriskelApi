"""
Servicio de Migraciones

Proporciona funciones para gestionar migraciones de Alembic
desde el dashboard web.
"""

import io
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from app.config.settings import settings


@dataclass
class MigrationInfo:
    """Información de una migración."""

    revision: str
    description: str
    date: Optional[str]
    is_applied: bool


class MigrationService:
    """
    Servicio para gestionar migraciones de base de datos.

    Permite listar, aplicar y revertir migraciones desde código Python,
    sin necesidad de usar la línea de comandos de Alembic.
    """

    def __init__(self):
        """Inicializa el servicio con la configuración de Alembic."""
        self._alembic_cfg = None
        self._engine = None

    def _get_alembic_config(self) -> Config:
        """Obtiene la configuración de Alembic."""
        if self._alembic_cfg is None:
            # Ruta al directorio raíz del proyecto
            project_root = Path(__file__).resolve().parents[4]
            alembic_ini = project_root / "alembic.ini"

            self._alembic_cfg = Config(str(alembic_ini))
            self._alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

        return self._alembic_cfg

    def _get_engine(self):
        """Obtiene el engine de SQLAlchemy."""
        if self._engine is None:
            if not settings.db_host:
                raise ValueError("Base de datos SQL no configurada")

            db_url = (
                f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )
            self._engine = create_engine(db_url)

        return self._engine

    def is_database_configured(self) -> bool:
        """Verifica si la base de datos SQL está configurada."""
        return bool(settings.db_host)

    def get_current_revision(self) -> Optional[str]:
        """
        Obtiene la revisión actual de la base de datos.

        Returns:
            ID de la revisión actual o None si no hay migraciones aplicadas.
        """
        engine = self._get_engine()

        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            return context.get_current_revision()

    def get_migration_history(self) -> list[MigrationInfo]:
        """
        Obtiene el historial de todas las migraciones.

        Returns:
            Lista de MigrationInfo con todas las migraciones disponibles.
        """
        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)
        current = self.get_current_revision()

        migrations = []

        # Obtener todas las revisiones en orden
        for revision in script.walk_revisions():
            # Extraer fecha del nombre del archivo si existe
            date_str = None
            if revision.module.__file__:
                filename = os.path.basename(revision.module.__file__)
                # Formato: YYYYMMDD_HHMM_revision_slug.py
                if len(filename) > 8 and filename[:8].isdigit():
                    try:
                        date_str = datetime.strptime(filename[:8], "%Y%m%d").strftime("%Y-%m-%d")
                    except ValueError:
                        pass

            migrations.append(
                MigrationInfo(
                    revision=revision.revision,
                    description=revision.doc or "Sin descripción",
                    date=date_str,
                    is_applied=self._is_revision_applied(revision.revision, current),
                )
            )

        # Ordenar: más recientes primero
        migrations.reverse()
        return migrations

    def _is_revision_applied(self, revision: str, current: Optional[str]) -> bool:
        """
        Verifica si una revisión está aplicada.

        Una revisión está aplicada si es igual o anterior a la actual.
        """
        if current is None:
            return False

        config = self._get_alembic_config()
        script = ScriptDirectory.from_config(config)

        # Obtener la cadena de revisiones desde la actual hasta la base
        current_script = script.get_revision(current)
        if current_script is None:
            return False

        # Verificar si la revisión está en la cadena de aplicadas
        applied = {current}
        for rev in script.iterate_revisions(current, "base"):
            applied.add(rev.revision)

        return revision in applied

    def upgrade(self, revision: str = "head") -> dict:
        """
        Aplica migraciones hasta la revisión especificada.

        Args:
            revision: ID de revisión objetivo o "head" para la última.

        Returns:
            Diccionario con resultado de la operación.
        """
        try:
            config = self._get_alembic_config()
            before = self.get_current_revision()

            command.upgrade(config, revision)

            after = self.get_current_revision()

            return {
                "success": True,
                "message": f"Migración completada: {before or 'base'} -> {after}",
                "previous_revision": before,
                "current_revision": after,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al aplicar migración: {str(e)}",
                "error": str(e),
            }

    def downgrade(self, revision: str = "-1") -> dict:
        """
        Revierte migraciones hasta la revisión especificada.

        Args:
            revision: ID de revisión objetivo o "-1" para revertir una.

        Returns:
            Diccionario con resultado de la operación.
        """
        try:
            config = self._get_alembic_config()
            before = self.get_current_revision()

            command.downgrade(config, revision)

            after = self.get_current_revision()

            return {
                "success": True,
                "message": f"Rollback completado: {before} -> {after or 'base'}",
                "previous_revision": before,
                "current_revision": after,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al revertir migración: {str(e)}",
                "error": str(e),
            }

    def get_pending_migrations(self) -> list[MigrationInfo]:
        """
        Obtiene las migraciones pendientes de aplicar.

        Returns:
            Lista de migraciones no aplicadas.
        """
        all_migrations = self.get_migration_history()
        return [m for m in all_migrations if not m.is_applied]

    def get_database_status(self) -> dict:
        """
        Obtiene el estado actual de la base de datos.

        Returns:
            Diccionario con información del estado.
        """
        if not self.is_database_configured():
            return {
                "configured": False,
                "connected": False,
                "message": "Base de datos SQL no configurada",
            }

        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            current = self.get_current_revision()
            pending = self.get_pending_migrations()

            return {
                "configured": True,
                "connected": True,
                "current_revision": current,
                "pending_count": len(pending),
                "message": "Conectado correctamente",
            }
        except Exception as e:
            return {
                "configured": True,
                "connected": False,
                "message": f"Error de conexión: {str(e)}",
            }

    def generate_sql(self, revision: str = "head", direction: str = "upgrade") -> dict:
        """
        Genera el SQL de las migraciones sin ejecutarlo.

        Equivalente a: alembic upgrade head --sql

        Args:
            revision: ID de revisión objetivo o "head" para la última.
            direction: "upgrade" o "downgrade"

        Returns:
            Diccionario con el SQL generado o error.
        """
        try:
            config = self._get_alembic_config()

            # Capturar la salida del comando en un buffer
            sql_buffer = io.StringIO()

            # Redirigir stdout temporalmente
            old_stdout = sys.stdout
            sys.stdout = sql_buffer

            try:
                if direction == "upgrade":
                    command.upgrade(config, revision, sql=True)
                else:
                    command.downgrade(config, revision, sql=True)
            finally:
                # Restaurar stdout
                sys.stdout = old_stdout

            sql_content = sql_buffer.getvalue()
            sql_buffer.close()

            # Si no hay SQL generado, crear un archivo informativo
            if not sql_content or sql_content.strip() == "":
                current_rev = self.get_current_revision()
                sql_content = f"""-- Migraciones de Base de Datos Triskel/Mandrágora
-- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Revisión actual: {current_rev or 'base (sin migraciones)'}
-- Estado: Sin migraciones pendientes

-- No hay cambios de esquema pendientes de aplicar.
-- La base de datos está actualizada.
"""
                message = "No hay migraciones pendientes (base de datos actualizada)"
            else:
                message = f"SQL generado para {direction} {revision}"

            return {
                "success": True,
                "message": message,
                "sql": sql_content,
                "revision": revision,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error al generar SQL: {str(e)}",
                "error": str(e),
                "sql": "",
            }
