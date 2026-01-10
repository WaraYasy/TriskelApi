"""
Middleware Layer

Middleware y utilidades de autenticación/autorización:
- Auth middleware
- Security utilities
"""

from .auth import auth_middleware

__all__ = [
    'auth_middleware'
]
