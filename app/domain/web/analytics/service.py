"""Servicio de Analytics.

Consume la API REST de Triskel para obtener datos y generar métricas.

Este servicio NO accede directamente a la base de datos.
En su lugar, hace peticiones HTTP a la propia API REST.

Esto mantiene el desacoplamiento y asegura que:
- Analytics no tiene lógica de negocio duplicada.
- Usa las mismas validaciones que el juego.
- Es más fácil de escalar (puede estar en otro servidor).

Autor: Mandrágora
"""

import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Imports opcionales (instalar si se necesitan visualizaciones)
try:
    import httpx
    import pandas as pd
    import plotly.express as px

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("⚠️  Analytics libs no instaladas. Instala: pip install httpx pandas plotly")


class AnalyticsService:
    """Servicio para agregación de datos y generación de métricas.

    Consume la API REST y genera:
    - Métricas agregadas.
    - DataFrames con Pandas.
    - Gráficos con Plotly.
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        api_key: str = None,
        use_mock_data: bool = False,
    ):
        """Inicializa el servicio.

        Args:
            api_base_url (str): URL base de la API REST.
            api_key (str, optional): API Key para acceso admin.
            use_mock_data (bool): Si es True, usa datos ficticios en lugar de Firebase (para pruebas).
        """
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.use_mock_data = use_mock_data

        # Sistema de caching con TTL
        self._cache = {}
        self._cache_timestamp = {}
        self._cache_ttl = 300  # 5 minutos

        # DEBUG: Log de inicialización
        print("[Analytics] Initializing service:")
        print(f"  - API Base URL: {api_base_url}")
        print(f"  - API Key: {'SET' if api_key else 'NOT SET'}")
        print(f"  - Mock Mode: {use_mock_data}")

        if ANALYTICS_AVAILABLE:
            headers = {}
            if api_key:
                headers["X-API-Key"] = api_key
                print("  - X-API-Key header: Added to client")
            # Configurar timeout extendido para peticiones lentas de Firebase
            # timeout=60s para requests individuales, 120s para todo el proceso
            self.client = httpx.Client(
                base_url=api_base_url, headers=headers, timeout=httpx.Timeout(60.0, connect=10.0)
            )
        else:
            self.client = None

    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el caché para una clave es válido (no expiró el TTL).

        Args:
            key (str): Clave del caché.

        Returns:
            bool: True si el caché es válido, False si expiró o no existe.
        """
        if key not in self._cache_timestamp:
            return False
        return (time.time() - self._cache_timestamp[key]) < self._cache_ttl

    def _get_from_cache(self, key: str):
        """Obtiene un valor del cache."""
        return self._cache.get(key)

    def _set_cache(self, key: str, value):
        """Guarda un valor en el cache con timestamp."""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()

    def _generate_mock_players(self) -> List[Dict[str, Any]]:
        """Genera datos mock de jugadores para pruebas sin Firebase."""
        from datetime import datetime, timedelta

        base_date = datetime.now()

        return [
            {
                "player_id": "player001",
                "username": "TestPlayer1",
                "email": "test1@example.com",
                "moral_alignment": 0.75,  # Jugador bueno
                "stats": {"moral_alignment": 0.75},
                "total_playtime_seconds": 1200,  # 20 minutos
                "created_at": (base_date - timedelta(days=30)).isoformat(),
            },
            {
                "player_id": "player002",
                "username": "TestPlayer2",
                "email": "test2@example.com",
                "moral_alignment": 0.30,  # Jugador malo
                "stats": {"moral_alignment": 0.30},
                "total_playtime_seconds": 1800,  # 30 minutos
                "created_at": (base_date - timedelta(days=15)).isoformat(),
            },
            {
                "player_id": "player003",
                "username": "TestPlayer3",
                "email": "test3@example.com",
                "moral_alignment": 0.50,  # Jugador neutral
                "stats": {"moral_alignment": 0.50},
                "total_playtime_seconds": 900,  # 15 minutos
                "created_at": (base_date - timedelta(days=7)).isoformat(),
            },
        ]

    def _generate_mock_games(self) -> List[Dict[str, Any]]:
        """Genera datos mock de partidas para pruebas sin Firebase."""
        return [
            {
                "game_id": "game001",
                "player_id": "player001",
                "status": "completed",
                "choices": {
                    "senda_ebano": "sanar",  # Buena decisión
                    "fortaleza_gigantes": "construir",  # Buena decisión
                    "aquelarre_sombras": "revelar",  # Buena decisión
                },
                "levels_completed": ["senda_ebano", "fortaleza_gigantes", "aquelarre_sombras"],
                "levels_data": {
                    "senda_ebano": {"time_seconds": 300, "deaths": 2},
                    "fortaleza_gigantes": {"time_seconds": 450, "deaths": 5},
                    "aquelarre_sombras": {"time_seconds": 600, "deaths": 8},
                },
                "relics": ["reliquia_fuego", "reliquia_agua"],
                "completion_percentage": 100,
                "metrics": {
                    "total_deaths": 15,
                    "time_per_level": {
                        "senda_ebano": 300,
                        "fortaleza_gigantes": 450,
                        "aquelarre_sombras": 600,
                    },
                },
            },
            {
                "game_id": "game002",
                "player_id": "player002",
                "status": "in_progress",
                "choices": {
                    "senda_ebano": "forzar",  # Mala decisión
                    "fortaleza_gigantes": "destruir",  # Mala decisión
                },
                "levels_completed": ["senda_ebano", "fortaleza_gigantes"],
                "levels_data": {
                    "senda_ebano": {"time_seconds": 250, "deaths": 1},
                    "fortaleza_gigantes": {"time_seconds": 400, "deaths": 3},
                },
                "relics": ["reliquia_tierra"],
                "completion_percentage": 66,
                "metrics": {
                    "total_deaths": 4,
                    "time_per_level": {"senda_ebano": 250, "fortaleza_gigantes": 400},
                },
            },
            {
                "game_id": "game003",
                "player_id": "player003",
                "status": "completed",
                "choices": {
                    "senda_ebano": "sanar",  # Buena decisión
                    "fortaleza_gigantes": "destruir",  # Mala decisión
                    "aquelarre_sombras": "ocultar",  # Mala decisión
                },
                "levels_completed": ["senda_ebano", "fortaleza_gigantes", "aquelarre_sombras"],
                "levels_data": {
                    "senda_ebano": {"time_seconds": 350, "deaths": 4},
                    "fortaleza_gigantes": {"time_seconds": 500, "deaths": 6},
                    "aquelarre_sombras": {"time_seconds": 550, "deaths": 10},
                },
                "relics": ["reliquia_viento"],
                "completion_percentage": 100,
                "metrics": {
                    "total_deaths": 20,
                    "time_per_level": {
                        "senda_ebano": 350,
                        "fortaleza_gigantes": 500,
                        "aquelarre_sombras": 550,
                    },
                },
            },
        ]

    def _generate_mock_events(self) -> List[Dict[str, Any]]:
        """Genera datos mock de eventos para pruebas sin Firebase."""
        from datetime import datetime, timedelta

        base_date = datetime.now()

        return [
            {
                "event_id": "evt001",
                "event_type": "level_start",
                "player_id": "player001",
                "level": "1",
                "timestamp": (base_date - timedelta(days=2)).isoformat(),
                "player_username": "TestPlayer1",
            },
            {
                "event_id": "evt002",
                "event_type": "death",
                "player_id": "player001",
                "level": "1",
                "timestamp": (base_date - timedelta(days=2)).isoformat(),
                "player_username": "TestPlayer1",
            },
            {
                "event_id": "evt003",
                "event_type": "level_complete",
                "player_id": "player002",
                "level": "2",
                "timestamp": (base_date - timedelta(days=1)).isoformat(),
                "player_username": "TestPlayer2",
            },
            {
                "event_id": "evt004",
                "event_type": "death",
                "player_id": "player002",
                "level": "2",
                "timestamp": (base_date - timedelta(days=1)).isoformat(),
                "player_username": "TestPlayer2",
            },
            {
                "event_id": "evt005",
                "event_type": "level_start",
                "player_id": "player003",
                "level": "1",
                "timestamp": base_date.isoformat(),
                "player_username": "TestPlayer3",
            },
            {
                "event_id": "evt006",
                "event_type": "death",
                "player_id": "player003",
                "level": "3",
                "timestamp": base_date.isoformat(),
                "player_username": "TestPlayer3",
            },
        ]

    def _empty_chart(self, message: str = "No hay datos disponibles") -> str:
        """
        Retorna un JSON vacío válido para Plotly cuando no hay datos.

        Evita retornar HTML que causaría error de JSON parse en el frontend.
        """
        return f'{{"data":[],"layout":{{"title":"{message}","paper_bgcolor":"rgba(0,0,0,0)","plot_bgcolor":"rgba(0,0,0,0)","font":{{"color":"#a0aec0"}}}}}}'

    def _get_dark_layout(self):
        """
        Retorna configuración de layout oscuro para gráficos de Plotly.
        """
        return {
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#a0aec0", "family": "Inter, sans-serif"},
            "xaxis": {
                "gridcolor": "#2d3748",
                "color": "#a0aec0",
                "showline": False,
                "zeroline": False,
            },
            "yaxis": {
                "gridcolor": "#2d3748",
                "color": "#a0aec0",
                "showline": False,
                "zeroline": False,
            },
            "legend": {"font": {"color": "#a0aec0"}, "bgcolor": "rgba(0,0,0,0)"},
            "margin": {"t": 40, "r": 20, "b": 40, "l": 60},
        }

    def get_all_players(self) -> List[Dict[str, Any]]:
        """Obtiene todos los jugadores desde la API.

        Usa caché con TTL de 5 minutos para evitar llamadas repetidas.

        Returns:
            List[Dict[str, Any]]: Lista de jugadores con sus estadísticas.
        """
        # 🎨 MODO MOCK: Retornar datos ficticios sin Firebase
        if self.use_mock_data:
            print("[Analytics] 🎨 Using MOCK players data (no Firebase)")
            return self._generate_mock_players()

        cache_key = "players"

        # Verificar si hay cache válido
        if self._is_cache_valid(cache_key):
            age = time.time() - self._cache_timestamp[cache_key]
            print(f"[Analytics] Using cached players (age: {age:.1f}s)")
            return self._get_from_cache(cache_key)

        if not self.client:
            return []

        try:
            response = self.client.get("/v1/players")
            response.raise_for_status()
            players = response.json()

            # Guardar en cache
            self._set_cache(cache_key, players)
            print(
                f"[Analytics] Fetched {len(players)} players from API (cached for {self._cache_ttl}s)"
            )

            return players
        except Exception as e:
            print(f"Error obteniendo jugadores: {e}")
            return []

    def get_all_games(self) -> List[Dict[str, Any]]:
        """Obtiene todas las partidas usando el endpoint admin optimizado.

        OPTIMIZADO: Usa GET /v1/games en lugar de iterar sobre jugadores.
        Reduce de ~100 llamadas HTTP a 1 sola llamada.

        Usa caché con TTL de 5 minutos para evitar llamadas repetidas.

        Returns:
            List[Dict[str, Any]]: Lista de partidas.
        """
        # 🎨 MODO MOCK: Retornar datos ficticios sin Firebase
        if self.use_mock_data:
            print("[Analytics] 🎨 Using MOCK games data (no Firebase)")
            return self._generate_mock_games()

        cache_key = "games"

        # Verificar si hay cache válido
        if self._is_cache_valid(cache_key):
            age = time.time() - self._cache_timestamp[cache_key]
            cached_games = self._get_from_cache(cache_key)
            print(f"[Analytics] Using cached games (age: {age:.1f}s, {len(cached_games)} games)")
            return cached_games

        if not self.client:
            return []

        start_time = time.time()

        try:
            # OPTIMIZACIÓN: Llamar endpoint admin directo en lugar de iterar jugadores
            print("[Analytics] Calling GET /v1/games with limit=1000")
            print(f"[Analytics] Client headers: {dict(self.client.headers)}")

            response = self.client.get("/v1/games", params={"limit": 1000})

            print(f"[Analytics] Response status: {response.status_code}")
            print(f"[Analytics] Response content-type: {response.headers.get('content-type')}")

            response.raise_for_status()
            all_games = response.json()

            elapsed = time.time() - start_time
            print(f"[Analytics] ✅ Fetched {len(all_games)} games in {elapsed:.2f}s (1 HTTP call)")

            # Guardar en cache
            self._set_cache(cache_key, all_games)
            print(f"[Analytics] Cached {len(all_games)} games for {self._cache_ttl}s")

            return all_games

        except httpx.HTTPStatusError as e:
            print(f"[Analytics] ❌ HTTP Error {e.response.status_code}")
            print(f"[Analytics] Response preview: {e.response.text[:500]}")
            if e.response.status_code == 403:
                print("[Analytics] ERROR: Endpoint requires admin auth. Make sure API Key is set.")
            return []
        except Exception as e:
            print(f"[Analytics] ❌ Error fetching games: {type(e).__name__}: {e}")
            return []

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Obtiene todos los eventos usando el endpoint admin optimizado.

        OPTIMIZADO: Usa GET /v1/events en lugar de iterar sobre jugadores.
        Reduce de ~100 llamadas HTTP a 1 sola llamada.

        Usa caché con TTL de 5 minutos para evitar llamadas repetidas.

        Returns:
            List[Dict[str, Any]]: Lista de eventos.
        """
        # 🎨 MODO MOCK: Retornar datos ficticios sin Firebase
        if self.use_mock_data:
            print("[Analytics] 🎨 Using MOCK events data (no Firebase)")
            return self._generate_mock_events()

        cache_key = "events"

        # Verificar si hay cache válido
        if self._is_cache_valid(cache_key):
            age = time.time() - self._cache_timestamp[cache_key]
            cached_events = self._get_from_cache(cache_key)
            print(f"[Analytics] Using cached events (age: {age:.1f}s, {len(cached_events)} events)")
            return cached_events

        if not self.client:
            return []

        start_time = time.time()

        try:
            # OPTIMIZACIÓN: Llamar endpoint admin directo
            print("[Analytics] Calling GET /v1/events with limit=5000")

            response = self.client.get("/v1/events", params={"limit": 5000})

            print(f"[Analytics] Response status: {response.status_code}")
            print(f"[Analytics] Response content-type: {response.headers.get('content-type')}")

            response.raise_for_status()
            all_events = response.json()

            # Enriquecer eventos con usernames
            players = self.get_all_players()
            player_map = {p["player_id"]: p.get("username", "Unknown") for p in players}

            for event in all_events:
                event["player_username"] = player_map.get(event.get("player_id"), "Unknown")

            elapsed = time.time() - start_time
            print(
                f"[Analytics] ✅ Fetched {len(all_events)} events in {elapsed:.2f}s (1 HTTP call)"
            )

            # Guardar en cache
            self._set_cache(cache_key, all_events)
            print(f"[Analytics] Cached {len(all_events)} events for {self._cache_ttl}s")

            return all_events

        except httpx.HTTPStatusError as e:
            print(f"[Analytics] ❌ HTTP Error {e.response.status_code}")
            print(f"[Analytics] Response preview: {e.response.text[:500]}")
            if e.response.status_code == 403:
                print("[Analytics] ERROR: Endpoint requires admin auth. Make sure API Key is set.")
            return []
        except Exception as e:
            print(f"[Analytics] ❌ Error fetching events: {type(e).__name__}: {e}")
            return []

    def calculate_global_metrics(self, players: List[Dict], games: List[Dict]) -> Dict[str, Any]:
        """Calcula las métricas globales del juego.

        Args:
            players (List[Dict]): Lista de jugadores.
            games (List[Dict]): Lista de partidas.

        Returns:
            Dict[str, Any]: Métricas agregadas.
        """
        if not ANALYTICS_AVAILABLE or not games:
            return {
                "total_players": len(players),
                "total_games": len(games),
                "completed_games": 0,
                "avg_playtime": 0,
                "completion_rate": 0,
                "avg_deaths": 0,
                "total_deaths": 0,
                "total_relics": 0,
                "total_events": 0,
            }

        df = pd.DataFrame(games)

        # Calcular métricas
        completed_games = df[df["status"] == "completed"]

        # Total de tiempo jugado (suma de todos los tiempos de niveles)
        total_playtime = 0
        for game in games:
            metrics_data = game.get("metrics", {})
            # Sumar tiempo de cada nivel desde metrics.time_per_level
            time_per_level = metrics_data.get("time_per_level", {})
            for time_seconds in time_per_level.values():
                total_playtime += time_seconds

        avg_playtime = total_playtime / len(games) if games else 0

        # Total de muertes (usar metrics.total_deaths directamente)
        total_deaths = 0
        for game in games:
            metrics_data = game.get("metrics", {})
            total_deaths += metrics_data.get("total_deaths", 0)

        avg_deaths = total_deaths / len(games) if games else 0

        # Total de reliquias obtenidas
        total_relics = 0
        for game in games:
            relics = game.get("relics", [])
            total_relics += len(relics)

        return {
            "total_players": len(players),
            "total_games": len(games),
            "completed_games": len(completed_games),
            "avg_playtime": round(avg_playtime, 2),
            "completion_rate": (round(len(completed_games) / len(games) * 100, 2) if games else 0),
            "avg_deaths": round(avg_deaths, 2),
            "total_deaths": total_deaths,
            "total_relics": total_relics,
        }

    def create_moral_choices_chart(self, games: List[Dict]) -> str:
        """Genera un gráfico de barras apiladas de buenas vs malas decisiones por nivel.

        Args:
            games (List[Dict]): Lista de partidas.

        Returns:
            str: Representación JSON del gráfico Plotly.
        """
        if not ANALYTICS_AVAILABLE:
            return '{"data":[],"layout":{"title":"Analytics no disponible"}}'

        if not games:
            return '{"data":[],"layout":{"title":"No hay datos de partidas"}}'

        # Mapeo de decisiones a good/bad
        good_choices = {"sanar", "construir", "revelar"}
        bad_choices = {"forzar", "destruir", "ocultar"}

        # Nombres amigables para niveles
        level_names = {
            "senda_ebano": "Senda del Ébano",
            "fortaleza_gigantes": "Fortaleza de Gigantes",
            "aquelarre_sombras": "Aquelarre de Sombras",
        }

        # Recopilar decisiones por nivel
        choices_data = []

        for game in games:
            choices = game.get("choices", {})

            # Procesar cada nivel
            for level_key, choice_value in choices.items():
                if choice_value:  # Si hay decisión
                    # Determinar si es buena o mala
                    if choice_value in good_choices:
                        decision_type = "Buena"
                    elif choice_value in bad_choices:
                        decision_type = "Mala"
                    else:
                        continue  # Ignorar decisiones no reconocidas

                    level_name = level_names.get(level_key, level_key)
                    choices_data.append(
                        {"Nivel": level_name, "Decisión": decision_type, "count": 1}
                    )

        if not choices_data:
            return self._empty_chart("No hay decisiones morales registradas")

        df = pd.DataFrame(choices_data)
        # Agrupar por Nivel y Decisión
        df_grouped = df.groupby(["Nivel", "Decisión"]).count().reset_index()

        fig = px.bar(
            df_grouped,
            x="Nivel",
            y="count",
            color="Decisión",
            title="Decisiones por Nivel (Buenas vs Malas)",
            labels={"count": "Cantidad", "Decisión": "Tipo"},
            barmode="stack",
            color_discrete_map={
                "Buena": "#10b981",  # Green
                "Mala": "#ef4444",  # Red
            },
        )

        fig.update_layout(self._get_dark_layout())
        return fig.to_json()

    def create_global_good_vs_bad_chart(self, games: List[Dict]) -> str:
        """Genera un gráfico circular (Pie Chart) del total de decisiones buenas vs malas.

        Args:
            games (List[Dict]): Lista de partidas.

        Returns:
            str: Representación JSON del gráfico Plotly.
        """
        if not ANALYTICS_AVAILABLE or not games:
            return self._empty_chart("No hay datos disponibles")

        # Mapeo de decisiones a good/bad
        good_choices = {"sanar", "construir", "revelar"}
        bad_choices = {"forzar", "destruir", "ocultar"}

        good_count = 0
        bad_count = 0

        for game in games:
            choices = game.get("choices", {})
            for choice_value in choices.values():
                if choice_value in good_choices:
                    good_count += 1
                elif choice_value in bad_choices:
                    bad_count += 1

        if good_count == 0 and bad_count == 0:
            return self._empty_chart("No hay decisiones registradas")

        df = pd.DataFrame({"Tipo": ["Buenas", "Malas"], "Cantidad": [good_count, bad_count]})

        fig = px.pie(
            df,
            values="Cantidad",
            names="Tipo",
            title="Total Decisiones Buenas vs Malas",
            color="Tipo",
            color_discrete_map={"Buenas": "#10b981", "Malas": "#ef4444"},
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_traces(textinfo="percent+label", textfont_color="#ffffff")
        return fig.to_json()

    def create_playtime_distribution(self, players: List[Dict]) -> str:
        """
        Genera gráfico de distribución de tiempo de juego.

        Args:
            players: Lista de jugadores

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not players:
            return self._empty_chart("No hay datos disponibles")

        # Usar total_playtime_seconds (nombre correcto) o total_playtime (legacy/mock data)
        playtimes = [p.get("total_playtime_seconds") or p.get("total_playtime", 0) for p in players]

        df = pd.DataFrame(
            {
                "Jugador": [p.get("username", "Unknown") for p in players],
                "Tiempo (min)": [pt / 60 for pt in playtimes],
            }
        )

        fig = px.histogram(
            df,
            x="Tiempo (min)",
            title="Distribución de Tiempo de Juego",
            labels={"Tiempo (min)": "Tiempo total de juego (minutos)"},
            nbins=20,
        )

        fig.update_layout(self._get_dark_layout())

        return fig.to_json()

    def create_deaths_per_level_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de muertes promedio por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return self._empty_chart("No hay datos disponibles")

        # Recopilar muertes por nivel
        deaths_by_level = {}

        for game in games:
            for level_name, level_data in game.get("levels_data", {}).items():
                if level_name not in deaths_by_level:
                    deaths_by_level[level_name] = []
                deaths_by_level[level_name].append(level_data.get("deaths", 0))

        # Calcular promedio
        avg_deaths = {
            level: sum(deaths) / len(deaths) if deaths else 0
            for level, deaths in deaths_by_level.items()
        }

        df = pd.DataFrame(
            {
                "Nivel": list(avg_deaths.keys()),
                "Muertes promedio": list(avg_deaths.values()),
            }
        )

        fig = px.bar(
            df,
            x="Nivel",
            y="Muertes promedio",
            labels={"Muertes promedio": "Promedio de muertes"},
            color_discrete_sequence=["#10b981"],
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None)

        return fig.to_json()

    def create_events_by_type_chart(self, events: List[Dict]) -> str:
        """
        Genera gráfico de eventos por tipo.

        Args:
            events: Lista de eventos

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not events:
            return self._empty_chart("No hay eventos registrados")

        # Contar eventos por tipo
        event_types = [e.get("event_type") for e in events]
        type_counts = Counter(event_types)

        df = pd.DataFrame(
            {
                "Tipo de evento": list(type_counts.keys()),
                "Cantidad": list(type_counts.values()),
            }
        )

        fig = px.pie(
            df,
            values="Cantidad",
            names="Tipo de evento",
            color_discrete_sequence=[
                "#10b981",
                "#3b82f6",
                "#f59e0b",
                "#ef4444",
                "#8b5cf6",
            ],
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None, showlegend=True)
        fig.update_traces(textfont_color="#ffffff")

        # Retornar JSON para que el frontend use Plotly.newPlot()
        return fig.to_json()

    def create_events_timeline_chart(self, events: List[Dict]) -> str:
        """
        Genera gráfico de línea temporal de eventos.

        Args:
            events: Lista de eventos

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not events:
            return self._empty_chart("No hay eventos registrados")

        # Procesar fechas
        dates = []
        for e in events:
            ts = e.get("timestamp")
            if ts:
                try:
                    # Convertir ISO string a datetime y truncar a fecha (o hora si se prefiere)
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    dates.append(dt.date())
                except ValueError:
                    pass

        if not dates:
            return self._empty_chart("No hay fechas válidas en eventos")

        date_counts = Counter(dates)

        df = pd.DataFrame(
            {
                "Fecha": list(date_counts.keys()),
                "Cantidad": list(date_counts.values()),
            }
        ).sort_values("Fecha")

        fig = px.line(
            df,
            x="Fecha",
            y="Cantidad",
            title="Actividad de Eventos en el Tiempo",
            labels={"Cantidad": "Número de eventos"},
            markers=True,
        )

        fig.update_traces(line_color="#3b82f6")
        fig.update_layout(self._get_dark_layout())

        # Retornar JSON para que el frontend use Plotly.newPlot()
        return fig.to_json()

    def create_deaths_event_chart(self, events: List[Dict]) -> str:
        """
        Genera gráfico de muertes por nivel basado en eventos.

        Args:
            events: Lista de eventos

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not events:
            return self._empty_chart("No hay eventos registrados")

        # Filtrar solo eventos de muerte ('death', 'player_death', etc.)
        death_events = [e for e in events if "death" in str(e.get("event_type", "")).lower()]

        if not death_events:
            return self._empty_chart("No hay eventos de muerte")

        # Agrupar por nivel
        level_counts = Counter([e.get("level", "Unknown") for e in death_events])

        df = pd.DataFrame(
            {
                "Nivel": list(level_counts.keys()),
                "Muertes": list(level_counts.values()),
            }
        )

        fig = px.bar(
            df,
            x="Nivel",
            y="Muertes",
            title="Muertes por Nivel (Eventos)",
            labels={"Muertes": "Cantidad de muertes"},
            color="Muertes",
            color_continuous_scale="Reds",
        )

        fig.update_layout(self._get_dark_layout())

        # Retornar JSON para que el frontend use Plotly.newPlot()
        return fig.to_json()

    def create_moral_alignment_chart(self, players: List[Dict]) -> str:
        """
        Genera Histograma de alineación moral (0-1).
        """
        if not ANALYTICS_AVAILABLE or not players:
            return self._empty_chart("No hay datos disponibles")

        alignments = []
        for player in players:
            # Intentar obtener de stats.moral_alignment o directamente de moral_alignment
            val = player.get("stats", {}).get("moral_alignment") or player.get("moral_alignment")
            if val is not None:
                alignments.append(val)

        if not alignments:
            return self._empty_chart("No hay datos de alineación moral")

        df = pd.DataFrame({"Align": alignments})

        fig = px.histogram(
            df,
            x="Align",
            nbins=20,
            labels={"Align": "Alineación Moral (0=Malo, 1=Bueno)"},
            color_discrete_sequence=["#8b5cf6"],
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None, bargap=0.1)
        return fig.to_json()

    def create_relics_distribution_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de distribución de reliquias obtenidas.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return self._empty_chart("No hay datos disponibles")

        all_relics = []
        for game in games:
            relics = game.get("relics", [])
            all_relics.extend(relics)

        if not all_relics:
            return self._empty_chart("No hay reliquias obtenidas")

        relic_counts = Counter(all_relics)

        df = pd.DataFrame(
            {
                "Reliquia": list(relic_counts.keys()),
                "Cantidad": list(relic_counts.values()),
            }
        )

        fig = px.bar(
            df,
            x="Reliquia",
            y="Cantidad",
            labels={"Cantidad": "Veces obtenida"},
            color="Reliquia",
            color_discrete_sequence=["#10b981", "#3b82f6", "#f59e0b"],
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None, showlegend=False)

        return fig.to_json()

    def create_level_completion_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de tasa de completado por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return self._empty_chart("No hay datos disponibles")

        level_completions = {}
        total_games = len(games)

        for game in games:
            levels_completed = game.get("levels_completed", [])
            for level in levels_completed:
                if level not in level_completions:
                    level_completions[level] = 0
                level_completions[level] += 1

        if not level_completions:
            return self._empty_chart("No hay niveles completados")

        # Calcular porcentaje
        level_percentages = {
            level: (count / total_games) * 100 for level, count in level_completions.items()
        }

        df = pd.DataFrame(
            {
                "Nivel": list(level_percentages.keys()),
                "Porcentaje Completado": list(level_percentages.values()),
            }
        )

        fig = px.bar(
            df,
            x="Nivel",
            y="Porcentaje Completado",
            labels={"Porcentaje Completado": "% de jugadores que completaron"},
            color="Porcentaje Completado",
            color_continuous_scale="Viridis",
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None)

        return fig.to_json()

    def create_playtime_per_level_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de tiempo promedio por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return self._empty_chart("No hay datos disponibles")

        level_times = {}

        for game in games:
            metrics = game.get("metrics", {})
            time_per_level = metrics.get("time_per_level", {})

            for level, time_seconds in time_per_level.items():
                if level not in level_times:
                    level_times[level] = []
                level_times[level].append(time_seconds)

        if not level_times:
            return self._empty_chart("No hay datos de tiempo por nivel")

        # Calcular promedio en minutos
        avg_times = {
            level: (sum(times) / len(times)) / 60  # Convertir a minutos
            for level, times in level_times.items()
        }

        df = pd.DataFrame(
            {
                "Nivel": list(avg_times.keys()),
                "Tiempo Promedio (min)": list(avg_times.values()),
            }
        )

        fig = px.bar(
            df,
            x="Nivel",
            y="Tiempo Promedio (min)",
            labels={"Tiempo Promedio (min)": "Minutos"},
            color="Tiempo Promedio (min)",
            color_continuous_scale="Blues",
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None)

        return fig.to_json()

    def create_active_players_chart(self, events: List[Dict]) -> str:
        """
        Genera gráfico de jugadores activos en los últimos 7 días.

        Args:
            events: Lista de eventos

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not events:
            return self._empty_chart("No hay datos disponibles")

        # Calcular fecha límite (7 días atrás)
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=7)

        # Agrupar eventos por fecha y contar jugadores únicos
        daily_players = {}

        for event in events:
            ts = event.get("timestamp")
            player_id = event.get("player_id")

            if not ts or not player_id:
                continue

            try:
                # Manejar diferentes tipos de timestamp
                if isinstance(ts, datetime):
                    dt = ts
                elif isinstance(ts, str):
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    continue

                event_date = dt.date()

                # Solo últimos 7 días
                if event_date >= seven_days_ago and event_date <= today:
                    if event_date not in daily_players:
                        daily_players[event_date] = set()
                    daily_players[event_date].add(player_id)

            except ValueError:
                continue

        if not daily_players:
            return self._empty_chart("No hay actividad en 7 días")

        # Asegurar que todos los días estén representados (incluso con 0)
        all_dates = [seven_days_ago + timedelta(days=i) for i in range(8)]
        data = []
        for date in all_dates:
            count = len(daily_players.get(date, set()))
            data.append({"Fecha": date, "Jugadores": count})

        df = pd.DataFrame(data)

        fig = px.bar(
            df,
            x="Fecha",
            y="Jugadores",
            labels={"Jugadores": "Jugadores únicos"},
            color="Jugadores",
            color_continuous_scale="Greens",
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None)

        return fig.to_html(
            include_plotlyjs="cdn", div_id="active-players-chart", config={"displayModeBar": False}
        )

    def export_to_csv(self, data: List[Dict], filename: str) -> str:
        """
        Exporta datos a CSV usando Pandas.

        Args:
            data: Lista de diccionarios
            filename: Nombre del archivo

        Returns:
            Path del archivo generado
        """
        if not ANALYTICS_AVAILABLE or not data:
            return ""

        df = pd.DataFrame(data)
        path = f"/tmp/{filename}.csv"
        df.to_csv(path, index=False)
        return path
