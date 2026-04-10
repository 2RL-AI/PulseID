"""API routes — employees, badges, records, users, reader, reports."""

from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request, send_file

from . import db
from .auth import require_auth
from .models import AccessLog, Employee, OfficeSettings, User
from .reader import detect_readers, read_uid, reader_service
from .reports import build_report_pdf
from .version import APP_VERSION, DB_SCHEMA_VERSION

api_bp = Blueprint("api", __name__)


@api_bp.before_request
def check_api_key():
    if request.endpoint and request.endpoint.startswith("auth."):
        return None
    api_key = request.headers.get("X-API-Key", "")
    expected = current_app.config.get("API_KEY", "")
    if not expected or api_key != expected:
        return jsonify({"error": "Invalid or missing API key"}), 401


def _company_info() -> dict:
    cfg = current_app.config
    info = {}
    if cfg.get("COMPANY_NAME"):
        info["name"] = cfg["COMPANY_NAME"]
    addr = {}
    for key in ("COMPANY_STREET", "COMPANY_CITY", "COMPANY_ZIP", "COMPANY_COUNTRY"):
        short = key.replace("COMPANY_", "").lower()
        if cfg.get(key):
            addr[short] = cfg[key]
    if addr:
        info["address"] = addr
    if cfg.get("COMPANY_PHONE"):
        info["phone"] = cfg["COMPANY_PHONE"]
    if cfg.get("COMPANY_EMAIL"):
        info["email"] = cfg["COMPANY_EMAIL"]
    return info


# ── Employees CRUD ─────────────────────────────────────────

@api_bp.route("/employees", methods=["GET"])
@require_auth
def list_employees():
    employees = Employee.query.order_by(Employee.last_name, Employee.first_name).all()
    return jsonify([e.to_dict() for e in employees])


@api_bp.route("/employees", methods=["POST"])
@require_auth
def create_employee():
    data = request.get_json(silent=True) or {}
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    if not first_name or not last_name:
        return jsonify({"error": "first_name and last_name are required."}), 400

    emp = Employee(
        first_name=first_name,
        last_name=last_name,
        email=(data.get("email") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        position=(data.get("position") or "").strip() or None,
        department=(data.get("department") or "").strip() or None,
    )
    db.session.add(emp)
    db.session.commit()
    return jsonify(emp.to_dict()), 201


@api_bp.route("/employees/<int:eid>", methods=["GET"])
@require_auth
def get_employee(eid):
    emp = db.session.get(Employee, eid)
    if not emp:
        return jsonify({"error": "Employee not found."}), 404
    return jsonify(emp.to_dict())


@api_bp.route("/employees/<int:eid>", methods=["PUT"])
@require_auth
def update_employee(eid):
    emp = db.session.get(Employee, eid)
    if not emp:
        return jsonify({"error": "Employee not found."}), 404
    data = request.get_json(silent=True) or {}
    if "first_name" in data:
        v = (data["first_name"] or "").strip()
        if not v:
            return jsonify({"error": "first_name cannot be empty."}), 400
        emp.first_name = v
    if "last_name" in data:
        v = (data["last_name"] or "").strip()
        if not v:
            return jsonify({"error": "last_name cannot be empty."}), 400
        emp.last_name = v
    for field in ("email", "phone", "position", "department"):
        if field in data:
            setattr(emp, field, (data[field] or "").strip() or None)
    db.session.commit()
    return jsonify(emp.to_dict())


@api_bp.route("/employees/<int:eid>", methods=["DELETE"])
@require_auth
def delete_employee(eid):
    emp = db.session.get(Employee, eid)
    if not emp:
        return jsonify({"error": "Employee not found."}), 404
    name = emp.full_name
    db.session.delete(emp)
    db.session.commit()
    return jsonify({"message": f"Employee '{name}' deleted."})


# ── Badge assignment ───────────────────────────────────────

@api_bp.route("/employees/<int:eid>/assign-badge", methods=["POST"])
@require_auth
def assign_badge(eid):
    """Put the badge on the reader, then call this endpoint. Blocks up to 30 s."""
    emp = db.session.get(Employee, eid)
    if not emp:
        return jsonify({"success": False, "message": "Employee not found."}), 404

    result = reader_service.request_registration(eid, timeout=30)
    if result is None:
        return jsonify({"success": False, "message": "Timeout — no badge detected. Hold the badge on the reader and try again."}), 408
    status = 200 if result.get("success") else 400
    return jsonify(result), status


@api_bp.route("/employees/<int:eid>/assign-badge", methods=["DELETE"])
@require_auth
def unassign_badge(eid):
    emp = db.session.get(Employee, eid)
    if not emp:
        return jsonify({"error": "Employee not found."}), 404
    if not emp.badge_uid:
        return jsonify({"message": "No badge assigned."}), 200
    emp.badge_uid = None
    db.session.commit()
    return jsonify({"message": f"Badge unassigned from {emp.full_name}."})


# ── Records ────────────────────────────────────────────────

@api_bp.route("/records", methods=["GET"])
@require_auth
def list_records():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 200)
    employee_id = request.args.get("employee_id", type=int)
    event_type = request.args.get("event_type")

    query = AccessLog.query
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if event_type:
        query = query.filter_by(event_type=event_type)
    query = query.order_by(AccessLog.timestamp.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "records": [l.to_dict() for l in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@api_bp.route("/records/latest", methods=["GET"])
@require_auth
def latest_records():
    """Return records created after `since` ISO timestamp (for polling)."""
    since = request.args.get("since")
    limit = min(request.args.get("limit", 20, type=int), 100)
    query = AccessLog.query
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            query = query.filter(AccessLog.timestamp > since_dt)
        except (ValueError, TypeError):
            pass
    logs = query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
    return jsonify({
        "records": [l.to_dict() for l in logs],
        "server_time": datetime.now(timezone.utc).isoformat(),
    })


@api_bp.route("/records/remove-period", methods=["POST"])
@require_auth
def remove_records_period():
    data = request.get_json(silent=True) or {}
    year = data.get("year")
    month = data.get("month")
    employee_id = data.get("employee_id")
    if year is None or month is None:
        return jsonify({"error": "year and month are required."}), 400
    year, month = int(year), int(month)

    query = AccessLog.query.filter(
        db.extract("year", AccessLog.timestamp) == year,
        db.extract("month", AccessLog.timestamp) == month,
    )
    if employee_id:
        query = query.filter_by(employee_id=int(employee_id))
    removed = query.delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"message": f"Removed {removed} record(s) for {month:02d}/{year}."})


