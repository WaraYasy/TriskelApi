"""
Repositorio para operaciones CRUD de Games en Firestore
"""
from typing import Optional, List
from google.cloud.firestore_v1 import Client
from datetime import datetime
from app.models.game import Game, GameCreate, GameUpdate, LevelStart, LevelComplete
from app.firebase import get_firestore_client


class GameRepository:
    """Repositorio para gestionar partidas en Firestore"""

    COLLECTION_NAME = "games"

    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def create(self, game_data: GameCreate) -> Game:
        """Crea una nueva partida"""
        game = Game(player_id=game_data.player_id)

        doc_ref = self.collection.document(game.game_id)
        doc_ref.set(game.to_dict())

        print(f"✅ Partida creada: {game.game_id}")
        return game

    def get_by_id(self, game_id: str) -> Optional[Game]:
        """Obtiene una partida por ID"""
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return Game.from_dict(data)

    def get_by_player(self, player_id: str, limit: int = 100) -> List[Game]:
        """Obtiene todas las partidas de un jugador"""
        query = self.collection.where("player_id", "==", player_id).limit(limit)
        docs = query.stream()

        games = []
        for doc in docs:
            data = doc.to_dict()
            games.append(Game.from_dict(data))

        return games

    def get_active_game(self, player_id: str) -> Optional[Game]:
        """Obtiene la partida activa de un jugador (si existe)"""
        query = self.collection.where("player_id", "==", player_id).where("status", "==", "in_progress").limit(1)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            return Game.from_dict(data)

        return None

    def update(self, game_id: str, game_update: GameUpdate) -> Optional[Game]:
        """Actualiza una partida"""
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        update_data = game_update.model_dump(exclude_none=True)

        if not update_data:
            return self.get_by_id(game_id)

        doc_ref.update(update_data)
        print(f"✅ Partida actualizada: {game_id}")

        return self.get_by_id(game_id)

    def start_level(self, game_id: str, level_data: LevelStart) -> Optional[Game]:
        """Registra el inicio de un nivel"""
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        # Actualizar nivel actual
        doc_ref.update({
            "current_level": level_data.level
        })

        print(f"✅ Nivel iniciado: {level_data.level} en partida {game_id}")
        return self.get_by_id(game_id)

    def complete_level(self, game_id: str, level_data: LevelComplete) -> Optional[Game]:
        """Registra la completación de un nivel"""
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        game = Game.from_dict(doc.to_dict())

        # Actualizar niveles completados
        if level_data.level not in game.levels_completed:
            game.levels_completed.append(level_data.level)

        # Actualizar métricas
        game.metrics.time_per_level[level_data.level] = level_data.time_seconds
        game.metrics.deaths_per_level[level_data.level] = level_data.deaths
        game.metrics.total_deaths += level_data.deaths

        # Actualizar tiempo total
        game.total_time_seconds += level_data.time_seconds

        # Actualizar elección moral si aplica
        if level_data.choice:
            if level_data.level == "senda_ebano":
                game.choices.senda_ebano = level_data.choice
            elif level_data.level == "fortaleza_gigantes":
                game.choices.fortaleza_gigantes = level_data.choice
            elif level_data.level == "aquelarre_sombras":
                game.choices.aquelarre_sombras = level_data.choice

        # Actualizar reliquia si aplica
        if level_data.relic and level_data.relic not in game.relics:
            game.relics.append(level_data.relic)

        # Calcular porcentaje de completado (5 niveles totales)
        game.completion_percentage = (len(game.levels_completed) / 5) * 100

        # Guardar cambios
        doc_ref.set(game.to_dict())

        print(f"✅ Nivel completado: {level_data.level} en partida {game_id}")
        return game

    def delete(self, game_id: str) -> bool:
        """Elimina una partida"""
        doc_ref = self.collection.document(game_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        print(f"✅ Partida eliminada: {game_id}")
        return True
