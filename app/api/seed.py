"""Script de sembrado de datos (Seed).

Utilidad para crear datos iniciales como el administrador por defecto.
DEBE SER ELIMINADO O PROTEGIDO EN PRODUCCIÓN.

Autor: Mandrágora
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domain.auth.adapters.sql_repository import SQLAuthRepository
from app.domain.auth.schemas import AdminUserCreate
from app.domain.auth.service import AuthService
from app.infrastructure.database.sql_client import get_db_session

router = APIRouter(prefix="/seed", tags=["Seed"])


@router.post("/admin")
def seed_admin(db: Session = Depends(get_db_session)):
    """Crea el admin inicial. ELIMINAR después de usar.

    Args:
        db (Session): Sesión de base de datos.

    Returns:
        dict: Datos del administrador creado.

    Raises:
        HTTPException: Si el admin ya existe (400) o error interno (500).
    """
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
