"""
Triskel API - Main Application

Aplicación principal con arquitectura hexagonal por dominios.
Integra FastAPI para la API REST del juego + Flask para el dashboard web.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.openapi.utils import get_openapi

# Imports desde la nueva arquitectura
from app.config.settings import settings
from app.core.logger import logger
from app.domain.auth.api import router as auth_router
from app.domain.events.api import router as events_router
from app.domain.games.api import router as games_router
from app.domain.leaderboard.api import admin_router as leaderboard_admin_router
from app.domain.leaderboard.api import router as leaderboard_router
from app.domain.players.api import router as players_router
from app.domain.sessions.api import router as sessions_router
from app.domain.web import flask_app  # ⭐ Flask app
from app.infrastructure.database.firebase_client import firebase_manager
from app.infrastructure.database.sql_client import sql_manager
from app.middleware.auth import auth_middleware
from app.scheduler import shutdown_scheduler, start_scheduler

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="API REST para el videojuego Triskel: La Balada del Último Guardián",
    version="2.0.0",
    # Esquemas de seguridad para Swagger UI
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
    # Definir esquemas de seguridad
    openapi_tags=[
        {"name": "Players", "description": "Gestión de jugadores y perfiles"},
        {"name": "Games", "description": "Gestión de partidas y estadísticas"},
        {"name": "Events", "description": "Eventos de gameplay y telemetría"},
        {"name": "Sessions", "description": "Sesiones de juego (tracking de tiempo)"},
        {"name": "Leaderboard", "description": "Tablas de clasificación (públicas)"},
        {
            "name": "Auth",
            "description": "Autenticación JWT para administradores del dashboard",
        },
        {
            "name": "Admin - Leaderboard",
            "description": "Administración de leaderboards (solo admin)",
        },
    ],
)


# Personalizar esquema OpenAPI para mostrar esquemas de seguridad
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Agregar esquemas de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key para administradores (acceso total)",
        },
        "PlayerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Player credentials",
            "description": "Autenticación de jugador: requiere headers X-Player-ID y X-Player-Token",
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token para administradores del dashboard. Obtener con POST /v1/auth/login",
        },
    }

    # Marcar endpoints protegidos con candaditos
    for path, path_item in openapi_schema["paths"].items():
        # Endpoints públicos (sin autenticación)
        public_endpoints = [
            ("/", "get"),
            ("/health", "get"),
            ("/v1/players", "post"),  # Crear jugador es público
        ]

        for method, operation in path_item.items():
            if method not in ["get", "post", "put", "patch", "delete"]:
                continue

            # Si es endpoint público, skip
            if (path, method) in public_endpoints:
                continue

            # Determinar qué tipo de autenticación requiere
            if path == "/v1/players" and method == "get":
                # GET /v1/players (listar todos) - solo admin
                operation["security"] = [{"ApiKeyAuth": []}]
                operation["summary"] = operation.get("summary", "") + " 🔑"

            elif path.startswith("/v1/"):
                # Todos los demás endpoints v1 - admin O jugador
                operation["security"] = [
                    {"ApiKeyAuth": []},  # Admin puede acceder
                    {"PlayerAuth": []},  # O jugador autenticado
                ]

                # Marcar si es solo del propio jugador
                if "/me" in path or "{player_id}" in path:
                    if "summary" in operation:
                        operation["summary"] += " 🔒"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# CORS - Configuración automática según entorno
cors_origins = settings.cors_origins
# Si cors_origins es "*", no lo separamos por comas
if cors_origins == "*":
    allowed_origins = ["*"]
elif cors_origins:
    allowed_origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    # Sin CORS configurado en producción - no permitir ningún origen
    allowed_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de autenticación
app.middleware("http")(auth_middleware)


# Eventos de ciclo de vida
@app.on_event("startup")
def startup_event():
    """Inicializa servicios al arrancar la aplicación"""
    logger.info("Iniciando Triskel API", version="2.0.0")

    # Inicializar Firebase
    firebase_manager.initialize()

    # Inicializar Base de Datos SQL (para Auth)
    try:
        sql_manager.initialize()
        sql_manager.create_tables()
    except Exception as e:
        logger.warning(f"Base de datos SQL no disponible (opcional): {e}")

    # Inicializar Scheduler de Leaderboards
    try:
        start_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler no disponible: {e}")

    logger.info("Triskel API lista")


@app.on_event("shutdown")
def shutdown_event():
    """Limpia recursos al cerrar la aplicación"""
    logger.info("Cerrando Triskel API...")

    # Detener scheduler
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Error deteniendo scheduler: {e}")

    logger.info("Triskel API cerrada")


# Registrar routers de dominios (FastAPI REST API)
app.include_router(players_router)
app.include_router(games_router)
app.include_router(events_router)
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(leaderboard_router)
app.include_router(leaderboard_admin_router)
# app.include_router(seed_router)  # DESHABILITADO por seguridad - solo usar en desarrollo

# Montar Flask app (Dashboard Web)
app.mount("/web", WSGIMiddleware(flask_app))
logger.info("Flask app montada en /web")


# Endpoints raíz
@app.get("/")
def read_root():
    """Endpoint raíz - Bienvenida"""
    return {
        "message": "Bienvenido a Triskel-API",
        "version": "2.0.0",
        "status": "online",
        "api_docs": "/docs",
        "dashboard": "/web/",
        "analytics": "/web/dashboard/",
    }


@app.get("/health")
def health_check():
    """Health check para monitoreo"""
    return {"status": "ok", "version": "2.0.0"}


# Punto de entrada
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
