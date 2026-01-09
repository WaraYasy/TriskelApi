"""
Blueprint de Admin (Panel de Administración)

TODO: Implementar panel de administración.

Rutas futuras:
- GET  /admin/             → Dashboard admin
- GET  /admin/users        → Gestión de usuarios
- GET  /admin/moderate     → Moderación de contenido
- POST /admin/ban          → Banear jugador
- GET  /admin/logs         → Ver logs de auditoría
"""
from flask import Blueprint, render_template

# Crear blueprint
admin_bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates'
)

# TODO: Implementar rutas de admin
