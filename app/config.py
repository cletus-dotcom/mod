import os
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://motorela:motorela_local@127.0.0.1:5433/motorela",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=10)
    UPLOAD_FOLDER = str(ROOT / "static" / "uploads")
    RECORD_YEAR = int(os.environ.get("RECORD_YEAR", "2026"))
    EXCEL_CANDIDATES = [
        os.environ.get("EXCEL_PATH", ""),
        r"c:\Users\jagna\MICT\docs\motorela\MOTORELA OPERATOR AND DRIVER (1).xlsx",
        str(ROOT / "data" / "motorela-source.xlsx"),
    ]
    ID_TEMPLATE_CANDIDATES = [
        os.environ.get("ID_TEMPLATE_PATH", ""),
        r"C:\Users\jagna\MICT\docs\motorela\motorela_id.pdf",
        str(ROOT / "data" / "motorela_id.pdf"),
    ]
