"""
Blueprint de Public (Contenido Público)

TODO: Implementar landing page y contenido público.

Rutas futuras:
- GET /public/              → Home del juego
- GET /public/leaderboards  → Rankings públicos
- GET /public/about         → Sobre el juego
- GET /public/guides        → Guías y tutoriales
- GET /public/community     → Comunidad/Foros
"""

from flask import Blueprint

# Crear blueprint
public_bp = Blueprint("public", __name__, template_folder="templates")

# TODO: Implementar rutas públicas
