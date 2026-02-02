"""Schemas (DTOs) para la API de Games.

Modelos de entrada y salida para los endpoints de partidas.

Autor: Mandrágora
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.core.exceptions import ValidationException
from app.core.validators import validate_choice, validate_level_name, validate_relic


class GameCreate(BaseModel):
    """Datos necesarios para crear una partida nueva.

    El player_id es opcional - si no se envía, se usa el del jugador autenticado.

    Attributes:
        player_id (Optional[str]): ID del usuario (opcional).
    """

    player_id: Optional[str] = None

    class Config:
        json_schema_extra = {"example": {"player_id": "123e4567-e89b-12d3-a456-426614174000"}}


class GameUpdate(BaseModel):
    """Datos que se pueden actualizar de una partida.

    Todos los campos son opcionales.

    Attributes:
        status (Optional[str]): Nuevo estado.
        ended_at (Optional[datetime]): Fecha de fin.
        completion_percentage (Optional[float]): Nuevo porcentaje.
        total_time_seconds (Optional[int]): Nuevo tiempo total.
        current_level (Optional[str]): Nuevo nivel actual.
        boss_defeated (Optional[bool]): Estado del jefe.
    """

    status: Optional[str] = None
    ended_at: Optional[datetime] = None
    completion_percentage: Optional[float] = None
    total_time_seconds: Optional[int] = None
    current_level: Optional[str] = None
    boss_defeated: Optional[bool] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el status sea uno de los válidos."""
        if v is None:
            return v
        valid_statuses = ["in_progress", "completed", "abandoned"]
        if v not in valid_statuses:
            raise ValueError(f"Status '{v}' no válido. Válidos: {', '.join(valid_statuses)}")
        return v

    @field_validator("completion_percentage")
    @classmethod
    def validate_completion(cls, v: Optional[float]) -> Optional[float]:
        """Valida que el porcentaje esté entre 0 y 100."""
        if v is None:
            return v
        if v < 0 or v > 100:
            raise ValueError("El porcentaje de completado debe estar entre 0 y 100")
        return v

    @field_validator("total_time_seconds")
    @classmethod
    def validate_total_time(cls, v: Optional[int]) -> Optional[int]:
        """Valida que el tiempo total sea positivo."""
        if v is None:
            return v
        if v < 0:
            raise ValueError("El tiempo total no puede ser negativo")
        return v

    @field_validator("current_level")
    @classmethod
    def validate_current_level(cls, v: Optional[str]) -> Optional[str]:
        """Valida que el nivel actual sea válido."""
        if v is None:
            return v
        try:
            validate_level_name(v)
        except ValidationException as e:
            raise ValueError(str(e))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "completion_percentage": 100.0,
                "boss_defeated": True,
            }
        }


class LevelStart(BaseModel):
    """Datos al iniciar un nivel.

    Solo necesita el nombre del nivel.

    Attributes:
        level (str): Identificador del nivel.
    """

    level: str  # hub_central | senda_ebano | fortaleza_gigantes | aquelarre_sombras | claro_almas

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Valida que el nivel sea uno de los 5 niveles válidos."""
        try:
            validate_level_name(v)
        except ValidationException as e:
            raise ValueError(str(e))
        return v

    class Config:
        json_schema_extra = {"example": {"level": "senda_ebano"}}


class LevelComplete(BaseModel):
    """Datos al completar un nivel.

    Incluye métricas, decisión moral (si aplica) y reliquia (si aplica).

    Attributes:
        level (str): Nombre del nivel completado.
        time_seconds (Optional[int]): Tiempo que tardó (opcional, se calcula automáticamente si no se envía).
        deaths (int): Número de muertes en el nivel.
        choice (Optional[str]): Decisión moral (si aplica).
        relic (Optional[str]): Reliquia obtenida (si aplica).
    """

    level: str  # Nombre del nivel completado
    time_seconds: Optional[int] = None  # Tiempo (opcional, se calcula si no se envía)
    deaths: int  # Número de muertes en el nivel
    choice: Optional[str] = None  # Decisión moral (si el nivel tiene)
    relic: Optional[str] = None  # Reliquia obtenida (si el nivel da una)

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Valida que el nivel sea uno de los 5 niveles válidos."""
        try:
            validate_level_name(v)
        except ValidationException as e:
            raise ValueError(str(e))
        return v

    @field_validator("time_seconds")
    @classmethod
    def validate_time(cls, v: Optional[int]) -> Optional[int]:
        """Valida que el tiempo sea positivo y mayor a 0 (si se proporciona)."""
        if v is None:
            return v  # Será calculado automáticamente por el servidor
        if v <= 0:
            raise ValueError(
                "El tiempo debe ser mayor a 0 segundos (no se permiten valores 0 o negativos)"
            )
        if v > 86400:  # 24 horas en segundos
            raise ValueError("El tiempo no puede ser mayor a 24 horas")
        return v

    @field_validator("deaths")
    @classmethod
    def validate_deaths(cls, v: int) -> int:
        """Valida que las muertes sean un número válido."""
        if v < 0:
            raise ValueError("El número de muertes no puede ser negativo")
        if v > 9999:  # Límite razonable
            raise ValueError("El número de muertes no puede ser mayor a 9999")
        return v

    @field_validator("choice")
    @classmethod
    def validate_choice_value(cls, v: Optional[str], info) -> Optional[str]:
        """Valida que la decisión moral sea válida para el nivel."""
        if v is None:
            return v
        # Obtener el nivel del contexto de validación
        level = info.data.get("level")
        if level:
            try:
                validate_choice(level, v)
            except ValidationException as e:
                raise ValueError(str(e))
        return v

    @field_validator("relic")
    @classmethod
    def validate_relic_value(cls, v: Optional[str]) -> Optional[str]:
        """Valida que la reliquia sea una de las 3 válidas."""
        if v is None:
            return v
        try:
            validate_relic(v)
        except ValidationException as e:
            raise ValueError(str(e))
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "level": "senda_ebano",
                "deaths": 3,
                "choice": "sanar",
                "relic": "lirio",
                # time_seconds es opcional - se calcula automáticamente si no se envía
            }
        }
