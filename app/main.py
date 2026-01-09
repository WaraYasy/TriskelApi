"""
Triskel API - Main Application

Aplicación principal con arquitectura hexagonal por dominios.
Integra FastAPI para la API REST del juego.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Imports desde la nueva arquitectura
from app.shared.settings import settings
from app.shared.firebase_client import firebase_manager
from app.shared.logger import logger
from app.domain.players.api import router as players_router
from app.domain.games.api import router as games_router
from app.middleware.auth import auth_middleware

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="API REST para el videojuego Triskel: La Balada del Último Guardián",
    version="2.0.0"
)

# CORS - Permitir peticiones desde cualquier origen (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
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

    # TODO: Inicializar MariaDB cuando esté configurado
    # mariadb_manager.initialize()

    logger.info("Triskel API lista")


# Registrar routers de dominios
app.include_router(players_router)
app.include_router(games_router)

# TODO: Añadir routers adicionales cuando estén implementados:
# app.include_router(events_router)
# app.include_router(sessions_router)
# app.include_router(auth_router)
# app.include_router(analytics_router)


# Endpoints raíz
@app.get("/")
def read_root():
    """Endpoint raíz - Bienvenida"""
    return {
        "message": "Bienvenido a Triskel-API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check para monitoreo"""
    return {
        "status": "ok",
        "version": "2.0.0"
    }


# Punto de entrada
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
