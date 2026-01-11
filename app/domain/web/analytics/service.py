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
from typing import List, Dict, Any, Optional
from collections import Counter

# Imports opcionales (instalar si se necesitan visualizaciones)
try:
    import httpx
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
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

    def __init__(self, api_base_url: str = "http://localhost:8000", api_key: str = None):
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
                print(f"Error obteniendo partidas del jugador {player['player_id']}: {e}")

        return all_games

    def calculate_global_metrics(self, players: List[Dict], games: List[Dict]) -> Dict[str, Any]:
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
                'total_players': len(players),
                'total_games': len(games),
                'avg_playtime': 0,
                'completion_rate': 0,
                'avg_deaths': 0,
                'total_events': 0
            }

        df = pd.DataFrame(games)

        # Calcular métricas
        completed_games = df[df['status'] == 'completed']

        # Total de tiempo jugado (suma de todos los tiempos de niveles)
        total_playtime = 0
        for game in games:
            for level_data in game.get('levels_data', {}).values():
                total_playtime += level_data.get('time_seconds', 0)

        avg_playtime = total_playtime / len(games) if games else 0

        # Total de muertes
        total_deaths = 0
        for game in games:
            for level_data in game.get('levels_data', {}).values():
                total_deaths += level_data.get('deaths', 0)

        avg_deaths = total_deaths / len(games) if games else 0

        return {
            'total_players': len(players),
            'total_games': len(games),
            'completed_games': len(completed_games),
            'avg_playtime': round(avg_playtime, 2),
            'completion_rate': round(len(completed_games) / len(games) * 100, 2) if games else 0,
            'avg_deaths': round(avg_deaths, 2),
            'total_deaths': total_deaths
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
            for level_name, level_data in game.get('levels_data', {}).items():
                choice = level_data.get('choice')
                if choice:
                    choices_data.append({
                        'Nivel': level_name,
                        'Decisión': choice,
                        'count': 1
                    })

        if not choices_data:
            return "<div>No hay decisiones morales registradas</div>"

        df = pd.DataFrame(choices_data)
        df_grouped = df.groupby(['Nivel', 'Decisión']).count().reset_index()

        fig = px.bar(
            df_grouped,
            x='Nivel',
            y='count',
            color='Decisión',
            title='Distribución de Decisiones Morales por Nivel',
            labels={'count': 'Cantidad de jugadores'},
            barmode='group'
        )

        return fig.to_html(full_html=False)

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

        playtimes = [p.get('total_playtime', 0) for p in players]

        df = pd.DataFrame({
            'Jugador': [p.get('username', 'Unknown') for p in players],
            'Tiempo (min)': [pt / 60 for pt in playtimes]
        })

        fig = px.histogram(
            df,
            x='Tiempo (min)',
            title='Distribución de Tiempo de Juego',
            labels={'Tiempo (min)': 'Tiempo total de juego (minutos)'},
            nbins=20
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
            for level_name, level_data in game.get('levels_data', {}).items():
                if level_name not in deaths_by_level:
                    deaths_by_level[level_name] = []
                deaths_by_level[level_name].append(level_data.get('deaths', 0))

        # Calcular promedio
        avg_deaths = {
            level: sum(deaths) / len(deaths) if deaths else 0
            for level, deaths in deaths_by_level.items()
        }

        df = pd.DataFrame({
            'Nivel': list(avg_deaths.keys()),
            'Muertes promedio': list(avg_deaths.values())
        })

        fig = px.bar(
            df,
            x='Nivel',
            y='Muertes promedio',
            title='Muertes Promedio por Nivel',
            labels={'Muertes promedio': 'Promedio de muertes'}
        )

        return fig.to_html(full_html=False)

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
        event_types = [e.get('event_type') for e in events]
        type_counts = Counter(event_types)

        df = pd.DataFrame({
            'Tipo de evento': list(type_counts.keys()),
            'Cantidad': list(type_counts.values())
        })

        fig = px.pie(
            df,
            values='Cantidad',
            names='Tipo de evento',
            title='Distribución de Eventos por Tipo'
        )

        return fig.to_html(full_html=False)

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
