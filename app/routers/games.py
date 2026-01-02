"""
Endpoints REST para Games
"""
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.game import Game, GameCreate, GameUpdate, LevelStart, LevelComplete
from app.services.game_service import GameService

router = APIRouter(prefix="/v1/games", tags=["games"])

game_service = GameService()


@router.post("", response_model=Game, status_code=201)
def create_game(game_data: GameCreate):
    """Iniciar una nueva partida"""
    try:
        return game_service.create_game(game_data)
    except ValueError as e:
        if "no encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=409, detail=str(e))


@router.get("/{game_id}", response_model=Game)
def get_game(game_id: str):
    """Obtener una partida por ID"""
    game = game_service.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return game


@router.get("/player/{player_id}", response_model=List[Game])
def get_player_games(player_id: str, limit: int = 100):
    """Obtener todas las partidas de un jugador"""
    return game_service.get_player_games(player_id, limit=limit)


@router.patch("/{game_id}", response_model=Game)
def update_game(game_id: str, game_update: GameUpdate):
    """Actualizar una partida"""
    game = game_service.update_game(game_id, game_update)
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return game


@router.post("/{game_id}/level/start", response_model=Game)
def start_level(game_id: str, level_data: LevelStart):
    """Registrar inicio de un nivel"""
    try:
        game = game_service.start_level(game_id, level_data)
        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/level/complete", response_model=Game)
def complete_level(game_id: str, level_data: LevelComplete):
    """Registrar completado de un nivel"""
    try:
        game = game_service.complete_level(game_id, level_data)
        if not game:
            raise HTTPException(status_code=404, detail="Partida no encontrada")
        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{game_id}")
def delete_game(game_id: str):
    """Eliminar una partida"""
    deleted = game_service.delete_game(game_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Partida no encontrada")
    return {"message": "Partida eliminada correctamente"}
