"""judgments.py — Judgment Simplifier API endpoint."""

import logging

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.config import settings
from app.db.database import get_db
from app.models.database_models import JudgmentAnalysis, User
from app.models.schemas import JudgmentResponse
from app.services import judgment_service


logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post(
    "/simplify-judgment",
    response_model=JudgmentResponse,
    tags=["Judgment Simplifier"],
)
async def simplify_judgment(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts an uploaded court judgment (PDF or TXT) and returns
    a structured simplified analysis.

    Successful judgment analyses are stored in PostgreSQL under the authenticated user.

    The response fields match what the existing frontend
    (JudgmentSimplifier.jsx) expects.
    """

    # ---------------------------------------------------------
    # 1. Validate file extension
    # ---------------------------------------------------------

    filename = file.filename or "upload"

    ext = (
        "." + filename.rsplit(".", 1)[-1].lower()
        if "." in filename
        else ""
    )

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{ext}'. "
                "Please upload a PDF or TXT file."
            ),
        )

    # ---------------------------------------------------------
    # 2. Read uploaded file
    # ---------------------------------------------------------

    file_bytes = await file.read()

    # ---------------------------------------------------------
    # 3. Validate file size
    # ---------------------------------------------------------

    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is too large. Maximum allowed size is "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    logger.info(
        "Simplify judgment — file: %s, size: %s bytes, user_id: %s",
        filename,
        len(file_bytes),
        current_user.id,
    )

    # ---------------------------------------------------------
    # 4. Run existing Judgment Simplifier pipeline
    # ---------------------------------------------------------

    result = await judgment_service.simplify_judgment(
        file_bytes,
        filename,
    )

    # ---------------------------------------------------------
    # 5. Store only successful analyses in PostgreSQL
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
                "Judgment analysis saved to PostgreSQL — id: %s, user_id: %s",
                history_entry.id,
                current_user.id,
            )

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to save judgment analysis to PostgreSQL."
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Judgment analysis was generated but could not "
                    "be saved to the database."
                ),
            )

    # ---------------------------------------------------------
    # 6. Return original response unchanged
    # ---------------------------------------------------------

    return result


# ============================================================
# JUDGMENT HISTORY
# ============================================================

@router.get(
    "/judgment-history",
    tags=["Judgment Simplifier"],
)
def get_judgment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns previously completed Judgment Simplifier analyses
    stored in PostgreSQL for the authenticated user only.

    Newest analyses are returned first.
    """

    records = (
        db.query(JudgmentAnalysis)
        .filter(JudgmentAnalysis.user_id == current_user.id)
        .order_by(JudgmentAnalysis.created_at.desc())
        .all()
    )


    return {
        "success": True,
        "count": len(records),
        "data": [
            {
                "id": record.id,
                "filename": record.filename,
                "response": record.response,
                "createdAt": (
                    record.created_at.isoformat()
                    if record.created_at
                    else None
                ),
            }
            for record in records
        ],
    }