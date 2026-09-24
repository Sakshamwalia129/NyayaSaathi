"""
legal_service.py — Orchestrates the Rights Explorer pipeline.

Pipeline:
    user query
        → semantic retrieval from ChromaDB
        → relevance validation
        → grounded legal context
        → LLM structured response
        → citation validation
        → final Rights Checker response
"""

import logging

from app.config import settings
from app.services import citation_service, llm_service, rag_service


logger = logging.getLogger(__name__)


def _build_context(chunks: list[dict]) -> str:
    """
    Convert retrieved ChromaDB chunks into grounded legal context
    for the LLM.
    """

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        text = chunk.get("text", "")

        source_name = (
            metadata.get("source_name")
            or metadata.get("source")
            or metadata.get("document_name")
            or "Legal Source"
        )

        section = (
            metadata.get("section")
            or metadata.get("section_title")
            or metadata.get("title")
            or "Relevant Provision"
        )

        context_parts.append(
            f"""
SOURCE {index}

Source Name:
{source_name}

Section:
{section}

Legal Text:
{text}
""".strip()
        )

    return "\n\n---\n\n".join(context_parts)


async def check_rights(
    query: str,
    category: str | None = None,
) -> dict:
    """
    Run the complete Rights Explorer pipeline.
    """

    # ---------------------------------------------------------
    # 1. Validate query
    # ---------------------------------------------------------

    if not query or not query.strip():
        return {
            "success": False,
            "error": {
                "code": "EMPTY_QUERY",
                "message": "Please describe your legal situation.",
            },
        }

    # ---------------------------------------------------------
    # 2. Retrieve relevant legal chunks from ChromaDB
    # ---------------------------------------------------------

    chunks = rag_service.retrieve(
        query=query.strip(),
        n_results=settings.RETRIEVAL_TOP_K,
        category=category,
    )

    # ---------------------------------------------------------
    # 3. Handle missing legal context
    # ---------------------------------------------------------

    if not chunks:
        logger.info(
            "No legal documents retrieved for category '%s'.",
            category or "all",
        )

        return {
            "success": False,
            "error": {
                "code": "NO_LEGAL_CONTEXT",
                "message": (
                    "No relevant legal material is currently "
                    "available for this category."
                ),
            },
        }

    # ---------------------------------------------------------
    # 4. Calculate best retrieval similarity
    # ---------------------------------------------------------

    best_similarity = max(
        (
            chunk.get("similarity", 0.0)
            for chunk in chunks
        ),
        default=0.0,
    )

    # ---------------------------------------------------------
    # 5. Check semantic relevance
    # ---------------------------------------------------------

    if not rag_service.is_relevant(chunks):
        logger.info(
            "Retrieved legal context below relevance threshold. "
            "Best similarity: %.4f",
            best_similarity,
        )

        return {
            "success": False,
            "error": {
                "code": "LOW_RELEVANCE",
                "message": (
                    "The available legal material does not appear "
                    "relevant enough to answer this situation reliably."
                ),
            },
        }

    # ---------------------------------------------------------
    # 6. Build grounded legal context
    # ---------------------------------------------------------

    context = _build_context(chunks)

    # ---------------------------------------------------------
    # 7. Generate structured Rights response
    # ---------------------------------------------------------

    try:
        llm_data = llm_service.generate_rights_response(
            query=query.strip(),
            context=context,
            category=category,
        )

    except ValueError as exc:
        return {
            "success": False,
            "error": {
                "code": "LLM_ERROR",
                "message": str(exc),
            },
        }

    # ---------------------------------------------------------
    # 8. Validate legal provisions / citations
    # ---------------------------------------------------------

    provisions = llm_data.get(
        "provisions",
        [],
    )

    if hasattr(
        citation_service,
        "validate_provisions",
    ):
        try:
            provisions = citation_service.validate_provisions(
                provisions,
                chunks,
            )

        except Exception as exc:
            logger.warning(
                "Provision validation failed: %s",
                exc,
            )

    elif hasattr(
        citation_service,
        "validate_rights_citations",
    ):
        try:
            provisions = (
                citation_service.validate_rights_citations(
                    provisions,
                    chunks,
                )
            )

        except Exception as exc:
            logger.warning(
                "Rights citation validation failed: %s",
                exc,
            )

    # ---------------------------------------------------------
    # 9. Normalize citation verification field
    # ---------------------------------------------------------

    normalized_provisions = []

    for provision in provisions:
        normalized = dict(provision)

        if "_verified" in normalized:
            normalized["verified"] = bool(
                normalized.pop("_verified")
            )

        elif "verified" not in normalized:
            normalized["verified"] = False

        normalized_provisions.append(
            normalized
        )

    # ---------------------------------------------------------
    # 10. Build final frontend-compatible response
    # ---------------------------------------------------------

    return {
        "success": True,

        "data": {
            "situation": llm_data.get(
                "situation",
                "Your Legal Situation",
            ),

            "explanation": llm_data.get(
                "explanation",
                "",
            ),

            "provisions": normalized_provisions,

            "nextSteps": llm_data.get(
                "nextSteps",
                llm_data.get(
                    "next_steps",
                    [],
                ),
            ),

            # Legal Action Plan.
            # This is additive so existing nextSteps/history
            # remain fully compatible.
            "actionPlan": llm_data.get(
                "actionPlan",
                llm_data.get(
                    "action_plan",
                    None,
                ),
            ),

            "groundingNote": llm_data.get(
                "groundingNote",
                llm_data.get(
                    "grounding_note",
                    "",
                ),
            ),

            # Required by RightsCheckData schema.
            # Kept for backend/frontend compatibility.
            "retrievalConfidence": float(
                best_similarity
            ),
        },
    }