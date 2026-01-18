from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.sql_client import get_db_session
from app.domain.auth.adapters.sql_repository import SQLAuthRepository
from app.domain.auth.service import AuthService
from app.domain.auth.schemas import AdminUserCreate

router = APIRouter(prefix="/seed", tags=["Seed"])


@router.post("/admin")
def seed_admin(db: Session = Depends(get_db_session)):
    """Crea el admin inicial. ELIMINAR después de usar."""
    try:
        repo = SQLAuthRepository(session=db)
        service = AuthService(repository=repo)

        existing = repo.get_user_by_username("admin")
        if existing:
            raise HTTPException(status_code=400, detail="Admin ya existe")

        admin_data = AdminUserCreate(
            username="admin",
            email="admin@triskel.com",
            password="Admin123!",
            role="admin",
        )

        user = service.create_admin(admin_data)
        return {
            "message": "Admin creado",
            "username": user["username"],
            "email": user["email"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
