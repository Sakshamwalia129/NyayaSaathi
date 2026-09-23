"""
legal_update_service.py

Automated Legal Knowledge Update Pipeline for NyayaSaathi.

Responsibilities:
    official legal source
        → validate trusted domain
        → download document
        → calculate document fingerprint
        → detect new / unchanged / updated document
        → extract text
        → clean + chunk
        → store/update ChromaDB

Only trusted official Indian government sources are accepted.
"""

import hashlib
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.services.rag_service import store_chunks
from app.utils.pdf_processing import extract_text_from_bytes
from app.utils.text_processing import clean_text, chunk_by_sections


logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

UPDATE_STATE_FILE = Path(
    "data/legal_update_state.json"
)

DOWNLOAD_TIMEOUT_SECONDS = 30

MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


TRUSTED_GOVERNMENT_DOMAINS = {
    "indiacode.nic.in",
    "labour.gov.in",
    "mohua.gov.in",
    "legislative.gov.in",
    "egazette.nic.in",
}


# ---------------------------------------------------------
# Trusted source validation
# ---------------------------------------------------------

def is_trusted_source(url: str) -> bool:
    """
    Check whether a URL belongs to an approved official
    Indian government domain.
    """

    try:
        parsed = urlparse(url)

        if parsed.scheme != "https":
            return False

        hostname = (
            parsed.hostname or ""
        ).lower()

        return any(
            hostname == domain
            or hostname.endswith("." + domain)
            for domain in TRUSTED_GOVERNMENT_DOMAINS
        )

    except Exception:
        return False


# ---------------------------------------------------------
# State management
# ---------------------------------------------------------

def _load_update_state() -> dict:
    """
    Load fingerprints of previously processed documents.
    """

    if not UPDATE_STATE_FILE.exists():
        return {}

    try:
        with open(
            UPDATE_STATE_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except Exception as exc:
        logger.warning(
            "Could not read legal update state: %s",
            exc,
        )
        return {}


def _save_update_state(state: dict) -> None:
    """
    Save legal document fingerprints.
    """

    UPDATE_STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        UPDATE_STATE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            state,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# Document fingerprint
# ---------------------------------------------------------

def _calculate_hash(
    file_bytes: bytes,
) -> str:
    """
    SHA-256 fingerprint used to detect document changes.
    """

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# ---------------------------------------------------------
# Download
# ---------------------------------------------------------

def _download_document(
    url: str,
) -> tuple[bytes, str]:
    """
    Download an official legal document.

    Returns:
        (file_bytes, filename)
    """

    if not is_trusted_source(url):
        raise ValueError(
            "Source rejected. Only approved official "
            "government HTTPS sources are allowed."
        )

    request = Request(
        url,
        headers={
            "User-Agent": (
                "NyayaSaathi-LegalUpdater/1.0"
            )
        },
    )

    try:
        with urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:

            content_length = response.headers.get(
                "Content-Length"
            )

            if content_length:
                try:
                    declared_size = int(
                        content_length
                    )

                    if (
                        declared_size
                        > MAX_DOCUMENT_SIZE_BYTES
                    ):
                        raise ValueError(
                            "Official document is larger "
                            "than the allowed update size."
                        )

                except ValueError as exc:
                    if (
                        "larger than"
                        in str(exc)
                    ):
                        raise

            file_bytes = response.read(
                MAX_DOCUMENT_SIZE_BYTES + 1
            )

            if (
                len(file_bytes)
                > MAX_DOCUMENT_SIZE_BYTES
            ):
                raise ValueError(
                    "Official document is larger "
                    "than the allowed update size."
                )

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            f"Could not download official legal document: {exc}"
        ) from exc

    if not file_bytes:
        raise ValueError(
            "Downloaded legal document is empty."
        )

    filename = Path(
        urlparse(url).path
    ).name

    if not filename:
        filename = "official_document.pdf"

    return file_bytes, filename


# ---------------------------------------------------------
# Text extraction
# ---------------------------------------------------------

def _extract_document_text(
    file_bytes: bytes,
    filename: str,
) -> str:
    """
    Extract and clean text from the downloaded document.
    """

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in {
        ".pdf",
        ".txt",
    }:
        raise ValueError(
            "Updater currently supports official "
            "PDF and TXT documents only."
        )

    text = extract_text_from_bytes(
        file_bytes,
        filename,
    )

    text = clean_text(
        text
    )

    if len(text) < 100:
        raise ValueError(
            "The downloaded document did not contain "
            "enough extractable legal text."
        )

    return text


# ---------------------------------------------------------
# Chunk preparation
# ---------------------------------------------------------

