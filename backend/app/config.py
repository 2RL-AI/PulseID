import os
import secrets


def _secure_default(env_var, fallback_prefix="pulseid"):
    """Return env var value, or generate a persistent random key for development."""
    val = os.environ.get(env_var, "")
    if val and val not in ("change-me-in-production", ""):
        return val
    return secrets.token_hex(32)


class Config:
    SECRET_KEY = _secure_default("PULSEID_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://pulseid:pulseid_secret@localhost:5432/pulseid",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    API_KEY = _secure_default("PULSEID_API_KEY")
    ADMIN_USERNAME = os.environ.get("PULSEID_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("PULSEID_PASSWORD", "admin")

    READER_FILTER = os.environ.get("PULSEID_READER_FILTER", "")

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    COMPANY_NAME = os.environ.get("COMPANY_NAME", "")
    COMPANY_STREET = os.environ.get("COMPANY_STREET", "")
    COMPANY_CITY = os.environ.get("COMPANY_CITY", "")
    COMPANY_ZIP = os.environ.get("COMPANY_ZIP", "")
    COMPANY_COUNTRY = os.environ.get("COMPANY_COUNTRY", "")
    COMPANY_PHONE = os.environ.get("COMPANY_PHONE", "")
    COMPANY_EMAIL = os.environ.get("COMPANY_EMAIL", "")
    LOGO_PATH = os.environ.get("LOGO_PATH", "")
