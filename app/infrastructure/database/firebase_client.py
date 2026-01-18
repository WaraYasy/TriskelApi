"""
Cliente de Firebase Firestore

Gestor centralizado para conectarse a Firebase.
Usa patrón Singleton para tener una sola conexión.
"""

import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from app.config.settings import settings
from app.core.logger import logger
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
            # Opción 1: Credenciales desde Base64 (RECOMENDADO para Railway/Producción)
            if settings.firebase_credentials_base64:
                logger.info("Cargando credenciales de Firebase desde Base64")
                try:
                    # Decodificar base64 a JSON string
                    decoded_bytes = base64.b64decode(settings.firebase_credentials_base64)
                    decoded_str = decoded_bytes.decode("utf-8")
                    creds_dict = json.loads(decoded_str)
                    cred = credentials.Certificate(creds_dict)
                    logger.info("Credenciales Base64 decodificadas correctamente")
                except Exception as e:
                    raise ValueError(f"Error decodificando FIREBASE_CREDENTIALS_BASE64: {e}")

            # Opción 2: Credenciales desde JSON string (Alternativa)
            elif settings.firebase_credentials_json:
                logger.info("Cargando credenciales de Firebase desde JSON string")
                creds_dict = json.loads(settings.firebase_credentials_json)
                cred = credentials.Certificate(creds_dict)

            # Opción 3: Credenciales desde archivo (Local/Desarrollo)
            elif os.path.exists(settings.firebase_credentials_path):
                logger.info(
                    f"Cargando credenciales de Firebase desde archivo: {settings.firebase_credentials_path}"
                )
                cred = credentials.Certificate(settings.firebase_credentials_path)

            else:
                raise ValueError(
                    "No se encontraron credenciales de Firebase. "
                    "Configura FIREBASE_CREDENTIALS_BASE64, FIREBASE_CREDENTIALS_JSON o FIREBASE_CREDENTIALS_PATH"
                )

            # Inicializar Firebase
            firebase_admin.initialize_app(cred)

            # Obtener cliente de Firestore
            self._db = firestore.client()

            self._initialized = True
            logger.info("Firebase conectado correctamente")

        except Exception as e:
            logger.error(f"Error conectando a Firebase: {e}")
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
