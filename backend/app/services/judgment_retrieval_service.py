"""
judgment_retrieval_service.py

Two-stage retrieval service for uploaded court judgments.

Pipeline:
    extracted paragraphs
        → bi-encoder paragraph embeddings
        → semantic candidate retrieval
        → CrossEncoder reranking
        → best match per analysis category
        → preserve structural context
        → de-duplication
        → original judgment order
"""

import logging
import math

from app.services.embedding_service import (
    get_embedding,
    get_embeddings,
)
from app.services.reranker_service import rerank_paragraphs


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# ANALYSIS QUERIES
# ─────────────────────────────────────────────────────────────

ANALYSIS_QUERIES = {
    "metadata": (
        "case title parties court name judgment date year "
        "case number jurisdiction"
    ),
    "facts": (
        "material facts factual background events dispute history "
        "what happened between the parties circumstances of the case"
    ),
    "arguments": (
        "arguments submissions contentions claims pleaded by appellant "
        "respondent petitioner defendant counsel parties"
    ),
    "issues": (
        "main issue before the court question of law legal issue "
        "point for determination whether court must decide"
    ),
    "decision": (
        "court decided final judgment final order holding conclusion "
        "appeal allowed dismissed relief granted court held"
    ),
    "reasoning": (
        "court reasoned reasoning reasons analysis finding rationale "
        "because therefore court concluded why decision was reached"
    ),
    "legal_principles": (
        "legal principle ratio decidendi rule of law precedent "
        "statutory interpretation doctrine legal proposition"
    ),
}


# ─────────────────────────────────────────────────────────────
# VECTOR SIMILARITY
# ─────────────────────────────────────────────────────────────

def _cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """Calculate cosine similarity between two embedding vectors."""

    if not vector_a or not vector_b:
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


# ─────────────────────────────────────────────────────────────
# MAIN TWO-STAGE RETRIEVAL
# ─────────────────────────────────────────────────────────────

