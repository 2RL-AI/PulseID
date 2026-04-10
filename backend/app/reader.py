"""NFC badge reader interface and background service."""

import logging
import sys
import threading
import time
from datetime import datetime, timezone

try:
    from smartcard.System import readers as list_readers
    from smartcard.util import toHexString

    HAS_PCSCD = True
except ImportError:
    HAS_PCSCD = False

logger = logging.getLogger(__name__)

GET_UID_CMD = [0xFF, 0xCA, 0x00, 0x00, 0x00]


def get_reader(reader_name_filter: str | None = None):
    if not HAS_PCSCD:
        return None
    try:
        available = list_readers()
    except Exception as exc:
        logger.warning("PC/SC list_readers() failed: %s", exc)
        return None
    if not available:
        return None
    if reader_name_filter:
        match = next((r for r in available if reader_name_filter in str(r)), None)
        return match if match is not None else available[0]
    return available[0]


def read_uid(reader_name_filter: str | None = None) -> str | None:
    """Read UID from NFC reader. Returns lowercase hex string or None."""
    reader = get_reader(reader_name_filter)
    if not reader:
        return None
    connection = reader.createConnection()
    try:
        connection.connect()
    except Exception:
        return None
    try:
        data, sw1, sw2 = connection.transmit(GET_UID_CMD)
    finally:
        try:
            connection.disconnect()
        except Exception:
            pass
    if (sw1, sw2) == (0x90, 0x00):
        return toHexString(data).replace(" ", "").lower()
    return None


def detect_readers() -> list[dict]:
    """Return info about all available PC/SC readers."""
    if not HAS_PCSCD:
        return []
    try:
        available = list_readers()
    except Exception:
        return []
    result = []
    for r in available:
        result.append({"name": str(r), "index": available.index(r)})
    return result


class ReaderService:
    """Background service that continuously polls the NFC reader.

    Normal mode: every badge scan creates a NEW_RECORD for the associated employee.
    Register mode: next badge scan assigns the badge to a specific employee.
    """

    SCAN_COOLDOWN = 8

    def __init__(self):
        self._app = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._reader_filter: str | None = None
        self._lock = threading.Lock()

        self._register_employee_id: int | None = None
        self._register_result: dict | None = None
        self._register_event = threading.Event()

        self._last_uid: str | None = None
        self._last_read_time: float = 0

        self.reader_connected = False
        self.reader_name: str | None = None
        self.last_event: dict | None = None

        self._last_no_reader_log: float = 0

    def init_app(self, app):
        self._app = app
        self._reader_filter = app.config.get("READER_FILTER") or None
        logger.info("ReaderService initialized (filter=%s, pcscd=%s)", self._reader_filter, HAS_PCSCD)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        if not HAS_PCSCD:
            logger.warning("pyscard not available — reader service will NOT start.")
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Reader service background thread started.")

    def stop(self):
        self._running = False

    def request_registration(self, employee_id: int, timeout: float = 30) -> dict | None:
        """Block until a badge is read and assigned to the employee, or timeout."""
        logger.info("Registration requested for employee_id=%d (timeout=%.0fs)", employee_id, timeout)
        with self._lock:
            self._register_employee_id = employee_id
            self._register_result = None
            self._register_event.clear()
            self._last_uid = None

        success = self._register_event.wait(timeout=timeout)

        with self._lock:
            result = self._register_result
            self._register_employee_id = None
            self._register_result = None

        if not success:
            logger.warning("Registration timed out for employee_id=%d", employee_id)
        return result if success else None

    def get_status(self) -> dict:
        return {
            "reader_connected": self.reader_connected,
            "reader_name": self.reader_name,
            "pcscd_available": HAS_PCSCD,
            "service_running": self._running and (self._thread is not None and self._thread.is_alive()),
            "last_event": self.last_event,
        }

    def _poll_loop(self):
        logger.info("Poll loop started. Looking for PC/SC readers...")
        while self._running:
            try:
                self._poll_once()
            except Exception as exc:
                logger.error("Unexpected error in poll loop: %s", exc, exc_info=True)
            time.sleep(1)
        logger.info("Poll loop stopped.")

    def _poll_once(self):
        reader = get_reader(self._reader_filter)
        was_connected = self.reader_connected
        self.reader_connected = reader is not None
        self.reader_name = str(reader) if reader else None

        if not reader:
            now = time.time()
            if now - self._last_no_reader_log > 30:
                logger.warning("No PC/SC reader found. Is pcscd running? Is the USB device mounted?")
                self._last_no_reader_log = now
            if was_connected:
                logger.warning("Reader disconnected.")
            time.sleep(1)
            return

        if not was_connected:
            logger.info("Reader connected: %s", self.reader_name)

        uid = read_uid(self._reader_filter)
        if not uid:
            return

        with self._lock:
            registering = self._register_employee_id is not None

        if registering:
            logger.info("Badge detected on reader: UID=%s (registration mode)", uid)
            self._do_register(uid)
        else:
            now = time.time()
            if uid == self._last_uid and (now - self._last_read_time) < self.SCAN_COOLDOWN:
                return
            self._last_uid = uid
            self._last_read_time = now
            logger.info("Badge detected on reader: UID=%s", uid)
            self._do_record(uid)

    def _do_record(self, uid: str):
        if not self._app:
            return
        with self._app.app_context():
            from . import db
            from .models import AccessLog, Employee

            employee = Employee.query.filter_by(badge_uid=uid).first()
            if not employee:
                logger.info("Badge UID=%s is not assigned to any employee — skipping record.", uid)
                return

            log = AccessLog(
                employee_id=employee.id,
                name=employee.full_name,
                uid=uid,
                event_type="NEW_RECORD",
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(log)
            db.session.commit()

            self.last_event = {
                "type": "NEW_RECORD",
                "employee": employee.full_name,
                "uid": uid,
                "timestamp": log.timestamp.isoformat(),
            }
            logger.info("NEW_RECORD created: %s (UID=%s, log_id=%d)", employee.full_name, uid, log.id)

    def _do_register(self, uid: str):
        if not self._app:
            return
        with self._app.app_context():
            from . import db
            from .models import AccessLog, Employee

            employee_id = self._register_employee_id
            employee = db.session.get(Employee, employee_id)
            if not employee:
                logger.warning("Registration failed: employee_id=%d not found.", employee_id)
                with self._lock:
                    self._register_result = {"success": False, "message": "Employee not found."}
                    self._register_event.set()
                return

            existing = Employee.query.filter(Employee.badge_uid == uid, Employee.id != employee_id).first()
            if existing:
                logger.warning("Registration failed: badge UID=%s already assigned to %s.", uid, existing.full_name)
                with self._lock:
                    self._register_result = {
                        "success": False,
                        "message": f"Badge already assigned to {existing.full_name}.",
                    }
                    self._register_event.set()
                return

            employee.badge_uid = uid
            log = AccessLog(
                employee_id=employee.id,
                name=employee.full_name,
                uid=uid,
                event_type="BADGE_CREATION",
                timestamp=datetime.now(timezone.utc),
            )
            db.session.add(log)
            db.session.commit()

            self.last_event = {
                "type": "BADGE_CREATION",
                "employee": employee.full_name,
                "uid": uid,
                "timestamp": log.timestamp.isoformat(),
            }

            with self._lock:
                self._register_result = {
                    "success": True,
                    "message": f"Badge {uid} assigned to {employee.full_name}.",
                    "uid": uid,
                }
                self._register_event.set()

            logger.info("BADGE_CREATION: %s assigned badge UID=%s (log_id=%d)", employee.full_name, uid, log.id)


reader_service = ReaderService()
