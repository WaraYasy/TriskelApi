#!/usr/bin/env python3
"""
Script para crear el primer usuario administrador

Uso:
    python scripts/seed_admin.py

Credenciales default:
    Username: admin
    Password: Admin123!
    Role: admin

IMPORTANTE: Cambia el password después del primer login en producción.
"""
import sys
import os

# Añadir el directorio raíz al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.database.sql_client import sql_manager, get_db_session
from app.domain.auth.adapters.sql_repository import SQLAuthRepository
from app.domain.auth.service import AuthService
from app.domain.auth.schemas import AdminUserCreate


def create_first_admin():
    """
    Crea el primer usuario administrador.

    Credenciales:
    - Username: admin
    - Email: admin@triskel.local
    - Password: Admin123!
    - Role: admin
    """
    print("=" * 60)
    print("Triskel API - Seed Admin User")
    print("=" * 60)

    # Inicializar Base de Datos SQL
    print("\n1. Inicializando Base de Datos SQL...")
    try:
        sql_manager.initialize()
        sql_manager.create_tables()
        print("   ✅ Base de Datos SQL inicializado y tablas creadas")
    except Exception as e:
        print(f"   ❌ Error inicializando Base de Datos SQL: {e}")
        print("\n⚠️  Asegúrate de que Base de Datos SQL esté corriendo y configurado en .env")
        return

    # Crear usuario admin
    print("\n2. Creando usuario administrador...")
    try:
        # Obtener sesión de base de datos
        session = next(get_db_session())

        # Crear repository y service
        repo = SQLAuthRepository(session=session)
        service = AuthService(repository=repo)

        # Verificar si ya existe admin
        existing = repo.get_user_by_username("admin")
        if existing:
            print("   ⚠️  Usuario 'admin' ya existe")
            print(f"      ID: {existing['id']}")
            print(f"      Email: {existing['email']}")
            print(f"      Role: {existing['role']}")
            print(f"      Active: {existing['is_active']}")
            session.close()
            return

        # Crear admin
        admin_data = AdminUserCreate(
            username="admin",
            email="admin@triskel.local",
            password="Admin123!",
            role="admin"
        )

        user = service.create_admin(
            admin_data=admin_data,
            created_by_user_id=None,
            created_by_username="system"
        )

        print("   ✅ Usuario administrador creado exitosamente")
        print(f"      ID: {user['id']}")
        print(f"      Username: {user['username']}")
        print(f"      Email: {user['email']}")
        print(f"      Role: {user['role']}")

        session.close()

    except Exception as e:
        print(f"   ❌ Error creando admin: {e}")
        return

    # Mostrar credenciales
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETO")
    print("=" * 60)
    print("\nCredenciales de acceso:")
    print("   Username: admin")
    print("   Password: Admin123!")
    print("\nAccede al dashboard en:")
    print("   http://localhost:8000/web/admin/login")
    print("\nAccede a la documentación API en:")
    print("   http://localhost:8000/docs")
    print("\n⚠️  IMPORTANTE: Cambia el password después del primer login en producción")
    print("=" * 60)


if __name__ == "__main__":
    create_first_admin()
