"""
API REST para Players

Endpoints de FastAPI para gestionar jugadores.
Usa Dependency Injection para desacoplar de implementaciones concretas.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from .ports import IPlayerRepository
from .service import PlayerService
from .models import Player
from .schemas import PlayerCreate, PlayerUpdate, PlayerAuthResponse
from .adapters.firestore_repository import FirestorePlayerRepository


# Router de FastAPI
router = APIRouter(prefix="/v1/players", tags=["Players"])


# ==================== DEPENDENCY INJECTION ====================

def get_player_repository() -> IPlayerRepository:
    """
    Dependency que provee el repositorio de Players.

    Retorna la implementación concreta (Firestore).
    Si queremos cambiar a otra BD, solo cambiamos esto.

    Returns:
        IPlayerRepository: Implementación del repositorio
    """
    return FirestorePlayerRepository()


def get_player_service(
    repository: IPlayerRepository = Depends(get_player_repository)
) -> PlayerService:
    """
    Dependency que provee el servicio de Players.

    Recibe el repository por inyección automática.

    Args:
        repository: Repositorio inyectado por FastAPI

    Returns:
        PlayerService: Servicio configurado
    """
    return PlayerService(repository=repository)


# ==================== ENDPOINTS ====================

@router.post("", response_model=PlayerAuthResponse, status_code=201)
def create_player(
    player_data: PlayerCreate,
    service: PlayerService = Depends(get_player_service)
):
    """
    Crear un nuevo jugador.

    Devuelve player_id y player_token que el juego debe guardar.
    El token se envía en futuras peticiones para autenticación.

    Args:
        player_data: Datos del jugador (username, email)
        service: Servicio inyectado automáticamente

    Returns:
        PlayerAuthResponse: ID, username y token del jugador

    Raises:
        HTTPException 400: Si el username ya existe
    """
    try:
        player = service.create_player(player_data)

        # Retornar solo los datos necesarios para autenticación
        return PlayerAuthResponse(
            player_id=player.player_id,
            username=player.username,
            player_token=player.player_token
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{player_id}", response_model=Player)
def get_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service)
):
    """
    Obtener un jugador por ID.

    Args:
        player_id: ID único del jugador
        service: Servicio inyectado

    Returns:
        Player: Datos completos del jugador

    Raises:
        HTTPException 404: Si el jugador no existe
    """
    player = service.get_player(player_id)

    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return player


@router.get("", response_model=List[Player])
def get_all_players(
    limit: int = 100,
    service: PlayerService = Depends(get_player_service)
):
    """
    Listar todos los jugadores.

    Args:
        limit: Máximo número de jugadores a retornar (default: 100)
        service: Servicio inyectado

    Returns:
        List[Player]: Lista de jugadores
    """
    return service.get_all_players(limit=limit)


@router.patch("/{player_id}", response_model=Player)
def update_player(
    player_id: str,
    player_update: PlayerUpdate,
    service: PlayerService = Depends(get_player_service)
):
    """
    Actualizar un jugador.

    Solo se actualizan los campos enviados (parcial).

    Args:
        player_id: ID del jugador
        player_update: Campos a actualizar
        service: Servicio inyectado

    Returns:
        Player: Jugador actualizado

    Raises:
        HTTPException 404: Si el jugador no existe
    """
    player = service.update_player(player_id, player_update)

    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return player


@router.delete("/{player_id}")
def delete_player(
    player_id: str,
    service: PlayerService = Depends(get_player_service)
):
    """
    Eliminar un jugador.

    Args:
        player_id: ID del jugador
        service: Servicio inyectado

    Returns:
        dict: Mensaje de confirmación

    Raises:
        HTTPException 404: Si el jugador no existe
    """
    deleted = service.delete_player(player_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return {"message": "Jugador eliminado correctamente"}
