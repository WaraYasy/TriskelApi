"""
Rate Limiting Middleware usando slowapi.

Protege la API contra abusos y ataques de fuerza bruta.
Configuración por endpoint con límites específicos.

En producción usa Redis para almacenamiento distribuido.
En desarrollo o si Redis no está disponible, usa memoria local.

Autor: Mandrágora
"""

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address as slowapi_get_remote_address

from app.core.logger import logger


def get_remote_address(request):
    """
    Obtiene la IP real del cliente, considerando proxies (Railway, Cloudflare, etc.).

    En producción, Railway/Cloudflare ponen la IP real en X-Forwarded-For.
    Sin este ajuste, todas las requests parecen venir de la misma IP (el proxy).

    Args:
        request: Request de FastAPI

    Returns:
        str: IP address del cliente
    """
    # 1. Intentar obtener IP desde X-Forwarded-For (proxy/CDN)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For puede tener múltiples IPs: "client, proxy1, proxy2"
        # La primera es la IP real del cliente
        return forwarded.split(",")[0].strip()

    # 2. Fallback a la función por defecto de slowapi
    return slowapi_get_remote_address(request)


def get_storage_uri():
    """
    Determina el storage URI para rate limiting.

    Prioridad:
    1. Variable de entorno REDIS_URL (Railway, Heroku, etc.)
    2. Redis local en desarrollo (redis://localhost:6379)
    3. Fallback a memoria si Redis no está disponible

    Returns:
        str: URI de storage para slowapi
    """
    # 1. Intentar usar REDIS_URL de entorno (producción)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        logger.info(f"Rate limiting usando Redis: {redis_url.split('@')[0]}@***")
        return redis_url

    # 2. Intentar conectar a Redis local (desarrollo)
    try:
        import redis

        client = redis.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=1)
        client.ping()
        logger.info("Rate limiting usando Redis local: redis://localhost:6379")
        return "redis://localhost:6379"
    except Exception:
        pass

    # 3. Fallback a memoria
    logger.warning("Redis no disponible, usando memoria para rate limiting")
    logger.warning("Para producción, configura REDIS_URL en variables de entorno")
    return "memory://"


# Inicializar limiter
# - key_func: función para obtener la clave (IP por defecto)
# - default_limits: límites por defecto si no se especifica
# - storage_uri: Redis en producción, memoria en desarrollo
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],  # Sin límites por defecto, se configuran por endpoint
    storage_uri=get_storage_uri(),
)


# ==================== Límites por Endpoint ====================

# Autenticación (crítico - prevenir brute force)
AUTH_LOGIN_LIMIT = "5/minute"  # 5 intentos de login por minuto por IP
AUTH_REFRESH_LIMIT = "10/minute"  # 10 renovaciones de token por minuto
AUTH_CHANGE_PASSWORD_LIMIT = "3/minute"  # 3 cambios de contraseña por minuto

# Jugadores
PLAYER_CREATE_LIMIT = "10/minute"  # 10 jugadores nuevos por minuto por IP
PLAYER_LIST_LIMIT = "30/minute"  # 30 consultas de listado por minuto

# Partidas
GAME_CREATE_LIMIT = "20/hour"  # 20 partidas nuevas por hora por jugador
GAME_UPDATE_LIMIT = "100/minute"  # 100 actualizaciones por minuto (telemetría)

# Eventos (telemetría del juego)
EVENT_CREATE_LIMIT = "200/minute"  # 200 eventos por minuto (juego intensivo)

# Admin - Exportaciones (operaciones costosas)
ADMIN_EXPORT_LIMIT = "5/hour"  # 5 exportaciones por hora por usuario

# Admin - Migraciones (operaciones críticas)
ADMIN_MIGRATION_LIMIT = "10/hour"  # 10 operaciones de migración por hora

# Leaderboard (consultas públicas)
LEADERBOARD_LIMIT = "30/minute"  # 30 consultas de rankings por minuto


def get_user_id_from_request(request):
    """
    Función alternativa para rate limiting por user_id en lugar de IP.

    Útil para endpoints autenticados donde queremos limitar por usuario.
    Si no hay usuario autenticado, usa la IP.

    Args:
        request: Request de FastAPI

    Returns:
        str: user_id o IP address
    """
    # Intentar obtener user_id del estado del request (si fue autenticado)
    user = getattr(request.state, "user", None)
    if user and isinstance(user, dict):
        return f"user:{user.get('id', 'unknown')}"

    # Fallback a IP
    return get_remote_address(request)


# ==================== Error Handler Personalizado ====================


def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handler personalizado para errores de rate limiting.

    Retorna mensajes en español con información útil:
    - Cuándo puede volver a intentar (retry_after)
    - Qué límite se excedió
    - Mensaje claro en español

    Args:
        request: Request que excedió el límite
        exc: Excepción de RateLimitExceeded

    Returns:
        JSONResponse con mensaje de error personalizado
    """
    # Extraer información del error
    # exc.detail tiene formato: "5 per 1 minute"
    limit_info = str(exc.detail)

    # Calcular retry_after en segundos (aproximado)
    retry_after = 60  # Por defecto 1 minuto
    if "minute" in limit_info:
        retry_after = 60
    elif "hour" in limit_info:
        retry_after = 3600
    elif "day" in limit_info:
        retry_after = 86400

    # Traducir mensaje a español
    mensaje = (
        f"Has excedido el límite de solicitudes permitidas ({limit_info}). "
        f"Por favor, espera {retry_after // 60} minuto(s) antes de intentar nuevamente."
    )

    # Agregar contexto específico según el endpoint
    path = request.url.path
    if "/auth/login" in path:
        mensaje = (
            "Demasiados intentos de inicio de sesión. "
            "Por seguridad, debes esperar unos minutos antes de volver a intentar."
        )
    elif "/players" in path and request.method == "POST":
        mensaje = "Has creado demasiadas cuentas. Por favor, espera antes de crear otra."
    elif "/games" in path and request.method == "POST":
        mensaje = "Has iniciado demasiadas partidas. Por favor, espera antes de iniciar otra."

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": mensaje,
            "limit": limit_info,
            "retry_after_seconds": retry_after,
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": limit_info,
        },
    )
