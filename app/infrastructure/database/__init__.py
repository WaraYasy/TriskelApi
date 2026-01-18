"""
Database Clients

Clientes para conexión con bases de datos:
- Firebase/Firestore (NoSQL)
- SQL Database (PostgreSQL, MySQL, MariaDB)
"""

from .firebase_client import firebase_manager, get_firestore_client
from .sql_client import sql_manager, get_db_session

__all__ = ["firebase_manager", "get_firestore_client", "sql_manager", "get_db_session"]
