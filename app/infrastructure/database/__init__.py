"""
Database Clients

Clientes para conexión con bases de datos:
- Firebase/Firestore
- MariaDB
"""

from .firebase_client import firebase_manager, get_firestore_client
from .mariadb_client import mariadb_manager

__all__ = [
    'firebase_manager',
    'get_firestore_client',
    'mariadb_manager'
]
