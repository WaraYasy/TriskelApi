import re

"""Validadores para el módulo de Auth.

Este módulo contiene utilidades para validar datos de entrada,
como contraseñas.

Autor: Mandrágora
"""


class PasswordValidator:
    """Validador de contraseñas seguras.

    Asegura que la contraseña cumpla con:
    - Longitud mínima y máxima.
    - Presencia de mayúsculas.
    - Presencia de números.
    - Presencia de caracteres especiales.
    """

    MIN_LENGTH = 8
    MAX_LENGTH = 72

    @staticmethod
    def validate(password: str) -> str:
        """Valida una contraseña.

        Args:
            password (str): La contraseña a validar.

        Returns:
            str: La contraseña si es válida.

        Raises:
            ValueError: Si la contraseña no cumple con los requisitos.
        """
        if len(password) < PasswordValidator.MIN_LENGTH:
            raise ValueError(
                f"Password debe tener al menos {PasswordValidator.MIN_LENGTH} caracteres"
            )

        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError(f"Password no puede exceder {PasswordValidator.MAX_LENGTH} caracteres")

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password debe contener al menos una mayúscula")

        if not re.search(r"[0-9]", password):
            raise ValueError("Password debe contener al menos un número")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/]', password):
            raise ValueError("Password debe contener al menos un carácter especial")

        return password
