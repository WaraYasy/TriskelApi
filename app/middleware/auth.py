"""
Middleware de autenticación

Valida player_id + player_token en headers para proteger endpoints.
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from app.domain.players.adapters.firestore_repository import FirestorePlayerRepository


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
    Middleware que valida player_id + player_token en los headers

    El juego debe incluir:
    - Header "X-Player-ID": el UUID del jugador
    - Header "X-Player-Token": el token secreto del jugador
    """
    path = request.url.path

    # Rutas públicas (sin autenticación)
    if path in PUBLIC_ROUTES or path.startswith("/docs") or path.startswith("/openapi"):
        return await call_next(request)

    # POST /v1/players (crear jugador) no requiere autenticación
    if path in CREATION_ROUTES and request.method == "POST":
        return await call_next(request)

    # El resto de rutas v1 requieren autenticación
    if path.startswith("/v1/"):
        player_id = request.headers.get("X-Player-ID")
        player_token = request.headers.get("X-Player-Token")

        # Verificar que los headers existan
        if not player_id or not player_token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Headers de autenticación requeridos: X-Player-ID y X-Player-Token"
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
            request.state.player_id = player_id
            request.state.player = player

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error de autenticación: {str(e)}"}
            )

    return await call_next(request)
