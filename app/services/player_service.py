"""
Service Layer para Players - Lógica de negocio
"""
from typing import Optional, List
from app.models.player import Player, PlayerCreate, PlayerUpdate
from app.repositories.player_repository import PlayerRepository


class PlayerService:
    """Servicio para lógica de negocio de jugadores"""

    def __init__(self):
        self.player_repo = PlayerRepository()

    def create_player(self, player_data: PlayerCreate) -> Player:
        """
        Crea un nuevo jugador

        Lógica de negocio:
        - Verifica que el username no exista
        """
        # Verificar username único
        existing = self.player_repo.get_by_username(player_data.username)
        if existing:
            raise ValueError(f"Username '{player_data.username}' ya existe")

        return self.player_repo.create(player_data)

    def get_player(self, player_id: str) -> Optional[Player]:
        """Obtiene un jugador por ID"""
        return self.player_repo.get_by_id(player_id)

    def get_all_players(self, limit: int = 100) -> List[Player]:
        """Lista todos los jugadores"""
        return self.player_repo.get_all(limit=limit)

    def update_player(self, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
        """Actualiza un jugador"""
        player = self.player_repo.get_by_id(player_id)
        if not player:
            return None

        return self.player_repo.update(player_id, player_update)

    def delete_player(self, player_id: str) -> bool:
        """Elimina un jugador"""
        return self.player_repo.delete(player_id)

    def update_player_stats_after_game(self, player_id: str, game) -> Optional[Player]:
        """
        Actualiza las estadísticas del jugador después de completar una partida

        Lógica de negocio:
        - Incrementa games_played y games_completed
        - Suma total_playtime_seconds
        - Actualiza stats globales
        - Calcula moral alignment
        """
        player = self.player_repo.get_by_id(player_id)
        if not player:
            return None

        # Incrementar contadores
        player.games_played += 1
        if game.status == "completed":
            player.games_completed += 1

        # Sumar tiempo de juego
        player.total_playtime_seconds += game.total_time_seconds

        # Actualizar muertes totales
        player.stats.total_deaths += game.metrics.total_deaths

        # Actualizar elecciones morales
        good_choices = 0
        bad_choices = 0

        if game.choices.senda_ebano == "sanar":
            good_choices += 1
        elif game.choices.senda_ebano == "forzar":
            bad_choices += 1

        if game.choices.fortaleza_gigantes == "construir":
            good_choices += 1
        elif game.choices.fortaleza_gigantes == "destruir":
            bad_choices += 1

        if game.choices.aquelarre_sombras == "revelar":
            good_choices += 1
        elif game.choices.aquelarre_sombras == "ocultar":
            bad_choices += 1

        player.stats.total_good_choices += good_choices
        player.stats.total_bad_choices += bad_choices

        # Calcular moral alignment (-1 a 1)
        total_choices = player.stats.total_good_choices + player.stats.total_bad_choices
        if total_choices > 0:
            player.stats.moral_alignment = (
                (player.stats.total_good_choices - player.stats.total_bad_choices) / total_choices
            )

        # Actualizar reliquia favorita (la más usada)
        # Por simplicidad, usar la última obtenida
        if game.relics:
            player.stats.favorite_relic = game.relics[-1]

        # Actualizar best speedrun
        if game.status == "completed":
            if player.stats.best_speedrun_seconds is None or game.total_time_seconds < player.stats.best_speedrun_seconds:
                player.stats.best_speedrun_seconds = game.total_time_seconds

        # Guardar cambios
        update_data = PlayerUpdate(
            total_playtime_seconds=player.total_playtime_seconds,
            games_played=player.games_played,
            games_completed=player.games_completed,
            stats=player.stats
        )

        return self.player_repo.update(player_id, update_data)
