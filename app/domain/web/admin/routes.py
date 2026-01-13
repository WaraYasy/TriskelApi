from flask import Blueprint, render_template, Response, request, jsonify
from datetime import datetime
import csv
import io

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


@admin_bp.route('/login')
def login():
    """Página de login para administradores"""
    return render_template('admin/login.html')


@admin_bp.route('/dashboard')
def dashboard():
    """Dashboard principal del admin"""
    return render_template('admin/dashboard.html')


@admin_bp.route('/export')
def export_page():
    """Página de exportación de datos"""
    return render_template('admin/export.html')


@admin_bp.route('/export/download', methods=['POST'])
def export_download():
    """Descarga datos en formato CSV"""
    from app.infrastructure.firebase import db
    from app.core.logger import logger

    try:
        # Obtener el tipo de datos a exportar del formulario
        data_type = request.form.get('data_type', 'players')

        # Crear buffer para CSV
        output = io.StringIO()

        if data_type == 'players':
            # Exportar jugadores
            players_ref = db.collection('players')
            players = players_ref.stream()

            writer = csv.DictWriter(output, fieldnames=[
                'uid', 'username', 'display_name', 'email', 'created_at',
                'last_active', 'total_games', 'total_playtime_minutes'
            ])
            writer.writeheader()

            for player in players:
                data = player.to_dict()
                writer.writerow({
                    'uid': player.id,
                    'username': data.get('username', ''),
                    'display_name': data.get('display_name', ''),
                    'email': data.get('email', ''),
                    'created_at': data.get('created_at', ''),
                    'last_active': data.get('last_active', ''),
                    'total_games': data.get('total_games', 0),
                    'total_playtime_minutes': data.get('total_playtime_minutes', 0)
                })

        elif data_type == 'games':
            # Exportar partidas
            games_ref = db.collection('games')
            games = games_ref.stream()

            writer = csv.DictWriter(output, fieldnames=[
                'game_id', 'player_uid', 'started_at', 'ended_at',
                'status', 'current_chapter', 'moral_alignment'
            ])
            writer.writeheader()

            for game in games:
                data = game.to_dict()
                writer.writerow({
                    'game_id': game.id,
                    'player_uid': data.get('player_uid', ''),
                    'started_at': data.get('started_at', ''),
                    'ended_at': data.get('ended_at', ''),
                    'status': data.get('status', ''),
                    'current_chapter': data.get('current_chapter', ''),
                    'moral_alignment': data.get('moral_alignment', '')
                })

        elif data_type == 'decisions':
            # Exportar decisiones
            decisions_ref = db.collection('decisions')
            decisions = decisions_ref.stream()

            writer = csv.DictWriter(output, fieldnames=[
                'decision_id', 'game_id', 'player_uid', 'event_id',
                'choice_made', 'timestamp', 'moral_impact'
            ])
            writer.writeheader()

            for decision in decisions:
                data = decision.to_dict()
                writer.writerow({
                    'decision_id': decision.id,
                    'game_id': data.get('game_id', ''),
                    'player_uid': data.get('player_uid', ''),
                    'event_id': data.get('event_id', ''),
                    'choice_made': data.get('choice_made', ''),
                    'timestamp': data.get('timestamp', ''),
                    'moral_impact': data.get('moral_impact', '')
                })

        elif data_type == 'events':
            # Exportar eventos
            events_ref = db.collection('events')
            events = events_ref.stream()

            writer = csv.DictWriter(output, fieldnames=[
                'event_id', 'player_uid', 'game_id', 'event_type',
                'timestamp', 'chapter', 'data'
            ])
            writer.writeheader()

            for event in events:
                data = event.to_dict()
                writer.writerow({
                    'event_id': event.id,
                    'player_uid': data.get('player_uid', ''),
                    'game_id': data.get('game_id', ''),
                    'event_type': data.get('event_type', ''),
                    'timestamp': data.get('timestamp', ''),
                    'chapter': data.get('chapter', ''),
                    'data': str(data.get('data', ''))
                })

        # Obtener el contenido CSV
        csv_content = output.getvalue()
        output.close()

        # Crear respuesta con el archivo CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'triskel_{data_type}_{timestamp}.csv'

        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )

        logger.info(f"Datos exportados: {data_type}", filename=filename)
        return response

    except Exception as e:
        logger.error("Error al exportar datos", error=str(e), data_type=data_type)
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/migrations')
def migrations_page():
    """Página de migraciones (placeholder)"""
    return render_template('admin/migrations.html')
