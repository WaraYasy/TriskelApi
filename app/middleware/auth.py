"""
Middleware de autenticación

Soporta DOS tipos de autenticación:
1. Player Token: Para jugadores (solo acceden a sus propios datos)
2. API Key: Para administración (acceso completo)
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.players.adapters.firestore_repository import FirestorePlayerRepository
from app.config.settings import settings


# Rutas que NO requieren autenticación
PUBLIC_ROUTES = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
]

# Rutas que permiten crear jugadores sin autenticación
CREATION_ROUTES = [
    "/v1/players",  # POST crear jugador
]


async def auth_middleware(request: Request, call_next):
    """
    Middleware que valida autenticación de dos formas:

    1. API KEY (admin):
       - Header "X-API-Key": la clave de administración
       - Acceso completo a todos los endpoints

    2. PLAYER TOKEN (jugadores):
       - Header "X-Player-ID": el UUID del jugador
       - Header "X-Player-Token": el token secreto del jugador
       - Solo accede a sus propios datos
    """
    path = request.url.path

    # Rutas públicas (sin autenticación)
    if path in PUBLIC_ROUTES or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/web"):
        return await call_next(request)

    # POST /v1/players (crear jugador) no requiere autenticación
    if path in CREATION_ROUTES and request.method == "POST":
        return await call_next(request)

    # El resto de rutas v1 requieren autenticación
    if path.startswith("/v1/"):
        # OPCIÓN 1: Autenticación con API Key (admin)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if api_key != settings.api_key:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "API Key inválida"}
                )

            # API Key válida - marcar como admin
            request.state.is_admin = True
            request.state.player_id = None
            return await call_next(request)

        # OPCIÓN 2: Autenticación con Player Token (jugador)
        player_id = request.headers.get("X-Player-ID")
        player_token = request.headers.get("X-Player-Token")

        # Verificar que los headers existan
        if not player_id or not player_token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Autenticación requerida. Usa X-API-Key (admin) o X-Player-ID + X-Player-Token (jugador)"
                }
            )

        # Validar que el player_id y token sean correctos
        try:
            player_repo = FirestorePlayerRepository()
            player = player_repo.get_by_id(player_id)

            if not player:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Player ID inválido"}
                )

            if player.player_token != player_token:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Token inválido"}
                )

            # Autenticación exitosa - agregar player_id al request state
            request.state.is_admin = False
            request.state.player_id = player_id
            request.state.player = player

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error de autenticación: {str(e)}"}
            )

    return await call_next(request)