@api_bp.route("/records/remove-before-current-month", methods=["POST"])
@require_auth
def remove_records_before_current_month():
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    now = datetime.now(timezone.utc)
    first_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    query = AccessLog.query.filter(AccessLog.timestamp < first_of_month)
    if employee_id:
        query = query.filter_by(employee_id=int(employee_id))
    removed = query.delete(synchronize_session=False)
    db.session.commit()
    return jsonify({"message": f"Removed {removed} record(s) before {now.year}-{now.month:02d}."})


# ── Reports ────────────────────────────────────────────────

@api_bp.route("/available-months", methods=["GET"])
@require_auth
def available_months():
    rows = db.session.query(
        db.func.extract("year", AccessLog.timestamp).label("year"),
        db.func.extract("month", AccessLog.timestamp).label("month"),
    ).distinct().all()
    months = []
    for row in rows:
        y, m = int(row.year), int(row.month)
        label = datetime(y, m, 1).strftime("%B %Y")
        months.append({"year": y, "month": m, "label": label})
    months.sort(key=lambda x: (x["year"], x["month"]))
    return jsonify({"months": months})


@api_bp.route("/reports/download", methods=["POST"])
@require_auth
def download_report():
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    year = data.get("year")
    month = data.get("month")
    if year is not None:
        year = int(year)
    if month is not None:
        month = int(month)

    if not employee_id:
        return jsonify({"error": "employee_id is required."}), 400

    emp = db.session.get(Employee, int(employee_id))
    if not emp:
        return jsonify({"error": "Employee not found."}), 404
    if not emp.badge_uid:
        return jsonify({"error": f"{emp.full_name} has no badge assigned."}), 400

    logs = AccessLog.query.filter_by(uid=emp.badge_uid).order_by(AccessLog.timestamp).all()
    if not logs:
        return jsonify({"error": f"No access records found for {emp.full_name}."}), 404

    office = OfficeSettings.get()
    records = [{"name": l.name, "uid": l.uid, "timestamp": l.timestamp} for l in logs]
    try:
        buf = build_report_pdf(
            employee_name=emp.full_name,
            uid=emp.badge_uid,
            records=records,
            company_info=_company_info(),
            logo_path=current_app.config.get("LOGO_PATH") or None,
            filter_year=year,
            filter_month=month,
            office_name=office.office_name or None,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if year is not None and month is not None:
        from datetime import datetime as _dt
        period = _dt(year, month, 1).strftime("%B_%Y")
    else:
        period = "full"
    filename = f"PulseID_{emp.full_name.replace(' ', '_')}_{period}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)


# ── Users CRUD ─────────────────────────────────────────────

@api_bp.route("/users", methods=["GET"])
@require_auth
def list_users():
    users = User.query.order_by(User.username).all()
    return jsonify([u.to_dict() for u in users])


@api_bp.route("/users", methods=["POST"])
@require_auth
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username and password are required."}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters."}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": f"Username '{username}' already exists."}), 409
    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@api_bp.route("/users/<int:uid>", methods=["PUT"])
