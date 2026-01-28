"""Core Utilities.

Utilidades comunes usadas en toda la aplicación:
- Excepciones personalizadas.
- Validadores de negocio.
- Logger estructurado.

Autor: Mandrágora
"""

from .exceptions import (
    AuthenticationException,
    AuthorizationException,
    BusinessRuleException,
    ConflictException,
    NotFoundException,
    TriskelAPIException,
    ValidationException,
)
from .logger import logger
from .validators import (
    validate_choice,
    validate_email,
    validate_level_name,
    validate_relic,
    validate_username,
)

__all__ = [
    # Exceptions
    "TriskelAPIException",
    "NotFoundException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "ConflictException",
    "BusinessRuleException",
    # Validators
    "validate_username",
    "validate_email",
    "validate_level_name",
    "validate_choice",
    "validate_relic",
    # Logger
    "logger",
]
