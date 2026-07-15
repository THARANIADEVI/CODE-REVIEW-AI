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

    # LLM provider for AI code review + auto-refactor: Mistral AI's native API.
    # Falls back to a local heuristic reviewer if MISTRAL_API_KEY isn't set.
    MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
    MISTRAL_BASE_URL = os.environ.get("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
    MISTRAL_MODEL = os.environ.get("MISTRAL_MODEL", "mistral-small-latest")

    # Comma-separated list of allowed origins for the deployed frontend
    # (e.g. "https://your-app.vercel.app"). Defaults to "*" for local dev.
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
