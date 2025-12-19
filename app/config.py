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
    
    # Admin Dashboard JWT Settings (separate from user auth)
    ADMIN_SECRET_KEY: str = "admin-secret-key-change-in-production"
    ADMIN_TOKEN_EXPIRE_HOURS: int = 24

    # Scaleway / OpenAI-compatible API
    SCALEWAY_API_URL: str = "https://api.scaleway.ai/d067acb3-2897-4c85-a126-957eb6768d0b/v1"
    SCALEWAY_API_KEY: str = "6b673550-8c7c-4fed-bac4-3e5a85b7860d"
    SCALEWAY_MODEL: str = "gpt-oss-120b"

    # Deprecated: LM Studio / Chatbot service
    # LMSTUDIO_URL: str = "http://localhost:1234"
    # LMSTUDIO_VISION_MODEL: str = "llava-v1.6-34b"
    SCALEWAY_VISION_MODEL: str = "gemma-3-27b-it"

    # OCR service endpoint (your PaddleOCR wrapper)
    OCR_SERVICE_URL: str = "http://localhost:8001"

    # RAG service endpoint
    RAG_SERVICE_URL: str = "http://localhost:8002"

    # Timeouts (seconds)
    LM_TIMEOUT: int = 500
    RAG_TIMEOUT: int = 15
    OCR_TIMEOUT: int = 60

    # Model Generation Settings
    MAX_TOKENS: int = 4096
    CONTEXT_WINDOW_SIZE: int = 18000

    # Google Custom Search API
    GOOGLE_API_KEY: str = "your-google-api-key-here"
    GOOGLE_SEARCH_ENGINE_ID: str = "your-search-engine-id-here"
    
    # Gemini Pro Mode API (Google AI)
    # TODO: Override this in .env for production
    GEMINI_API_KEY: str = "AIzaSyCR1TlKBb-3saTcHCVKMoBkiCyUkngJ4WE"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # External widget defaults
    DEFAULT_WIDGET_USER_ID: int = 1
    DEFAULT_WIDGET_TENANT_ID: str = "external_widget"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

settings = Settings()
