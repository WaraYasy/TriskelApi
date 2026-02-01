"""Service Layer para Games - Lógica de negocio.

Contiene todas las reglas de negocio de partidas.
Depende de interfaces, no de implementaciones concretas.

Autor: Mandrágora
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.core.logger import logger

from ..players.ports import IPlayerRepository
from ..players.service import PlayerService
from .models import Game
from .ports import IGameRepository
from .schemas import GameCreate, GameUpdate, LevelComplete, LevelStart


class GameService:
    """Servicio de lógica de negocio para partidas.

    Recibe sus dependencias por inyección:
    - game_repository: Para persistir partidas.
    - player_repository: Para verificar que el jugador existe.
    - player_service: Para actualizar stats del jugador al terminar.
    """

    def __init__(
        self,
        game_repository: IGameRepository,
        player_repository: IPlayerRepository,
        player_service: PlayerService,
    ):
        """Inicializa el servicio con sus dependencias.

        Args:
            game_repository (IGameRepository): Implementación de IGameRepository.
            player_repository (IPlayerRepository): Implementación de IPlayerRepository.
            player_service (PlayerService): Servicio de Players.
        """
        self.game_repository = game_repository
        self.player_repository = player_repository
        self.player_service = player_service

    def create_game(self, game_data: GameCreate) -> Game:
        """Crea una nueva partida.

        Reglas de negocio:
        - El jugador debe existir.
        - Si el jugador tiene otra partida activa, se cierra automáticamente como "abandoned".

        Args:
            game_data (GameCreate): Datos de la partida a crear.

        Returns:
            Game: Partida creada.

        Raises:
            ValueError: Si el jugador no existe.
        """
        # Verificar que el jugador existe
        player = self.player_repository.get_by_id(game_data.player_id)
        if not player:
            raise ValueError("Jugador no encontrado")

        # Si tiene partida activa, cerrarla automáticamente
        active_game = self.game_repository.get_active_game(game_data.player_id)
        if active_game:
            close_update = GameUpdate(status="abandoned", ended_at=datetime.now(timezone.utc))
            closed_game = self.game_repository.update(active_game.game_id, close_update)
            # Actualizar stats del jugador con la partida abandonada
            if closed_game:
                self.player_service.update_player_stats_after_game(game_data.player_id, closed_game)
            print(
                f"⚠️  Partida anterior {active_game.game_id} cerrada automáticamente como 'abandoned'"
            )

        # Crear y retornar la nueva partida
        return self.game_repository.create(game_data)

    def get_game(self, game_id: str) -> Optional[Game]:
        """Obtiene una partida por ID.

        Args:
            game_id (str): ID de la partida.

        Returns:
            Optional[Game]: Game si existe, None si no.
        """
        return self.game_repository.get_by_id(game_id)

    def get_player_games(
        self,
        player_id: str,
        limit: int = 100,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Game]:
        """Obtiene todas las partidas de un jugador con filtros opcionales.

        Args:
            player_id (str): ID del jugador.
            limit (int): Máximo número de partidas a retornar.
            days (Optional[int]): Si se especifica, solo partidas de últimos N días.
            since (Optional[datetime]): Si se especifica, solo partidas después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo partidas antes de esta fecha.

        Returns:
            List[Game]: Lista de partidas filtradas.
        """
        return self.game_repository.get_by_player(
            player_id, limit=limit, days=days, since=since, until=until
        )

    def get_all_games(
        self,
        limit: int = 200,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Game]:
        """Obtiene todas las partidas de todos los jugadores con filtros opcionales.

        ADMIN ONLY: Este método no debe ser expuesto a jugadores normales.
        OPTIMIZACIÓN: Límite reducido de 1000 → 200. Usa filtros de fecha para mejor rendimiento.

        Args:
            limit (int): Máximo número de partidas a retornar (default: 200).
            days (Optional[int]): Si se especifica, solo partidas de últimos N días.
            since (Optional[datetime]): Si se especifica, solo partidas después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo partidas antes de esta fecha.

        Returns:
            List[Game]: Lista de todas las partidas filtradas.
        """
        return self.game_repository.get_all(limit=limit, days=days, since=since, until=until)

    def update_game(self, game_id: str, game_update: GameUpdate) -> Optional[Game]:
        """Actualiza una partida.

        Regla de negocio:
        - Si la partida se completa o abandona, actualiza stats del jugador.

        Args:
            game_id (str): ID de la partida.
            game_update (GameUpdate): Campos a actualizar.

        Returns:
            Optional[Game]: Game actualizado si existe, None si no.
        """
        game = self.game_repository.get_by_id(game_id)
        if not game:
            return None

        # Actualizar la partida
        updated_game = self.game_repository.update(game_id, game_update)

        # Si la partida terminó, actualizar stats del jugador
        if game_update.status in ["completed", "abandoned"]:
            self.player_service.update_player_stats_after_game(game.player_id, updated_game)

        return updated_game

    def start_level(self, game_id: str, level_data: LevelStart) -> Optional[Game]:
        """Inicia un nivel.

        Regla de negocio:
        - La partida debe estar activa (status="in_progress").

        Args:
            game_id (str): ID de la partida.
            level_data (LevelStart): Datos del nivel a iniciar.

        Returns:
            Optional[Game]: Game actualizado si existe, None si no.

        Raises:
            ValueError: Si la partida no está activa.
        """
        game = self.game_repository.get_by_id(game_id)
        if not game:
            return None

        # Verificar que está activa
        if game.status != "in_progress":
            raise ValueError("La partida no está activa")

        return self.game_repository.start_level(game_id, level_data)

    def complete_level(self, game_id: str, level_data: LevelComplete) -> Optional[Game]:
        """Completa un nivel.

        Reglas de negocio:
        - La partida debe estar activa.
        - Si es el nivel final (claro_almas), marca boss_defeated=True.

        Args:
            game_id (str): ID de la partida.
            level_data (LevelComplete): Datos del nivel completado.

        Returns:
            Optional[Game]: Game actualizado si existe, None si no.

        Raises:
            ValueError: Si la partida no está activa.
        """
        game = self.game_repository.get_by_id(game_id)
        if not game:
            return None

        # Verificar que está activa
        if game.status != "in_progress":
            raise ValueError("La partida no está activa")

        # Completar el nivel
        updated_game = self.game_repository.complete_level(game_id, level_data)

        # Si completó el nivel final (boss), marcarlo
        if level_data.level == "claro_almas":
            boss_update = GameUpdate(boss_defeated=True)
            updated_game = self.game_repository.update(game_id, boss_update)

        return updated_game

    def delete_game(self, game_id: str) -> bool:
        """Elimina una partida.

        Args:
            game_id (str): ID de la partida.

        Returns:
            bool: True si se eliminó, False si no existía.
        """
        return self.game_repository.delete(game_id)

    def finish_game(self, game_id: str, completed: bool = True) -> Optional[Game]:
        """Finaliza una partida.

        Marca la partida como completed o abandoned y actualiza stats del jugador.

        Args:
            game_id (str): ID de la partida.
            completed (bool): True si completó, False si abandonó.

        Returns:
            Optional[Game]: Game actualizado si existe, None si no.
        """
        game = self.game_repository.get_by_id(game_id)
        if not game:
            return None

        # Preparar actualización
        status = "completed" if completed else "abandoned"
        update_data = GameUpdate(status=status, ended_at=datetime.now(timezone.utc))

        # Actualizar partida
        updated_game = self.game_repository.update(game_id, update_data)

        # Actualizar stats del jugador
        self.player_service.update_player_stats_after_game(game.player_id, updated_game)

        return updated_game
