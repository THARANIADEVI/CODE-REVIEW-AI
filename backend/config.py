import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    # PostgreSQL via DATABASE_URL (e.g. postgresql://user:pass@localhost:5432/aicra)
    # falls back to local SQLite so project runs with zero external setup
    # `os.environ.get(key, default)` returns "" when the var is set but empty, so an empty
    # DATABASE_URL= line in .env would override the default and crash SQLAlchemy. Treat
    # empty/unset identically so the zero-setup SQLite fallback actually works.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or (
        f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pool_pre_ping tests each pooled connection with a lightweight query before use and
    # transparently reconnects if it's dead; without it, a connection Supabase has already
    # closed/reset on idle gets reused and fails with "SSL error: decryption failed or bad
    # record mac". pool_recycle proactively retires connections before Supabase's own idle
    # timeout, so the pool stays fresh instead of relying solely on pre-ping.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    REPORT_FOLDER = os.path.join(basedir, "reports")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    ALLOWED_EXTENSIONS = {"py", "js", "jsx", "ts", "tsx"}

    # LLM provider for AI code review + auto-refactor: Mistral AI's native API.
    # Falls back to a local heuristic reviewer if MISTRAL_API_KEY isn't set.
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
    MISTRAL_BASE_URL = os.environ.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
    MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

    # Comma-separated list of allowed origins for the deployed frontend
    # (e.g. "https://your-app.vercel.app"). Defaults to "*" for local dev.
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
