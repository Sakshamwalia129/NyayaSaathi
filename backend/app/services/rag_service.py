"""
rag_service.py — ChromaDB based retrieval service.

Responsibilities:
- Create/load persistent ChromaDB collection
- Store embedded legal document chunks
- Retrieve semantically similar legal chunks
- Apply strict category filtering
- Prevent cross-category fallback
- Check retrieval relevance
- Report database status for health endpoint
"""

import logging


from app.config import settings
from app.services.embedding_service import (
    get_embedding,
    get_embeddings,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# GLOBAL CHROMADB OBJECTS
# ---------------------------------------------------------

_client = None
_collection = None


# ---------------------------------------------------------
# CLIENT
# ---------------------------------------------------------

def _get_client():
    """
    Create and reuse the persistent ChromaDB client.

    ChromaDB is imported lazily so the heavy dependency
    stack is not loaded during FastAPI startup.
    """

    global _client

    if _client is None:
        import chromadb

        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH
        )

    return _client

# ---------------------------------------------------------
# COLLECTION
# ---------------------------------------------------------

def _get_collection():
    """
    Create or load the configured ChromaDB collection.
    """

    global _collection

    if _collection is None:
        client = _get_client()

        _collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={
                "hnsw:space": "cosine"
            },
        )

        logger.info(
            "ChromaDB collection '%s' ready. Documents stored: %s",
            settings.CHROMA_COLLECTION,
            _collection.count(),
        )

    return _collection


# ---------------------------------------------------------
# DATABASE STATUS
# ---------------------------------------------------------

def get_db_status() -> dict:
    """
    Return basic ChromaDB status information.

    Used by the health API.
    """

    try:
        col = _get_collection()

        return {
            "connected": True,
            "collection": settings.CHROMA_COLLECTION,
            "document_count": col.count(),
            "path": settings.CHROMA_PATH,
        }

    except Exception as exc:
        logger.exception(
            "Failed to get ChromaDB status."
        )

        return {
            "connected": False,
            "collection": settings.CHROMA_COLLECTION,
            "document_count": 0,
            "path": settings.CHROMA_PATH,
            "error": str(exc),
        }


# ---------------------------------------------------------
# STORE DOCUMENT CHUNKS
# ---------------------------------------------------------

def store_chunks(chunks: list[dict]) -> None:
    """
    Store or update chunks inside ChromaDB.

    Expected chunk format:

    {
        "id": "unique_chunk_id",
        "text": "legal text",
        "metadata": {
            "category": "rental",
            ...
        }
    }
    """

    if not chunks:
        logger.warning(
            "No chunks supplied for storage."
        )
        return

    col = _get_collection()

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:

        chunk_id = chunk.get("id")
        chunk_text = chunk.get("text")

        if not chunk_id or not chunk_text:
            logger.warning(
                "Skipping invalid chunk without id or text."
            )
            continue

        ids.append(
            chunk_id
        )

        documents.append(
            chunk_text
        )

        metadatas.append(
            chunk.get(
                "metadata",
                {},
            )
        )

    if not documents:
        logger.warning(
            "No valid chunks available for storage."
        )
        return

    embeddings = get_embeddings(
        documents
    )

    col.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(
        "Stored/updated %s chunks in ChromaDB.",
        len(documents),
    )


# ---------------------------------------------------------
# CATEGORY NORMALIZATION
# ---------------------------------------------------------

def _normalize_category(
    category: str | None,
) -> str | None:
    """
    Convert category names into the format stored
    in ChromaDB metadata.

    Example:
        "Motor Accident"
        -> "motor_accident"
    """

    if not category:
        return None

    normalized = (
        category
        .strip()
        .lower()
        .replace(" / ", "_")
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )

    return normalized or None


# ---------------------------------------------------------
# RETRIEVAL
# ---------------------------------------------------------

