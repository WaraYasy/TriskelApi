"""
Service Layer para Games - Lógica de negocio
"""
from typing import Optional, List
from datetime import datetime
from app.models.game import Game, GameCreate, GameUpdate, LevelStart, LevelComplete
from app.repositories.game_repository import GameRepository
from app.repositories.player_repository import PlayerRepository
from app.services.player_service import PlayerService


class GameService:
    """Servicio para lógica de negocio de partidas"""

    def __init__(self):
        self.game_repo = GameRepository()
        self.player_repo = PlayerRepository()
        self.player_service = PlayerService()

    def create_game(self, game_data: GameCreate) -> Game:
        """
        Crea una nueva partida

        Lógica de negocio:
        - Verifica que el jugador exista
        - Verifica que no tenga partida activa
        """
        # Verificar que el jugador existe
        player = self.player_repo.get_by_id(game_data.player_id)
        if not player:
            raise ValueError("Jugador no encontrado")

        # Verificar que no tenga partida activa
        active_game = self.game_repo.get_active_game(game_data.player_id)
        if active_game:
            raise ValueError(f"El jugador ya tiene una partida activa: {active_game.game_id}")

        return self.game_repo.create(game_data)

    def get_game(self, game_id: str) -> Optional[Game]:
        """Obtiene una partida por ID"""
        return self.game_repo.get_by_id(game_id)

    def get_player_games(self, player_id: str, limit: int = 100) -> List[Game]:
        """Obtiene todas las partidas de un jugador"""
        return self.game_repo.get_by_player(player_id, limit=limit)

    def update_game(self, game_id: str, game_update: GameUpdate) -> Optional[Game]:
        """
        Actualiza una partida

        Lógica de negocio:
        - Si se completa la partida, actualiza stats del jugador
        """
        game = self.game_repo.get_by_id(game_id)
        if not game:
            return None

        # Actualizar la partida
        updated_game = self.game_repo.update(game_id, game_update)

        # Si la partida se completó o abandonó, actualizar stats del jugador
        if game_update.status in ["completed", "abandoned"]:
            self.player_service.update_player_stats_after_game(game.player_id, updated_game)

        return updated_game

    def start_level(self, game_id: str, level_data: LevelStart) -> Optional[Game]:
        """
        Inicia un nivel

        Lógica de negocio:
        - Verifica que la partida esté activa
        """
        game = self.game_repo.get_by_id(game_id)
        if not game:
            return None

        if game.status != "in_progress":
            raise ValueError("La partida no está activa")

        return self.game_repo.start_level(game_id, level_data)

    def complete_level(self, game_id: str, level_data: LevelComplete) -> Optional[Game]:
        """
        Completa un nivel

        Lógica de negocio:
        - Verifica que la partida esté activa
        - Actualiza completion_percentage
        - Si es el boss y lo derrota, marca boss_defeated
        """
        game = self.game_repo.get_by_id(game_id)
        if not game:
            return None

        if game.status != "in_progress":
            raise ValueError("La partida no está activa")

        # Completar el nivel
        updated_game = self.game_repo.complete_level(game_id, level_data)

        # Si completó el nivel final (boss), marcar como derrotado
        if level_data.level == "claro_almas":
            boss_update = GameUpdate(boss_defeated=True)
            updated_game = self.game_repo.update(game_id, boss_update)

        return updated_game

    def delete_game(self, game_id: str) -> bool:
        """Elimina una partida"""
        return self.game_repo.delete(game_id)

    def finish_game(self, game_id: str, completed: bool = True) -> Optional[Game]:
        """
        Finaliza una partida

        Lógica de negocio:
        - Marca la partida como completed o abandoned
        - Actualiza ended_at
        - Actualiza stats del jugador
        """
        game = self.game_repo.get_by_id(game_id)
        if not game:
            return None

        status = "completed" if completed else "abandoned"
        update_data = GameUpdate(
            status=status,
            ended_at=datetime.utcnow()
        )

        updated_game = self.game_repo.update(game_id, update_data)

        # Actualizar stats del jugador
        self.player_service.update_player_stats_after_game(game.player_id, updated_game)

        return updated_game
