"""
Service Layer para Players - Lógica de negocio

Contiene todas las reglas de negocio y validaciones.
Depende de la INTERFAZ IPlayerRepository, no de una implementación concreta.
"""

from typing import Optional, List

from .ports import IPlayerRepository
from .models import Player
from .schemas import PlayerCreate, PlayerUpdate


class PlayerService:
    """
    Servicio de lógica de negocio para jugadores.

    IMPORTANTE: Recibe el repository por Dependency Injection.
    No sabe si es Firestore, PostgreSQL o un Mock - solo usa la interfaz.
    """

    def __init__(self, repository: IPlayerRepository):
        """
        Inicializa el servicio con un repositorio.

        Args:
            repository: Implementación de IPlayerRepository (inyectada)
        """
        self.repository = repository

    def create_player(self, player_data: PlayerCreate) -> Player:
        """
        Crea un nuevo jugador.

        Regla de negocio: El username debe ser único.

        Args:
            player_data: Datos del jugador a crear

        Returns:
            Player: Jugador creado

        Raises:
            ValueError: Si el username ya existe
        """
        # Verificar que el username no exista
        existing = self.repository.get_by_username(player_data.username)
        if existing:
            raise ValueError(f"Username '{player_data.username}' ya existe")

        # Crear y retornar
        return self.repository.create(player_data)

    def get_player(self, player_id: str) -> Optional[Player]:
        """
        Obtiene un jugador por ID.

        Args:
            player_id: ID del jugador

        Returns:
            Player si existe, None si no
        """
        return self.repository.get_by_id(player_id)

    def get_all_players(self, limit: int = 100) -> List[Player]:
        """
        Lista todos los jugadores.

        Args:
            limit: Máximo número de jugadores a retornar

        Returns:
            Lista de jugadores
        """
        return self.repository.get_all(limit=limit)

    def update_player(self, player_id: str, player_update: PlayerUpdate) -> Optional[Player]:
        """
        Actualiza un jugador.

        Args:
            player_id: ID del jugador
            player_update: Campos a actualizar

        Returns:
            Player actualizado si existe, None si no
        """
        # Verificar que existe
        player = self.repository.get_by_id(player_id)
        if not player:
            return None

        # Actualizar y retornar
        return self.repository.update(player_id, player_update)

    def delete_player(self, player_id: str) -> bool:
        """
        Elimina un jugador.

        Args:
            player_id: ID del jugador

        Returns:
            True si se eliminó, False si no existía
        """
        return self.repository.delete(player_id)

    def update_player_stats_after_game(self, player_id: str, game) -> Optional[Player]:
        """
        Actualiza las estadísticas del jugador después de completar una partida.

        Esta es la LÓGICA COMPLEJA de negocio que calcula:
        - Incremento de partidas jugadas/completadas
        - Acumulación de tiempo de juego
        - Conteo de muertes totales
        - Análisis de elecciones morales (buenas vs malas)
        - Cálculo de alineación moral (-1 a 1)
        - Actualización de reliquia favorita
        - Actualización de mejor speedrun

        Args:
            player_id: ID del jugador
            game: Objeto Game con los datos de la partida

        Returns:
            Player actualizado si existe, None si no
        """
        player = self.repository.get_by_id(player_id)
        if not player:
            return None

        # 1. CONTADORES DE PARTIDAS
        player.games_played += 1
        if game.status == "completed":
            player.games_completed += 1

        # 2. TIEMPO TOTAL DE JUEGO
        player.total_playtime_seconds += game.total_time_seconds

        # 3. MUERTES TOTALES
        player.stats.total_deaths += game.metrics.total_deaths

        # 4. ANÁLISIS DE ELECCIONES MORALES
        # Mapeo de decisiones: {nivel: {acción_buena: nombre, acción_mala: nombre}}
        moral_choices_map = {
            "senda_ebano": {"good": "sanar", "bad": "forzar"},
            "fortaleza_gigantes": {"good": "construir", "bad": "destruir"},
            "aquelarre_sombras": {"good": "revelar", "bad": "ocultar"},
        }

        good_choices = 0
        bad_choices = 0

        # Analizar cada nivel
        for level, choices in moral_choices_map.items():
            # Obtener la decisión del jugador para este nivel
            player_choice = getattr(game.choices, level, None)

            if player_choice == choices["good"]:
                good_choices += 1
            elif player_choice == choices["bad"]:
                bad_choices += 1
            # Si es None, el jugador no tomó decisión en este nivel

        # Acumular en el total histórico
        player.stats.total_good_choices += good_choices
        player.stats.total_bad_choices += bad_choices

        # 5. CALCULAR ALINEACIÓN MORAL
        # Fórmula: (decisiones_buenas - decisiones_malas) / total_decisiones
        # Rango: -1.0 (completamente malo) a +1.0 (completamente bueno)
        total_choices = player.stats.total_good_choices + player.stats.total_bad_choices

        if total_choices > 0:
            player.stats.moral_alignment = (
                player.stats.total_good_choices - player.stats.total_bad_choices
            ) / total_choices
        # Si total_choices == 0, moral_alignment se queda en 0.0 (neutral)

        # 6. RELIQUIA FAVORITA (TODO: mejorar lógica para contar la más usada)
        # Por ahora: simplificación - usar la última obtenida
        if game.relics and len(game.relics) > 0:
            player.stats.favorite_relic = game.relics[-1]

        # 7. MEJOR SPEEDRUN (solo si completó el juego)
        if game.status == "completed":
            current_best = player.stats.best_speedrun_seconds

            # Si no tiene record o superó el record actual
            if current_best is None or game.total_time_seconds < current_best:
                player.stats.best_speedrun_seconds = game.total_time_seconds

        # 8. GUARDAR CAMBIOS
        # Usar PlayerUpdate para actualizar solo los campos modificados
        update_data = PlayerUpdate(
            total_playtime_seconds=player.total_playtime_seconds,
            games_played=player.games_played,
            games_completed=player.games_completed,
            stats=player.stats,
        )

        return self.repository.update(player_id, update_data)
