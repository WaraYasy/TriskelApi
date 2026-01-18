from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from .ports import IAuthRepository
from .schemas import AdminUserCreate, AdminUserUpdate
from .validators import PasswordValidator
from app.config.settings import settings


class AuthService:
    ROLE_PERMISSIONS = {
        "admin": [
            "view_players",
            "edit_players",
            "delete_players",
            "view_games",
            "edit_games",
            "delete_games",
            "view_events",
            "edit_events",
            "delete_events",
            "view_admins",
            "create_admins",
            "edit_admins",
            "delete_admins",
            "view_audit_logs",
        ],
        "support": [
            "view_players",
            "edit_players",
            "view_games",
            "edit_games",
            "view_events",
            "edit_events",
            "view_audit_logs",
        ],
        "viewer": [
            "view_players",
            "view_games",
            "view_events",
        ],
    }

    def __init__(self, repository: IAuthRepository):
        self.repository = repository

    @staticmethod
    def hash_password(password: str) -> str:
        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError(f"Password no puede exceder {PasswordValidator.MAX_LENGTH} caracteres")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def create_access_token(self, user_id: int, username: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "type": "access",
            "user_id": user_id,
            "username": username,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def create_refresh_token(self, user_id: int, username: str) -> str:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
        payload = {
            "type": "refresh",
            "user_id": user_id,
            "username": username,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != token_type:
            raise JWTError(f"Token tipo '{payload.get('type')}', esperado '{token_type}'")
        return payload

    def login(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        username = username.strip()

        if len(password) > PasswordValidator.MAX_LENGTH:
            raise ValueError("Password inválido")

        user = self.repository.get_user_by_username(username)
        if not user:
            raise ValueError("Credenciales inválidas")

        if not self.verify_password(password, user["password_hash"]):
            raise ValueError("Credenciales inválidas")

        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        self.repository.update_last_login(user["id"])

        access_token = self.create_access_token(user["id"], user["username"], user["role"])
        refresh_token = self.create_refresh_token(user["id"], user["username"])

        self.repository.create_audit_log(
            user_id=user["id"],
            username=username,
            action="login_success",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
            },
        }

    def refresh_access_token(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = self.verify_token(refresh_token, token_type="refresh")
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")
        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        new_access_token = self.create_access_token(user["id"], user["username"], user["role"])
        new_refresh_token = self.create_refresh_token(user["id"], user["username"])

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
        }

    def get_current_user(self, token: str) -> Dict[str, Any]:
        payload = self.verify_token(token, token_type="access")
        user = self.repository.get_user_by_id(payload["user_id"])

        if not user:
            raise ValueError("Usuario no existe")
        if not user["is_active"]:
            raise ValueError("Usuario desactivado")

        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_active": user["is_active"],
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
            "last_login": user["last_login"],
            "permissions": self.get_role_permissions(user["role"]),
        }

    def create_admin(self, admin_data: AdminUserCreate) -> Dict[str, Any]:
        password_hash = self.hash_password(admin_data.password)
        return self.repository.create_admin_user(
            username=admin_data.username,
            email=admin_data.email,
            password_hash=password_hash,
            role=admin_data.role,
        )

    def update_admin(self, user_id: int, admin_update: AdminUserUpdate) -> Optional[Dict[str, Any]]:
        return self.repository.update_user(
            user_id=user_id,
            email=admin_update.email,
            role=admin_update.role,
            is_active=admin_update.is_active,
        )

    def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise ValueError("Usuario no existe")

        if not self.verify_password(old_password, user["password_hash"]):
            return False

        new_password_hash = self.hash_password(new_password)
        success = self.repository.update_password(user_id, new_password_hash)

        if success:
            self.repository.create_audit_log(
                user_id=user_id,
                username=user["username"],
                action="change_password",
                ip_address=ip_address,
                success=True,
            )

        return success

    def list_admins(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return self.repository.list_users(role=role, is_active=is_active, limit=limit)

    def get_admin(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            return None
        user_copy = user.copy()
        user_copy.pop("password_hash", None)
        return user_copy

    @classmethod
    def get_role_permissions(cls, role: str) -> List[str]:
        return cls.ROLE_PERMISSIONS.get(role, [])

    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        return permission in cls.get_role_permissions(role)

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        logs = self.repository.get_audit_logs(
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date,
            success=success,
            limit=limit,
            offset=offset,
        )
        total = self.repository.count_audit_logs(
            user_id=user_id, action=action, start_date=start_date, end_date=end_date
        )
        return {"logs": logs, "total": total, "limit": limit, "offset": offset}
