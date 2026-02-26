#!/usr/bin/env python3
"""
NFC badge: register cards, log auth events, generate reports.
Uses PC/SC (e.g. ACS ACR122U). Hold tag on reader when prompted.
"""

import argparse
import csv
import io
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import yaml
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from smartcard.System import readers
from smartcard.util import toHexString

try:
    from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, session
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

# Paths: set from conf file (default conf.toml next to script, or --config)
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONF = SCRIPT_DIR / "conf.toml"

_CONFIG_DEFAULTS = {
    "registry_file": "registry.yaml",
    "company_file": "company.yaml",
    "auth_log_file": "auth_log.csv",
    "logo_path": "company-logo.webp",
}


def _load_config_raw(config_path: Path) -> dict:
    """Load [configuration] from config_path. Returns dict; missing keys use defaults."""
    if not config_path.exists():
        return dict(_CONFIG_DEFAULTS)
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        cfg = data.get("configuration") if isinstance(data.get("configuration"), dict) else {}
        return {k: cfg.get(k) or v for k, v in _CONFIG_DEFAULTS.items()}
    except Exception:
        return dict(_CONFIG_DEFAULTS)


def _resolve_path(value: str, base_dir: Path) -> Path:
    """Resolve path: if absolute use as-is; else relative to base_dir."""
    p = Path(value)
    return p if p.is_absolute() else (base_dir / p)


def apply_config(config_path: Path) -> None:
    """Load config from config_path and set global path variables. Relative paths are resolved against config file dir."""
    global REGISTRY_FILE, COMPANY_FILE, AUTH_LOG_CSV, LOGO_PATH
    base = config_path.resolve().parent
    raw = _load_config_raw(config_path)
    REGISTRY_FILE = _resolve_path(raw["registry_file"], base)
    COMPANY_FILE = _resolve_path(raw["company_file"], base)
    AUTH_LOG_CSV = _resolve_path(raw["auth_log_file"], base)
    LOGO_PATH = _resolve_path(raw["logo_path"], base)


# Initial defaults (from default conf or built-in)
apply_config(DEFAULT_CONF)


def get_reader(reader_name_filter=None):
    """Return first matching PC/SC reader or None."""
    r = readers()
    if not r:
        return None
    if reader_name_filter:
        match = next((x for x in r if reader_name_filter in str(x)), None)
        return match if match is not None else r[0]
    return r[0]


