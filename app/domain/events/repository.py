"""Repositorio para Events (acceso directo a Firestore).

Este dominio usa arquitectura SIMPLE (sin ports ni adapters).
El repository accede directamente a Firestore.

Autor: Mandrágora
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from google.cloud.firestore_v1 import Client, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from app.infrastructure.database.firebase_client import get_firestore_client

from .models import GameEvent
from .schemas import EventCreate


class EventRepository:
    """Repositorio de eventos de gameplay usando Firestore.

    Los eventos son inmutables (solo inserción, no actualización ni borrado).
    """

    COLLECTION_NAME = "events"

    def __init__(self, db: Optional[Client] = None):
        """Inicializa el repositorio.

        Args:
            db (Optional[Client]): Cliente Firestore opcional.
        """
        self.db = db or get_firestore_client()
        self.collection = self.db.collection(self.COLLECTION_NAME)

    def create(self, event_data: EventCreate) -> GameEvent:
        """Crea un nuevo evento en Firestore.

        Args:
            event_data (EventCreate): Datos del evento a crear.

        Returns:
            GameEvent: Evento creado con ID y timestamp generados.
        """
        # Crear el objeto GameEvent completo
        event = GameEvent(
            game_id=event_data.game_id,
            player_id=event_data.player_id,
            event_type=event_data.event_type,
            level=event_data.level,
            data=event_data.data,
        )

        # Guardar en Firestore
        doc_ref = self.collection.document(event.event_id)
        doc_ref.set(event.to_dict())

        print(f"✅ Evento creado: {event.event_type} en {event.level}")
        return event

    def create_batch(self, events_data: List[EventCreate]) -> List[GameEvent]:
        """Crea múltiples eventos en una sola operación batch.

        Optimización para Unity: reducir número de requests HTTP.

        Args:
            events_data (List[EventCreate]): Lista de eventos a crear.

        Returns:
            List[GameEvent]: Lista de eventos creados.
        """
        # Usar batch write para optimizar
        batch = self.db.batch()
        created_events = []

        for event_data in events_data:
            # Crear el objeto GameEvent
            event = GameEvent(
                game_id=event_data.game_id,
                player_id=event_data.player_id,
                event_type=event_data.event_type,
                level=event_data.level,
                data=event_data.data,
            )

            # Añadir al batch
            doc_ref = self.collection.document(event.event_id)
            batch.set(doc_ref, event.to_dict())
            created_events.append(event)

        # Ejecutar batch
        batch.commit()
        print(f"✅ Batch de {len(created_events)} eventos creado")

        return created_events

    def get_by_id(self, event_id: str) -> Optional[GameEvent]:
        """Obtiene un evento por su ID.

        Args:
            event_id (str): ID del evento.

        Returns:
            Optional[GameEvent]: Evento encontrado o None.
        """
        doc_ref = self.collection.document(event_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return GameEvent.from_dict(data)

    def get_by_game(
        self,
        game_id: str,
        limit: int = 500,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[GameEvent]:
        """Obtiene todos los eventos de una partida con filtros opcionales.

        Args:
            game_id (str): ID de la partida.
            limit (int): Máximo número de eventos a retornar (default: 500, antes: 1000).
            days (Optional[int]): Si se especifica, solo eventos de últimos N días.
            since (Optional[datetime]): Si se especifica, solo eventos después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo eventos antes de esta fecha.

        Returns:
            List[GameEvent]: Lista de eventos ordenados por timestamp descendente.
        """
        query = self.collection.where(filter=FieldFilter("game_id", "==", game_id))

        # Aplicar filtros de fecha si se especificaron
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("timestamp", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("timestamp", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("timestamp", "<=", until))

        query = query.order_by("timestamp", direction=Query.DESCENDING).limit(limit)
        docs = query.stream()

        events = []
        for doc in docs:
            data = doc.to_dict()
            events.append(GameEvent.from_dict(data))

        return events

    def get_by_player(
        self,
        player_id: str,
        limit: int = 200,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[GameEvent]:
        """Obtiene todos los eventos de un jugador con filtros opcionales.

        Args:
            player_id (str): ID del jugador.
            limit (int): Máximo número de eventos a retornar (default: 200, antes: 1000).
            days (Optional[int]): Si se especifica, solo eventos de últimos N días.
            since (Optional[datetime]): Si se especifica, solo eventos después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo eventos antes de esta fecha.

        Returns:
            List[GameEvent]: Lista de eventos ordenados por timestamp descendente.
        """
        query = self.collection.where(filter=FieldFilter("player_id", "==", player_id))

        # Aplicar filtros de fecha si se especificaron
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("timestamp", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("timestamp", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("timestamp", "<=", until))

        query = query.order_by("timestamp", direction=Query.DESCENDING).limit(limit)
        docs = query.stream()

        events = []
        for doc in docs:
            data = doc.to_dict()
            events.append(GameEvent.from_dict(data))

        return events

    def get_all(
        self,
        limit: int = 100,
        days: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[GameEvent]:
        """Obtiene todos los eventos de todos los jugadores con filtros opcionales (admin only).

        OPTIMIZACIÓN CRÍTICA: Límite reducido de 5000 → 100 por defecto.
        Events son muy numerosos y pesados. Se RECOMIENDA usar filtros de fecha.

        Args:
            limit (int): Máximo número de eventos a retornar (default: 100, antes: 5000).
            days (Optional[int]): Si se especifica, solo eventos de últimos N días.
            since (Optional[datetime]): Si se especifica, solo eventos después de esta fecha.
            until (Optional[datetime]): Si se especifica, solo eventos antes de esta fecha.

        Returns:
            List[GameEvent]: Lista de eventos ordenados por timestamp descendente.
        """
        query = self.collection

        # Aplicar filtros de fecha si se especificaron
        if days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            query = query.where(filter=FieldFilter("timestamp", ">=", cutoff))
        elif since is not None:
            query = query.where(filter=FieldFilter("timestamp", ">=", since))

        if until is not None:
            query = query.where(filter=FieldFilter("timestamp", "<=", until))

        query = query.order_by("timestamp", direction=Query.DESCENDING).limit(limit)
        docs = query.stream()

        events = []
        for doc in docs:
            data = doc.to_dict()
            events.append(GameEvent.from_dict(data))

        filter_info = ""
        if days:
            filter_info = f" (últimos {days} días)"
        elif since or until:
            filter_info = " (filtrado por fecha)"

        print(f"✅ Fetched {len(events)} events{filter_info}")
        return events

    def get_by_type(
        self, event_type: str, game_id: Optional[str] = None, limit: int = 1000
    ) -> List[GameEvent]:
        """Obtiene eventos filtrados por tipo.

        Args:
            event_type (str): Tipo de evento a buscar.
            game_id (Optional[str]): Opcional - filtrar también por partida.
            limit (int): Máximo número de eventos a retornar.

        Returns:
            List[GameEvent]: Lista de eventos ordenados por timestamp.
        """
        try:
            query = self.collection.where(filter=FieldFilter("event_type", "==", event_type))

            if game_id:
                query = query.where(filter=FieldFilter("game_id", "==", game_id))

            query = query.order_by("timestamp", direction=Query.DESCENDING).limit(limit)
            docs = query.stream()

            events = []
            for doc in docs:
                data = doc.to_dict()
                events.append(GameEvent.from_dict(data))

            return events
        except Exception as e:
            # Si la query falla por índice compuesto faltante en Firestore
            print(f"⚠️ Query get_by_type falló: {e}")
            print("   Puede que necesites crear un índice compuesto en Firestore")
            print("   Índice requerido: event_type (ASC) + game_id (ASC) + timestamp (DESC)")
            return []

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
        """Búsqueda de eventos con filtros múltiples.

        IMPORTANTE: Firestore tiene limitaciones con queries compuestas.
        Solo soportamos ciertas combinaciones de filtros.

        Args:
            game_id (Optional[str]): Filtrar por partida.
            player_id (Optional[str]): Filtrar por jugador.
            event_type (Optional[str]): Filtrar por tipo.
            level (Optional[str]): Filtrar por nivel.
            start_time (Optional[datetime]): Eventos desde esta fecha.
            end_time (Optional[datetime]): Eventos hasta esta fecha.
            limit (int): Máximo número de eventos.

        Returns:
            List[GameEvent]: Lista de eventos ordenados por timestamp.
        """
        query = self.collection

        # Aplicar filtros (máximo 1-2 por limitaciones de Firestore)
        if game_id:
            query = query.where(filter=FieldFilter("game_id", "==", game_id))

        if player_id:
            query = query.where(filter=FieldFilter("player_id", "==", player_id))

        if event_type:
            query = query.where(filter=FieldFilter("event_type", "==", event_type))

        if level:
            query = query.where(filter=FieldFilter("level", "==", level))

        # Filtros de rango de tiempo
        if start_time:
            query = query.where(filter=FieldFilter("timestamp", ">=", start_time))

        if end_time:
            query = query.where(filter=FieldFilter("timestamp", "<=", end_time))

        # Ordenar y limitar
        query = query.order_by("timestamp", direction=Query.DESCENDING).limit(limit)

        # Ejecutar query
        try:
            docs = query.stream()
            events = []
            for doc in docs:
                data = doc.to_dict()
                events.append(GameEvent.from_dict(data))
            return events
        except Exception as e:
            # Si la query falla por índice compuesto faltante en Firestore
            print(f"⚠️ Query compleja falló: {e}")
            print("   Puede que necesites crear un índice compuesto en Firestore")
            return []
