import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # PostgreSQL via DATABASE_URL (e.g. postgresql://user:pass@localhost:5432/aicra)
    # falls back to local SQLite so project runs with zero external setup
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    REPORT_FOLDER = os.path.join(basedir, "reports")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    ALLOWED_EXTENSIONS = {"py", "js", "jsx", "ts", "tsx"}

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
