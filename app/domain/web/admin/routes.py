import csv
import io
import json
from datetime import datetime
from functools import wraps

from flask import Blueprint, Response, g, jsonify, redirect, render_template, request, url_for
from jose import JWTError, jwt

from app.config.settings import settings

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


def login_required(f):
    """
    Decorador que protege rutas de admin.
    Valida el JWT desde la cookie 'admin_token'.
    Si no es válido, redirige al login.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get("admin_token")

        if not token:
            return redirect(url_for("admin.login"))

        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )

            # Verificar que sea un token de acceso
            if payload.get("type") != "access":
                return redirect(url_for("admin.login"))

            # Guardar info del usuario en g para usarla en la vista
            g.current_user = {
                "id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role"),
            }

        except JWTError:
            return redirect(url_for("admin.login"))

        return f(*args, **kwargs)

    return decorated_function


def _create_export_audit_log(
    data_type: str,
    filename: str = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    error_message: str = None,
):
    """
    Crea un registro de auditoría para exportaciones.
    Si la base de datos SQL no está disponible, solo registra en logs.
    Obtiene la información del usuario actual desde g.current_user.
    """
    from app.core.logger import logger
    from app.domain.auth.adapters.sql_repository import AuthSQLRepository
    from app.infrastructure.database.sql_client import get_db_session

    # Obtener información del usuario actual
    current_user = getattr(g, "current_user", None)
    user_id = current_user.get("id") if current_user else None
    username = current_user.get("username", "anonymous") if current_user else "anonymous"

    try:
        # Intentar obtener sesión SQL
        session = get_db_session()
        if not session:
            logger.warning("Base de datos SQL no disponible, no se puede registrar audit log")
            return

        # Crear repositorio y registrar
        repository = AuthSQLRepository(session)

        # Crear detalles JSON
        details = {"data_type": data_type, "format": "csv"}
        if filename:
            details["filename"] = filename

        repository.create_audit_log(
            user_id=user_id,
            username=username,
            action=f"export_{data_type}_csv",
            resource_type=data_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details),
            success=success,
            error_message=error_message,
        )

        logger.debug(f"Audit log creado para exportación: {data_type} por {username}")

    except Exception as e:
        # Si falla el audit log, solo logear pero no fallar la exportación
        logger.warning(f"No se pudo crear audit log: {e}")


@admin_bp.route("/login")
def login():
    """Página de login para administradores"""
    return render_template("admin/login.html")


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard principal del admin"""
    return render_template("admin/dashboard.html")


@admin_bp.route("/export")
@login_required
def export_page():
    """Página de exportación de datos"""
    return render_template("admin/export.html")


@admin_bp.route("/export/download", methods=["POST"])
@login_required
def export_download():
    """Descarga datos en formato CSV"""
    from app.core.logger import logger
    from app.infrastructure.database.firebase_client import get_firestore_client

    try:
        # Obtener cliente de Firestore
        db = get_firestore_client()

        # Obtener el tipo de datos a exportar del formulario
        data_type = request.form.get("data_type", "players")

        # Crear buffer para CSV
        output = io.StringIO()

        if data_type == "players":
            # Exportar jugadores
            players_ref = db.collection("players")
            players = players_ref.stream()

            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "uid",
                    "username",
                    "display_name",
                    "email",
                    "created_at",
                    "last_active",
                    "total_games",
                    "total_playtime_minutes",
                ],
            )
            writer.writeheader()

            for player in players:
                data = player.to_dict()
                writer.writerow(
                    {
                        "uid": player.id,
                        "username": data.get("username", ""),
                        "display_name": data.get("display_name", ""),
                        "email": data.get("email", ""),
                        "created_at": data.get("created_at", ""),
                        "last_active": data.get("last_active", ""),
                        "total_games": data.get("total_games", 0),
                        "total_playtime_minutes": data.get("total_playtime_minutes", 0),
                    }
                )

        elif data_type == "games":
            # Exportar partidas
            games_ref = db.collection("games")
            games = games_ref.stream()

            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "game_id",
                    "player_uid",
                    "started_at",
                    "ended_at",
                    "status",
                    "current_chapter",
                    "moral_alignment",
                ],
            )
            writer.writeheader()

            for game in games:
                data = game.to_dict()
                writer.writerow(
                    {
                        "game_id": game.id,
                        "player_uid": data.get("player_uid", ""),
                        "started_at": data.get("started_at", ""),
                        "ended_at": data.get("ended_at", ""),
                        "status": data.get("status", ""),
                        "current_chapter": data.get("current_chapter", ""),
                        "moral_alignment": data.get("moral_alignment", ""),
                    }
                )

        elif data_type == "decisions":
            # Exportar decisiones
            decisions_ref = db.collection("decisions")
            decisions = decisions_ref.stream()

            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "decision_id",
                    "game_id",
                    "player_uid",
                    "event_id",
                    "choice_made",
                    "timestamp",
                    "moral_impact",
                ],
            )
            writer.writeheader()

            for decision in decisions:
                data = decision.to_dict()
                writer.writerow(
                    {
                        "decision_id": decision.id,
                        "game_id": data.get("game_id", ""),
                        "player_uid": data.get("player_uid", ""),
                        "event_id": data.get("event_id", ""),
                        "choice_made": data.get("choice_made", ""),
                        "timestamp": data.get("timestamp", ""),
                        "moral_impact": data.get("moral_impact", ""),
                    }
                )

        elif data_type == "events":
            # Exportar eventos
            events_ref = db.collection("events")
            events = events_ref.stream()

            writer = csv.DictWriter(
                output,
                fieldnames=[
                    "event_id",
                    "player_uid",
                    "game_id",
                    "event_type",
                    "timestamp",
                    "chapter",
                    "data",
                ],
            )
            writer.writeheader()

            for event in events:
                data = event.to_dict()
                writer.writerow(
                    {
                        "event_id": event.id,
                        "player_uid": data.get("player_uid", ""),
                        "game_id": data.get("game_id", ""),
                        "event_type": data.get("event_type", ""),
                        "timestamp": data.get("timestamp", ""),
                        "chapter": data.get("chapter", ""),
                        "data": str(data.get("data", "")),
                    }
                )

        # Obtener el contenido CSV
        csv_content = output.getvalue()
        output.close()

        # Crear respuesta con el archivo CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"triskel_{data_type}_{timestamp}.csv"

        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

        logger.info(f"Datos exportados: {data_type}", filename=filename)

        # Registrar en audit log
        _create_export_audit_log(
            data_type=data_type,
            filename=filename,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
        )

        return response

    except Exception as e:
        logger.error("Error al exportar datos", error=str(e), data_type=data_type)

        # Registrar error en audit log
        _create_export_audit_log(
            data_type=data_type,
            filename=None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            success=False,
            error_message=str(e),
        )

        return jsonify({"error": str(e)}), 500


@admin_bp.route("/migrations")
@login_required
def migrations_page():
    """Página de migraciones (placeholder)"""
    return render_template("admin/migrations.html")
