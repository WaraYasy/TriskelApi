"""
Blueprint de Analytics

Dashboard de métricas y visualizaciones del juego.

Rutas:
- GET /dashboard/          → Dashboard principal con métricas globales
- GET /dashboard/players   → Análisis detallado de jugadores
- GET /dashboard/games     → Análisis de partidas y progresión
- GET /dashboard/choices   → Análisis de decisiones morales
- GET /dashboard/events    → Análisis de eventos de gameplay
- GET /dashboard/export    → Exportar datos a CSV
"""

from flask import Blueprint, render_template, jsonify, request, send_file
from .service import AnalyticsService
from app.config.settings import settings

# Crear blueprint
analytics_bp = Blueprint("analytics", __name__, template_folder="templates")

# Instanciar servicio con API Key
analytics_service = AnalyticsService(
    api_base_url="http://localhost:8000", api_key=settings.api_key
)


@analytics_bp.route("/")
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
    # Obtener datos de la API
    players = analytics_service.get_all_players()
    games = analytics_service.get_all_games()

    # Calcular métricas
    metrics = analytics_service.calculate_global_metrics(players, games)

    # Obtener total de eventos
    all_events = []
    for player in players:
        try:
            response = analytics_service.client.get(
                f"/v1/events/player/{player['player_id']}"
            )
            response.raise_for_status()
            events_data = response.json()
            all_events.extend(events_data)
        except Exception:
            pass

    metrics["total_events"] = len(all_events)

    # Generar gráficos
    moral_chart = analytics_service.create_moral_choices_chart(games)
    deaths_chart = analytics_service.create_deaths_per_level_chart(games)
    alignment_chart = analytics_service.create_moral_alignment_chart(players)

    return render_template(
        "analytics/index.html",
        metrics=metrics,
        moral_chart=moral_chart,
        deaths_chart=deaths_chart,
        alignment_chart=alignment_chart,
    )


@analytics_bp.route("/players")
def players():
    """
    Análisis detallado de jugadores.

    Muestra:
    - Lista de jugadores
    - Stats individuales
    - Distribución de alineación moral
    - Tiempo de juego por jugador
    """
    # Obtener datos
    players_data = analytics_service.get_all_players()

    # Generar gráfico de distribución de tiempo
    playtime_chart = analytics_service.create_playtime_distribution(players_data)

    return render_template(
        "analytics/players.html", players=players_data, playtime_chart=playtime_chart
    )


@analytics_bp.route("/games")
def games():
    """
    Análisis de partidas y progresión.

    Muestra:
    - Lista de partidas completadas
    - Tiempo por nivel
    - Muertes por nivel
    - Tasa de completado
    """
    # Obtener datos
    games_data = analytics_service.get_all_games()

    # Generar gráfico de muertes por nivel
    deaths_chart = analytics_service.create_deaths_per_level_chart(games_data)

    return render_template(
        "analytics/games.html", games=games_data, deaths_chart=deaths_chart
    )


@analytics_bp.route("/choices")
def choices():
    """
    Análisis de decisiones morales.

    Muestra:
    - Distribución de decisiones por nivel
    - Porcentaje buenas vs malas
    - Correlación con completado del juego
    - Gráficos de barras con Plotly
    """
    # Obtener datos
    games_data = analytics_service.get_all_games()

    # Generar gráfico de decisiones morales
    moral_chart = analytics_service.create_moral_choices_chart(games_data)

    return render_template("analytics/choices.html", moral_chart=moral_chart)


@analytics_bp.route("/events")
def events():
    """
    Análisis de eventos de gameplay.

    Muestra:
    - Total de eventos registrados
    - Distribución por tipo de evento
    - Eventos por nivel
    - Timeline de eventos
    """
    # Obtener eventos de todos los jugadores
    players = analytics_service.get_all_players()
    all_events = []

    for player in players:
        try:
            response = analytics_service.client.get(
                f"/v1/events/player/{player['player_id']}"
            )
            response.raise_for_status()
            events_data = response.json()
            all_events.extend(events_data)
        except Exception as e:
            print(f"Error obteniendo eventos del jugador {player['player_id']}: {e}")

    # Generar gráfico de eventos por tipo
    events_chart = analytics_service.create_events_by_type_chart(all_events)

    return render_template(
        "analytics/events.html", total_events=len(all_events), events_chart=events_chart
    )


@analytics_bp.route("/export")
def export():
    """
    Exporta datos a CSV.

    Query params:
    - type: players | games | events
    - format: csv | json

    Returns:
        File: Archivo descargable
    """
    export_type = request.args.get("type", "players")
    export_format = request.args.get("format", "csv")

    # Obtener datos según el tipo
    if export_type == "players":
        data = analytics_service.get_all_players()
        filename = "players"
    elif export_type == "games":
        data = analytics_service.get_all_games()
        filename = "games"
    elif export_type == "events":
        # Obtener todos los eventos
        players = analytics_service.get_all_players()
        data = []
        for player in players:
            try:
                response = analytics_service.client.get(
                    f"/v1/events/player/{player['player_id']}"
                )
                response.raise_for_status()
                data.extend(response.json())
            except Exception:
                pass
        filename = "events"
    else:
        return jsonify({"error": "Tipo de exportación no válido"}), 400

    if export_format == "csv":
        # Exportar a CSV
        filepath = analytics_service.export_to_csv(data, filename)
        if filepath:
            return send_file(
                filepath, as_attachment=True, download_name=f"{filename}.csv"
            )
        else:
            return jsonify({"error": "Error al exportar datos"}), 500
    elif export_format == "json":
        return jsonify(data)
    else:
        return jsonify({"error": "Formato no válido"}), 400


@analytics_bp.route("/advanced")
def advanced():
    """
    Dashboard avanzado con métricas adicionales.

    Muestra:
    - Reliquias más obtenidas
    - Tasa de completado por nivel
    - Tiempo promedio por nivel
    - Estadísticas detalladas
    """
    # Obtener datos
    games_data = analytics_service.get_all_games()
    players_data = analytics_service.get_all_players()

    # Generar gráficos adicionales
    relics_chart = analytics_service.create_relics_distribution_chart(games_data)
    completion_chart = analytics_service.create_level_completion_chart(games_data)
    playtime_chart = analytics_service.create_playtime_per_level_chart(games_data)

    # Calcular métricas adicionales
    total_relics = sum(len(g.get("relics", [])) for g in games_data)
    total_deaths = sum(g.get("metrics", {}).get("total_deaths", 0) for g in games_data)
    avg_completion = (
        sum(g.get("completion_percentage", 0) for g in games_data) / len(games_data)
        if games_data
        else 0
    )

    advanced_metrics = {
        "total_relics": total_relics,
        "total_deaths": total_deaths,
        "avg_completion_percentage": round(avg_completion, 2),
        "total_games": len(games_data),
        "total_players": len(players_data),
    }

    return render_template(
        "analytics/advanced.html",
        metrics=advanced_metrics,
        relics_chart=relics_chart,
        completion_chart=completion_chart,
        playtime_chart=playtime_chart,
        games=games_data,
    )


@analytics_bp.route("/api/metrics")
def api_metrics():
    """
    API endpoint para obtener métricas en JSON.

    Útil para actualizar el dashboard sin recargar la página.

    Returns:
        JSON: Métricas actualizadas
    """
    players = analytics_service.get_all_players()
    games = analytics_service.get_all_games()
    metrics = analytics_service.calculate_global_metrics(players, games)

    return jsonify(metrics)
