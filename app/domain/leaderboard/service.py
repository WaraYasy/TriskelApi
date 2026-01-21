"""
Service para Leaderboard

Logica de calculo y actualizacion de rankings.
"""

from datetime import datetime, timezone
from typing import List, Optional

from app.core.logger import logger

from ..games.adapters.firestore_repository import FirestoreGameRepository
from ..players.adapters.firestore_repository import FirestorePlayerRepository
from .models import Leaderboard, LeaderboardEntry, LeaderboardType
from .repository import LeaderboardRepository

# Nombres legibles para cada tipo de leaderboard
LEADERBOARD_NAMES = {
    LeaderboardType.SPEEDRUN: "Speedrun - Mejor Tiempo",
    LeaderboardType.MORAL_GOOD: "Guardian del Bien",
    LeaderboardType.MORAL_EVIL: "Senor de la Oscuridad",
    LeaderboardType.COMPLETIONS: "Completionista",
}

LEADERBOARD_DESCRIPTIONS = {
    LeaderboardType.SPEEDRUN: "Jugadores mas rapidos en completar el juego",
    LeaderboardType.MORAL_GOOD: "Jugadores con mayor alineacion hacia el bien",
    LeaderboardType.MORAL_EVIL: "Jugadores con mayor alineacion hacia el mal",
    LeaderboardType.COMPLETIONS: "Jugadores con mas partidas completadas",
}


