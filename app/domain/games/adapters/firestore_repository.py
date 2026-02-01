"""Adaptador Firestore para Games.

Implementación concreta del repositorio usando Firestore.

Autor: Mandrágora
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from google.cloud.firestore_v1 import Client, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.logger import logger
from app.infrastructure.database.firebase_client import get_firestore_client

from ..models import Game
from ..ports import IGameRepository
from ..schemas import GameCreate, GameUpdate, LevelComplete, LevelStart


class FirestoreGameRepository(IGameRepository):
    """Repositorio de Games usando Firestore.

    Implementa todos los métodos definidos en IGameRepository.
    """

    COLLECTION_NAME = "games"

    def __init__(self, db: Optional[Client] = None):
        """Inicializa el repositorio."""
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def create(self, game_data: GameCreate) -> Game:
        """Crea una nueva partida en Firestore.

        Args:
            game_data (GameCreate): Datos de la partida a crear.

        Returns:
            Game: Partida creada.
        """
        # Crear el objeto Game completo
        game = Game(player_id=game_data.player_id)

        # Guardar en Firestore
        doc_ref = self.collection.document(game.game_id)
        doc_ref.set(game.to_dict())

        logger.info(f"Partida creada: {game.game_id}")
        return game

    def get_by_id(self, game_id: str) -> Optional[Game]:
        """Obtiene una partida por su ID.

        Args:
            game_id (str): ID de la partida.

        Returns:
            Optional[Game]: Game si existe, None si no.
        """
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return Game.from_dict(data)

    def get_by_player(
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
            limit (int): Máximo número de partidas.
            days (Optional[int]): Si se especifica, solo partidas de últimos N días.
            since (Optional[datetime]): Si se especifica, solo partidas después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo partidas antes de esta fecha.

        Returns:
            List[Game]: Lista de partidas del jugador filtradas.
        """
        # Base query: WHERE player_id == X
        query = self.collection.where(filter=FieldFilter("player_id", "==", player_id))

        # Aplicar filtro de fecha si se especificó
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("started_at", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("started_at", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("started_at", "<=", until))

        # Ordenar por fecha descendente y limitar
        query = query.order_by("started_at", direction=Query.DESCENDING).limit(limit)
        docs = query.stream()

        games = []
        for doc in docs:
            data = doc.to_dict()
            games.append(Game.from_dict(data))

        return games

    def get_active_game(self, player_id: str) -> Optional[Game]:
        """Obtiene la partida activa de un jugador.

        Una partida activa tiene status="in_progress".

        Args:
            player_id (str): ID del jugador.

        Returns:
            Optional[Game]: Partida activa si existe, None si no.
        """
        # Query: WHERE player_id == X AND status == "in_progress" LIMIT 1
        query = (
            self.collection.where(filter=FieldFilter("player_id", "==", player_id))
            .where(filter=FieldFilter("status", "==", "in_progress"))
            .limit(1)
        )
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            return Game.from_dict(data)

        return None

    def get_all(
        self,
        limit: int = 200,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Game]:
        """Obtiene todas las partidas de todos los jugadores con filtros opcionales.

        OPTIMIZACIÓN: Usar filtros de fecha reduce significativamente los costos de Firestore
        y mejora el rendimiento. Por defecto, limitar a 200 partidas.

        Args:
            limit (int): Máximo número de partidas a retornar (default: 200, antes: 1000).
            days (Optional[int]): Si se especifica, solo partidas de últimos N días.
            since (Optional[datetime]): Si se especifica, solo partidas después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo partidas antes de esta fecha.

        Returns:
            List[Game]: Lista de partidas ordenadas por fecha de inicio descendente.

        Examples:
            # Últimos 7 días
            repo.get_all(days=7, limit=100)

            # Rango específico
            repo.get_all(since=datetime(2026, 1, 1), until=datetime(2026, 1, 31))

            # Solo límite (comportamiento legacy)
            repo.get_all(limit=500)
        """
        query = self.collection

        # Aplicar filtros de fecha si se especificaron
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("started_at", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("started_at", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("started_at", "<=", until))

        # Ordenar por fecha descendente y limitar
        query = query.order_by("started_at", direction=Query.DESCENDING).limit(limit)
        docs = query.stream()

        games = []
        for doc in docs:
            data = doc.to_dict()
            games.append(Game.from_dict(data))

        filter_info = ""
        if days:
            filter_info = f" (últimos {days} días)"
        elif since or until:
            filter_info = " (filtrado por fecha)"

        logger.info(f"Fetched {len(games)} games{filter_info}")
        return games

    def update(self, game_id: str, game_update: GameUpdate) -> Optional[Game]:
        """Actualiza una partida existente.

        Args:
            game_id (str): ID de la partida.
            game_update (GameUpdate): Campos a actualizar.

        Returns:
            Optional[Game]: Partida actualizada si existe, None si no.
        """
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Obtener solo los campos que no son None
        update_data = game_update.model_dump(exclude_none=True)

        if not update_data:
            # No hay nada que actualizar
            return self.get_by_id(game_id)

        # Actualizar en Firestore
        doc_ref.update(update_data)
        logger.info(f"Partida actualizada: {game_id}")

        return self.get_by_id(game_id)

    def start_level(self, game_id: str, level_data: LevelStart) -> Optional[Game]:
        """Registra el inicio de un nivel.

        Args:
            game_id (str): ID de la partida.
            level_data (LevelStart): Datos del nivel.

        Returns:
            Optional[Game]: Partida actualizada si existe, None si no.
        """
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Actualizar nivel actual
        doc_ref.update({"current_level": level_data.level})

        logger.info(f"Nivel iniciado: {level_data.level} en partida {game_id}")
        return self.get_by_id(game_id)

    def complete_level(self, game_id: str, level_data: LevelComplete) -> Optional[Game]:
        """Registra la completación de un nivel.

        Actualiza múltiples campos:
        - Añade el nivel a levels_completed.
        - Actualiza métricas (tiempo, muertes).
        - Registra decisión moral si aplica.
        - Añade reliquia si aplica.
        - Calcula porcentaje de completado.

        Args:
            game_id (str): ID de la partida.
            level_data (LevelComplete): Datos del nivel completado.

        Returns:
            Optional[Game]: Partida actualizada si existe, None si no.
        """
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Obtener el game actual
        game = Game.from_dict(doc.to_dict())

        # Añadir a niveles completados (evitar duplicados)
        if level_data.level not in game.levels_completed:
            game.levels_completed.append(level_data.level)

        # Actualizar métricas del nivel
        game.metrics.time_per_level[level_data.level] = level_data.time_seconds
        game.metrics.deaths_per_level[level_data.level] = level_data.deaths
        game.metrics.total_deaths += level_data.deaths

        # Actualizar tiempo total de juego
        game.total_time_seconds += level_data.time_seconds

        # Registrar decisión moral si el nivel tiene una
        if level_data.choice:
            if level_data.level == "senda_ebano":
                game.choices.senda_ebano = level_data.choice
            elif level_data.level == "fortaleza_gigantes":
                game.choices.fortaleza_gigantes = level_data.choice
            elif level_data.level == "aquelarre_sombras":
                game.choices.aquelarre_sombras = level_data.choice

        # Añadir reliquia obtenida (evitar duplicados)
        if level_data.relic and level_data.relic not in game.relics:
            game.relics.append(level_data.relic)

        # Calcular porcentaje de completado (5 niveles totales en el juego)
        game.completion_percentage = (len(game.levels_completed) / 5) * 100

        # Guardar todos los cambios
        doc_ref.set(game.to_dict())

        logger.info(f"Nivel completado: {level_data.level} en partida {game_id}")
        return game

    def delete(self, game_id: str) -> bool:
        """Elimina una partida.

        Args:
            game_id (str): ID de la partida.

        Returns:
            bool: True si se eliminó, False si no existía.
        """
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        logger.info(f"Partida eliminada: {game_id}")
        return True

    def count(
        self,
        player_id: Optional[str] = None,
        status: Optional[str] = None,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> int:
        """Cuenta partidas usando Firestore count aggregation (eficiente).

        En lugar de traer todos los documentos y hacer len(), usa la API
        de agregación de Firestore que es mucho más eficiente.

        Args:
            player_id (Optional[str]): Filtrar por jugador.
            status (Optional[str]): Filtrar por estado (in_progress, completed, abandoned).
            days (Optional[int]): Solo partidas de últimos N días.
            since (Optional[datetime]): Partidas desde esta fecha.
            until (Optional[datetime]): Partidas hasta esta fecha.

        Returns:
            int: Número total de partidas que cumplen los filtros.

        Examples:
            # Contar todas las partidas
            total = repo.count()

            # Contar partidas de un jugador
            player_games = repo.count(player_id="player123")

            # Contar partidas completadas de últimos 30 días
            completed = repo.count(status="completed", days=30)
        """

        query = self.collection

        # Aplicar filtros
        if player_id:
            query = query.where(filter=FieldFilter("player_id", "==", player_id))

        if status:
            query = query.where(filter=FieldFilter("status", "==", status))

        # Filtros de fecha
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("started_at", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("started_at", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("started_at", "<=", until))

        # Ejecutar count aggregation
        try:
            aggregate_query = query.count(alias="game_count")
            results = aggregate_query.get()

            count_value = results[0][0].value
            logger.debug(f"Counted {count_value} games (aggregation query)")
            return count_value

        except Exception as e:
            logger.error(f"Error en count aggregation: {e}")
            # Fallback a método ineficiente si falla
            logger.warning("Usando fallback ineficiente: get_all + len()")
            games = self.get_all(limit=10000, days=days, since=since, until=until)
            return len(games)
