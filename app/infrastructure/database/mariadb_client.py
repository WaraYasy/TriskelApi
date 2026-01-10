"""
Cliente de MariaDB usando SQLAlchemy

Este archivo prepara la conexión a MariaDB (base de datos SQL).
Se usará para Auth (usuarios admin) y logs de auditoría.

NOTA: MariaDB es OPCIONAL. Si no está configurado, la app funcionará igual.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Generator
from app.config.settings import settings


# Base para crear modelos de tablas SQL
Base = declarative_base()


class MariaDBManager:
    """
    Gestor de MariaDB (Singleton).
    Maneja la conexión a la base de datos SQL.
    """

    _instance: Optional["MariaDBManager"] = None
    _engine = None
    _session_factory = None
    _initialized: bool = False

    def __new__(cls):
        """Solo permite una instancia (Singleton)"""
        if cls._instance is None:
            cls._instance = super(MariaDBManager, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Inicializa la conexión a MariaDB"""
        if self._initialized:
            return

        # Si no hay configuración de MariaDB, saltar
        if not settings.mariadb_host:
            print("⚠️  MariaDB no configurado (opcional)")
            return

        try:
            # Crear URL de conexión
            db_url = (
                f"mysql+pymysql://{settings.mariadb_user}:{settings.mariadb_password}"
                f"@{settings.mariadb_host}:{settings.mariadb_port}/{settings.mariadb_database}"
            )

            # Crear motor de conexión
            self._engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verifica que la conexión esté viva
                pool_recycle=3600    # Recicla conexiones cada hora
            )

            # Crear fábrica de sesiones
            self._session_factory = sessionmaker(bind=self._engine)

            self._initialized = True
            print("✅ MariaDB conectado correctamente")

        except Exception as e:
            print(f"❌ Error conectando a MariaDB: {e}")
            raise

    def get_session(self) -> Session:
        """
        Obtiene una nueva sesión de base de datos.
        Cada operación debe usar su propia sesión.
        """
        if not self._initialized:
            self.initialize()

        if not self._session_factory:
            raise RuntimeError("MariaDB no está configurado")

        return self._session_factory()

    def create_tables(self) -> None:
        """
        Crea todas las tablas definidas en los modelos.
        Solo se debe llamar una vez al configurar la BD.
        """
        if not self._engine:
            raise RuntimeError("MariaDB no está inicializado")

        Base.metadata.create_all(bind=self._engine)
        print("✅ Tablas creadas en MariaDB")


# Instancia única compartida
mariadb_manager = MariaDBManager()


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
    session = mariadb_manager.get_session()
    try:
        yield session
    finally:
        session.close()