@require_auth
def update_user(uid):
    user = db.session.get(User, uid)
    if not user:
        return jsonify({"error": "User not found."}), 404
    data = request.get_json(silent=True) or {}
    if "username" in data:
        v = (data["username"] or "").strip()
        if not v:
            return jsonify({"error": "username cannot be empty."}), 400
        dup = User.query.filter(User.username == v, User.id != uid).first()
        if dup:
            return jsonify({"error": f"Username '{v}' already exists."}), 409
        user.username = v
    if "password" in data and data["password"]:
        if len(data["password"]) < 4:
            return jsonify({"error": "Password must be at least 4 characters."}), 400
        user.set_password(data["password"])
    db.session.commit()
    return jsonify(user.to_dict())


@api_bp.route("/users/<int:uid>", methods=["DELETE"])
@require_auth
def delete_user(uid):
    user = db.session.get(User, uid)
    if not user:
        return jsonify({"error": "User not found."}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User '{user.username}' deleted."})


# ── Reader ─────────────────────────────────────────────────

@api_bp.route("/reader/status", methods=["GET"])
@require_auth
def reader_status():
    return jsonify(reader_service.get_status())


@api_bp.route("/reader/detect", methods=["GET"])
@require_auth
def reader_detect():
    return jsonify({"readers": detect_readers()})


# ── Version ────────────────────────────────────────────────

@api_bp.route("/version", methods=["GET"])
def api_version():
    return jsonify({"app_version": APP_VERSION, "db_schema_version": DB_SCHEMA_VERSION})


# ── Office settings ────────────────────────────────────────

@api_bp.route("/office", methods=["GET"])
@require_auth
def get_office():
    return jsonify(OfficeSettings.get().to_dict())


@api_bp.route("/office", methods=["PUT"])
@require_auth
def update_office():
    data = request.get_json(silent=True) or {}
    office = OfficeSettings.get()
    if "office_name" in data:
        office.office_name = (data["office_name"] or "").strip()
    if "timezone" in data:
        tz = (data["timezone"] or "").strip()
        if tz:
            import zoneinfo
            try:
                zoneinfo.ZoneInfo(tz)
            except (KeyError, Exception):
                return jsonify({"error": f"Invalid timezone: {tz}"}), 400
        office.timezone = tz or "UTC"
    if "backup_enabled" in data:
        office.backup_enabled = bool(data["backup_enabled"])
    if "backup_frequency" in data:
        freq = data["backup_frequency"]
        if freq not in ("daily", "weekly"):
            return jsonify({"error": "backup_frequency must be 'daily' or 'weekly'."}), 400
        office.backup_frequency = freq
    if "backup_day_of_week" in data:
        d = int(data["backup_day_of_week"])
        if d < 0 or d > 6:
            return jsonify({"error": "backup_day_of_week must be 0 (Mon) to 6 (Sun)."}), 400
        office.backup_day_of_week = d
    if "backup_hour" in data:
        h = int(data["backup_hour"])
        if h < 0 or h > 23:
            return jsonify({"error": "backup_hour must be 0-23."}), 400
        office.backup_hour = h
    if "backup_retention_days" in data:
        r = int(data["backup_retention_days"])
        if r < 1:
            return jsonify({"error": "backup_retention_days must be >= 1."}), 400
        office.backup_retention_days = r
    db.session.commit()

    from .backup_scheduler import reschedule_backup
    reschedule_backup()

    return jsonify(office.to_dict())


@api_bp.route("/timezones", methods=["GET"])
def list_timezones():
    import zoneinfo
    return jsonify(sorted(zoneinfo.available_timezones()))
