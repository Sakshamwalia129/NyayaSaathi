"""
judgment_service.py — Orchestrates the Judgment Simplifier pipeline.

Pipeline:
    uploaded PDF/TXT
        → text extraction
        → text cleaning
        → paragraph segmentation
        → semantic retrieval + reranking
        → LLM analysis
        → paragraph citation validation
        → exact original paragraph grounding
        → structured response
"""

import logging

from app.services import citation_service, llm_service
from app.utils.pdf_processing import extract_text_from_bytes
from app.utils.text_processing import clean_text, split_into_paragraphs


logger = logging.getLogger(__name__)


async def simplify_judgment(
    file_bytes: bytes,
    filename: str,
) -> dict:
    """
    Simplify an uploaded court judgment.

    The LLM is allowed to select paragraph IDs, but the paragraph
    text returned to the frontend always comes from the original
    uploaded document.
    """

    # ---------------------------------------------------------
    # 1. Extract text from uploaded PDF/TXT
    # ---------------------------------------------------------

    try:
        raw_text = extract_text_from_bytes(
            file_bytes,
            filename,
        )

    except ValueError as exc:
        return {
            "success": False,
            "error": {
                "code": "EXTRACTION_ERROR",
                "message": str(exc),
            },
        }

    # ---------------------------------------------------------
    # 2. Reject empty documents
    # ---------------------------------------------------------

    if not raw_text.strip():
        return {
            "success": False,
            "error": {
                "code": "EMPTY_DOCUMENT",
                "message": (
                    "The uploaded file appears to be empty."
                ),
            },
        }

    # ---------------------------------------------------------
    # 3. Clean extracted judgment text
    # ---------------------------------------------------------

    text = clean_text(raw_text)

    # ---------------------------------------------------------
    # 4. Split judgment into grounded paragraphs
    # ---------------------------------------------------------

    paragraphs = split_into_paragraphs(text)

    if not paragraphs:
        return {
            "success": False,
            "error": {
                "code": "NO_PARAGRAPHS",
                "message": (
                    "No usable paragraphs could be extracted "
                    "from the uploaded judgment."
                ),
            },
        }

    logger.info(
        "Judgment '%s': %s chars, %s paragraphs extracted.",
        filename,
        len(text),
        len(paragraphs),
    )

    # ---------------------------------------------------------
    # 5. Generate judgment analysis
    #
    # llm_service handles:
    #   paragraphs
    #       → semantic retrieval
    #       → CrossEncoder reranking
    #       → relevant context
    #       → LLM
    # ---------------------------------------------------------

    try:
        llm_data = llm_service.generate_judgment_response(
            text,
            paragraphs,
        )

    except ValueError as exc:
        logger.warning(
            "Judgment LLM processing failed: %s",
            exc,
        )

        return {
            "success": False,
            "error": {
                "code": "LLM_ERROR",
                "message": str(exc),
            },
        }

    # ---------------------------------------------------------
    # 6. Validate important paragraph citations
    # ---------------------------------------------------------

    raw_paras = llm_data.get(
        "paragraphs",
        [],
    )

    if not raw_paras:
        logger.warning(
            "LLM returned no important paragraph citations. "
            "Using extracted paragraphs as fallback."
        )

        grounded_paras = paragraphs[:5]

    else:
        # IMPORTANT:
        # Pass the COMPLETE extracted paragraph objects.
        #
        # The citation validator uses the LLM-selected paragraph ID
        # only to locate the original paragraph. It then restores the
        # exact paragraph number and text from the uploaded judgment.
        grounded_paras = (
            citation_service.validate_judgment_paragraphs(
                raw_paras,
                paragraphs,
            )
        )

        # If every paragraph ID produced by the LLM was invalid,
        # use original extracted paragraphs rather than hallucinated
        # content.
        if not grounded_paras:
            logger.warning(
                "All LLM paragraph IDs were invalid. "
                "Using extracted paragraphs as fallback."
            )

            grounded_paras = paragraphs[:5]

    # ---------------------------------------------------------
    # 7. Build final structured API response
    # ---------------------------------------------------------

    return {
        "success": True,
        "data": {
            "caseTitle": llm_data.get(
                "caseTitle",
                llm_data.get(
                    "case_title",
                    "Unknown Case",
                ),
            ),
            "court": llm_data.get(
                "court",
                "Unknown Court",
            ),
            "year": str(
                llm_data.get(
                    "year",
                    "—",
                )
            ),
            "caseType": llm_data.get(
                "caseType",
                llm_data.get(
                    "case_type",
                    "—",
                ),
            ),
            "brief": llm_data.get(
                "brief",
                "",
            ),
            "facts": llm_data.get(
                "facts",
                "",
            ),
            "arguments": llm_data.get(
                "arguments",
                "",
            ),
            "issues": llm_data.get(
                "issues",
                [],
            ),
            "decision": llm_data.get(
                "decision",
                "",
            ),
            "legalPrinciples": llm_data.get(
                "legalPrinciples",
                llm_data.get(
                    "legal_principles",
                    [],
                ),
            ),

            # Only exact paragraphs from the uploaded judgment
            # are returned to the frontend.
            "paragraphs": [
                {
                    "id": paragraph["id"],
                    "number": paragraph["number"],
                    "text": paragraph["text"],
                }
                for paragraph in grounded_paras
            ],
        },
    }