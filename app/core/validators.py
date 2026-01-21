"""
Validadores comunes de la aplicación

Funciones simples para validar datos que se usan en múltiples lugares.
Lanzan ValidationException si algo no es válido.
"""

import re
from typing import Optional

from .exceptions import ValidationException


def validate_username(username: str) -> None:
    """
    Valida que un username sea correcto.

    Reglas:
    - Obligatorio (no vacío)
    - Mínimo 3 caracteres
    - Máximo 20 caracteres
    - Solo letras, números y guiones bajos

    Ejemplo:
        validate_username("player123")  # OK
        validate_username("ab")  # Error: muy corto
    """
    if not username:
        raise ValidationException("El username es obligatorio")

    if len(username) < 3:
        raise ValidationException("El username debe tener al menos 3 caracteres")

    if len(username) > 20:
        raise ValidationException("El username no puede tener más de 20 caracteres")

    # Solo permite: letras, números y _ (guión bajo)
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        raise ValidationException(
            "El username solo puede contener letras, números y guiones bajos"
        )


def validate_email(email: Optional[str]) -> None:
    """
    Valida formato de email (solo si se proporciona).

    El email es opcional, pero si se envía debe ser válido.

    Ejemplo:
        validate_email("player@example.com")  # OK
        validate_email(None)  # OK (opcional)
        validate_email("invalid")  # Error
    """
    if email is None:
        return  # Email es opcional

    # Patrón simple de email
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(pattern, email):
        raise ValidationException("El formato del email no es válido")


def validate_level_name(level: str) -> None:
    """
    Valida que el nombre de nivel sea uno de los 5 niveles del juego.

    Niveles válidos:
    - hub_central
    - senda_ebano
    - fortaleza_gigantes
    - aquelarre_sombras
    - claro_almas
    """
    valid_levels = [
        "hub_central",
        "senda_ebano",
        "fortaleza_gigantes",
        "aquelarre_sombras",
        "claro_almas",
    ]

    if level not in valid_levels:
        raise ValidationException(
            f"Nivel '{level}' no válido. Válidos: {', '.join(valid_levels)}"
        )


def validate_choice(level: str, choice: str) -> None:
    """
    Valida que una elección moral sea válida para ese nivel.

    Decisiones morales por nivel:
    - senda_ebano: forzar (malo) o sanar (bueno)
    - fortaleza_gigantes: destruir (malo) o construir (bueno)
    - aquelarre_sombras: ocultar (malo) o revelar (bueno)

    Nota: No todos los niveles tienen decisión moral.
    """
    choices_by_level = {
        "senda_ebano": ["forzar", "sanar"],
        "fortaleza_gigantes": ["destruir", "construir"],
        "aquelarre_sombras": ["ocultar", "revelar"],
    }

    # Si el nivel no tiene elección, no validar
    if level not in choices_by_level:
        return

    valid_choices = choices_by_level[level]

    if choice not in valid_choices:
        raise ValidationException(
            f"Elección '{choice}' no válida para '{level}'. "
            f"Válidas: {', '.join(valid_choices)}"
        )


def validate_relic(relic: str) -> None:
    """
    Valida que una reliquia sea una de las 3 del juego.

    Reliquias válidas:
    - lirio (Lirio Azul)
    - hacha (Hacha Sagrada)
    - manto (Manto de Luna)
    """
    valid_relics = ["lirio", "hacha", "manto"]

    if relic not in valid_relics:
        raise ValidationException(
            f"Reliquia '{relic}' no válida. Válidas: {', '.join(valid_relics)}"
        )
