"""health.py — Health check endpoint."""

from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.services.rag_service import get_db_status
from app.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Returns backend status.
    Does NOT fail if LLM key is missing — the server should always be reachable.
    """
    return HealthResponse(
        status="ok",
        service="NyayaSaathi Backend",
        vector_database=get_db_status(),
        llm_configured=settings.llm_configured,
    )
