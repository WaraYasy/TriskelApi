"""
Logger estructurado para la aplicación

Sistema simple de logging con diferentes niveles.
Muestra mensajes en consola con formato claro.
"""
import logging
import sys
from typing import Any, Dict
from app.config.settings import settings


class StructuredLogger:
    """
    Logger simple con formato estructurado.

    Niveles disponibles:
    - DEBUG: Información detallada para debugging
    - INFO: Mensajes informativos normales
    - WARNING: Algo inesperado pero no crítico
    - ERROR: Error que impide una operación
    - CRITICAL: Error grave que puede parar la app
    """

    def __init__(self, name: str = "triskel-api"):
        self.logger = logging.getLogger(name)
        self._setup()

    def _setup(self):
        """Configura el logger"""
        # Nivel desde configuración (DEBUG, INFO, etc.)
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(level)

        # Si ya tiene handlers, no añadir más (evitar duplicados)
        if self.logger.handlers:
            return

        # Handler que escribe en consola
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Formato: "2025-01-09 10:30:45 | INFO | triskel-api | Mensaje aquí"
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _add_context(self, extra: Dict[str, Any]) -> str:
        """Convierte información extra en string legible"""
        if not extra:
            return ""

        parts = [f"{key}={value}" for key, value in extra.items()]
        return f" | {' | '.join(parts)}"

    def debug(self, message: str, **extra):
        """
        Log de debug (solo visible si LOG_LEVEL=DEBUG).

        Ejemplo:
            logger.debug("Consultando BD", player_id="123", query="SELECT")
        """
        context = self._add_context(extra)
        self.logger.debug(f"{message}{context}")

    def info(self, message: str, **extra):
        """
        Log informativo normal.

        Ejemplo:
            logger.info("Jugador creado", player_id="123", username="player1")
        """
        context = self._add_context(extra)
        self.logger.info(f"{message}{context}")

    def warning(self, message: str, **extra):
        """
        Log de advertencia (algo inesperado pero no crítico).

        Ejemplo:
            logger.warning("Username casi duplicado", username="test")
        """
        context = self._add_context(extra)
        self.logger.warning(f"{message}{context}")

    def error(self, message: str, **extra):
        """
        Log de error (algo falló).

        Ejemplo:
            logger.error("No se pudo crear jugador", error=str(e))
        """
        context = self._add_context(extra)
        self.logger.error(f"{message}{context}")

    def critical(self, message: str, **extra):
        """
        Log crítico (error grave).

        Ejemplo:
            logger.critical("Firebase no responde", error=str(e))
        """
        context = self._add_context(extra)
        self.logger.critical(f"{message}{context}")


# Instancia única para usar en toda la app
logger = StructuredLogger()
