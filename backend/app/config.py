"""
Configuration module — loads settings from environment variables / .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve the .env path relative to the backend directory
_env_file = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings, loaded from .env or environment variables."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./reviewer.db"

    # ── JWT Authentication ────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── Limits ────────────────────────────────────────────────────────────
    MAX_CODE_LENGTH: int = 50_000  # characters

    model_config = {
        "env_file": str(_env_file),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()
