"""
embedding_service.py — Generates text embeddings using sentence-transformers.

The heavy sentence-transformers / PyTorch stack is imported lazily,
only when embeddings are actually required.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
_model: Any = None


def _get_model():
    """Return the loaded model, loading it only on the first embedding request."""
    global _model

    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")

        # Lazy import: prevents PyTorch / sentence-transformers from being
        # loaded into memory during FastAPI startup.
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)

        logger.info("Embedding model loaded.")

    return _model


def get_embedding(text: str) -> list[float]:
    """Return the embedding vector for a single text string."""
    model = _get_model()
    vector = model.encode(
        text,
        convert_to_numpy=True,
    )
    return vector.tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a list of text strings (batched)."""
    model = _get_model()
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        batch_size=32,
    )
    return vectors.tolist()