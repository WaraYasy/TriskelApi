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

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Inicializa el servicio.

        Args:
            api_base_url: URL base de la API REST
        """
        self.api_base_url = api_base_url
        if ANALYTICS_AVAILABLE:
            self.client = httpx.AsyncClient(base_url=api_base_url)
        else:
            self.client = None

    async def get_all_players(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los jugadores desde la API.

        Returns:
            Lista de jugadores con sus stats
        """
        # TODO: Implementar
        # response = await self.client.get("/v1/players")
        # return response.json()
        return []

    async def get_all_games(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las partidas desde la API.

        Returns:
            Lista de partidas
        """
        # TODO: Implementar
        return []

    def calculate_global_metrics(self, players: List[Dict], games: List[Dict]) -> Dict[str, Any]:
        """
        Calcula métricas globales del juego.

        Args:
            players: Lista de jugadores
            games: Lista de partidas

        Returns:
            Dict con métricas agregadas:
            - total_players: Número de jugadores
            - total_games: Número de partidas
            - avg_playtime: Tiempo promedio por partida
            - completion_rate: % de partidas completadas
            - avg_deaths: Promedio de muertes
        """
        # TODO: Implementar con Pandas
        return {
            'total_players': len(players),
            'total_games': len(games),
            'avg_playtime': 0,
            'completion_rate': 0,
            'avg_deaths': 0
        }

    def create_moral_choices_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de distribución de decisiones morales.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico de Plotly
        """
        # TODO: Implementar con Plotly
        # Ejemplo:
        # fig = px.bar(df, x='level', y='count', color='choice')
        # return fig.to_html(full_html=False)
        return "<div>TODO: Gráfico de decisiones morales</div>"

    def create_playtime_distribution(self, players: List[Dict]) -> str:
        """
        Genera gráfico de distribución de tiempo de juego.

        Args:
            players: Lista de jugadores

        Returns:
            HTML del gráfico
        """
        # TODO: Implementar
        return "<div>TODO: Gráfico de tiempo de juego</div>"

    def create_deaths_per_level_chart(self, games: List[Dict]) -> str:
        """
        Genera gráfico de muertes promedio por nivel.

        Args:
            games: Lista de partidas

        Returns:
            HTML del gráfico
        """
        # TODO: Implementar
        return "<div>TODO: Gráfico de muertes por nivel</div>"

    def export_to_csv(self, data: List[Dict], filename: str) -> str:
        """
        Exporta datos a CSV usando Pandas.

        Args:
            data: Lista de diccionarios
            filename: Nombre del archivo

        Returns:
            Path del archivo generado
        """
        # TODO: Implementar
        # df = pd.DataFrame(data)
        # path = f"/tmp/{filename}.csv"
        # df.to_csv(path, index=False)
        # return path
        return ""
