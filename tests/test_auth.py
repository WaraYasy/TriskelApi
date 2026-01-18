import pytest
from jose import jwt

from app.domain.auth.validators import PasswordValidator
from app.domain.auth.service import AuthService
from app.domain.auth.schemas import LoginRequest, AdminUserCreate, ChangePasswordRequest
from app.config.settings import settings


class TestPasswordValidator:
    def test_valid_password(self):
        password = "SecurePass123!"
        assert PasswordValidator.validate(password) == password

    def test_password_too_short(self):
        with pytest.raises(ValueError, match="al menos 8 caracteres"):
            PasswordValidator.validate("Short1!")

    def test_password_too_long(self):
        with pytest.raises(ValueError, match="72 caracteres"):
            PasswordValidator.validate("A" * 100)

    def test_password_missing_requirements(self):
        with pytest.raises(ValueError, match="mayúscula"):
            PasswordValidator.validate("password123!")

        with pytest.raises(ValueError, match="número"):
            PasswordValidator.validate("PasswordABC!")

        with pytest.raises(ValueError, match="carácter especial"):
            PasswordValidator.validate("Password123")


class TestSchemas:
    def test_login_request_valid(self):
        data = {"username": "admin", "password": "Admin123!"}
        request = LoginRequest(**data)
        assert request.username == "admin"
        assert request.password == "Admin123!"

    def test_login_request_trims_username(self):
        data = {"username": "  admin  ", "password": "Admin123!"}
        request = LoginRequest(**data)
        assert request.username == "admin"

    def test_admin_user_create_valid(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123!",
            "role": "admin",
        }
        user = AdminUserCreate(**data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_admin_user_create_password_weak(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "weak",
            "role": "admin",
        }
        with pytest.raises(ValueError):
            AdminUserCreate(**data)

    def test_change_password_different_passwords(self):
        data = {"old_password": "OldPass123!", "new_password": "OldPass123!"}
        with pytest.raises(ValueError, match="diferente"):
            ChangePasswordRequest(**data)


class TestAuthService:
    def test_hash_password_valid(self):
        password = "SecurePass123!"
        hashed = AuthService.hash_password(password)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_hash_password_too_long(self):
        with pytest.raises(ValueError, match="72 caracteres"):
            AuthService.hash_password("A" * 100)

    def test_verify_password_correct(self):
        password = "SecurePass123!"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "SecurePass123!"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password("WrongPass123!", hashed) is False

    def test_create_access_token(self):
        service = AuthService(repository=None)
        token = service.create_access_token(user_id=1, username="admin", role="admin")

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["type"] == "access"
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"
        assert payload["role"] == "admin"

    def test_create_refresh_token(self):
        service = AuthService(repository=None)
        token = service.create_refresh_token(user_id=1, username="admin")

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["type"] == "refresh"
        assert payload["user_id"] == 1
        assert payload["username"] == "admin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
