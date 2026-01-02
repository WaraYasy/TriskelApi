"""
Endpoints REST para Players
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.player import Player, PlayerCreate, PlayerUpdate
from app.services.player_service import PlayerService

router = APIRouter(prefix="/v1/players", tags=["players"])

# Instancia del servicio
player_service = PlayerService()


@router.post("", response_model=Player, status_code=201)
def create_player(player_data: PlayerCreate):
    """Crear un nuevo jugador"""
    try:
        return player_service.create_player(player_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{player_id}", response_model=Player)
def get_player(player_id: str):
    """Obtener un jugador por ID"""
    player = player_service.get_player(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@router.get("", response_model=List[Player])
def get_all_players(limit: int = 100):
    """Listar todos los jugadores"""
    return player_service.get_all_players(limit=limit)


@router.patch("/{player_id}", response_model=Player)
def update_player(player_id: str, player_update: PlayerUpdate):
    """Actualizar un jugador"""
    player = player_service.update_player(player_id, player_update)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@router.delete("/{player_id}")
def delete_player(player_id: str):
    """Eliminar un jugador"""
    deleted = player_service.delete_player(player_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return {"message": "Jugador eliminado correctamente"}