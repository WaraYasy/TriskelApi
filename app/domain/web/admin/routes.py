"""Rutas del Panel de Administración Web.

Este módulo implementa la interfaz web Flask para administradores con:
- Login y gestión de sesiones (cookies JWT)
- Panel de control (dashboard)
- Gestión de migraciones de base de datos SQL
- Logs de auditoría de acciones
- Exportación de datos (CSV/JSON) con auditoría
- Visualización de métricas del sistema

Todos los endpoints requieren autenticación mediante JWT almacenado
en cookie 'admin_token'. Los usuarios deben tener role='admin'.

Autor: Mandrágora
"""

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
    """Decorador que protege rutas de admin requiriendo autenticación JWT.

    Valida el JWT desde la cookie 'admin_token' y redirige al login
    si el token es inválido, expirado o no existe. Guarda la información
    del usuario en el contexto Flask global (g.current_user) para su
    uso en las vistas protegidas.

    Args:
        f (callable): Función de vista Flask a proteger.

    Returns:
        callable: Función decorada con validación de JWT.

    Example:
        ```python
        @admin_bp.route("/dashboard")
        @login_required
        def dashboard():
            username = g.current_user["username"]
            return render_template("dashboard.html", username=username)
        ```

    Note:
        - Verifica que el token sea de tipo "access" (no refresh)
        - Almacena user_id, username y role en g.current_user
        - Redirige a admin.login si falla la validación
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
    export_format: str = "csv",
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    error_message: str = None,
):
    """Crea un registro de auditoría para exportaciones de datos.

    Registra en la base de datos SQL (tabla audit_logs) todas las
    exportaciones realizadas por administradores, incluyendo metadatos
    de la operación. Si la BD SQL no está disponible, solo registra
    en logs estructurados.

    Args:
        data_type (str): Tipo de datos exportados (ej: "players", "games", "events").
        filename (str, optional): Nombre del archivo generado (ej: "players_20260204.csv").
        export_format (str): Formato de exportación ("csv" o "json"). Default: "csv".
        ip_address (str, optional): Dirección IP del cliente que exporta.
        user_agent (str, optional): User-Agent del navegador.
        success (bool): Indica si la exportación fue exitosa. Default: True.
        error_message (str, optional): Mensaje de error si la exportación falló.

    Returns:
        None

    Note:
        - Obtiene user_id y username de g.current_user (Flask context global)
        - Si SQL no está disponible, solo registra warning en logs
        - La acción se registra como "export_{data_type}_{format}"
        - Los detalles JSON incluyen data_type, format y filename

    Example:
        ```python
        _create_export_audit_log(
            data_type="players",
            filename="players_20260204.csv",
            export_format="csv",
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            success=True
        )
        ```
    """
    from app.core.logger import logger
    from app.domain.auth.adapters.sql_repository import SQLAuthRepository
    from app.infrastructure.database.sql_client import sql_manager

    # Obtener información del usuario actual
    current_user = getattr(g, "current_user", None)
    user_id = current_user.get("id") if current_user else None
    username = current_user.get("username", "anonymous") if current_user else "anonymous"

    try:
        # Intentar obtener sesión SQL directamente del manager
        session = sql_manager.get_session()
        if not session:
            logger.warning(
                "Audit log no registrado: Base de datos SQL no disponible",
                extra={"action": f"export_{data_type}_csv", "user": username},
            )
            return

        # Crear repositorio y registrar
        repository = SQLAuthRepository(session)

        # Crear detalles JSON
        details = {"data_type": data_type, "format": export_format}
        if filename:
            details["filename"] = filename

        repository.create_audit_log(
            user_id=user_id,
            username=username,
            action=f"export_{data_type}_{export_format}",
            resource_type=data_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details),
            success=success,
            error_message=error_message,
        )

        session.close()
        logger.debug(f"Audit log registrado: export_{data_type}_csv")

    except Exception as e:
        # Si falla el audit log, solo logear pero no fallar la exportación
        logger.error(
            f"Error al registrar audit log de exportación: {e}",
            extra={"action": f"export_{data_type}_csv", "user": username},
        )


def _create_migration_audit_log(
    action: str,
    revision: str = None,
    direction: str = None,
    filename: str = None,
    ip_address: str = None,
    user_agent: str = None,
    success: bool = True,
    error_message: str = None,
):
    """
    Crea un registro de auditoría para operaciones de migración.
    Si la base de datos SQL no está disponible, solo registra en logs.
    Obtiene la información del usuario actual desde g.current_user.
    """
    from app.core.logger import logger
    from app.domain.auth.adapters.sql_repository import SQLAuthRepository
    from app.infrastructure.database.sql_client import sql_manager

    # Obtener información del usuario actual
    current_user = getattr(g, "current_user", None)
    user_id = current_user.get("id") if current_user else None
    username = current_user.get("username", "anonymous") if current_user else "anonymous"

    try:
        # Intentar obtener sesión SQL directamente del manager
        session = sql_manager.get_session()
        if not session:
            logger.warning(
                "Audit log no registrado: Base de datos SQL no disponible",
                extra={"action": action, "user": username},
            )
            return

        # Crear repositorio y registrar
        repository = SQLAuthRepository(session)

        # Crear detalles JSON
        details = {}
        if revision:
            details["revision"] = revision
        if direction:
            details["direction"] = direction
        if filename:
            details["filename"] = filename

        repository.create_audit_log(
            user_id=user_id,
            username=username,
            action=action,
            resource_type="migration",
            ip_address=ip_address,
            user_agent=user_agent,
            details=json.dumps(details),
            success=success,
            error_message=error_message,
        )

        session.close()
        logger.debug(f"Audit log registrado: {action}")

    except Exception as e:
        # Si falla el audit log, solo logear pero no fallar la operación
        logger.error(
            f"Error al registrar audit log de migración: {e}",
            extra={"action": action, "user": username},
        )


@admin_bp.route("/login")
def login():
    """Página de login para administradores"""
    return render_template("admin/login.html")


@admin_bp.route("/export")
@login_required
def export_page():
    """Página de exportación de datos"""
    return render_template("admin/export.html")


@admin_bp.route("/export/download", methods=["POST"])
@login_required
def export_download():
    """Descarga datos en formato CSV o JSON"""
    from app.core.logger import logger
    from app.infrastructure.database.firebase_client import get_firestore_client

    try:
        # Obtener cliente de Firestore
        db = get_firestore_client()

        # Obtener el tipo de datos a exportar del formulario
        data_type = request.form.get("data_type", "players")
        export_format = request.form.get("format", "csv")  # csv o json

        # Lista para almacenar datos (usado tanto para CSV como JSON)
        data_list = []

        if data_type == "players":
            # Exportar jugadores
            players_ref = db.collection("players")
            players = players_ref.stream()

            for player in players:
                data = player.to_dict()
                data_list.append(
                    {
                        "uid": player.id,
                        "username": data.get("username", ""),
                        "display_name": data.get("display_name", ""),
                        "email": data.get("email", ""),
                        "created_at": str(data.get("created_at", "")),
                        "last_active": str(data.get("last_active", "")),
                        "total_games": data.get("total_games", 0),
                        "total_playtime_minutes": data.get("total_playtime_minutes", 0),
                    }
                )

        elif data_type == "games":
            # Exportar partidas
            games_ref = db.collection("games")
            games = games_ref.stream()

            for game in games:
                data = game.to_dict()
                data_list.append(
                    {
                        "game_id": game.id,
                        "player_uid": data.get("player_uid", ""),
                        "started_at": str(data.get("started_at", "")),
                        "ended_at": str(data.get("ended_at", "")),
                        "status": data.get("status", ""),
                        "current_chapter": data.get("current_chapter", ""),
                        "moral_alignment": data.get("moral_alignment", ""),
                    }
                )

        elif data_type == "decisions":
            # Exportar decisiones
            decisions_ref = db.collection("decisions")
            decisions = decisions_ref.stream()

            for decision in decisions:
                data = decision.to_dict()
                data_list.append(
                    {
                        "decision_id": decision.id,
                        "game_id": data.get("game_id", ""),
                        "player_uid": data.get("player_uid", ""),
                        "event_id": data.get("event_id", ""),
                        "choice_made": data.get("choice_made", ""),
                        "timestamp": str(data.get("timestamp", "")),
                        "moral_impact": data.get("moral_impact", ""),
                    }
                )

        elif data_type == "events":
            # Exportar eventos
            events_ref = db.collection("events")
            events = events_ref.stream()

            for event in events:
                data = event.to_dict()
                data_list.append(
                    {
                        "event_id": event.id,
                        "player_uid": data.get("player_uid", ""),
                        "game_id": data.get("game_id", ""),
                        "event_type": data.get("event_type", ""),
                        "timestamp": str(data.get("timestamp", "")),
                        "chapter": data.get("chapter", ""),
                        "data": str(data.get("data", "")),
                    }
                )

        elif data_type == "admin_users":
            # Exportar usuarios administradores (SQL)
            from app.domain.auth.models import AdminUser
            from app.infrastructure.database.sql_client import sql_manager

            session = sql_manager.get_session()
            if not session:
                raise Exception("Base de datos SQL no disponible")

            try:
                users = session.query(AdminUser).all()
                for user in users:
                    data_list.append(
                        {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "role": user.role,
                            "is_active": user.is_active,
                            "created_at": user.created_at.isoformat() if user.created_at else "",
                            "updated_at": user.updated_at.isoformat() if user.updated_at else "",
                            "last_login": user.last_login.isoformat() if user.last_login else "",
                        }
                    )
            finally:
                session.close()

        elif data_type == "audit_logs":
            # Exportar audit logs (SQL)
            from app.domain.auth.models import AuditLog
            from app.infrastructure.database.sql_client import sql_manager

            session = sql_manager.get_session()
            if not session:
                raise Exception("Base de datos SQL no disponible")

            try:
                logs = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).all()
                for log in logs:
                    data_list.append(
                        {
                            "id": log.id,
                            "user_id": log.user_id,
                            "username": log.username,
                            "action": log.action,
                            "resource_type": log.resource_type,
                            "resource_id": log.resource_id,
                            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                            "ip_address": log.ip_address or "",
                            "user_agent": log.user_agent or "",
                            "details": log.details or "",
                            "success": log.success,
                            "error_message": log.error_message or "",
                        }
                    )
            finally:
                session.close()

        # Verificar si el tipo de datos soporta JSON
        # Solo los datos de SQL (admin_users, audit_logs) soportan JSON
        sql_data_types = ["admin_users", "audit_logs"]
        if export_format == "json" and data_type not in sql_data_types:
            # Forzar CSV para datos de Firestore
            export_format = "csv"

        # Generar el archivo según el formato solicitado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == "json":
            # Exportar como JSON
            json_content = json.dumps(data_list, indent=2, ensure_ascii=False)
            filename = f"triskel_{data_type}_{timestamp}.json"

            response = Response(
                json_content,
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            # Exportar como CSV (por defecto)
            output = io.StringIO()

            if data_list:
                # Usar las claves del primer elemento como fieldnames
                fieldnames = list(data_list[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for row in data_list:
                    # Convertir objetos complejos a string para CSV
                    csv_row = {}
                    for key, value in row.items():
                        if isinstance(value, (dict, list)):
                            csv_row[key] = str(value)
                        else:
                            csv_row[key] = value
                    writer.writerow(csv_row)

            csv_content = output.getvalue()
            output.close()
            filename = f"triskel_{data_type}_{timestamp}.csv"

            response = Response(
                csv_content,
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        logger.info(f"Datos exportados: {data_type} ({export_format})", filename=filename)

        # Registrar en audit log
        _create_export_audit_log(
            data_type=data_type,
            filename=filename,
            export_format=export_format,
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
    """Página de migraciones de base de datos"""
    return render_template("admin/migrations.html")


# ==================== API de Migraciones ====================


def admin_required(f):
    """
    Decorador que requiere rol 'admin' para acceder.
    Debe usarse después de @login_required.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = getattr(g, "current_user", None)
        if not current_user or current_user.get("role") != "admin":
            return jsonify({"error": "Acceso denegado. Se requiere rol admin."}), 403
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/migrations/api/status")
@login_required
@admin_required
def migrations_status():
    """Obtiene el estado de la base de datos y migraciones."""
    from app.domain.web.migrations.service import MigrationService

    service = MigrationService()
    status = service.get_database_status()
    return jsonify(status)


