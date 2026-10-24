"""
TrendPulse Enterprise Backend Configuration.

Handles environment variables, security secrets, CORS origins,
database connection strings, and upload limits.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env if present
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent.parent.parent / ".env")


class Settings(BaseModel):
    # App Info
    PROJECT_NAME: str = "TrendPulse Fashion Intelligence API"
    VERSION: str = "4.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "trendpulse-super-secret-production-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth 2.0 Configuration
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8000/api/v1/auth/google/callback"
    )
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Database
    # Defaults to local SQLite database in project root, easily configured for PostgreSQL/MySQL in prod
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent.parent / 'trendpulse.db'}"
    )

    # File Storage
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB max file size
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*",
    ]


settings = Settings()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
