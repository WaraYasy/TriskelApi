"""
Blueprint de Analytics

Dashboard de métricas y visualizaciones del juego.

Rutas:
- GET /dashboard/          → Dashboard principal con métricas globales
- GET /dashboard/players   → Análisis detallado de jugadores
- GET /dashboard/games     → Análisis de partidas y progresión
- GET /dashboard/choices   → Análisis de decisiones morales
- GET /dashboard/export    → Exportar datos a CSV
"""
from flask import Blueprint, render_template, jsonify, request, send_file
from .service import AnalyticsService

# Crear blueprint
analytics_bp = Blueprint(
    'analytics',
    __name__,
    template_folder='templates'
)

# Instanciar servicio
# TODO: Usar dependency injection cuando esté implementado
analytics_service = AnalyticsService()


@analytics_bp.route('/')
def index():
    """
    Dashboard principal con métricas globales.

    Muestra:
    - Total de jugadores
    - Total de partidas
    - Tiempo promedio de juego
    - Distribución de decisiones morales
    - Gráficos con Plotly
    """
    # TODO: Implementar obtención de métricas
    metrics = {
        'total_players': 0,
        'total_games': 0,
        'avg_playtime': 0,
        'completion_rate': 0
    }

    return render_template(
        'analytics/index.html',
        metrics=metrics
    )


@analytics_bp.route('/players')
def players():
    """
    Análisis detallado de jugadores.

    Muestra:
    - Lista de jugadores
    - Stats individuales
    - Distribución de alineación moral
    - Tiempo de juego por jugador
    """
    # TODO: Implementar
    players_data = []

    return render_template(
        'analytics/players.html',
        players=players_data
    )


@analytics_bp.route('/games')
def games():
    """
    Análisis de partidas y progresión.

    Muestra:
    - Lista de partidas completadas
    - Tiempo por nivel
    - Muertes por nivel
    - Tasa de completado
    """
    # TODO: Implementar
    games_data = []

    return render_template(
        'analytics/games.html',
        games=games_data
    )


@analytics_bp.route('/choices')
def choices():
    """
    Análisis de decisiones morales.

    Muestra:
    - Distribución de decisiones por nivel
    - Porcentaje buenas vs malas
    - Correlación con completado del juego
    - Gráficos de barras con Plotly
    """
    # TODO: Implementar
    choices_data = {}

    return render_template(
        'analytics/choices.html',
        choices=choices_data
    )


@analytics_bp.route('/export')
def export():
    """
    Exporta datos a CSV.

    Query params:
    - type: players | games | events
    - format: csv | json

    Returns:
        File: Archivo descargable
    """
    export_type = request.args.get('type', 'players')
    export_format = request.args.get('format', 'csv')

    # TODO: Implementar exportación
    return jsonify({
        'message': 'TODO: Implementar exportación',
        'type': export_type,
        'format': export_format
    })


@analytics_bp.route('/api/metrics')
def api_metrics():
    """
    API endpoint para obtener métricas en JSON.

    Útil para actualizar el dashboard sin recargar la página.

    Returns:
        JSON: Métricas actualizadas
    """
    # TODO: Implementar
    return jsonify({
        'total_players': 0,
        'total_games': 0,
        'avg_playtime': 0
    })
