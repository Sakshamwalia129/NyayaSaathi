"""
latest_judgments.py — Latest Supreme Court Judgments API.

Provides:
- Latest judgments feed with date filtering
- Individual judgment details
- Manual SCI update trigger for authenticated users
- Analyze an official SCI judgment using the existing
  Judgment Simplifier pipeline

AI-generated headline/summary are clearly separated from
official Supreme Court metadata.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.database_models import (
    JudgmentAnalysis,
    LatestJudgment,
    User,
)
from app.services import judgment_service
from app.services.latest_judgment_service import (
    download_pdf,
    update_latest_judgments,
)


logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# SERIALIZER
# ============================================================

def _serialize_judgment(record: LatestJudgment) -> dict:
    """
    Convert LatestJudgment database model into frontend-safe JSON.

    Official SCI metadata and AI-generated content remain
    clearly separated.
    """

    return {
        "id": record.id,

        "official": {
            "caseTitle": record.case_title,
            "caseNumber": record.case_number,
            "diaryNumber": record.diary_number,

            "judgmentDate": (
                record.judgment_date.isoformat()
                if record.judgment_date
                else None
            ),

            "uploadedAt": (
                record.uploaded_at.isoformat()
                if record.uploaded_at
                else None
            ),

            "pdfUrl": record.official_pdf_url,
            "sourceUrl": record.source_url,
        },

        "ai": {
            "headline": record.ai_headline,
            "summary": record.ai_summary,
            "label": "AI-generated summary",
        },

        "processingStatus": record.processing_status,

        "createdAt": (
            record.created_at.isoformat()
            if record.created_at
            else None
        ),

        "updatedAt": (
            record.updated_at.isoformat()
            if record.updated_at
            else None
        ),
    }


# ============================================================
# DATE FILTER HELPER
# ============================================================

def _parse_custom_date(
    value: str,
    field_name: str,
) -> datetime:
    """
    Parse YYYY-MM-DD date used by the Custom filter.
    """

    try:
        parsed_date = datetime.strptime(
            value,
            "%Y-%m-%d",
        )

        return parsed_date.replace(
            tzinfo=timezone.utc
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} must use YYYY-MM-DD format."
            ),
        ) from exc


# ============================================================
# LATEST JUDGMENTS FEED
# ============================================================

@router.get(
    "/latest-judgments",
    tags=["Latest Supreme Court Judgments"],
)
def get_latest_judgments(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    period: str = Query(
        default="all",
        description=(
            "Date filter: all, today, 7d, 30d, 6m, custom"
        ),
    ),

    from_date: str | None = Query(
        default=None,
        description=(
            "Custom start date in YYYY-MM-DD format"
        ),
    ),

    to_date: str | None = Query(
        default=None,
        description=(
            "Custom end date in YYYY-MM-DD format"
        ),
    ),

    db: Session = Depends(get_db),
):
    """
    Return processed Supreme Court judgments.

    Supported date filters:

    - all
    - today
    - 7d
    - 30d
    - 6m
    - custom

    Filtering is based on the date/time the judgment was
    uploaded by the Supreme Court.
    """

    normalized_period = period.strip().lower()

    allowed_periods = {
        "all",
        "today",
        "7d",
        "30d",
        "6m",
        "custom",
    }

    if normalized_period not in allowed_periods:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid period. Use all, today, 7d, "
                "30d, 6m, or custom."
            ),
        )

    query = (
        db.query(LatestJudgment)
        .filter(
            LatestJudgment.processing_status
            == "processed"
        )
    )

    # ---------------------------------------------------------
    # CURRENT TIME
    # ---------------------------------------------------------

    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------
    # TODAY
    # ---------------------------------------------------------

    if normalized_period == "today":

        start_date = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        query = query.filter(
            LatestJudgment.uploaded_at >= start_date
        )

    # ---------------------------------------------------------
    # LAST 7 DAYS
    # ---------------------------------------------------------

    elif normalized_period == "7d":

        start_date = now - timedelta(days=7)

        query = query.filter(
            LatestJudgment.uploaded_at >= start_date
        )

    # ---------------------------------------------------------
    # LAST 30 DAYS
    # ---------------------------------------------------------

    elif normalized_period == "30d":

        start_date = now - timedelta(days=30)

        query = query.filter(
            LatestJudgment.uploaded_at >= start_date
        )

    # ---------------------------------------------------------
    # LAST 6 MONTHS
    # ---------------------------------------------------------

    elif normalized_period == "6m":

        # Approximate six months as 183 days.
        start_date = now - timedelta(days=183)

        query = query.filter(
            LatestJudgment.uploaded_at >= start_date
        )

    # ---------------------------------------------------------
    # CUSTOM DATE RANGE
    # ---------------------------------------------------------

    elif normalized_period == "custom":

        if not from_date or not to_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    "from_date and to_date are required "
                    "when period=custom."
                ),
            )

        start_date = _parse_custom_date(
            from_date,
            "from_date",
        )

        end_date = _parse_custom_date(
            to_date,
            "to_date",
        )

        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail=(
                    "from_date cannot be later than to_date."
                ),
            )

        # Include the complete selected final day.
        end_date = end_date + timedelta(days=1)

        query = query.filter(
            LatestJudgment.uploaded_at >= start_date,
            LatestJudgment.uploaded_at < end_date,
        )

    # ---------------------------------------------------------
    # ORDER + LIMIT
    # ---------------------------------------------------------

    records = (
        query
        .order_by(
            LatestJudgment.uploaded_at.desc(),
            LatestJudgment.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "count": len(records),

        "filter": {
            "period": normalized_period,
            "fromDate": from_date,
            "toDate": to_date,
        },

        "data": [
            _serialize_judgment(record)
            for record in records
        ],
    }


# ============================================================
# SINGLE JUDGMENT
# ============================================================

@router.get(
    "/latest-judgments/{judgment_id}",
    tags=["Latest Supreme Court Judgments"],
)
def get_latest_judgment(
    judgment_id: int,
    db: Session = Depends(get_db),
):
    """
    Return one stored Supreme Court judgment.
    """

    record = (
        db.query(LatestJudgment)
        .filter(
            LatestJudgment.id
            == judgment_id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Judgment not found.",
        )

    return {
        "success": True,
        "data": _serialize_judgment(record),
    }


# ============================================================
# MANUAL UPDATE
# ============================================================

@router.post(
    "/latest-judgments/update",
    tags=["Latest Supreme Court Judgments"],
)
def update_judgments(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually check the official Supreme Court website for
    newly uploaded judgments.

    Authentication is required so this operation is not
    exposed anonymously.

    V1 does not yet implement administrator roles.
    """

    if limit < 1:
        raise HTTPException(
            status_code=400,
            detail="Limit must be at least 1.",
        )

    if limit > 10:
        limit = 10

    logger.info(
        "Latest judgments update requested by user_id=%s",
        current_user.id,
    )

    try:
        result = update_latest_judgments(
            db=db,
            limit=limit,
        )

        return result

    except Exception as exc:

        logger.exception(
            "Latest judgments update failed."
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not update judgments from the "
                "Supreme Court website."
            ),
        ) from exc


