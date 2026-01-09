"""
Shared Kernel - Componentes compartidos por todos los dominios

Este módulo contiene infraestructura común:
- Clientes de bases de datos (Firebase, MariaDB)
- Configuración global
- Logger estructurado
- Validadores comunes
- Excepciones personalizadas
"""

from .settings import settings
from .firebase_client import firebase_manager, get_firestore_client
from .logger import logger
from .exceptions import (
    TriskelAPIException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    ConflictException
)

__all__ = [
    'settings',
    'firebase_manager',
    'get_firestore_client',
    'logger',
    'TriskelAPIException',
    'NotFoundException',
    'ValidationException',
    'AuthenticationException',
    'ConflictException'
]
