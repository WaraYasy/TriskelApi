"""
API REST para Games

Endpoints de FastAPI para gestionar partidas.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from .ports import IGameRepository
from .service import GameService
from .models import Game
from .schemas import GameCreate, GameUpdate, LevelStart, LevelComplete
from .adapters.firestore_repository import FirestoreGameRepository

# Importar dependencies de Players (Games depende de Players)
from ..players.ports import IPlayerRepository
from ..players.service import PlayerService
from ..players.adapters.firestore_repository import FirestorePlayerRepository


# Router de FastAPI
router = APIRouter(prefix="/v1/games", tags=["Games"])


# ==================== DEPENDENCY INJECTION ====================

def get_game_repository() -> IGameRepository:
    """Dependency que provee el repositorio de Games"""
    return FirestoreGameRepository()


def get_player_repository() -> IPlayerRepository:
    """Dependency que provee el repositorio de Players"""
    return FirestorePlayerRepository()


def get_player_service(
    player_repository: IPlayerRepository = Depends(get_player_repository)
) -> PlayerService:
    """Dependency que provee el servicio de Players"""
    return PlayerService(repository=player_repository)


def get_game_service(
    game_repository: IGameRepository = Depends(get_game_repository),
    player_repository: IPlayerRepository = Depends(get_player_repository),
    player_service: PlayerService = Depends(get_player_service)
) -> GameService:
    """
    Dependency que provee el servicio de Games.

    Games depende de Players para:
    - Verificar que el jugador existe al crear partida
    - Actualizar stats del jugador al terminar partida
    """
    return GameService(
        game_repository=game_repository,
        player_repository=player_repository,
        player_service=player_service
    )


# ==================== ENDPOINTS ====================

@router.post("", response_model=Game, status_code=201)
def create_game(
    game_data: GameCreate,
    service: GameService = Depends(get_game_service)
):
    """
    Iniciar una nueva partida.

    Reglas:
    - El jugador debe existir
    - No puede tener otra partida activa

    Args:
        game_data: Datos de la partida (solo player_id)
        service: Servicio inyectado

    Returns:
        Game: Partida creada

    Raises:
        HTTPException 404: Si el jugador no existe
        HTTPException 409: Si ya tiene partida activa
    """
    try:
        return service.create_game(game_data)
    except ValueError as e:
        # Distinguir tipo de error
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))


@router.get("/{game_id}", response_model=Game)
def get_game(
    game_id: str,
    service: GameService = Depends(get_game_service)
):
    """
    Obtener una partida por ID.

    Args:
        game_id: ID de la partida
        service: Servicio inyectado

    Returns:
        Game: Partida completa

    Raises:
        HTTPException 404: Si la partida no existe
    """
    game = service.get_game(game_id)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    return game


@router.get("/player/{player_id}", response_model=List[Game])
def get_player_games(
    player_id: str,
    limit: int = 100,
    service: GameService = Depends(get_game_service)
):
    """
    Obtener todas las partidas de un jugador.

    Args:
        player_id: ID del jugador
        limit: Máximo número de partidas a retornar
        service: Servicio inyectado

    Returns:
        List[Game]: Lista de partidas
    """
    return service.get_player_games(player_id, limit=limit)


@router.patch("/{game_id}", response_model=Game)
def update_game(
    game_id: str,
    game_update: GameUpdate,
    service: GameService = Depends(get_game_service)
):
    """
    Actualizar una partida.

    Args:
        game_id: ID de la partida
        game_update: Campos a actualizar
        service: Servicio inyectado

    Returns:
        Game: Partida actualizada

    Raises:
        HTTPException 404: Si la partida no existe
    """
    game = service.update_game(game_id, game_update)

    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    return game


@router.post("/{game_id}/level/start", response_model=Game)
def start_level(
    game_id: str,
    level_data: LevelStart,
    service: GameService = Depends(get_game_service)
):
    """
    Registrar inicio de un nivel.

    Args:
        game_id: ID de la partida
        level_data: Datos del nivel a iniciar
        service: Servicio inyectado

    Returns:
        Game: Partida actualizada

    Raises:
        HTTPException 404: Si la partida no existe
        HTTPException 400: Si la partida no está activa
    """
    try:
        game = service.start_level(game_id, level_data)

        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")

        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/level/complete", response_model=Game)
def complete_level(
    game_id: str,
    level_data: LevelComplete,
    service: GameService = Depends(get_game_service)
):
    """
    Registrar completado de un nivel.

    Actualiza:
    - Niveles completados
    - Métricas (tiempo, muertes)
    - Decisión moral (si aplica)
    - Reliquia obtenida (si aplica)
    - Porcentaje de completado

    Args:
        game_id: ID de la partida
        level_data: Datos del nivel completado
        service: Servicio inyectado

    Returns:
        Game: Partida actualizada

    Raises:
        HTTPException 404: Si la partida no existe
        HTTPException 400: Si la partida no está activa
    """
    try:
        game = service.complete_level(game_id, level_data)

        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")

        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{game_id}")
def delete_game(
    game_id: str,
    service: GameService = Depends(get_game_service)
):
    """
    Eliminar una partida.

    Args:
        game_id: ID de la partida
        service: Servicio inyectado

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException 404: Si la partida no existe
    """
    deleted = service.delete_game(game_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    return {"message": "Partida eliminada correctamente"}