def retrieve(
    query: str,
    n_results: int = 5,
    category: str | None = None,
) -> list[dict]:
    """
    Retrieve the most semantically relevant legal chunks.

    Important safety rule:
    If a category is supplied, retrieval remains strictly
    inside that category.

    It NEVER silently retries against unrelated categories.

    Returns:
        [
            {
                "text": "...",
                "metadata": {...},
                "similarity": 0.6433
            }
        ]
    """

    if not query or not query.strip():
        logger.warning(
            "Empty retrieval query received."
        )
        return []

    col = _get_collection()

    total_documents = col.count()

    if total_documents == 0:
        logger.warning(
            "ChromaDB collection is empty. "
            "No documents have been ingested."
        )
        return []

    # -----------------------------------------------------
    # CREATE CATEGORY FILTER
    # -----------------------------------------------------

    normalized_category = _normalize_category(
        category
    )

    where_filter = None

    if normalized_category:
        where_filter = {
            "category": {
                "$eq": normalized_category
            }
        }

        # Check how many documents actually exist
        # inside the requested category.
        try:
            category_documents = col.get(
                where=where_filter,
            )

            category_ids = (
                category_documents.get(
                    "ids",
                    [],
                )
                if category_documents
                else []
            )

        except Exception as exc:
            logger.exception(
                "Failed to inspect category '%s': %s",
                normalized_category,
                exc,
            )

            return []

        # No legal documents for selected category.
        if not category_ids:
            logger.info(
                "No legal documents found for category '%s'.",
                normalized_category,
            )

            return []

        result_limit = min(
            n_results,
            len(category_ids),
        )

    else:
        result_limit = min(
            n_results,
            total_documents,
        )

    if result_limit <= 0:
        return []

    # -----------------------------------------------------
    # CREATE QUERY EMBEDDING
    # -----------------------------------------------------

    try:
        query_embedding = get_embedding(
            query.strip()
        )

    except Exception as exc:
        logger.exception(
            "Failed to create query embedding: %s",
            exc,
        )

        return []

    # -----------------------------------------------------
    # QUERY CHROMADB
    # -----------------------------------------------------

    try:
        results = col.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=result_limit,
            where=where_filter,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

    except Exception as exc:
        logger.exception(
            "ChromaDB retrieval failed"
            " for category '%s': %s",
            normalized_category,
            exc,
        )

        # IMPORTANT:
        # Never retry without category filter.
        return []

    # -----------------------------------------------------
    # PROCESS RESULTS
    # -----------------------------------------------------

    chunks = []

    if not results:
        return chunks

    documents_result = results.get(
        "documents",
        [],
    )

    metadatas_result = results.get(
        "metadatas",
        [],
    )

    distances_result = results.get(
        "distances",
        [],
    )

    if (
        not documents_result
        or not documents_result[0]
    ):
        return chunks

    documents = documents_result[0]

    metadatas = (
        metadatas_result[0]
        if metadatas_result
        else []
    )

    distances = (
        distances_result[0]
        if distances_result
        else []
    )

    # -----------------------------------------------------
    # BUILD FINAL RETRIEVED CHUNKS
    # -----------------------------------------------------

    for doc, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):

        similarity = (
            1.0
            - float(distance)
        )

        chunks.append(
            {
                "text": doc,
                "metadata": metadata or {},
                "similarity": round(
                    similarity,
                    4,
                ),
            }
        )

    logger.info(
        "Retrieved %s chunks for category '%s'.",
        len(chunks),
        normalized_category or "all",
    )

    return chunks


# ---------------------------------------------------------
# RELEVANCE CHECK
# ---------------------------------------------------------

def is_relevant(
    chunks: list[dict],
    threshold: float | None = None,
) -> bool:
    """
    Return True if at least one retrieved chunk
    meets the configured similarity threshold.
    """

    if not chunks:
        return False

    if threshold is None:
        threshold = (
            settings.RETRIEVAL_SCORE_THRESHOLD
        )

    return any(
        chunk.get(
            "similarity",
            0.0,
        ) >= threshold
        for chunk in chunks
    )