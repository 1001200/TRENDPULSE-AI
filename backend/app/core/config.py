from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "TrendPulse"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins (supports local Vite frontend development)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]
    
    # SQLite local database by default, upgradable to PostgreSQL via DATABASE_URL
    DATABASE_URL: str = "sqlite:///./trendpulse.db"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
