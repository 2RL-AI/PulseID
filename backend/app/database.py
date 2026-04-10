"""Database dump and restore endpoints."""

import io
import json
import logging
import zipfile
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request, send_file

from . import db
from .auth import require_auth
from .models import AccessLog, Employee, OfficeSettings, User
from .version import APP_VERSION, DB_SCHEMA_VERSION

logger = logging.getLogger(__name__)

db_bp = Blueprint("database", __name__)


def _serialize_table(model):
    rows = model.query.all()
    return [r.to_dict() for r in rows]


def _dump_all():
    return {
        "meta": {
            "app_version": APP_VERSION,
            "db_schema_version": DB_SCHEMA_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        },
        "users": _serialize_table(User),
        "employees": [
            {
                **e.to_dict(),
                "password_hash": e.password_hash if hasattr(e, "password_hash") else None,
            }
            for e in []
        ],
        "employees": [
            {
                "id": e.id,
                "first_name": e.first_name,
                "last_name": e.last_name,
                "email": e.email,
                "phone": e.phone,
                "position": e.position,
                "department": e.department,
                "badge_uid": e.badge_uid,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            }
            for e in Employee.query.all()
        ],
        "access_logs": [
            {
                "id": l.id,
                "employee_id": l.employee_id,
                "name": l.name,
                "uid": l.uid,
                "event_type": l.event_type,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in AccessLog.query.order_by(AccessLog.id).all()
        ],
        "users_full": [
            {
                "id": u.id,
                "username": u.username,
                "password_hash": u.password_hash,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in User.query.all()
        ],
        "office_settings": OfficeSettings.get().to_dict(),
    }


@db_bp.route("/dump", methods=["POST"])
@require_auth
def dump_database():
    data = _dump_all()
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("pulseid_dump.json", json_bytes)
    buf.seek(0)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"pulseid_backup_{APP_VERSION}_{ts}.zip"
    logger.info("Database dump created: %s (%d bytes)", filename, len(json_bytes))
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=filename)


@db_bp.route("/restore", methods=["POST"])
@require_auth
def restore_database():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    f = request.files["file"]
    if not f.filename.endswith(".zip"):
        return jsonify({"error": "File must be a .zip archive."}), 400

    try:
        with zipfile.ZipFile(io.BytesIO(f.read()), "r") as zf:
            names = zf.namelist()
            json_name = next((n for n in names if n.endswith(".json")), None)
            if not json_name:
                return jsonify({"error": "No JSON file found in archive."}), 400
            data = json.loads(zf.read(json_name).decode("utf-8"))
    except (zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return jsonify({"error": f"Invalid archive: {exc}"}), 400

    meta = data.get("meta", {})
    dump_schema = meta.get("db_schema_version")
    dump_version = meta.get("app_version", "unknown")

    if dump_schema is None:
        return jsonify({"error": "Invalid dump file: missing schema version."}), 400

    if dump_schema != DB_SCHEMA_VERSION:
        return jsonify({
            "error": f"Incompatible database schema. Dump is schema v{dump_schema} "
                     f"(app {dump_version}), but this instance requires schema "
                     f"v{DB_SCHEMA_VERSION} (app {APP_VERSION})."
        }), 409

    try:
        AccessLog.query.delete()
        Employee.query.delete()
        User.query.delete()
        db.session.flush()

        for u in data.get("users_full", []):
            user = User(
                id=u["id"],
                username=u["username"],
                password_hash=u["password_hash"],
            )
            if u.get("created_at"):
                user.created_at = datetime.fromisoformat(u["created_at"])
            db.session.add(user)

        db.session.flush()

        for e in data.get("employees", []):
            emp = Employee(
                id=e["id"],
                first_name=e["first_name"],
                last_name=e["last_name"],
                email=e.get("email"),
                phone=e.get("phone"),
                position=e.get("position"),
                department=e.get("department"),
                badge_uid=e.get("badge_uid"),
            )
            if e.get("created_at"):
                emp.created_at = datetime.fromisoformat(e["created_at"])
            if e.get("updated_at"):
                emp.updated_at = datetime.fromisoformat(e["updated_at"])
            db.session.add(emp)

        db.session.flush()

        for l in data.get("access_logs", []):
            log = AccessLog(
                id=l["id"],
                employee_id=l.get("employee_id"),
                name=l["name"],
                uid=l["uid"],
                event_type=l.get("event_type", "NEW_RECORD"),
            )
            if l.get("timestamp"):
                log.timestamp = datetime.fromisoformat(l["timestamp"])
            db.session.add(log)

        office_data = data.get("office_settings")
        if office_data:
            office = OfficeSettings.get()
            office.office_name = office_data.get("office_name", "")
            office.timezone = office_data.get("timezone", "UTC")
            office.backup_enabled = office_data.get("backup_enabled", False)
            office.backup_frequency = office_data.get("backup_frequency", "daily")
            office.backup_day_of_week = office_data.get("backup_day_of_week", 0)
            office.backup_hour = office_data.get("backup_hour", 2)
            office.backup_retention_days = office_data.get("backup_retention_days", 30)

        db.session.commit()

        _reset_sequences()

        counts = {
            "users": len(data.get("users_full", [])),
            "employees": len(data.get("employees", [])),
            "access_logs": len(data.get("access_logs", [])),
        }
        logger.info("Database restored from dump (app %s, schema v%d): %s", dump_version, dump_schema, counts)
        return jsonify({
            "message": f"Database restored successfully from {dump_version} backup.",
            "counts": counts,
        })

    except Exception as exc:
        db.session.rollback()
        logger.error("Database restore failed: %s", exc, exc_info=True)
        return jsonify({"error": f"Restore failed: {exc}"}), 500


def _reset_sequences():
    """Reset PostgreSQL sequences to max(id)+1 after bulk insert."""
    try:
        for table in ("users", "employees", "access_logs"):
            db.session.execute(
                db.text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 0) + 1, false) FROM {table}")
            )
        db.session.commit()
    except Exception:
        db.session.rollback()


@db_bp.route("/info", methods=["GET"])
@require_auth
def database_info():
    return jsonify({
        "app_version": APP_VERSION,
        "db_schema_version": DB_SCHEMA_VERSION,
        "counts": {
            "users": User.query.count(),
            "employees": Employee.query.count(),
            "access_logs": AccessLog.query.count(),
        },
    })
