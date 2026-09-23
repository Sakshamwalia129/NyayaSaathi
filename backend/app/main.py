"""
main.py — NyayaSaathi FastAPI application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import (
    health,
    rights,
    judgments,
    auth,
    latest_judgments,
)
from app.db.database import engine, Base
from app.db.migrations import run_migrations
from app.services.latest_judgment_scheduler import (
    start_latest_judgment_scheduler,
    stop_latest_judgment_scheduler,
)

import app.models.database_models  # Ensure models are loaded for create_all


# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# FastAPI application
# ─────────────────────────────────────────────

app = FastAPI(
    title="NyayaSaathi API",
    description=(
        "Backend API for NyayaSaathi — an AI-powered legal information "
        "and judgment intelligence platform for Indian users.\n\n"
        "**Note:** This API provides general legal information only. "
        "It is not a substitute for advice from a qualified legal professional."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ─────────────────────────────────────────────
# CORS — allow the Vite frontend to call this API
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Accept",
        "Authorization",
    ],
)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

app.include_router(
    health.router,
    prefix="/api",
)

app.include_router(
    rights.router,
    prefix="/api",
)

app.include_router(
    judgments.router,
    prefix="/api",
)

app.include_router(
    auth.router,
    prefix="/api",
)

app.include_router(
    latest_judgments.router,
    prefix="/api",
)


# ─────────────────────────────────────────────
# Startup event
# ─────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():

    logger.info(
        "NyayaSaathi backend starting..."
    )

    try:
        Base.metadata.create_all(
            bind=engine
        )

        run_migrations(
            engine
        )

        logger.info(
            "Database tables and migrations initialized safely."
        )

    except Exception as e:

        logger.error(
            f"Error initializing database tables: {e}"
        )

    logger.info(
        f"Frontend URL: {settings.FRONTEND_URL}"
    )

    logger.info(
        f"LLM configured: {settings.llm_configured}"
    )

    logger.info(
        f"Mock mode: {settings.USE_MOCK_LLM}"
    )

    logger.info(
        f"ChromaDB path: {settings.CHROMA_PATH}"
    )

    if (
        not settings.llm_configured
        and not settings.USE_MOCK_LLM
    ):
        logger.warning(
            "LLM_API_KEY is not set and USE_MOCK_LLM=false. "
            "API requests requiring LLM will return an error. "
            "Set USE_MOCK_LLM=true in .env for demo mode."
        )

    # Start automatic Supreme Court judgment updates.
    try:
        start_latest_judgment_scheduler()

    except Exception:

        logger.exception(
            "Could not start Latest Supreme Court judgment scheduler."
        )

    logger.info(
        "Backend ready. "
        "Visit http://localhost:8000/docs "
        "for API documentation."
    )


# ─────────────────────────────────────────────
# Shutdown event
# ─────────────────────────────────────────────

@app.on_event("shutdown")
async def on_shutdown():

    logger.info(
        "NyayaSaathi backend shutting down..."
    )

    try:
        stop_latest_judgment_scheduler()

    except Exception:

        logger.exception(
            "Could not stop Latest Supreme Court judgment scheduler."
        )