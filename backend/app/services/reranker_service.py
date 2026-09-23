"""
reranker_service.py

Cross-Encoder based reranking service for NyayaSaathi.

Dense embedding retrieval is used to find candidate paragraphs.
This service then scores each query-paragraph pair more precisely
using a CrossEncoder model.

Pipeline:
    semantic retrieval
        → candidate paragraphs
        → CrossEncoder reranking
        → highest relevance paragraphs
"""

import logging

from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)


# Lightweight and widely used reranking model.
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker_model = None


def _get_reranker() -> CrossEncoder:
    """
    Lazy-load the CrossEncoder model.

    The model is loaded only on the first reranking request
    and then reused for later requests.
    """

    global _reranker_model

    if _reranker_model is None:
        logger.info(
            "Loading CrossEncoder reranker: %s",
            RERANKER_MODEL_NAME,
        )

        _reranker_model = CrossEncoder(
            RERANKER_MODEL_NAME
        )

        logger.info(
            "CrossEncoder reranker loaded successfully."
        )

    return _reranker_model


def rerank_paragraphs(
    query: str,
    paragraphs: list[dict],
    top_k: int = 6,
) -> list[dict]:
    """
    Rerank candidate judgment paragraphs for a query.

    Each paragraph is scored by the CrossEncoder using:

        (query, paragraph_text)

    Returns the most relevant paragraphs ordered from
    highest to lowest reranker score.

    The original paragraph dictionaries are preserved.
    A temporary `_rerank_score` field is added internally.
    """

    if not paragraphs:
        return []

    if top_k <= 0:
        return []

    try:
        model = _get_reranker()

        pairs = [
            (
                query,
                paragraph.get("text", ""),
            )
            for paragraph in paragraphs
        ]

        scores = model.predict(
            pairs,
            show_progress_bar=False,
        )

        scored_paragraphs = []

        for paragraph, score in zip(
            paragraphs,
            scores,
        ):
            scored_paragraphs.append(
                {
                    **paragraph,
                    "_rerank_score": float(score),
                }
            )

        scored_paragraphs.sort(
            key=lambda paragraph: paragraph[
                "_rerank_score"
            ],
            reverse=True,
        )

        result = scored_paragraphs[:top_k]

        logger.debug(
            "Reranked %s candidates and selected top %s.",
            len(paragraphs),
            len(result),
        )

        return result

    except Exception as exc:
        logger.exception(
            "CrossEncoder reranking failed: %s",
            exc,
        )

        # Safe fallback:
        # if reranking fails, preserve the incoming retrieval order.
        return paragraphs[:top_k]