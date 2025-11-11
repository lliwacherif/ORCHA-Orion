# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/orcha_db"

    # Redis URL for simple job queue (optional now)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Settings for Authentication
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # LM Studio / Chatbot service
    LMSTUDIO_URL: str = "http://localhost:1234"
    LMSTUDIO_VISION_MODEL: str = "llava-v1.6-34b"
    GEMMA_MODEL: str = "google/gemma-3-12b"

    # OCR service endpoint (your PaddleOCR wrapper)
    OCR_SERVICE_URL: str = "http://localhost:8001"

    # RAG service endpoint
    RAG_SERVICE_URL: str = "http://localhost:8002"

    # Timeouts (seconds)
    LM_TIMEOUT: int = 500
    RAG_TIMEOUT: int = 15
    OCR_TIMEOUT: int = 60

    # Google Custom Search API
    GOOGLE_API_KEY: str = "your-google-api-key-here"
    GOOGLE_SEARCH_ENGINE_ID: str = "your-search-engine-id-here"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
