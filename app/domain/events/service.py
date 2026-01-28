"""Service para Events.

Lógica de negocio de eventos de gameplay.

Autor: Mandrágora
"""

from datetime import datetime
from typing import List, Optional

# Importar repositories de otros dominios para validación
from ..games.adapters.firestore_repository import FirestoreGameRepository
from ..players.adapters.firestore_repository import FirestorePlayerRepository
from .models import GameEvent
from .repository import EventRepository
from .schemas import EventBatchCreate, EventCreate


class EventService:
    """Servicio de eventos de gameplay.

    Responsabilidades:
    - Validar que game_id y player_id existen.
    - Delegar persistencia al repository.
    - Coordinar operaciones complejas.
    """

    def __init__(
        self,
        repository: EventRepository,
        game_repo: Optional[FirestoreGameRepository] = None,
        player_repo: Optional[FirestorePlayerRepository] = None,
    ):
        """Inicializa el servicio.

        Args:
            repository (EventRepository): Repositorio de eventos.
            game_repo (Optional[FirestoreGameRepository]): Repositorio de juegos (opcional).
            player_repo (Optional[FirestorePlayerRepository]): Repositorio de jugadores (opcional).
        """
        self.repository = repository
        self.game_repo = game_repo or FirestoreGameRepository()
        self.player_repo = player_repo or FirestorePlayerRepository()

    def create_event(self, event_data: EventCreate) -> GameEvent:
        """Crea un nuevo evento.

        Validaciones:
        - El jugador debe existir.
        - La partida debe existir (opcional: podemos hacerlo más permisivo).

        Args:
            event_data (EventCreate): Datos del evento.

        Returns:
            GameEvent: Evento creado.

        Raises:
            ValueError: Si el jugador o partida no existen.
        """
        # Validar que el jugador existe
        player = self.player_repo.get_by_id(event_data.player_id)
        if not player:
            raise ValueError(f"Jugador {event_data.player_id} no encontrado")

        # Validar que la partida existe (opcional)
        # Comentado por ahora para permitir eventos sin partida activa
        # game = self.game_repo.get_by_id(event_data.game_id)
        # if not game:
        #     raise ValueError(f"Partida {event_data.game_id} no encontrada")

        # Crear el evento
        return self.repository.create(event_data)

    def create_batch(self, batch_data: EventBatchCreate) -> List[GameEvent]:
        """Crea múltiples eventos en batch.

        Optimización: valida jugadores únicos una sola vez.

        Args:
            batch_data (EventBatchCreate): Datos del batch de eventos.

        Returns:
            List[GameEvent]: Lista de eventos creados.

        Raises:
            ValueError: Si algún jugador no existe.
        """
        # Extraer player_ids únicos
        player_ids = set(e.player_id for e in batch_data.events)

        # Validar que todos los jugadores existen
        for player_id in player_ids:
            player = self.player_repo.get_by_id(player_id)
            if not player:
                raise ValueError(f"Jugador {player_id} no encontrado")

        # Crear todos los eventos
        return self.repository.create_batch(batch_data.events)

    def get_event(self, event_id: str) -> Optional[GameEvent]:
        """Obtiene un evento por ID."""
        return self.repository.get_by_id(event_id)

    def get_game_events(self, game_id: str, limit: int = 1000) -> List[GameEvent]:
        """Obtiene todos los eventos de una partida."""
        return self.repository.get_by_game(game_id, limit)

    def get_player_events(self, player_id: str, limit: int = 1000) -> List[GameEvent]:
        """Obtiene todos los eventos de un jugador."""
        return self.repository.get_by_player(player_id, limit)

    def get_all_events(self, limit: int = 5000) -> List[GameEvent]:
        """Obtiene todos los eventos de todos los jugadores.

        ADMIN ONLY: Este método no debe ser expuesto a jugadores normales.

        Args:
            limit (int): Máximo número de eventos a retornar.

        Returns:
            List[GameEvent]: Lista de todos los eventos.
        """
        return self.repository.get_all(limit=limit)

    def get_events_by_type(
        self, event_type: str, game_id: Optional[str] = None, limit: int = 1000
    ) -> List[GameEvent]:
        """Obtiene eventos filtrados por tipo."""
        return self.repository.get_by_type(event_type, game_id, limit)

    def query_events(
        self,
        game_id: Optional[str] = None,
        player_id: Optional[str] = None,
        event_type: Optional[str] = None,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[GameEvent]:
        """Búsqueda de eventos con filtros múltiples."""
        return self.repository.query_events(
            game_id=game_id,
            player_id=player_id,
            event_type=event_type,
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
