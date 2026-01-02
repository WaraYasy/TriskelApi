"""
Módulo de inicialización y gestión de Firebase
"""
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
from typing import Optional


class FirebaseManager:
    """Gestor centralizado de Firebase"""

    _instance: Optional["FirebaseManager"] = None
    _db: Optional[firestore.Client] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton: asegura una única instancia"""
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Inicializa Firebase Admin SDK"""
        if self._initialized:
            return

        try:
            # Cargar credenciales
            cred = credentials.Certificate(settings.firebase_credentials_path)

            # Inicializar Firebase
            firebase_admin.initialize_app(cred)

            # Obtener cliente de Firestore
            self._db = firestore.client()

            self._initialized = True
            print("Firebase inicializado correctamente")

        except Exception as e:
            print(f"Error al inicializar Firebase: {e}")
            raise

    def get_db(self) -> firestore.Client:
        """Obtiene el cliente de Firestore"""
        if not self._initialized:
            self.initialize()
        return self._db

    @property
    def db(self) -> firestore.Client:
        """Propiedad para acceder al cliente de Firestore"""
        return self.get_db()


# Instancia global del manager
firebase_manager = FirebaseManager()


def get_firestore_client() -> firestore.Client:
    """
    Función helper para obtener el cliente de Firestore.
    Útil para inyección de dependencias en FastAPI.
    """
    return firebase_manager.get_db()
