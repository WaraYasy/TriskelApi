"""
Middleware de autenticación

Soporta TRES tipos de autenticación:
1. JWT Token: Para administradores del dashboard (Bearer token)
2. API Key: Para administración programática (acceso completo)
3. Player Token: Para jugadores (solo acceden a sus propios datos)
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from app.config.settings import settings
from app.domain.players.adapters.firestore_repository import FirestorePlayerRepository

# Rutas que NO requieren autenticación
PUBLIC_ROUTES = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/v1/auth/login",  # Login público
    "/v1/auth/refresh",  # Refresh público
]

# Rutas que permiten crear jugadores sin autenticación
CREATION_ROUTES = [
    "/v1/players",  # POST crear jugador
    "/v1/players/login",  # POST login/registro
]


async def auth_middleware(request: Request, call_next):
    """
    Middleware que valida autenticación de tres formas:

    1. JWT TOKEN (admin dashboard):
       - Header "Authorization: Bearer <token>"
       - Acceso completo a endpoints de admin según permisos del rol

    2. API KEY (admin programmatic):
       - Header "X-API-Key": la clave de administración
       - Acceso completo a todos los endpoints

    3. PLAYER TOKEN (jugadores):
       - Header "X-Player-ID": el UUID del jugador
       - Header "X-Player-Token": el token secreto del jugador
       - Solo accede a sus propios datos
    """
    path = request.url.path

    # Rutas públicas (sin autenticación)
    if (
        path in PUBLIC_ROUTES
        or path.startswith("/docs")
        or path.startswith("/openapi")
        or path.startswith("/web")
    ):
        return await call_next(request)

    # POST /v1/players (crear jugador) no requiere autenticación
    if path in CREATION_ROUTES and request.method == "POST":
        return await call_next(request)

    # El resto de rutas v1 requieren autenticación
    if path.startswith("/v1/"):
        # OPCIÓN 1: Autenticación con JWT Token (admin dashboard)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

            try:
                # Decodificar y validar JWT
                payload = jwt.decode(
                    token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
                )

                # Verificar que sea access token
                if payload.get("type") == "access":
                    # JWT válido - marcar como admin con datos del token
                    request.state.is_admin = True
                    request.state.player_id = None
                    request.state.admin_user = {
                        "id": payload["user_id"],
                        "username": payload["username"],
                        "role": payload["role"],
                    }
                    return await call_next(request)
                else:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Token inválido. Usa access token, no refresh token"},
                    )

            except JWTError:
                return JSONResponse(status_code=401, content={"detail": "JWT inválido o expirado"})

        # OPCIÓN 2: Autenticación con API Key (admin programmatic)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            if api_key != settings.api_key:
                return JSONResponse(status_code=401, content={"detail": "API Key inválida"})

            # API Key válida - marcar como admin
            request.state.is_admin = True
            request.state.player_id = None
            return await call_next(request)

        # OPCIÓN 3: Autenticación con Player Token (jugador)
        player_id = request.headers.get("X-Player-ID")
        player_token = request.headers.get("X-Player-Token")

        # Verificar que los headers existan
        if not player_id or not player_token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Autenticación requerida. Usa Authorization: Bearer <JWT> (admin), X-API-Key (admin), o X-Player-ID + X-Player-Token (jugador)"
                },
            )

        # Validar que el player_id y token sean correctos
        try:
            player_repo = FirestorePlayerRepository()
            player = player_repo.get_by_id(player_id)

            if not player:
                return JSONResponse(status_code=401, content={"detail": "Player ID inválido"})

            if player.player_token != player_token:
                return JSONResponse(status_code=401, content={"detail": "Token inválido"})

            # Autenticación exitosa - agregar player_id al request state
            request.state.is_admin = False
            request.state.player_id = player_id
            request.state.player = player

        except Exception as e:
            return JSONResponse(
                status_code=500, content={"detail": f"Error de autenticación: {str(e)}"}
            )

    return await call_next(request)