class LeaderboardService:
    """
    Servicio de leaderboards.

    Responsabilidades:
    - Calcular rankings para cada tipo
    - Actualizar leaderboards en Firestore
    - Consultar leaderboards existentes
    """

    MAX_ENTRIES = 100  # Maximo entradas por leaderboard

    def __init__(
        self,
        repository: LeaderboardRepository,
        player_repo: Optional[FirestorePlayerRepository] = None,
        game_repo: Optional[FirestoreGameRepository] = None,
    ):
        """Inicializa el servicio"""
        self.repository = repository
        self.player_repo = player_repo or FirestorePlayerRepository()
        self.game_repo = game_repo or FirestoreGameRepository()

    def get_leaderboard(
        self, leaderboard_type: LeaderboardType
    ) -> Optional[Leaderboard]:
        """Obtiene un leaderboard por tipo"""
        return self.repository.get_by_type(leaderboard_type)

    def get_all_leaderboards_info(self) -> List[dict]:
        """
        Obtiene informacion basica de todos los leaderboards.

        Returns:
            Lista con info de cada leaderboard disponible
        """
        return [
            {
                "leaderboard_id": lb_type.value,
                "name": LEADERBOARD_NAMES[lb_type],
                "description": LEADERBOARD_DESCRIPTIONS[lb_type],
            }
            for lb_type in LeaderboardType
        ]

    def refresh_all_leaderboards(self) -> List[str]:
        """
        Recalcula y actualiza todos los leaderboards.

        Este metodo es llamado por el scheduler cada 6 horas.

        Returns:
            Lista de leaderboards actualizados
        """
        logger.info("Iniciando recalculo de leaderboards...")
        updated = []

        # Obtener todos los jugadores con partidas completadas
        players = self.player_repo.get_all(limit=1000)
        eligible_players = [p for p in players if p.games_completed > 0]

        logger.info(
            f"Procesando {len(eligible_players)} jugadores con partidas completadas"
        )

        # Calcular cada leaderboard
        self._refresh_speedrun(eligible_players)
        updated.append("speedrun")

        self._refresh_moral_good(eligible_players)
        updated.append("moral_good")

        self._refresh_moral_evil(eligible_players)
        updated.append("moral_evil")

        self._refresh_completions(eligible_players)
        updated.append("completions")

        logger.info(f"Leaderboards actualizados: {updated}")
        return updated

    def _refresh_speedrun(self, players) -> None:
        """
        Recalcula el leaderboard de speedrun.

        Criterio: Menor best_speedrun_seconds = mejor
        """
        # Filtrar jugadores con speedrun registrado
        speedrun_players = [
            p for p in players if p.stats.best_speedrun_seconds is not None
        ]

        # Ordenar por tiempo (menor = mejor)
        speedrun_players.sort(key=lambda p: p.stats.best_speedrun_seconds)

        entries = []
        for rank, player in enumerate(speedrun_players[: self.MAX_ENTRIES], 1):
            # Buscar la partida donde logro este tiempo
            games = self.game_repo.get_by_player(player.player_id)
            best_game = next(
                (
                    g
                    for g in games
                    if g.status == "completed"
                    and g.total_time_seconds == player.stats.best_speedrun_seconds
                ),
                None,
            )

            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    player_id=player.player_id,
                    username=player.username,
                    value=float(player.stats.best_speedrun_seconds),
                    game_id=best_game.game_id if best_game else "",
                    achieved_at=(
                        best_game.ended_at
                        if best_game and best_game.ended_at
                        else datetime.now(timezone.utc)
                    ),
                )
            )

        leaderboard = Leaderboard(
            leaderboard_id=LeaderboardType.SPEEDRUN, entries=entries
        )
        self.repository.save(leaderboard)

    def _refresh_moral_good(self, players) -> None:
        """
        Recalcula el leaderboard moral_good.

        Criterio: Mayor moral_alignment (+1) = mejor
        """
        # Ordenar por moral_alignment (mayor = mejor para bien)
        sorted_players = sorted(
            players,
            key=lambda p: p.stats.moral_alignment,
            reverse=True,  # Mayor primero
        )

        entries = []
        for rank, player in enumerate(sorted_players[: self.MAX_ENTRIES], 1):
            # Buscar ultima partida completada
            games = self.game_repo.get_by_player(player.player_id)
            last_completed = next((g for g in games if g.status == "completed"), None)

            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    player_id=player.player_id,
                    username=player.username,
                    value=player.stats.moral_alignment,
                    game_id=last_completed.game_id if last_completed else "",
                    achieved_at=(
                        last_completed.ended_at
                        if last_completed and last_completed.ended_at
                        else player.last_login or datetime.now(timezone.utc)
                    ),
                )
            )

        leaderboard = Leaderboard(
            leaderboard_id=LeaderboardType.MORAL_GOOD, entries=entries
        )
        self.repository.save(leaderboard)

    def _refresh_moral_evil(self, players) -> None:
        """
        Recalcula el leaderboard moral_evil.

        Criterio: Menor moral_alignment (-1) = mejor
        """
        # Ordenar por moral_alignment (menor = mejor para mal)
        sorted_players = sorted(
            players,
            key=lambda p: p.stats.moral_alignment,  # Menor primero (default ascending)
        )

        entries = []
        for rank, player in enumerate(sorted_players[: self.MAX_ENTRIES], 1):
            # Buscar ultima partida completada
            games = self.game_repo.get_by_player(player.player_id)
            last_completed = next((g for g in games if g.status == "completed"), None)

            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    player_id=player.player_id,
                    username=player.username,
                    value=player.stats.moral_alignment,
                    game_id=last_completed.game_id if last_completed else "",
                    achieved_at=(
                        last_completed.ended_at
                        if last_completed and last_completed.ended_at
                        else player.last_login or datetime.now(timezone.utc)
                    ),
                )
            )

        leaderboard = Leaderboard(
            leaderboard_id=LeaderboardType.MORAL_EVIL, entries=entries
        )
        self.repository.save(leaderboard)

    def _refresh_completions(self, players) -> None:
        """
        Recalcula el leaderboard de completions.

        Criterio: Mayor games_completed = mejor
        """
        # Ordenar por games_completed (mayor = mejor)
        sorted_players = sorted(players, key=lambda p: p.games_completed, reverse=True)

        entries = []
        for rank, player in enumerate(sorted_players[: self.MAX_ENTRIES], 1):
            # Buscar ultima partida completada
            games = self.game_repo.get_by_player(player.player_id)
            last_completed = next((g for g in games if g.status == "completed"), None)

            entries.append(
                LeaderboardEntry(
                    rank=rank,
                    player_id=player.player_id,
                    username=player.username,
                    value=float(player.games_completed),
                    game_id=last_completed.game_id if last_completed else "",
                    achieved_at=(
                        last_completed.ended_at
                        if last_completed and last_completed.ended_at
                        else player.last_login or datetime.now(timezone.utc)
                    ),
                )
            )

        leaderboard = Leaderboard(
            leaderboard_id=LeaderboardType.COMPLETIONS, entries=entries
        )
        self.repository.save(leaderboard)
