"""rights.py — Rights Checker API endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.database_models import RightsQuery, User
from app.models.schemas import RightsCheckRequest, RightsCheckResponse
from app.services import legal_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# RIGHTS CHECKER
# ============================================================

@router.post(
    "/rights-check",
    response_model=RightsCheckResponse,
    tags=["Rights Checker"],
)
async def rights_check(
    request: RightsCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts a user's legal situation description and returns
    relevant legal provisions, next steps, and grounding information.

    Successful Rights Checker responses are stored in PostgreSQL under the authenticated user.
    """

    logger.info(
        f"Rights check — query length: {len(request.query)}, "
        f"category: {request.category}, user_id: {current_user.id}"
    )

    result = await legal_service.check_rights(
        query=request.query,
        category=request.category,
    )

    # Store only successful responses.
    if result.get("success") is True:

        if hasattr(result, "model_dump"):
            stored_response = result.model_dump(mode="json")
        elif hasattr(result, "dict"):
            stored_response = result.dict()
        else:
            stored_response = result

        history_entry = RightsQuery(
            user_id=current_user.id,
            query=request.query,
            category=request.category or "general",
            response=stored_response,
        )

        try:
            db.add(history_entry)
            db.commit()
            db.refresh(history_entry)

            logger.info(
                f"Rights check saved to PostgreSQL — "
                f"id: {history_entry.id}, user_id: {current_user.id}"
            )

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to save Rights Checker response to PostgreSQL."
            )

    return result


# ============================================================
# RIGHTS HISTORY
# ============================================================

@router.get(
    "/rights-history",
    tags=["Rights Checker"],
)
def get_rights_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns previously completed Rights Checker queries
    stored in PostgreSQL for the authenticated user only.

    Newest queries are returned first.
    """

    records = (
        db.query(RightsQuery)
        .filter(RightsQuery.user_id == current_user.id)
        .order_by(RightsQuery.created_at.desc())
        .all()
    )


    return {
        "success": True,
        "count": len(records),
        "data": [
            {
                "id": record.id,
                "query": record.query,
                "category": record.category,
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