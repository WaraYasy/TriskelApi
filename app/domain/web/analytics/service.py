"""
Servicio de Analytics

Consume la API REST de Triskel para obtener datos y generar métricas.

Este servicio NO accede directamente a la base de datos.
En su lugar, hace peticiones HTTP a la propia API REST.

Esto mantiene el desacoplamiento y asegura que:
- Analytics no tiene lógica de negocio duplicada
- Usa las mismas validaciones que el juego
- Más fácil de escalar (puede estar en otro servidor)
"""

from collections import Counter
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
    """
    Servicio para agregación de datos y generación de métricas.

    Consume la API REST y genera:
    - Métricas agregadas
    - DataFrames con Pandas
    - Gráficos con Plotly
    """

    def __init__(
        self, api_base_url: str = "http://localhost:8000", api_key: str = None
    ):
        """
        Inicializa el servicio.

        Args:
            api_base_url: URL base de la API REST
            api_key: API Key para acceso admin
        """
        self.api_base_url = api_base_url
        self.api_key = api_key
        if ANALYTICS_AVAILABLE:
            headers = {}
            if api_key:
                headers["X-API-Key"] = api_key
            self.client = httpx.Client(base_url=api_base_url, headers=headers)
        else:
            self.client = None

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
        """
        Obtiene todos los jugadores desde la API.

        Returns:
            Lista de jugadores con sus stats
        """
        if not self.client:
            return []

        try:
            response = self.client.get("/v1/players")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error obteniendo jugadores: {e}")
            return []

    def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las partidas desde la API (requiere admin).

        Returns:
            Lista de partidas
        """
        if not self.client:
            return []

        # Por ahora, recopilamos partidas de todos los jugadores
        # En el futuro podríamos tener un endpoint admin /v1/games
        players = self.get_all_players()
        all_games = []

        for player in players:
            try:
                response = self.client.get(f"/v1/games/player/{player['player_id']}")
                response.raise_for_status()
                games = response.json()
                all_games.extend(games)
            except Exception as e:
                print(
                    f"Error obteniendo partidas del jugador {player['player_id']}: {e}"
                )

        return all_games

    def calculate_global_metrics(
        self, players: List[Dict], games: List[Dict]
    ) -> Dict[str, Any]:
        """
        Calcula métricas globales del juego.

        Args:
            players: Lista de jugadores
            games: Lista de partidas

        Returns:
            Dict con métricas agregadas
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
            for level_data in game.get("levels_data", {}).values():
                total_playtime += level_data.get("time_seconds", 0)

        avg_playtime = total_playtime / len(games) if games else 0

        # Total de muertes
        total_deaths = 0
        for game in games:
            for level_data in game.get("levels_data", {}).values():
                total_deaths += level_data.get("deaths", 0)

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
            "completion_rate": (
                round(len(completed_games) / len(games) * 100, 2) if games else 0
            ),
            "avg_deaths": round(avg_deaths, 2),
            "total_deaths": total_deaths,
            "total_relics": total_relics,
        }

    def create_moral_choices_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de distribución de decisiones morales.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico de Plotly
        """
        if not ANALYTICS_AVAILABLE or not games:
            return "<div>No hay datos disponibles</div>"

        # Recopilar decisiones morales por nivel
        choices_data = []

        for game in games:
            for level_name, level_data in game.get("levels_data", {}).items():
                choice = level_data.get("choice")
                if choice:
                    choices_data.append(
                        {"Nivel": level_name, "Decisión": choice, "count": 1}
                    )

        if not choices_data:
            return "<div>No hay decisiones morales registradas</div>"

        df = pd.DataFrame(choices_data)
        df_grouped = df.groupby(["Nivel", "Decisión"]).count().reset_index()

        fig = px.bar(
            df_grouped,
            x="Nivel",
            y="count",
            color="Decisión",
            labels={"count": "Cantidad de jugadores"},
            barmode="group",
            color_discrete_map={
                "good": "#10b981",
                "bad": "#ef4444",
                "neutral": "#6b7280",
            },
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(showlegend=True, title=None)

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_playtime_distribution(self, players: List[Dict]) -> str:
        """
        Genera gráfico de distribución de tiempo de juego.

        Args:
            players: Lista de jugadores

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not players:
            return "<div>No hay datos disponibles</div>"

        playtimes = [p.get("total_playtime", 0) for p in players]

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

        return fig.to_html(full_html=False)

    def create_deaths_per_level_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de muertes promedio por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return "<div>No hay datos disponibles</div>"

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

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_events_by_type_chart(self, events: List[Dict]) -> str:
        """
        Genera gráfico de eventos por tipo.

        Args:
            events: Lista de eventos

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not events:
            return "<div>No hay eventos registrados</div>"

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

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_moral_alignment_chart(self, players: List[Dict]) -> str:
        """
        Genera gráfico de distribución de alineación moral de jugadores.

        Args:
            players: Lista de jugadores

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not players:
            return "<div>No hay datos disponibles</div>"

        # Clasificar jugadores por alineación moral
        alignments = []
        for player in players:
            moral_alignment = player.get("stats", {}).get("moral_alignment", 0)
            if moral_alignment > 0.3:
                category = "Bueno"
            elif moral_alignment < -0.3:
                category = "Malo"
            else:
                category = "Neutral"
            alignments.append(category)

        if not alignments:
            return "<div>No hay jugadores con alineación moral registrada</div>"

        alignment_counts = Counter(alignments)

        df = pd.DataFrame(
            {
                "Alineación": list(alignment_counts.keys()),
                "Jugadores": list(alignment_counts.values()),
            }
        )

        # Colores personalizados
        colors = {"Bueno": "#10b981", "Neutral": "#6b7280", "Malo": "#ef4444"}
        df["color"] = df["Alineación"].map(colors)

        fig = px.pie(
            df,
            values="Jugadores",
            names="Alineación",
            color="Alineación",
            color_discrete_map=colors,
        )

        fig.update_layout(self._get_dark_layout())
        fig.update_layout(title=None, showlegend=True)
        fig.update_traces(textfont_color="#ffffff")

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_relics_distribution_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de distribución de reliquias obtenidas.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return "<div>No hay datos disponibles</div>"

        all_relics = []
        for game in games:
            relics = game.get("relics", [])
            all_relics.extend(relics)

        if not all_relics:
            return "<div>No hay reliquias obtenidas aún</div>"

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

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_level_completion_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de tasa de completado por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return "<div>No hay datos disponibles</div>"

        level_completions = {}
        total_games = len(games)

        for game in games:
            levels_completed = game.get("levels_completed", [])
            for level in levels_completed:
                if level not in level_completions:
                    level_completions[level] = 0
                level_completions[level] += 1

        if not level_completions:
            return "<div>No hay niveles completados aún</div>"

        # Calcular porcentaje
        level_percentages = {
            level: (count / total_games) * 100
            for level, count in level_completions.items()
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

        return fig.to_html(full_html=False, config={"displayModeBar": False})

    def create_playtime_per_level_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de tiempo promedio por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        if not ANALYTICS_AVAILABLE or not games:
            return "<div>No hay datos disponibles</div>"

        level_times = {}

        for game in games:
            metrics = game.get("metrics", {})
            time_per_level = metrics.get("time_per_level", {})

            for level, time_seconds in time_per_level.items():
                if level not in level_times:
                    level_times[level] = []
                level_times[level].append(time_seconds)

        if not level_times:
            return "<div>No hay datos de tiempo por nivel</div>"

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

        return fig.to_html(full_html=False, config={"displayModeBar": False})

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