def read_uid(reader_name_filter=None):
    """
    Read UID from NFC reader. Returns UID as hex string or None on failure.
    """
    reader = get_reader(reader_name_filter)
    if not reader:
        print("No PC/SC readers found.", file=sys.stderr)
        return None

    connection = reader.createConnection()
    try:
        connection.connect()
    except Exception as e:
        print("Hold the NFC tag on the reader.", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        return None

    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    try:
        data, sw1, sw2 = connection.transmit(GET_UID)
    finally:
        try:
            connection.disconnect()
        except Exception:
            pass

    if (sw1, sw2) == (0x90, 0x00):
        # toHexString returns e.g. "3F 4A 12 90"; normalize to lowercase no spaces for storage
        raw = toHexString(data)
        return raw.replace(" ", "").lower()
    return None


def load_registry():
    """Load registry from YAML (employees only). Returns dict with 'employees' key."""
    if not REGISTRY_FILE.exists():
        return {}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return {}
    # Keep only employees (ignore legacy 'company' key; company is in company.yaml)
    return {"employees": data.get("employees") if isinstance(data.get("employees"), list) else []}


def get_employee_name_by_uid(registry, uid):
    """Resolve UID to employee name from registry (employees list or legacy flat dict)."""
    uid = (uid or "").strip().lower()
    employees = registry.get("employees") if isinstance(registry.get("employees"), list) else []
    for emp in employees:
        if isinstance(emp, dict) and (emp.get("uid") or "").strip().lower() == uid:
            return (emp.get("name") or "").strip() or None
    return registry.get(uid) if isinstance(registry.get(uid), str) else None


def load_company_info():
    """Return company dict (name, address, phone, email, ...) from company.yaml."""
    if not COMPANY_FILE.exists():
        return {}
    with open(COMPANY_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("company") if isinstance(data.get("company"), dict) else {}


def save_registry(registry):
    """Save registry to YAML (employees only)."""
    payload = {"employees": registry.get("employees") if isinstance(registry.get("employees"), list) else []}
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def cmd_register(name: str, reader_name_filter=None):
    """Register mode: read UID and save name in registry.yaml (employees list)."""
    print(f"Registering as: {name}")
    print("Hold the NFC tag on the reader...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read UID.", file=sys.stderr)
        sys.exit(1)
    registry = load_registry()
    if not isinstance(registry.get("employees"), list):
        registry["employees"] = []
    employees = registry["employees"]
    uid_lower = uid.lower()
    for i, emp in enumerate(employees):
        if isinstance(emp, dict) and (emp.get("uid") or "").strip().lower() == uid_lower:
            employees[i] = {"name": name.strip(), "uid": uid}
            save_registry(registry)
            print(f"Registered UID {uid} as '{name}'.")
            return
    employees.append({"name": name.strip(), "uid": uid})
    save_registry(registry)
    print(f"Registered UID {uid} as '{name}'.")


def cmd_auth(reader_name_filter=None):
    """Auth mode: read UID, resolve name, append one row to auth_log.csv."""
    print("Hold the NFC tag on the reader...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read UID.", file=sys.stderr)
        sys.exit(1)
    registry = load_registry()
    name = get_employee_name_by_uid(registry, uid) or "Unknown"
    timestamp = datetime.now().isoformat()
    file_exists = AUTH_LOG_CSV.exists()
    with open(AUTH_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["name", "uid", "timestamp"])
        w.writerow([name, uid, timestamp])
    print(f"Badge recorded: {name} at {timestamp}")


def load_auth_records():
    """Load all rows from auth_log.csv. Returns list of dicts."""
    if not AUTH_LOG_CSV.exists():
        return []
    with open(AUTH_LOG_CSV, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)


def _parse_date_only(ts: str):
    """Parse timestamp string and return date as YYYY-MM-DD, or None."""
    if not ts:
        return None
    try:
        # Accept both ISO with time and date-only
        if "T" in ts:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        return datetime.strptime(ts.strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _employee_uuid(uid: str, name: str) -> str:
    """UID XOR reverse(UID) as hex (for Employee UUID column). Name is unused, kept for API compatibility."""
    uid = (uid or "").strip().lower()
    try:
        b = bytes.fromhex(uid)
    except ValueError:
        return uid
    rev = b[::-1]
    xored = bytes(a ^ b for a, b in zip(b, rev))
    return xored.hex()


def _records_by_month(records, default_office: str = "Frisange, LU"):
    """
    Normalize records: date only, deduplicate by (name, date), add Employee UUID, Access Type, Office.
    Group by (year, month). Date format DD/MM/YYYY.
    Returns: list of (month_key, month_label, rows). Each row has Name, Employee UUID, Access Type, Office, Date.
    """
    seen = set()
    normalized = []
    for r in records:
        ts = r.get("timestamp") or r.get("date") or ""
        d = _parse_date_only(ts)
        if d is None:
            continue
        name = (r.get("name") or "").strip()
        uid = (r.get("uid") or "").strip()
        key = (name, d)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({
            "Name": name,
            "Employee UUID": _employee_uuid(uid, name),
            "Access Type": "Card",
            "Office": default_office,
            "Date": d.strftime("%d/%m/%Y"),
        })

    by_month = defaultdict(list)
    for row in normalized:
        try:
            date_str = row["Date"]
            d = datetime.strptime(date_str, "%d/%m/%Y")
            by_month[(d.year, d.month)].append(row)
        except (ValueError, IndexError):
            continue

    result = []
    for (y, m) in sorted(by_month.keys()):
        label = datetime(y, m, 1).strftime("%B %Y")
        result.append(((y, m), label, by_month[(y, m)]))
    return result


# Header/footer use same horizontal margins as document body
DOC_LEFT_MARGIN = 2 * cm
DOC_RIGHT_MARGIN = 2 * cm


def _header_footer(canvas, doc):
    """Draw header (logo + line) and footer on each page. Header width matches document margins."""
    canvas.saveState()
    page_w = A4[0]
    page_h = A4[1]
    header_y = page_h - 2.2 * cm
    logo_h = 0.9 * cm
    # Logo (left side of header, aligned with content); flatten to RGB so ReportLab doesn't render alpha as black
    if LOGO_PATH.exists() and HAS_PIL:
        try:
            pil_img = Image.open(LOGO_PATH)
            if pil_img.mode != "RGB":
                pil_img = pil_img.convert("RGBA")
                rgb = Image.new("RGB", pil_img.size, (255, 255, 255))
                bands = pil_img.split()
                if len(bands) >= 4:
                    rgb.paste(pil_img, mask=bands[3])
                else:
                    rgb.paste(pil_img)
                pil_img = rgb
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            img = ImageReader(buf)
            img_w, img_ht = img.getSize()
            logo_w = logo_h * (img_w / img_ht) if img_ht else logo_h
            canvas.drawImage(img, DOC_LEFT_MARGIN, header_y - logo_h * 0.2, width=logo_w, height=logo_h, preserveAspectRatio=True)
        except Exception:
            try:
                img = ImageReader(str(LOGO_PATH))
                img_w, img_ht = img.getSize()
                logo_w = logo_h * (img_w / img_ht) if img_ht else logo_h
                canvas.drawImage(img, DOC_LEFT_MARGIN, header_y - logo_h * 0.2, width=logo_w, height=logo_h, preserveAspectRatio=True)
            except Exception:
                pass
    elif LOGO_PATH.exists():
        try:
            img = ImageReader(str(LOGO_PATH))
            img_w, img_ht = img.getSize()
            logo_w = logo_h * (img_w / img_ht) if img_ht else logo_h
            canvas.drawImage(img, DOC_LEFT_MARGIN, header_y - logo_h * 0.2, width=logo_w, height=logo_h, preserveAspectRatio=True)
        except Exception:
            pass
    canvas.setLineWidth(0.5)
    canvas.line(DOC_LEFT_MARGIN, page_h - 2.5 * cm, page_w - DOC_RIGHT_MARGIN, page_h - 2.5 * cm)
    # Footer: confidential text, then contact line (if any), then page number
    footer_text = getattr(doc, "_footer_confidential", None)
    contact_line = getattr(doc, "_footer_contact", None)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#7f8c8d"))
    y_footer = 1.0 * cm
    def draw_wrapped(text, max_chars=170):
        nonlocal y_footer
        words = text.split()
        lines = []
        current = []
        for w in words:
            current.append(w)
            if sum(len(x) + 1 for x in current) - 1 > max_chars:
                current.pop()
                lines.append(" ".join(current))
                current = [w]
        if current:
            lines.append(" ".join(current))
        for line in reversed(lines):
            canvas.drawCentredString(page_w / 2, y_footer, line)
            y_footer += 0.32 * cm
    if footer_text:
        draw_wrapped(footer_text)
    if contact_line:
        y_footer += 0.15 * cm
        draw_wrapped(contact_line)
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(page_w / 2, 0.5 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _table_style():
    """Shared table style (Helvetica, header, grid)."""
    return TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#2c3e50")),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.white, colors.HexColor("#ecf0f1")],
            ),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
    )


FOOTER_CONFIDENTIAL = (
    "This report was generated by the PulseID Access Badge System provided only upon request "
    "from the employee or an authorized authority and is strictly confidential."
)


def _build_report_pdf(uid: str, registry: dict, output_dest, filter_year=None, filter_month=None):
    """
    Build the badge report PDF into output_dest (file path or file-like).
    output_dest: path string or BytesIO. Returns employee_name.
    If filter_year and filter_month are set, only include records for that month.
    """
    employee_name = get_employee_name_by_uid(registry, uid)
    if not employee_name:
        raise ValueError("Badge UID not registered.")
    all_records = load_auth_records()
    records = [r for r in all_records if (r.get("uid") or "").strip() == uid]
    if not records:
        raise ValueError(f"No access records found for {employee_name}.")
    if filter_year is not None and filter_month is not None:
        filtered = []
        for r in records:
            d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
            if d and d.year == filter_year and d.month == filter_month:
                filtered.append(r)
        records = filtered
        if not records:
            raise ValueError(f"No records found for {filter_month:02d}/{filter_year}.")
    by_month = _records_by_month(records)
    if not by_month:
        raise ValueError("No valid dated records to report.")

    doc = SimpleDocTemplate(
        output_dest,
        pagesize=A4,
        rightMargin=DOC_RIGHT_MARGIN,
        leftMargin=DOC_LEFT_MARGIN,
        topMargin=3.0 * cm,
        bottomMargin=2.2 * cm,
    )
    company = load_company_info()
    contact_parts = []
    if company.get("phone"):
        contact_parts.append(str(company.get("phone")).strip())
    if company.get("email"):
        contact_parts.append(str(company.get("email")).strip())
    contact_line = " | ".join(contact_parts) if contact_parts else ""
    doc._footer_confidential = FOOTER_CONFIDENTIAL
    doc._footer_contact = f"For questions or to contact the security officer: {contact_line}" if contact_line else None

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        name="ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    intro_style = ParagraphStyle(
        name="ReportIntro",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        spaceAfter=8,
        leftIndent=0,
        rightIndent=0,
        alignment=TA_JUSTIFY,
    )
    month_style = ParagraphStyle(
        name="MonthHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        spaceBefore=14,
        spaceAfter=6,
    )
    company_title_style = ParagraphStyle(
        name="CompanyTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        spaceAfter=4,
        alignment=TA_RIGHT,
    )
    company_line_style = ParagraphStyle(
        name="CompanyLine",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        spaceAfter=2,
        alignment=TA_RIGHT,
    )

    company = load_company_info()
    generated_at = datetime.now().strftime("%d/%m/%Y at %H:%M")
    story = []
    # Company name and report title on the right
    if company:
        cname = (company.get("name") or "").strip()
        if cname:
            story.append(Paragraph(cname, company_title_style))
        addr = company.get("address")
        if isinstance(addr, dict):
            street = str(addr.get("street") or "").strip()
            city = str(addr.get("city") or "").strip()
            zipcode = str(addr.get("zip") or "").strip()
            country = str(addr.get("country") or "").strip()
            if street:
                story.append(Paragraph(street, company_line_style))
            if zipcode or city:
                story.append(Paragraph(f"{zipcode} {city}".strip(), company_line_style))
            if country:
                story.append(Paragraph(country, company_line_style))
        story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("PulseID Access Badge Report", title_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "This document is an access badge report issued by the PulseID Access Badge System. "
            "It lists badge access events for the person in the card named below, for the period covered by the tables. "
            "This report was generated on " + generated_at + ". "
            "It is provided for the sole use of the person in the card or an authorized authority and is strictly confidential.",
            intro_style,
        )
    )
    story.append(Paragraph(f"<b>Employee:</b> {employee_name}", body_style))
    story.append(Paragraph(f"<b>Report generated:</b> {generated_at}", body_style))
    story.append(Spacer(1, 0.6 * cm))

    content_width = A4[0] - DOC_LEFT_MARGIN - DOC_RIGHT_MARGIN
    ncols = 5
    col_width = content_width / ncols
    headers = ["Name", "Employee UUID", "Access Type", "Office", "Date"]
    for i, (_ym, month_label, rows) in enumerate(by_month, 1):
        story.append(Paragraph(f"{month_label}", month_style))
        data = [headers] + [[r.get(h, "") for h in headers] for r in rows]
        t = Table(data, colWidths=[col_width] * ncols, repeatRows=1)
        t.setStyle(_table_style())
        story.append(t)
        story.append(Spacer(1, 0.4 * cm))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return employee_name


