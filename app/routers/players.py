"""
Endpoints REST para Players
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.player import Player, PlayerCreate, PlayerUpdate
from app.repositories.player_repository import PlayerRepository

router = APIRouter(prefix="/v1/players", tags=["players"])

# Instancia del repositorio
player_repo = PlayerRepository()


@router.post("", response_model=Player, status_code=201)
def create_player(player_data: PlayerCreate):
    """Crear un nuevo jugador"""
    # Verificar que no exista el username
    existing = player_repo.get_by_username(player_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username ya existe")

    return player_repo.create(player_data)


@router.get("/{player_id}", response_model=Player)
def get_player(player_id: str):
    """Obtener un jugador por ID"""
    player = player_repo.get_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@router.get("", response_model=List[Player])
def get_all_players(limit: int = 100):
    """Listar todos los jugadores"""
    return player_repo.get_all(limit=limit)


@router.patch("/{player_id}", response_model=Player)
def update_player(player_id: str, player_update: PlayerUpdate):
    """Actualizar un jugador"""
    player = player_repo.update(player_id, player_update)
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@router.delete("/{player_id}")
def delete_player(player_id: str):
    """Eliminar un jugador"""
    deleted = player_repo.delete(player_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return {"message": "Jugador eliminado correctamente"}