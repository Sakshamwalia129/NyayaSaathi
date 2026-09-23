"""
embedding_service.py — Generates text embeddings using sentence-transformers.

The model is loaded ONCE at startup, not on every request.
"""

import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Load once globally — this is intentional to avoid repeated load overhead.
# The model is small (~80MB) and loads in a few seconds.
MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Return the loaded model, loading it on first call."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Embedding model loaded.")
    return _model


def get_embedding(text: str) -> list[float]:
    """Return the embedding vector for a single text string."""
    model = _get_model()
    vector = model.encode(text, convert_to_numpy=True)
    return vector.tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Return embedding vectors for a list of text strings (batched)."""
    model = _get_model()
    vectors = model.encode(texts, convert_to_numpy=True, batch_size=32)
    return vectors.tolist()
