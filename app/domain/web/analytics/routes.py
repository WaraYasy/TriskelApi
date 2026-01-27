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

from flask import Blueprint, jsonify, render_template, request, send_file

from app.config.settings import settings

from .service import AnalyticsService

# Crear blueprint
analytics_bp = Blueprint("analytics", __name__, template_folder="templates")

# Instanciar servicio con API Key
# Usa la URL configurada en settings (auto-detecta producción vs desarrollo)
analytics_service = AnalyticsService(
    api_base_url=settings.api_base_url, api_key=settings.api_key, use_mock_data=False
)


@analytics_bp.route("/")
def index():
    """
    Dashboard principal con métricas globales.
    Renderiza la página inmediatamente, los datos se cargan via AJAX.
    """
    return render_template("analytics/index.html")


@analytics_bp.route("/players")
def players():
    """Análisis detallado de jugadores. Datos se cargan via AJAX."""
    return render_template("analytics/players.html")


@analytics_bp.route("/games")
def games():
    """Análisis de partidas y progresión. Datos se cargan via AJAX."""
    return render_template("analytics/games.html")


@analytics_bp.route("/choices")
def choices():
    """Análisis de decisiones morales. Datos se cargan via AJAX."""
    return render_template("analytics/choices.html")


@analytics_bp.route("/events")
def events():
    """Análisis de eventos de gameplay. Datos se cargan via AJAX."""
    return render_template("analytics/events.html")


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
        data = analytics_service.get_all_events()
        filename = "events"
    else:
        return jsonify({"error": "Tipo de exportación no válido"}), 400

    if export_format == "csv":
        # Exportar a CSV
        filepath = analytics_service.export_to_csv(data, filename)
        if filepath:
            return send_file(filepath, as_attachment=True, download_name=f"{filename}.csv")
        else:
            return jsonify({"error": "Error al exportar datos"}), 500
    elif export_format == "json":
        return jsonify(data)
    else:
        return jsonify({"error": "Formato no válido"}), 400


@analytics_bp.route("/advanced")
def advanced():
    """Dashboard avanzado con métricas adicionales. Datos se cargan via AJAX."""
    return render_template("analytics/advanced.html")


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

    # Obtener total de eventos
    events_data = analytics_service.get_all_events()
    metrics["total_events"] = len(events_data)

    return jsonify(metrics)


@analytics_bp.route("/api/charts/moral")
def api_chart_moral():
    """API endpoint para gráfico de decisiones morales."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_moral_choices_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/deaths")
def api_chart_deaths():
    """API endpoint para gráfico de muertes por nivel."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_deaths_per_level_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/alignment")
def api_chart_alignment():
    """API endpoint para gráfico de alineación moral."""
    players = analytics_service.get_all_players()
    chart_html = analytics_service.create_moral_alignment_chart(players)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/choices/global")
def api_chart_choices_global():
    """API endpoint para gráfico de distribución global de decisiones morales."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_global_good_vs_bad_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/choices/alignment")
def api_chart_choices_alignment():
    """API endpoint para gráfico de alineación moral de jugadores."""
    players = analytics_service.get_all_players()
    chart_html = analytics_service.create_moral_alignment_chart(players)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/choices/levels")
def api_chart_choices_levels():
    """API endpoint para gráfico de decisiones morales por nivel."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_moral_choices_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/players")
def api_players():
    """API endpoint para lista de jugadores."""
    players_data = analytics_service.get_all_players()
    return jsonify(players_data)


@analytics_bp.route("/api/games")
def api_games():
    """API endpoint para lista de partidas."""
    games_data = analytics_service.get_all_games()
    return jsonify(games_data)


@analytics_bp.route("/api/charts/playtime")
def api_chart_playtime():
    """API endpoint para gráfico de distribución de tiempo de juego."""
    players = analytics_service.get_all_players()
    chart_html = analytics_service.create_playtime_distribution(players)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/events")
def api_chart_events():
    """API endpoint para gráfico de eventos por tipo."""
    try:
        all_events = analytics_service.get_all_events()
        chart_html = analytics_service.create_events_by_type_chart(all_events)
        return jsonify({"html": chart_html, "total": len(all_events)})
    except Exception as e:
        print(f"[ERROR] /api/charts/events failed: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/charts/events/timeline")
def api_chart_events_timeline():
    """API endpoint para gráfico de línea temporal de eventos."""
    try:
        all_events = analytics_service.get_all_events()
        chart_html = analytics_service.create_events_timeline_chart(all_events)
        return jsonify({"html": chart_html})
    except Exception as e:
        print(f"[ERROR] /api/charts/events/timeline failed: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/charts/events/deaths")
def api_chart_events_deaths():
    """API endpoint para gráfico de muertes por nivel (reportadas por eventos)."""
    try:
        all_events = analytics_service.get_all_events()
        chart_html = analytics_service.create_deaths_event_chart(all_events)
        return jsonify({"html": chart_html})
    except Exception as e:
        print(f"[ERROR] /api/charts/events/deaths failed: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/api/charts/relics")
def api_chart_relics():
    """API endpoint para gráfico de distribución de reliquias."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_relics_distribution_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/completion")
def api_chart_completion():
    """API endpoint para gráfico de tasa de completado por nivel."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_level_completion_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/playtime-level")
def api_chart_playtime_level():
    """API endpoint para gráfico de tiempo promedio por nivel."""
    games = analytics_service.get_all_games()
    chart_html = analytics_service.create_playtime_per_level_chart(games)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/charts/active-players")
def api_chart_active_players():
    """API endpoint para gráfico de jugadores activos en los últimos 7 días."""
    events = analytics_service.get_all_events()
    chart_html = analytics_service.create_active_players_chart(events)
    return jsonify({"html": chart_html})


@analytics_bp.route("/api/advanced")
def api_advanced():
    """API endpoint para métricas avanzadas."""
    games_data = analytics_service.get_all_games()
    players_data = analytics_service.get_all_players()

    total_relics = sum(len(g.get("relics", [])) for g in games_data)
    total_deaths = sum(g.get("metrics", {}).get("total_deaths", 0) for g in games_data)
    avg_completion = (
        sum(g.get("completion_percentage", 0) for g in games_data) / len(games_data)
        if games_data
        else 0
    )

    return jsonify(
        {
            "total_relics": total_relics,
            "total_deaths": total_deaths,
            "avg_completion_percentage": round(avg_completion, 2),
            "total_games": len(games_data),
            "total_players": len(players_data),
            "games": games_data[:20],
        }
    )


@analytics_bp.route("/api/events")
def api_events():
    """
    API endpoint para obtener eventos recientes en JSON.

    Returns:
        JSON: Lista de eventos recientes (máximo 10)
    """
    all_events = analytics_service.get_all_events()

    # Ordenar por fecha (más recientes primero) y limitar a 10
    all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    recent_events = all_events[:10]

    return jsonify(recent_events)
