import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Question Bank & RAG Tutor"
    VERSION: str = "1.0.0"

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:1234@localhost:5432/ai_project"

    # Embedding Model
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # Google AI Studio / Gemini
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-3.6-flash"
    GOOGLE_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # AI Tutor Configuration
    AI_TUTOR_TOP_K: int = 5
    AI_TUTOR_MAX_HISTORY: int = 10
    AI_TUTOR_MAX_TOKENS: int = 4000
    AI_TUTOR_TEMPERATURE: float = 0.4
    RAG_MIN_SIMILARITY: float = 0.65

    # CORS Configuration
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
