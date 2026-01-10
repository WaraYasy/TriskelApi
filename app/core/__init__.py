"""
Core Utilities

Utilidades comunes usadas en toda la aplicación:
- Excepciones personalizadas
- Validadores de negocio
- Logger estructurado
"""

from .exceptions import (
    TriskelAPIException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    ConflictException,
    BusinessRuleException
)
from .validators import (
    validate_username,
    validate_email,
    validate_level_name,
    validate_choice,
    validate_relic
)
from .logger import logger

__all__ = [
    # Exceptions
    'TriskelAPIException',
    'NotFoundException',
    'ValidationException',
    'AuthenticationException',
    'AuthorizationException',
    'ConflictException',
    'BusinessRuleException',
    # Validators
    'validate_username',
    'validate_email',
    'validate_level_name',
    'validate_choice',
    'validate_relic',
    # Logger
    'logger'
]
