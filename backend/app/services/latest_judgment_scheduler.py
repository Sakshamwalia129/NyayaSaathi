"""
latest_judgment_scheduler.py

Background scheduler for automatically checking the official
Supreme Court of India website for newly uploaded judgments.

The scheduler:
- checks immediately when the backend starts
- checks periodically for new Supreme Court judgments
- processes only new judgments
- stores them in PostgreSQL
- avoids overlapping runs
- keeps failures isolated from the FastAPI server
"""

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.db.database import SessionLocal

logger = logging.getLogger(__name__)

CHECK_INTERVAL_MINUTES = 60
PROCESS_LIMIT = 5

scheduler = BackgroundScheduler(
    timezone="Asia/Kolkata"
)


def run_latest_judgment_update():
    """
    Run one automatic Supreme Court judgment update cycle.

    Heavy judgment-processing dependencies are imported only
    when the scheduled job actually runs.
    """
    from app.services.latest_judgment_service import (
        update_latest_judgments,
    )

    logger.info(
        "Starting automatic Supreme Court judgment update..."
    )

    db = SessionLocal()

    try:
        result = update_latest_judgments(
            db,
            limit=PROCESS_LIMIT,
        )

        logger.info(
            "Supreme Court judgment update completed: %s",
            result,
        )

    except Exception:
        logger.exception(
            "Automatic Supreme Court judgment update failed."
        )

        try:
            db.rollback()
        except Exception:
            pass

    finally:
        db.close()


def start_latest_judgment_scheduler():
    """
    Start the background scheduler.

    Safe against accidental duplicate start calls inside
    the same Python process.

    The first update runs immediately when the backend starts.
    After that, updates run every configured interval.
    """
    if scheduler.running:
        logger.info(
            "Latest judgment scheduler is already running."
        )
        return

    scheduler.add_job(
        run_latest_judgment_update,
        trigger=IntervalTrigger(
            minutes=CHECK_INTERVAL_MINUTES
        ),
        id="latest_supreme_court_judgments",
        name="Latest Supreme Court Judgments Update",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),
    )

    scheduler.start()

    logger.info(
        "Latest Supreme Court judgment scheduler started. "
        "Check interval: %s minutes.",
        CHECK_INTERVAL_MINUTES,
    )


def stop_latest_judgment_scheduler():
    """
    Stop the scheduler safely when FastAPI shuts down.
    """
    if scheduler.running:
        scheduler.shutdown(
            wait=False
        )

        logger.info(
            "Latest Supreme Court judgment scheduler stopped."
        )