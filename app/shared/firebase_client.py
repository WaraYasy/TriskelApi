"""
Cliente de Firebase Firestore

Gestor centralizado para conectarse a Firebase.
Usa patrón Singleton para tener una sola conexión.
"""
import firebase_admin
from firebase_admin import credentials, firestore
from .settings import settings
from typing import Optional


class FirebaseManager:
    """
    Gestor de Firebase con patrón Singleton.

    Singleton = solo existe una instancia en toda la app.
    Esto asegura que solo haya una conexión a Firebase.
    """

    _instance: Optional["FirebaseManager"] = None
    _db: Optional[firestore.Client] = None
    _initialized: bool = False

    def __new__(cls):
        """Crea o retorna la única instancia (Singleton)"""
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Inicializa la conexión a Firebase"""
        if self._initialized:
            return  # Ya está inicializado, no hacer nada

        try:
            # Cargar archivo de credenciales
            cred = credentials.Certificate(settings.firebase_credentials_path)

            # Inicializar Firebase
            firebase_admin.initialize_app(cred)

            # Obtener cliente de Firestore
            self._db = firestore.client()

            self._initialized = True
            print("✅ Firebase conectado correctamente")

        except Exception as e:
            print(f"❌ Error conectando a Firebase: {e}")
            raise

    def get_db(self) -> firestore.Client:
        """
        Retorna el cliente de Firestore.
        Si no está inicializado, lo inicializa primero.
        """
        if not self._initialized:
            self.initialize()
        return self._db


# Instancia única compartida por toda la app
firebase_manager = FirebaseManager()


def get_firestore_client() -> firestore.Client:
    """
    Función simple para obtener el cliente de Firestore.

    Ejemplo de uso:
        db = get_firestore_client()
        players = db.collection('players').stream()
    """
    return firebase_manager.get_db()
