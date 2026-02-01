"""
Cliente de Base de Datos SQL usando SQLAlchemy

Este archivo prepara la conexión a la base de datos SQL relacional
(PostgreSQL, MySQL, MariaDB, etc.).
Se usará para Auth (usuarios admin) y logs de auditoría.

NOTA: La base de datos SQL es OPCIONAL. Si no está configurada, la app funcionará igual.
"""

from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

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
            print("⚠️  Base de datos SQL no configurada (opcional)")
            return

        try:
            # Crear URL de conexión para PostgreSQL
            db_url = (
                f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )

            # Crear motor de conexión
            self._engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verifica que la conexión esté viva
                pool_recycle=3600,  # Recicla conexiones cada hora
            )

            # Crear fábrica de sesiones
            self._session_factory = sessionmaker(bind=self._engine)

            self._initialized = True
            print("✅ Base de datos SQL conectada correctamente")

        except Exception as e:
            print(f"❌ Error conectando a la base de datos SQL: {e}")
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
        print("✅ Tablas creadas en la base de datos SQL")


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
