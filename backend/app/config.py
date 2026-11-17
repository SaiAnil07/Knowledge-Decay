import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Knowledge Decay Detection System"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = "sqlite+aiosqlite:///./knowledge_decay.db"
    SYNC_DATABASE_URL: str = "sqlite:///./knowledge_decay.db"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    MAX_SCAN_FILES: int = 5000
    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB safety limit per file

    model_config = ConfigDict(env_file=".env")

settings = Settings()