def generate_report_to_buffer(reader_name_filter=None, filter_year=None, filter_month=None):
    """
    Read badge from reader, build report PDF into BytesIO. Returns (buffer, employee_name) or (None, error_msg).
    If filter_year and filter_month are set, only that month is included.
    """
    uid = read_uid(reader_name_filter)
    if not uid:
        return None, "Could not read badge. Hold the badge on the reader."
    registry = load_registry()
    try:
        buf = io.BytesIO()
        employee_name = _build_report_pdf(uid, registry, buf, filter_year=filter_year, filter_month=filter_month)
        buf.seek(0)
        return buf, employee_name
    except ValueError as e:
        return None, str(e)


def cmd_report(pdf_path: str, reader_name_filter=None, filter_year=None, filter_month=None):
    """Generate PDF report for the person whose badge is read on the reader (filter by UID). Optional --month/--year for single month."""
    print("Hold the employee badge on the reader to generate their report...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read badge.", file=sys.stderr)
        sys.exit(1)
    registry = load_registry()
    try:
        employee_name = _build_report_pdf(uid, registry, pdf_path, filter_year=filter_year, filter_month=filter_month)
        print(f"Report for {employee_name} saved to {pdf_path}")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


def cmd_remove(reader_name_filter=None):
    """Remove the badge holder from registry and delete all their records from auth_log.csv."""
    print("Hold the badge on the reader to remove that person from the registry...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read badge.", file=sys.stderr)
        sys.exit(1)
    registry = load_registry()
    name = get_employee_name_by_uid(registry, uid)
    if not name:
        print("Badge UID not in registry.", file=sys.stderr)
        sys.exit(1)
    employees = registry.get("employees")
    if isinstance(employees, list):
        registry["employees"] = [e for e in employees if isinstance(e, dict) and (e.get("uid") or "").strip().lower() != uid.lower()]
        save_registry(registry)
    if AUTH_LOG_CSV.exists():
        with open(AUTH_LOG_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or ["name", "uid", "timestamp"]
            rows = list(reader)
        kept = [r for r in rows if (r.get("uid") or "").strip().lower() != uid.lower()]
        with open(AUTH_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(kept)
    print(f"Removed '{name}' from registry and deleted all their records.")


def _remove_records_for_uid_by_predicate(uid: str, keep_predicate):
    """
    Remove from auth_log.csv all rows for the given UID where keep_predicate(record) is False.
    keep_predicate receives a record dict; return True to keep, False to remove.
    Returns (num_removed, total_rows_for_uid).
    """
    uid_lower = (uid or "").strip().lower()
    if not AUTH_LOG_CSV.exists():
        return 0, 0
    with open(AUTH_LOG_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or ["name", "uid", "timestamp"]
        rows = list(reader)
    uid_rows = [r for r in rows if (r.get("uid") or "").strip().lower() == uid_lower]
    to_remove = [r for r in uid_rows if not keep_predicate(r)]
    kept = [r for r in rows if r not in to_remove]
    with open(AUTH_LOG_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(kept)
    return len(to_remove), len(uid_rows)


def cmd_remove_period(reader_name_filter=None, year: int = None, month: int = None):
    """Remove from CSV all records for the badge on the reader that fall in the given month/year."""
    if year is None or month is None:
        print("Specify --year and --month.", file=sys.stderr)
        sys.exit(1)
    print("Hold the badge on the reader...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read badge.", file=sys.stderr)
        sys.exit(1)
    def keep(r):
        d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
        if not d:
            return True
        return (d.year, d.month) != (year, month)
    removed, _ = _remove_records_for_uid_by_predicate(uid, keep)
    print(f"Removed {removed} record(s) for {year}-{month:02d}.")


def cmd_remove_before_current_month(reader_name_filter=None):
    """Remove from CSV all records for the badge on the reader with date before the current month (current month excluded)."""
    now = datetime.now()
    print("Hold the badge on the reader...")
    uid = read_uid(reader_name_filter)
    if not uid:
        print("Could not read badge.", file=sys.stderr)
        sys.exit(1)
    def keep(r):
        d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
        if not d:
            return True
        return (d.year, d.month) >= (now.year, now.month)
    removed, _ = _remove_records_for_uid_by_predicate(uid, keep)
    print(f"Removed {removed} record(s) before {now.year}-{now.month:02d}.")


# --- Web UI (Flask) ---
def _reader_filter():
    """Reader name filter from Flask app config (set when running with --server)."""
    if not HAS_FLASK:
        return None
    return (flask_app.config.get("READER_FILTER") or "").strip() or None


def _web_register(name: str):
    """Register badge (read UID, save to registry). Returns (success, message)."""
    uid = read_uid(_reader_filter())
    if not uid:
        return False, "Could not read badge. Hold the NFC tag on the reader."
    registry = load_registry()
    if not isinstance(registry.get("employees"), list):
        registry["employees"] = []
    employees = registry["employees"]
    uid_lower = uid.lower()
    for i, emp in enumerate(employees):
        if isinstance(emp, dict) and (emp.get("uid") or "").strip().lower() == uid_lower:
            employees[i] = {"name": name.strip(), "uid": uid}
            save_registry(registry)
            return True, f"Registered UID {uid} as '{name}'."
    employees.append({"name": name.strip(), "uid": uid})
    save_registry(registry)
    return True, f"Registered UID {uid} as '{name}'."


def _web_record():
    """Record badge (read UID, append to CSV). Returns (success, message)."""
    uid = read_uid(_reader_filter())
    if not uid:
        return False, "Could not read badge. Hold the NFC tag on the reader."
    registry = load_registry()
    name = get_employee_name_by_uid(registry, uid) or "Unknown"
    timestamp = datetime.now().isoformat()
    file_exists = AUTH_LOG_CSV.exists()
    with open(AUTH_LOG_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(["name", "uid", "timestamp"])
        w.writerow([name, uid, timestamp])
    return True, f"Badge recorded: {name} at {timestamp}"


def _web_remove():
    """Remove badge holder from registry and delete all their CSV records. Returns (success, message)."""
    uid = read_uid(_reader_filter())
    if not uid:
        return False, "Could not read badge. Hold the NFC tag on the reader."
    registry = load_registry()
    name = get_employee_name_by_uid(registry, uid)
    if not name:
        return False, "Badge UID not in registry."
    employees = registry.get("employees")
    if isinstance(employees, list):
        registry["employees"] = [e for e in employees if isinstance(e, dict) and (e.get("uid") or "").strip().lower() != uid.lower()]
        save_registry(registry)
    if AUTH_LOG_CSV.exists():
        with open(AUTH_LOG_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or ["name", "uid", "timestamp"]
            rows = list(reader)
        kept = [r for r in rows if (r.get("uid") or "").strip().lower() != uid.lower()]
        with open(AUTH_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(kept)
    return True, f"Removed '{name}' from registry and deleted all their records."


def _web_remove_records_for_period(year: int, month: int):
    """Remove CSV records for the badge on the reader in the given month/year. Returns (success, message)."""
    uid = read_uid(_reader_filter())
    if not uid:
        return False, "Could not read badge. Hold the NFC tag on the reader."
    def keep(r):
        d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
        if not d:
            return True
        return (d.year, d.month) != (year, month)
    removed, _ = _remove_records_for_uid_by_predicate(uid, keep)
    return True, f"Removed {removed} record(s) for {month:02d}/{year}."


def _web_remove_records_before_current_month():
    """Remove CSV records for the badge on the reader with date before current month (current month excluded). Returns (success, message)."""
    uid = read_uid(_reader_filter())
    if not uid:
        return False, "Could not read badge. Hold the NFC tag on the reader."
    now = datetime.now()
    def keep(r):
        d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
        if not d:
            return True
        return (d.year, d.month) >= (now.year, now.month)
    removed, _ = _remove_records_for_uid_by_predicate(uid, keep)
    return True, f"Removed {removed} record(s) before {now.year}-{now.month:02d}."


if HAS_FLASK:
    flask_app = Flask(__name__, template_folder=str(SCRIPT_DIR / "templates"))
    flask_app.secret_key = os.environ.get("PULSEID_SECRET_KEY") or os.urandom(24).hex()

    def _require_auth():
        """Check env credentials; return (True, None) if valid else (False, response)."""
        username = os.environ.get("PULSEID_USERNAME", "").strip()
        password = os.environ.get("PULSEID_PASSWORD", "").strip()
        if not username or not password:
            return False, None  # no auth configured
        return True, None

    @flask_app.before_request
    def _auth_before_request():
        auth_required, _ = _require_auth()
        if not auth_required:
            return None
        if request.endpoint == "login":
            return None
        if session.get("logged_in"):
            return None
        return redirect(url_for("login"))

    @flask_app.route("/login", methods=["GET", "POST"])
    def login():
        auth_required, _ = _require_auth()
        if not auth_required:
            return redirect(url_for("index"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = (request.form.get("password") or "")
            expected_user = os.environ.get("PULSEID_USERNAME", "").strip()
            expected_pass = os.environ.get("PULSEID_PASSWORD", "")
            if username == expected_user and password == expected_pass:
                session["logged_in"] = True
                return redirect(url_for("index"))
            return render_template("login.html", error="Invalid username or password.")
        return render_template("login.html", error=None)

    @flask_app.route("/logout", methods=["POST"])
    def logout():
        session.pop("logged_in", None)
        return redirect(url_for("login"))

    @flask_app.route("/")
    def index():
        return render_template("index.html")

    @flask_app.route("/api/register", methods=["POST"])
    def api_register():
        try:
            data = request.get_json(force=True, silent=True) or {}
            name = (data.get("name") or "").strip()
            if not name:
                return jsonify({"success": False, "message": "Name is required."}), 400
            ok, msg = _web_register(name)
            return jsonify({"success": ok, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/record", methods=["POST"])
    def api_record():
        try:
            ok, msg = _web_record()
            return jsonify({"success": ok, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/download-report", methods=["POST"])
    def api_download_report():
        try:
            data = request.get_json(force=True, silent=True) or {}
            year = data.get("year")
            month = data.get("month")
            if year is not None:
                year = int(year)
            if month is not None:
                month = int(month)
            buf, employee_name = generate_report_to_buffer(
                _reader_filter(), filter_year=year, filter_month=month
            )
            if buf is None:
                return jsonify({"success": False, "message": employee_name}), 400
            suffix = f"_{year}_{month:02d}" if (year is not None and month is not None) else ""
            filename = f"badge_report_{employee_name.replace(' ', '_')}{suffix}.pdf"
            return send_file(
                buf,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=filename,
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/remove", methods=["POST"])
    def api_remove():
        try:
            ok, msg = _web_remove()
            return jsonify({"success": ok, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/remove-records-period", methods=["POST"])
    def api_remove_records_period():
        try:
            data = request.get_json(force=True, silent=True) or {}
            year = data.get("year")
            month = data.get("month")
            if year is None or month is None:
                return jsonify({"success": False, "message": "year and month are required."}), 400
            year, month = int(year), int(month)
            ok, msg = _web_remove_records_for_period(year, month)
            return jsonify({"success": ok, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/remove-records-before-current-month", methods=["POST"])
    def api_remove_records_before_current_month():
        try:
            ok, msg = _web_remove_records_before_current_month()
            return jsonify({"success": ok, "message": msg})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @flask_app.route("/api/available-months", methods=["GET"])
    def api_available_months():
        """Return list of {year, month, label} for which auth records exist (for report filter dropdown)."""
        try:
            records = load_auth_records()
            months = set()
            for r in records:
                d = _parse_date_only(r.get("timestamp") or r.get("date") or "")
                if d:
                    months.add((d.year, d.month))
            out = [{"year": y, "month": m, "label": datetime(y, m, 1).strftime("%B %Y")} for (y, m) in sorted(months)]
            return jsonify({"months": out})
        except Exception as e:
            return jsonify({"months": []}), 500
else:
    flask_app = None


def main():
    parser = argparse.ArgumentParser(
        description="NFC badge: register cards, log auth, generate PDF reports.",
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Run as HTTP server (web UI) instead of CLI.",
    )
    parser.add_argument(
        "--reader", "-r",
        default="",
        metavar="NAME",
        help="PC/SC reader name substring (e.g. 'ACR122U'). Default: first reader.",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        metavar="PATH",
        help="Path to conf.toml (default: conf.toml in script directory).",
    )
    sub = parser.add_subparsers(dest="mode", help="Mode")

    reg = sub.add_parser("register", help="Register a card: read UID and save with --name")
    reg.add_argument("--name", "-n", required=True, help="Name to associate with the card")
    reg.set_defaults(func=lambda a: cmd_register(a.name, a.reader or None))

    auth = sub.add_parser("auth", help="Auth mode: log who badged (name, uid, timestamp) to CSV")
    auth.set_defaults(func=lambda a: cmd_auth(a.reader or None))

    report = sub.add_parser("report", help="Generate PDF report (full or for one month)")
    report.add_argument(
        "--output", "-o",
        default=str(SCRIPT_DIR / "badge_report.pdf"),
        metavar="PDF",
        help="Output PDF path (default: badge_report.pdf in script dir)",
    )
    report.add_argument("--month", "-m", type=int, default=None, metavar="M", help="Filter to month (1-12); use with --year")
    report.add_argument("--year", "-y", type=int, default=None, metavar="Y", help="Filter to year (e.g. 2026); use with --month")
    report.set_defaults(func=lambda a: cmd_report(a.output, a.reader or None, getattr(a, "year"), getattr(a, "month")))

    remove_parser = sub.add_parser("remove", help="Remove badge holder from registry and delete all their CSV records")
    remove_parser.set_defaults(func=lambda a: cmd_remove(a.reader or None))

    remove_period_parser = sub.add_parser("remove-period", help="Remove CSV records for the badge on the reader for a given month/year")
    remove_period_parser.add_argument("--year", "-y", type=int, required=True, help="Year (e.g. 2026)")
    remove_period_parser.add_argument("--month", "-m", type=int, required=True, help="Month (1-12)")
    remove_period_parser.set_defaults(func=lambda a: cmd_remove_period(a.reader or None, a.year, a.month))

    remove_before_parser = sub.add_parser("remove-before-current-month", help="Remove CSV records for the badge on the reader before current month (current month excluded)")
    remove_before_parser.set_defaults(func=lambda a: cmd_remove_before_current_month(a.reader or None))

    args = parser.parse_args()
    if getattr(args, "config", None):
        apply_config(Path(args.config))
    if getattr(args, "server", False):
        if not HAS_FLASK:
            print("Install Flask to run the web server: pip install flask", file=sys.stderr)
            sys.exit(1)
        if not os.environ.get("PULSEID_USERNAME") or not os.environ.get("PULSEID_PASSWORD"):
            print("Set PULSEID_USERNAME and PULSEID_PASSWORD environment variables before starting the server.", file=sys.stderr)
            sys.exit(1)
        flask_app.config["READER_FILTER"] = (args.reader or "").strip() or None
        print("Web UI at http://127.0.0.1:5005/")
        flask_app.run(host="0.0.0.0", port=5005, debug=False)
        return
    if not args.mode:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