def retrieve_judgment_paragraphs(
    paragraphs: list[dict],
    top_k_per_query: int = 6,
    max_total: int = 45,
) -> list[dict]:
    """
    Retrieve and rerank important judgment paragraphs.

    Stage 1:
        SentenceTransformer bi-encoder retrieves semantic candidates.

    Stage 2:
        CrossEncoder reranks those candidates using the complete
        query-paragraph pair.

    The strongest reranked paragraph for every analysis category
    is preserved.

    Beginning and ending paragraphs are also preserved for
    structural context.

    Final paragraphs are returned in original judgment order.
    """

    if not paragraphs:
        return []

    # Short judgments do not need filtering/reranking.
    if len(paragraphs) <= max_total:
        logger.info(
            "Judgment contains %s paragraphs. "
            "Using all paragraphs.",
            len(paragraphs),
        )
        return paragraphs

    paragraph_texts = [
        paragraph.get("text", "")
        for paragraph in paragraphs
    ]

    # ---------------------------------------------------------
    # Stage 1 — Paragraph embeddings
    # ---------------------------------------------------------

    try:
        paragraph_embeddings = get_embeddings(
            paragraph_texts
        )

    except Exception as exc:
        logger.exception(
            "Failed to create judgment paragraph embeddings: %s",
            exc,
        )

        return _fallback_selection(
            paragraphs,
            max_total,
        )

    required_indexes = set()

    # Stores strongest CrossEncoder score for each paragraph.
    candidate_scores = {}

    # Fast mapping from paragraph ID to its original index.
    id_to_index = {
        paragraph.get("id"): index
        for index, paragraph in enumerate(paragraphs)
        if paragraph.get("id")
    }

    # ---------------------------------------------------------
    # Preserve structural context
    # ---------------------------------------------------------

    beginning_count = min(
        4,
        len(paragraphs),
    )

    beginning_indexes = set(
        range(beginning_count)
    )

    ending_count = min(
        6,
        len(paragraphs),
    )

    ending_indexes = set(
        range(
            len(paragraphs) - ending_count,
            len(paragraphs),
        )
    )

    required_indexes.update(
        beginning_indexes
    )

    required_indexes.update(
        ending_indexes
    )

    for index in (
        beginning_indexes
        | ending_indexes
    ):
        candidate_scores[index] = 0.0

    # ---------------------------------------------------------
    # Retrieval + reranking for each analysis category
    # ---------------------------------------------------------

    for query_name, query_text in ANALYSIS_QUERIES.items():

        # -----------------------------------------------------
        # Stage 1 — Dense semantic retrieval
        # -----------------------------------------------------

        try:
            query_embedding = get_embedding(
                query_text
            )

        except Exception as exc:
            logger.exception(
                "Failed to create embedding for judgment query '%s': %s",
                query_name,
                exc,
            )
            continue

        dense_scores = []

        for index, paragraph_embedding in enumerate(
            paragraph_embeddings
        ):
            similarity = _cosine_similarity(
                query_embedding,
                paragraph_embedding,
            )

            dense_scores.append(
                (
                    similarity,
                    index,
                )
            )

        dense_scores.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        if not dense_scores:
            continue

        # Retrieve a broader candidate pool than the final top-K.
        # Example:
        # top_k_per_query = 6 → up to 18 candidates for reranking.
        candidate_pool_size = min(
            len(dense_scores),
            max(
                top_k_per_query * 3,
                top_k_per_query,
            ),
        )

        dense_candidates = []

        for _, index in dense_scores[
            :candidate_pool_size
        ]:
            dense_candidates.append(
                paragraphs[index]
            )

        # -----------------------------------------------------
        # Stage 2 — CrossEncoder reranking
        # -----------------------------------------------------

        reranked = rerank_paragraphs(
            query=query_text,
            paragraphs=dense_candidates,
            top_k=top_k_per_query,
        )

        if not reranked:
            continue

        # Best CrossEncoder result for this category must survive.
        best_paragraph = reranked[0]

        best_id = best_paragraph.get("id")

        best_index = id_to_index.get(
            best_id
        )

        if best_index is not None:
            required_indexes.add(
                best_index
            )

            best_score = float(
                best_paragraph.get(
                    "_rerank_score",
                    0.0,
                )
            )

            candidate_scores[best_index] = max(
                candidate_scores.get(
                    best_index,
                    float("-inf"),
                ),
                best_score,
            )

            logger.info(
                "Best reranked judgment match [%s] -> %s "
                "(rerank_score=%.4f)",
                query_name,
                best_id,
                best_score,
            )

        # -----------------------------------------------------
        # Store remaining reranked candidates
        # -----------------------------------------------------

        for reranked_paragraph in reranked:

            para_id = reranked_paragraph.get(
                "id"
            )

            index = id_to_index.get(
                para_id
            )

            if index is None:
                continue

            rerank_score = float(
                reranked_paragraph.get(
                    "_rerank_score",
                    0.0,
                )
            )

            candidate_scores[index] = max(
                candidate_scores.get(
                    index,
                    float("-inf"),
                ),
                rerank_score,
            )

            logger.debug(
                "Judgment reranking [%s] -> %s "
                "(score=%.4f)",
                query_name,
                para_id,
                rerank_score,
            )

    # ---------------------------------------------------------
    # Build final selection
    # ---------------------------------------------------------

    selected_indexes = set(
        required_indexes
    )

    remaining_candidates = sorted(
        (
            (
                score,
                index,
            )
            for index, score
            in candidate_scores.items()
            if index not in selected_indexes
        ),
        key=lambda item: item[0],
        reverse=True,
    )

    available_slots = max(
        0,
        max_total - len(selected_indexes),
    )

    for _, index in remaining_candidates[
        :available_slots
    ]:
        selected_indexes.add(
            index
        )

    # Return paragraphs in original judgment order.
    ordered_indexes = sorted(
        selected_indexes
    )

    selected_paragraphs = [
        paragraphs[index]
        for index in ordered_indexes
    ]

    logger.info(
        "Judgment two-stage retrieval selected %s "
        "paragraphs from %s total paragraphs.",
        len(selected_paragraphs),
        len(paragraphs),
    )

    return selected_paragraphs


# ─────────────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────────────

def _fallback_selection(
    paragraphs: list[dict],
    max_total: int,
) -> list[dict]:
    """
    Fallback used if embedding retrieval fails.

    Select paragraphs evenly across the complete judgment so
    beginning, middle and ending remain represented.
    """

    total = len(paragraphs)

    if total <= max_total:
        return paragraphs

    if max_total <= 1:
        return [
            paragraphs[0]
        ]

    step = (
        (total - 1)
        / (max_total - 1)
    )

    indexes = []

    for i in range(max_total):
        index = round(
            i * step
        )

        indexes.append(
            index
        )

    indexes = list(
        dict.fromkeys(indexes)
    )

    logger.warning(
        "Using fallback judgment paragraph selection. "
        "Selected %s of %s paragraphs.",
        len(indexes),
        total,
    )

    return [
        paragraphs[index]
        for index in indexes
    ]