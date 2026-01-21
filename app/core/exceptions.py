"""
Excepciones personalizadas de la aplicación

Define errores específicos para manejar casos comunes de forma clara.
Cada excepción tiene un código HTTP asociado.
"""

from typing import Any, Optional


class TriskelAPIException(Exception):
    """
    Excepción base de la aplicación.
    Todas las demás heredan de esta.
    """

    def __init__(
        self, message: str, status_code: int = 500, details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(TriskelAPIException):
    """
    Error cuando no se encuentra un recurso (HTTP 404).

    Ejemplo:
        raise NotFoundException("Player", "abc-123")
        # Mensaje: "Player con ID 'abc-123' no encontrado"
    """

    def __init__(self, resource: str, identifier: str):
        message = f"{resource} con ID '{identifier}' no encontrado"
        super().__init__(message=message, status_code=404)


class ValidationException(TriskelAPIException):
    """
    Error de validación de datos (HTTP 400).

    Ejemplo:
        raise ValidationException("Username debe tener al menos 3 caracteres")
    """

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=400, details=details)


class AuthenticationException(TriskelAPIException):
    """
    Error de autenticación (HTTP 401).

    Ejemplo:
        raise AuthenticationException("Token inválido")
    """

    def __init__(self, message: str = "No autenticado o credenciales inválidas"):
        super().__init__(message=message, status_code=401)


class AuthorizationException(TriskelAPIException):
    """
    Error de autorización/permisos (HTTP 403).

    Ejemplo:
        raise AuthorizationException("No tienes permisos de administrador")
    """

    def __init__(self, message: str = "No tiene permisos para esta acción"):
        super().__init__(message=message, status_code=403)


class ConflictException(TriskelAPIException):
    """
    Conflicto con el estado actual (HTTP 409).

    Ejemplo:
        raise ConflictException("Ya existe un jugador con ese username")
    """

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=409, details=details)


class BusinessRuleException(TriskelAPIException):
    """
    Violación de regla de negocio (HTTP 422).

    Ejemplo:
        raise BusinessRuleException(
            "No puedes tener dos partidas activas al mismo tiempo"
        )
    """

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=message, status_code=422, details=details)
