import re


class PasswordValidator:
    MIN_LENGTH = 8
    MAX_LENGTH = 72

    @staticmethod
    def validate(password: str) -> str:
        if len(password) < PasswordValidator.MIN_LENGTH:
            raise ValueError(
                f"Password debe tener al menos {PasswordValidator.MIN_LENGTH} caracteres"
            )

        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError(
                f"Password no puede exceder {PasswordValidator.MAX_LENGTH} caracteres"
            )

        if not re.search(r"[A-Z]", password):
            raise ValueError("Password debe contener al menos una mayúscula")

        if not re.search(r"[0-9]", password):
            raise ValueError("Password debe contener al menos un número")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/]', password):
            raise ValueError("Password debe contener al menos un carácter especial")

        return password
