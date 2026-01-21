#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.domain.auth.adapters.sql_repository import SQLAuthRepository
from app.domain.auth.schemas import AdminUserCreate
from app.domain.auth.service import AuthService
from app.infrastructure.database.sql_client import get_db_session, sql_manager


def create_first_admin():
    print("=" * 60)
    print("Triskel API - Seed Admin User")
    print("=" * 60)

    print("\n1. Inicializando Base de Datos SQL...")
    try:
        sql_manager.initialize()
        sql_manager.create_tables()
        print("   ✅ Base de Datos SQL inicializado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    print("\n2. Creando usuario administrador...")
    try:
        session = next(get_db_session())
        repo = SQLAuthRepository(session=session)
        service = AuthService(repository=repo)

        existing = repo.get_user_by_username("admin")
        if existing:
            print("   ⚠️  Usuario 'admin' ya existe")
            print(f"      ID: {existing['id']}")
            print(f"      Email: {existing['email']}")
            session.close()
            return

        admin_data = AdminUserCreate(
            username="admin",
            email="admin@triskel.com",
            password="Admin123!",
            role="admin",
        )

        user = service.create_admin(admin_data)

        print("   ✅ Usuario administrador creado")
        print(f"      Username: {user['username']}")
        print(f"      Email: {user['email']}")

        session.close()

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETO")
    print("=" * 60)
    print("\nCredenciales:")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("\n⚠️  Cambia el password después del primer login")
    print("=" * 60)


if __name__ == "__main__":
    create_first_admin()
