"""
config.py — Application configuration for NyayaSaathi backend.
Loads settings from environment variables (.env file).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")
    USE_MOCK_LLM: bool = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    # PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ChromaDB
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./chroma_db")
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "legal_documents")

    # Retrieval
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_SCORE_THRESHOLD: float = float(
        os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.3")
    )

    # Frontend
    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    )

    # File upload limits
    MAX_UPLOAD_SIZE_MB: int = int(
        os.getenv("MAX_UPLOAD_SIZE_MB", "10")
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "nyayasaathi_super_secret_jwt_key_change_in_production_2026"
    )
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "10080")  # Default: 7 days
    )

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_API_KEY)

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


# Single shared instance used throughout the app
settings = Settings()