# ============================================================
# ANALYZE OFFICIAL JUDGMENT
# ============================================================

@router.post(
    "/latest-judgments/{judgment_id}/analyze",
    tags=["Latest Supreme Court Judgments"],
)
async def analyze_latest_judgment(
    judgment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a stored official Supreme Court judgment using
    NyayaSaathi's existing Judgment Simplifier.

    The generated analysis is also saved to the authenticated
    user's Judgment History.
    """

    # ---------------------------------------------------------
    # 1. Find judgment
    # ---------------------------------------------------------

    record = (
        db.query(LatestJudgment)
        .filter(
            LatestJudgment.id
            == judgment_id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Judgment not found.",
        )

    if record.processing_status != "processed":
        raise HTTPException(
            status_code=409,
            detail=(
                "This judgment has not finished "
                "processing yet."
            ),
        )

    # ---------------------------------------------------------
    # 2. Download official SCI PDF
    # ---------------------------------------------------------

    try:
        pdf_bytes = download_pdf(
            record.official_pdf_url
        )

    except Exception as exc:

        logger.exception(
            "Could not download SCI judgment id=%s",
            judgment_id,
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not download the official "
                "Supreme Court judgment PDF."
            ),
        ) from exc

    # ---------------------------------------------------------
    # 3. Generate useful filename
    # ---------------------------------------------------------

    if record.case_number:
        safe_case_number = (
            record.case_number
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )

        filename = (
            f"SCI_{safe_case_number}.pdf"
        )

    else:
        filename = (
            f"SCI_Judgment_{record.id}.pdf"
        )

    logger.info(
        "Analyzing latest SCI judgment id=%s for user_id=%s",
        record.id,
        current_user.id,
    )

    # ---------------------------------------------------------
    # 4. Reuse existing Judgment Simplifier
    # ---------------------------------------------------------

    try:
        result = await judgment_service.simplify_judgment(
            pdf_bytes,
            filename,
        )

    except Exception as exc:

        logger.exception(
            "Judgment Simplifier failed for latest judgment id=%s",
            record.id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not analyze this judgment."
            ),
        ) from exc

    # ---------------------------------------------------------
    # 5. Save successful analysis to CURRENT USER'S history
    # ---------------------------------------------------------

    if result.get("success") is True:

        if hasattr(result, "model_dump"):
            stored_response = result.model_dump(
                mode="json"
            )

        elif hasattr(result, "dict"):
            stored_response = result.dict()

        else:
            stored_response = result

        history_entry = JudgmentAnalysis(
            user_id=current_user.id,
            filename=filename,
            response=stored_response,
        )

        try:
            db.add(history_entry)
            db.commit()
            db.refresh(history_entry)

            logger.info(
                (
                    "Latest SCI judgment analysis saved "
                    "to history — history_id=%s, "
                    "judgment_id=%s, user_id=%s"
                ),
                history_entry.id,
                record.id,
                current_user.id,
            )

        except Exception as exc:

            db.rollback()

            logger.exception(
                "Failed saving latest judgment analysis."
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Judgment analysis was generated "
                    "but could not be saved to history."
                ),
            ) from exc

    # ---------------------------------------------------------
    # 6. Return existing Judgment Simplifier response unchanged
    # ---------------------------------------------------------

    return result