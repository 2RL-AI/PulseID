from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def _iso_utc(dt):
    """Format a naive UTC datetime as ISO 8601 with Z suffix."""
    if dt is None:
        return None
    return dt.isoformat() + "Z"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": _iso_utc(self.created_at),
        }


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(100), nullable=True)
    position = db.Column(db.String(255), nullable=True)
    department = db.Column(db.String(255), nullable=True)
    badge_uid = db.Column(db.String(255), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    access_logs = db.relationship("AccessLog", backref="employee", lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "position": self.position,
            "department": self.department,
            "badge_uid": self.badge_uid,
            "created_at": _iso_utc(self.created_at),
            "updated_at": _iso_utc(self.updated_at),
        }


class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    uid = db.Column(db.String(255), nullable=False)
    event_type = db.Column(db.String(50), nullable=False, default="NEW_RECORD")
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "uid": self.uid,
            "event_type": self.event_type,
            "timestamp": _iso_utc(self.timestamp),
        }


class OfficeSettings(db.Model):
    """Singleton table — always exactly one row (id=1)."""
    __tablename__ = "office_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    office_name = db.Column(db.String(255), nullable=False, default="")
    timezone = db.Column(db.String(100), nullable=False, default="UTC")
    backup_enabled = db.Column(db.Boolean, nullable=False, default=False)
    backup_frequency = db.Column(db.String(20), nullable=False, default="daily")
    backup_day_of_week = db.Column(db.Integer, nullable=True, default=0)
    backup_hour = db.Column(db.Integer, nullable=False, default=2)
    backup_retention_days = db.Column(db.Integer, nullable=False, default=30)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "office_name": self.office_name,
            "timezone": self.timezone,
            "backup_enabled": self.backup_enabled,
            "backup_frequency": self.backup_frequency,
            "backup_day_of_week": self.backup_day_of_week,
            "backup_hour": self.backup_hour,
            "backup_retention_days": self.backup_retention_days,
            "updated_at": _iso_utc(self.updated_at),
        }

    @classmethod
    def get(cls):
        row = cls.query.get(1)
        if not row:
            from . import db as _db
            row = cls(id=1, office_name="", timezone="UTC")
            _db.session.add(row)
            _db.session.commit()
        return row
