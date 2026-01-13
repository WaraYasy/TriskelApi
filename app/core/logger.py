"""
Logger estructurado para la aplicación

Sistema avanzado de logging con:
- Rotación de archivos (por tamaño y tiempo)
- Formato JSON estructurado para producción
- Formato texto legible para desarrollo
- Múltiples handlers (consola + archivo)
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict
from app.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Formateador que convierte logs a JSON estructurado.

    Útil para producción donde los logs se procesan con herramientas
    de análisis (ELK, Splunk, CloudWatch, etc.)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Convierte el log record a JSON"""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Añadir campos extra si existen
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Añadir información de excepción si existe
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """
    Logger estructurado con rotación de archivos.

    Características:
    - Rotación por tamaño (RotatingFileHandler)
    - Rotación por tiempo (TimedRotatingFileHandler)
    - Formato JSON para producción
    - Formato texto para desarrollo
    - Logs en consola y archivo

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
        """Configura el logger con handlers y formateadores"""
        # Nivel desde configuración (DEBUG, INFO, etc.)
        level = getattr(logging, settings.log_level.upper(), logging.INFO)
        self.logger.setLevel(level)

        # Si ya tiene handlers, no añadir más (evitar duplicados)
        if self.logger.handlers:
            return

        # 1. Handler de consola (siempre activo)
        self._add_console_handler(level)

        # 2. Handler de archivo (solo si está activado)
        if settings.log_to_file:
            self._ensure_log_directory()
            self._add_file_handlers(level)

    def _ensure_log_directory(self):
        """Crea el directorio de logs si no existe"""
        log_dir = Path(settings.log_directory)
        log_dir.mkdir(parents=True, exist_ok=True)

    def _add_console_handler(self, level: int):
        """Añade handler para logs en consola"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Formato según configuración
        if settings.log_format == "json":
            console_handler.setFormatter(JSONFormatter())
        else:
            # Formato texto: "2025-01-09 10:30:45 | INFO | triskel-api | Mensaje aquí"
            text_formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(text_formatter)

        self.logger.addHandler(console_handler)

    def _add_file_handlers(self, level: int):
        """Añade handlers para logs en archivos con rotación"""
        log_dir = settings.log_directory

        # 1. Handler con rotación por TAMAÑO
        # Crea archivos como: app.log, app.log.1, app.log.2, etc.
        size_based_file = os.path.join(log_dir, "app.log")
        max_bytes = settings.log_max_file_size_mb * 1024 * 1024  # MB a bytes

        rotating_handler = RotatingFileHandler(
            filename=size_based_file,
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        rotating_handler.setLevel(level)

        # 2. Handler con rotación por TIEMPO
        # Crea archivos como: app.2025-01-13.log, app.2025-01-14.log, etc.
        time_based_file = os.path.join(log_dir, "app")

        timed_handler = TimedRotatingFileHandler(
            filename=time_based_file,
            when='midnight',  # Rotar a medianoche
            interval=1,  # Cada día
            backupCount=settings.log_rotation_days,
            encoding='utf-8'
        )
        timed_handler.suffix = "%Y-%m-%d.log"
        timed_handler.setLevel(level)

        # 3. Handler solo para ERRORES (útil para monitoreo)
        error_file = os.path.join(log_dir, "errors.log")
        error_handler = RotatingFileHandler(
            filename=error_file,
            maxBytes=max_bytes,
            backupCount=settings.log_backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)  # Solo ERROR y CRITICAL

        # Aplicar formateador a todos los handlers
        formatter = JSONFormatter() if settings.log_format == "json" else logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        rotating_handler.setFormatter(formatter)
        timed_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)

        # Añadir todos los handlers
        self.logger.addHandler(rotating_handler)
        self.logger.addHandler(timed_handler)
        self.logger.addHandler(error_handler)

    def _create_log_record(self, level: int, message: str, extra: Dict[str, Any]):
        """Crea un log record con campos extra"""
        # Para JSON formatter, guardamos los campos extra
        if settings.log_format == "json" and extra:
            # Crear un record con extra_fields
            record = self.logger.makeRecord(
                self.logger.name,
                level,
                "(unknown file)",
                0,
                message,
                (),
                None
            )
            record.extra_fields = extra
            return record
        else:
            # Para formato texto, añadir al mensaje
            context = self._add_context(extra)
            return message + context

    def _add_context(self, extra: Dict[str, Any]) -> str:
        """Convierte información extra en string legible (para formato texto)"""
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
        if settings.log_format == "json" and extra:
            record = self._create_log_record(logging.DEBUG, message, extra)
            self.logger.handle(record)
        else:
            context = self._add_context(extra)
            self.logger.debug(f"{message}{context}")

    def info(self, message: str, **extra):
        """
        Log informativo normal.

        Ejemplo:
            logger.info("Jugador creado", player_id="123", username="player1")
        """
        if settings.log_format == "json" and extra:
            record = self._create_log_record(logging.INFO, message, extra)
            self.logger.handle(record)
        else:
            context = self._add_context(extra)
            self.logger.info(f"{message}{context}")

    def warning(self, message: str, **extra):
        """
        Log de advertencia (algo inesperado pero no crítico).

        Ejemplo:
            logger.warning("Username casi duplicado", username="test")
        """
        if settings.log_format == "json" and extra:
            record = self._create_log_record(logging.WARNING, message, extra)
            self.logger.handle(record)
        else:
            context = self._add_context(extra)
            self.logger.warning(f"{message}{context}")

    def error(self, message: str, **extra):
        """
        Log de error (algo falló).

        Ejemplo:
            logger.error("No se pudo crear jugador", error=str(e))
        """
        if settings.log_format == "json" and extra:
            record = self._create_log_record(logging.ERROR, message, extra)
            self.logger.handle(record)
        else:
            context = self._add_context(extra)
            self.logger.error(f"{message}{context}")

    def critical(self, message: str, **extra):
        """
        Log crítico (error grave).

        Ejemplo:
            logger.critical("Firebase no responde", error=str(e))
        """
        if settings.log_format == "json" and extra:
            record = self._create_log_record(logging.CRITICAL, message, extra)
            self.logger.handle(record)
        else:
            context = self._add_context(extra)
            self.logger.critical(f"{message}{context}")


# Instancia única para usar en toda la app
logger = StructuredLogger()
