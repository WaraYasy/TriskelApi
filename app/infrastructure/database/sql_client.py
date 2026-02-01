"""
Cliente de Base de Datos SQL usando SQLAlchemy

Este archivo prepara la conexión a la base de datos SQL relacional
(PostgreSQL, MySQL, MariaDB, etc.).
Se usará para Auth (usuarios admin) y logs de auditoría.

NOTA: La base de datos SQL es OPCIONAL. Si no está configurada, la app funcionará igual.
"""

from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings
from app.core.logger import logger

# Base para crear modelos de tablas SQL
Base = declarative_base()


class SQLManager:
    """
    Gestor de Base de Datos SQL (Singleton).
    Maneja la conexión a la base de datos SQL relacional.
    Soporta PostgreSQL, MySQL, MariaDB, etc.
    """

    _instance: Optional["SQLManager"] = None
    _engine = None
    _session_factory = None
    _initialized: bool = False

    def __new__(cls):
        """Solo permite una instancia (Singleton)"""
        if cls._instance is None:
            cls._instance = super(SQLManager, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Inicializa la conexión a la base de datos SQL"""
        if self._initialized:
            return

        # Si no hay configuración de base de datos, saltar
        if not settings.db_host:
            logger.warning("Base de datos SQL no configurada (opcional)")
            return

        try:
            # Crear URL de conexión para PostgreSQL
            db_url = (
                f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )

            # Crear motor de conexión con pooling optimizado para Railway/producción
            self._engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verifica que la conexión esté viva antes de usar
                pool_recycle=300,  # Recicla conexiones cada 5 min (Railway cierra idle connections)
                pool_size=5,  # Número de conexiones permanentes en el pool
                max_overflow=10,  # Conexiones adicionales temporales permitidas
                pool_timeout=30,  # Timeout para obtener conexión del pool (segundos)
                echo=False,  # No loguear todas las queries SQL (verbose)
            )

            # Crear fábrica de sesiones
            self._session_factory = sessionmaker(bind=self._engine)

            self._initialized = True
            logger.info("Base de datos SQL conectada correctamente")

        except Exception as e:
            logger.error(f"Error conectando a la base de datos SQL: {e}")
            raise

    def get_session(self) -> Optional[Session]:
        """
        Obtiene una nueva sesión de base de datos.
        Cada operación debe usar su propia sesión.

        Returns:
            Session si la BD está configurada, None si no lo está.
        """
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                # Si falla la inicialización, retornar None
                return None

        if not self._session_factory:
            # Retornar None en lugar de lanzar excepción
            return None

        return self._session_factory()

    def create_tables(self) -> None:
        """
        Crea todas las tablas definidas en los modelos.
        Solo se debe llamar una vez al configurar la BD.
        """
        if not self._engine:
            raise RuntimeError("Base de datos SQL no está inicializada")

        Base.metadata.create_all(bind=self._engine)
        logger.info("Tablas creadas en la base de datos SQL")

    def dispose(self) -> None:
        """Cierra todas las conexiones del pool de forma segura.

        Útil para:
        - Shutdown de la aplicación
        - Limpiar conexiones obsoletas
        - Liberar recursos
        """
        if self._engine:
            self._engine.dispose()
            logger.info("Connection pool de SQL cerrado")

    def health_check(self) -> bool:
        """Verifica que la conexión a la base de datos funcione.

        Returns:
            bool: True si la conexión es exitosa, False si falla.
        """
        if not self._engine:
            return False

        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Health check de SQL falló: {e}")
            return False


# Instancia única compartida
sql_manager = SQLManager()


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que da una sesión de BD.
    La sesión se cierra automáticamente al terminar.

    Ejemplo:
        @router.get("/admin/users")
        def get_users(db: Session = Depends(get_db_session)):
            users = db.query(AdminUser).all()
            return users
    """
    session = sql_manager.get_session()
    if session is None:
        raise RuntimeError(
            "Base de datos SQL no está configurada. "
            "Configura DB_HOST, DB_NAME, DB_USER y DB_PASSWORD en variables de entorno."
        )
    try:
        yield session
    finally:
        session.close()
