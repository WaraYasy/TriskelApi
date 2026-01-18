"""
Aplicación Web de Triskel

Flask app que integra múltiples interfaces web:
- Dashboard: Métricas y visualizaciones del juego
- Admin: Panel de administración (futuro)
- Public: Landing page y rankings públicos (futuro)

Estructura de endpoints:
- GET  /                   → Landing page principal
- GET  /dashboard/         → Dashboard de métricas
- GET  /dashboard/players  → Análisis de jugadores
- GET  /dashboard/games    → Análisis de partidas
- GET  /dashboard/choices  → Decisiones morales
- GET  /admin/             → Panel admin (futuro)
- GET  /public/            → Contenido público (futuro)
"""

from flask import Flask, render_template
import os
from app.config.settings import settings as app_settings
from .analytics.routes import analytics_bp


def create_flask_app():
    """
    Crea y configura la aplicación Flask.

    Returns:
        Flask: Aplicación configurada con todos los blueprints
    """
    # Configurar paths de templates y static
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")

    # Crear app Flask
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # Configuración básica (desde settings)
    app.config.update(
        SECRET_KEY=app_settings.secret_key,  # Desde variables de entorno
        DEBUG=app_settings.debug,  # Detectado automáticamente según entorno
    )

    # Registrar blueprints
    # Dashboard principal (analytics)
    app.register_blueprint(analytics_bp, url_prefix="/dashboard")

    # Admin panel
    from .admin.routes import admin_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")

    # from .public.routes import public_bp
    # app.register_blueprint(public_bp, url_prefix='/public')

    # Ruta raíz: Landing page del portal web
    @app.route("/")
    def index():
        """Página de bienvenida del portal web"""
        return render_template("index.html")

    # Handler de errores
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("500.html"), 500

    return app


# Instancia global de Flask app
flask_app = create_flask_app()