@admin_bp.route("/migrations/api/list")
@login_required
@admin_required
def migrations_list():
    """Lista todas las migraciones disponibles."""
    from app.domain.web.migrations.service import MigrationService

    service = MigrationService()

    if not service.is_database_configured():
        return jsonify({"error": "Base de datos no configurada"}), 400

    try:
        migrations = service.get_migration_history()
        return jsonify(
            {
                "migrations": [
                    {
                        "revision": m.revision,
                        "description": m.description,
                        "date": m.date,
                        "is_applied": m.is_applied,
                    }
                    for m in migrations
                ]
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/migrations/api/upgrade", methods=["POST"])
@login_required
@admin_required
def migrations_upgrade():
    """Aplica migraciones pendientes."""
    from app.core.logger import logger
    from app.domain.web.migrations.service import MigrationService

    service = MigrationService()

    if not service.is_database_configured():
        return jsonify({"error": "Base de datos no configurada"}), 400

    # Obtener revisión objetivo (default: head)
    data = request.get_json() or {}
    revision = data.get("revision", "head")

    current_user = getattr(g, "current_user", {})
    logger.info(
        f"Upgrade de migraciones iniciado por {current_user.get('username')}",
        revision=revision,
    )

    result = service.upgrade(revision)

    if result["success"]:
        logger.info("Upgrade completado", **result)
    else:
        logger.error("Error en upgrade", **result)

    # Registrar en audit log
    _create_migration_audit_log(
        action="migration_upgrade",
        revision=revision,
        direction="upgrade",
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        success=result["success"],
        error_message=result.get("error"),
    )

    return jsonify(result)


@admin_bp.route("/migrations/api/downgrade", methods=["POST"])
@login_required
@admin_required
def migrations_downgrade():
    """Revierte la última migración aplicada."""
    from app.core.logger import logger
    from app.domain.web.migrations.service import MigrationService

    service = MigrationService()

    if not service.is_database_configured():
        return jsonify({"error": "Base de datos no configurada"}), 400

    # Obtener revisión objetivo (default: -1, revertir una)
    data = request.get_json() or {}
    revision = data.get("revision", "-1")

    current_user = getattr(g, "current_user", {})
    logger.info(
        f"Downgrade de migraciones iniciado por {current_user.get('username')}",
        revision=revision,
    )

    result = service.downgrade(revision)

    if result["success"]:
        logger.info("Downgrade completado", **result)
    else:
        logger.error("Error en downgrade", **result)

    # Registrar en audit log
    _create_migration_audit_log(
        action="migration_downgrade",
        revision=revision,
        direction="downgrade",
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
        success=result["success"],
        error_message=result.get("error"),
    )

    return jsonify(result)


@admin_bp.route("/migrations/api/download-sql", methods=["POST"])
@login_required
@admin_required
def migrations_download_sql():
    """Genera y descarga el SQL de las migraciones sin ejecutarlo."""
    from app.core.logger import logger
    from app.domain.web.migrations.service import MigrationService

    service = MigrationService()

    if not service.is_database_configured():
        return jsonify({"error": "Base de datos no configurada"}), 400

    # Obtener parámetros
    data = request.get_json() or {}
    revision = data.get("revision", "head")
    direction = data.get("direction", "upgrade")

    current_user = getattr(g, "current_user", {})
    logger.info(
        f"Generación de SQL iniciada por {current_user.get('username')}",
        revision=revision,
        direction=direction,
    )

    try:
        result = service.generate_sql(revision, direction)

        if not result["success"]:
            logger.error("Error al generar SQL", **result)

            # Registrar error en audit log
            _create_migration_audit_log(
                action="download_migration_sql",
                revision=revision,
                direction=direction,
                filename=None,
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
                success=False,
                error_message=result.get("message"),
            )

            return jsonify({"error": result["message"]}), 500

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"migration_{direction}_{revision}_{timestamp}.sql"

        logger.info("SQL generado exitosamente", filename=filename)

        # Registrar en audit log
        _create_migration_audit_log(
            action="download_migration_sql",
            revision=revision,
            direction=direction,
            filename=filename,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            success=True,
        )

        # Retornar como archivo descargable
        return Response(
            result["sql"],
            mimetype="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error("Error al descargar SQL de migración", error=str(e))

        # Registrar error en audit log
        _create_migration_audit_log(
            action="download_migration_sql",
            revision=revision,
            direction=direction,
            filename=None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent"),
            success=False,
            error_message=str(e),
        )

        return jsonify({"error": str(e)}), 500