def _prepare_chunks(
    text: str,
    document_id: str,
    source_name: str,
    category: str,
    source_url: str,
    version_hash: str,
) -> list[dict]:
    """
    Convert official legal text into structured chunks
    compatible with NyayaSaathi's ChromaDB ingestion.
    """

    text_chunks = chunk_by_sections(
        text,
        chunk_size=400,
        overlap=50,
    )

    structured_chunks = []

    for index, chunk in enumerate(
        text_chunks
    ):
        structured_chunks.append(
            {
                "id": (
                    f"auto_{document_id}_"
                    f"chunk_{index}"
                ),
                "text": chunk,
                "metadata": {
                    "source_name": source_name,
                    "category": category,
                    "source_url": source_url,
                    "document_id": document_id,
                    "version_hash": version_hash,
                    "update_source": "official",
                    "ingestion_mode": "automatic",
                    "chunk_index": index,
                },
            }
        )

    return structured_chunks


# ---------------------------------------------------------
# Main update pipeline
# ---------------------------------------------------------

def update_legal_document(
    *,
    document_id: str,
    source_name: str,
    category: str,
    source_url: str,
) -> dict:
    """
    Check and update one official legal document.

    Possible statuses:
        added
        updated
        unchanged
        failed
    """

    document_id = document_id.strip()
    source_name = source_name.strip()
    category = category.strip().lower()

    if not document_id:
        raise ValueError(
            "document_id is required."
        )

    if not source_name:
        raise ValueError(
            "source_name is required."
        )

    if not category:
        raise ValueError(
            "category is required."
        )

    if not is_trusted_source(
        source_url
    ):
        raise ValueError(
            "The supplied URL is not an approved "
            "official government source."
        )

    logger.info(
        "Checking legal update: %s",
        source_name,
    )

    # -----------------------------------------------------
    # Download latest official version
    # -----------------------------------------------------

    file_bytes, filename = (
        _download_document(
            source_url
        )
    )

    latest_hash = _calculate_hash(
        file_bytes
    )

    # -----------------------------------------------------
    # Compare with previous version
    # -----------------------------------------------------

    state = _load_update_state()

    previous = state.get(
        document_id
    )

    previous_hash = None

    if previous:
        previous_hash = previous.get(
            "version_hash"
        )

    if (
        previous_hash
        and previous_hash == latest_hash
    ):
        logger.info(
            "No legal update detected: %s",
            source_name,
        )

        return {
            "success": True,
            "status": "unchanged",
            "documentId": document_id,
            "sourceName": source_name,
            "message": (
                "No change detected in the "
                "official document."
            ),
        }

    # -----------------------------------------------------
    # Extract latest text
    # -----------------------------------------------------

    text = _extract_document_text(
        file_bytes,
        filename,
    )

    # -----------------------------------------------------
    # Prepare vector chunks
    # -----------------------------------------------------

    chunks = _prepare_chunks(
        text=text,
        document_id=document_id,
        source_name=source_name,
        category=category,
        source_url=source_url,
        version_hash=latest_hash,
    )

    if not chunks:
        raise ValueError(
            "No usable chunks could be generated "
            "from the official document."
        )

    # -----------------------------------------------------
    # Store/update ChromaDB
    # -----------------------------------------------------

    store_chunks(
        chunks
    )

    status = (
        "updated"
        if previous
        else "added"
    )

    # IMPORTANT:
    # State is saved only after successful vector ingestion.
    state[document_id] = {
        "source_name": source_name,
        "category": category,
        "source_url": source_url,
        "version_hash": latest_hash,
        "filename": filename,
        "chunk_count": len(chunks),
    }

    _save_update_state(
        state
    )

    logger.info(
        "Legal document %s: %s (%s chunks)",
        status,
        source_name,
        len(chunks),
    )

    return {
        "success": True,
        "status": status,
        "documentId": document_id,
        "sourceName": source_name,
        "chunksStored": len(chunks),
        "message": (
            f"Official legal document successfully "
            f"{status}."
        ),
    }


# ---------------------------------------------------------
# Batch updater
# ---------------------------------------------------------

def update_legal_sources(
    sources: list[dict],
) -> dict:
    """
    Run the update pipeline for multiple official sources.

    One failed source does not stop the remaining sources.
    """

    results = []

    for source in sources:

        try:
            result = update_legal_document(
                document_id=source[
                    "document_id"
                ],
                source_name=source[
                    "source_name"
                ],
                category=source[
                    "category"
                ],
                source_url=source[
                    "source_url"
                ],
            )

        except Exception as exc:
            logger.exception(
                "Legal update failed for %s",
                source.get(
                    "source_name",
                    "Unknown source",
                ),
            )

            result = {
                "success": False,
                "status": "failed",
                "documentId": source.get(
                    "document_id"
                ),
                "sourceName": source.get(
                    "source_name"
                ),
                "message": str(exc),
            }

        results.append(
            result
        )

    return {
        "success": all(
            result.get("success", False)
            for result in results
        ),
        "total": len(results),
        "results": results,
    }