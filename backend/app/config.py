"""
Configuration module — loads settings from environment variables / .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve the .env path relative to the backend directory
_env_file = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Application settings, loaded from .env or environment variables."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reviewer_db"

    # ── JWT Authentication ────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── Ollama LLM ────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 120  # seconds

    # ── Limits ────────────────────────────────────────────────────────────
    MAX_CODE_LENGTH: int = 50_000  # characters

    model_config = {
        "env_file": str(_env_file),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

# JWT Entropy Check for Production
if os.environ.get("ENV") == "production":
    if len(settings.JWT_SECRET) < 32 or settings.JWT_SECRET == "change-me-to-a-random-secret-in-production":
        raise ValueError("CRITICAL: JWT_SECRET must be at least 32 characters with high entropy in production!")
