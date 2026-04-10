"""Automatic backup scheduler — runs as a background thread."""

import io
import json
import logging
import os
import threading
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_default_backup_dir = "/app/backups" if Path("/app").exists() else str(Path(__file__).resolve().parent.parent / "backups")
BACKUP_DIR = Path(os.environ.get("PULSEID_BACKUP_DIR", _default_backup_dir))

_app = None
_thread: threading.Thread | None = None
_running = False
_stop_event = threading.Event()


def init_scheduler(app):
    global _app
    _app = app
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    _start_thread()


def reschedule_backup():
    _stop_event.set()


def _start_thread():
    global _thread, _running
    if _thread and _thread.is_alive():
        return
    _running = True
    _thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _thread.start()
    logger.info("Backup scheduler started (dir=%s).", BACKUP_DIR)


def _scheduler_loop():
    while _running:
        try:
            _stop_event.clear()
            interval = _compute_next_interval()
            if interval is None:
                _stop_event.wait(timeout=60)
                continue
            logger.info("Next backup in %.0f seconds.", interval)
            interrupted = _stop_event.wait(timeout=interval)
            if interrupted:
                continue
            _run_backup()
            _cleanup_old_backups()
        except Exception as exc:
            logger.error("Backup scheduler error: %s", exc, exc_info=True)
            _stop_event.wait(timeout=60)


def _compute_next_interval() -> float | None:
    if not _app:
        return None
    with _app.app_context():
        from .models import OfficeSettings
        settings = OfficeSettings.get()
        if not settings.backup_enabled:
            return None

        now = datetime.now(timezone.utc)
        target_hour = settings.backup_hour

        if settings.backup_frequency == "daily":
            target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            if target <= now:
                target = target.replace(day=target.day + 1)
            return max((target - now).total_seconds(), 10)

        if settings.backup_frequency == "weekly":
            days_ahead = (settings.backup_day_of_week - now.weekday()) % 7
            if days_ahead == 0 and now.hour >= target_hour:
                days_ahead = 7
            target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            target += timedelta(days=days_ahead)
            return max((target - now).total_seconds(), 10)

    return None


def _run_backup():
    if not _app:
        return
    with _app.app_context():
        from .database import _dump_all
        from .version import APP_VERSION

        data = _dump_all()
        json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"pulseid_auto_{APP_VERSION}_{ts}.zip"
        filepath = BACKUP_DIR / filename

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("pulseid_dump.json", json_bytes)

        filepath.write_bytes(buf.getvalue())
        logger.info("Automatic backup created: %s (%d bytes)", filepath, len(json_bytes))


def _cleanup_old_backups():
    if not _app:
        return
    with _app.app_context():
        from .models import OfficeSettings
        settings = OfficeSettings.get()
        retention = settings.backup_retention_days

    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention)
    removed = 0
    for f in BACKUP_DIR.glob("pulseid_auto_*.zip"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                f.unlink()
                removed += 1
        except Exception:
            pass
    if removed:
        logger.info("Cleaned up %d old backup(s) (retention=%d days).", removed, retention)
