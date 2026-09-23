"""
ingest_documents.py — NyayaSaathi Legal Document Ingestion

Responsibilities:
- Read legal documents from data/legal_documents/
- Read judgments from data/judgments/
- Support TXT, PDF and JSON files
- Clean extracted text
- Split documents into legal-friendly chunks
- Attach metadata to every chunk
- Store chunks in ChromaDB through rag_service
"""

import json
import logging
import re
import sys
from pathlib import Path

import pymupdf


# ---------------------------------------------------------
# PROJECT PATH SETUP
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.config import settings
from app.services.rag_service import store_chunks


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

DATA_DIR = BACKEND_DIR / "data"

LEGAL_DOCS_DIR = DATA_DIR / "legal_documents"

JUDGMENTS_DIR = DATA_DIR / "judgments"

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".json",
}


# ---------------------------------------------------------
# LOGGING
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# TEXT CLEANING
# ---------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Clean extracted document text while preserving
    paragraph and section boundaries.
    """

    if not text:
        return ""

    # Normalize line endings.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove null characters.
    text = text.replace("\x00", "")

    # Replace tabs with spaces.
    text = text.replace("\t", " ")

    # Remove excessive spaces.
    text = re.sub(
        r"[ ]{2,}",
        " ",
        text,
    )

    # Remove excessive blank lines.
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ---------------------------------------------------------
# FILE READERS
# ---------------------------------------------------------

def read_txt_file(path: Path) -> str:
    """
    Read a UTF-8 text document.
    """

    return path.read_text(
        encoding="utf-8",
        errors="ignore",
    )


def read_pdf_file(path: Path) -> str:
    """
    Extract text from a PDF using PyMuPDF.
    """

    pages = []

    with pymupdf.open(path) as document:
        for page in document:
            page_text = page.get_text("text")

            if page_text:
                pages.append(page_text)

    return "\n\n".join(pages)


def _extract_json_text(data) -> str:
    """
    Recursively extract useful text from JSON data.
    """

    if data is None:
        return ""

    if isinstance(data, str):
        return data

    if isinstance(data, list):
        parts = []

        for item in data:
            extracted = _extract_json_text(item)

            if extracted:
                parts.append(extracted)

        return "\n\n".join(parts)

    if isinstance(data, dict):

        # Prefer common text fields first.
        preferred_fields = [
            "text",
            "content",
            "body",
            "judgment",
            "document",
            "description",
        ]

        parts = []

        for field in preferred_fields:
            if field in data:
                extracted = _extract_json_text(
                    data[field]
                )

                if extracted:
                    parts.append(extracted)

        # If useful text was found, use it.
        if parts:
            return "\n\n".join(parts)

        # Otherwise recursively inspect all values.
        for value in data.values():
            extracted = _extract_json_text(value)

            if extracted:
                parts.append(extracted)

        return "\n\n".join(parts)

    return str(data)


def read_json_file(path: Path) -> str:
    """
    Extract textual content from a JSON document.
    """

    with path.open(
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as file:
        data = json.load(file)

    return _extract_json_text(data)


def extract_text(path: Path) -> str:
    """
    Extract text based on file extension.
    """

    extension = path.suffix.lower()

    if extension == ".txt":
        return read_txt_file(path)

    if extension == ".pdf":
        return read_pdf_file(path)

    if extension == ".json":
        return read_json_file(path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# ---------------------------------------------------------
# CHUNKING
# ---------------------------------------------------------

SECTION_PATTERN = re.compile(
    r"(?im)^(?="
    r"(?:section|article|chapter|part|rule|schedule)"
    r"\s+[\w.-]+"
    r")"
)


def _split_large_text(
    text: str,
    max_chars: int = 1800,
    overlap_chars: int = 200,
) -> list[str]:
    """
    Split oversized text while preserving some overlap.
    """

    if len(text) <= max_chars:
        return [text]

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + max_chars,
            len(text),
        )

        # Try to stop at a paragraph boundary.
        if end < len(text):
            paragraph_break = text.rfind(
                "\n\n",
                start,
                end,
            )

            if (
                paragraph_break > start + 500
            ):
                end = paragraph_break

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        next_start = end - overlap_chars

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def chunk_by_sections(
    text: str,
    max_chars: int = 1800,
    overlap_chars: int = 200,
) -> list[str]:
    """
    Split legal documents primarily by legal section headings.

    If a section is too large, it is further divided
    into smaller overlapping chunks.
    """

    text = clean_text(text)

    if not text:
        return []

    sections = SECTION_PATTERN.split(text)

    sections = [
        section.strip()
        for section in sections
        if section.strip()
    ]

    # If no useful section split happened,
    # treat the whole document as one section.
    if not sections:
        sections = [text]

    final_chunks = []

    for section in sections:

        section_chunks = _split_large_text(
            section,
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )

        final_chunks.extend(
            section_chunks
        )

    return final_chunks


# ---------------------------------------------------------
# METADATA HELPERS
# ---------------------------------------------------------

def create_source_id(
    path: Path,
) -> str:
    """
    Create a stable ID from a filename.

    Example:
    Industrial Relations Code 2020.txt
    -> industrial_relations_code_2020
    """

    source_id = path.stem.lower()

    source_id = re.sub(
        r"[^a-z0-9]+",
        "_",
        source_id,
    )

    return source_id.strip("_")


def detect_source_name(
    text: str,
    path: Path,
) -> str:
    """
    Use the first meaningful line as source name.
    Falls back to the filename.
    """

    for line in text.splitlines():

        line = line.strip()

        if len(line) >= 4:
            return line[:250]

    return path.stem.replace(
        "_",
        " ",
    ).title()


def detect_section(
    chunk: str,
) -> str:
    """
    Try to detect the legal section heading
    from the beginning of a chunk.
    """

    lines = chunk.splitlines()

    for line in lines[:5]:

        stripped = line.strip()

        if re.match(
            r"(?i)^section\s+[\w.-]+",
            stripped,
        ):
            return stripped[:200]

        if re.match(
            r"(?i)^article\s+[\w.-]+",
            stripped,
        ):
            return stripped[:200]

        if re.match(
            r"(?i)^chapter\s+[\w.-]+",
            stripped,
        ):
            return stripped[:200]

    return ""


# ---------------------------------------------------------
# DOCUMENT INGESTION
# ---------------------------------------------------------

def ingest_file(
    path: Path,
    root_directory: Path,
    source_type: str,
) -> int:
    """
    Extract, chunk and store one document.

    Returns the number of stored chunks.
    """

    relative_path = path.relative_to(
        root_directory
    )

    # legal_documents/<category>/<file>
    # judgment files usually do not have categories.
    if source_type == "statute":

        if len(relative_path.parts) > 1:
            category = (
                relative_path.parts[0]
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )
        else:
            category = "general"

    else:
        category = "judgment"

    logger.info(
        "  Processing: %s (category: %s)",
        path.name,
        category,
    )

    try:
        raw_text = extract_text(
            path
        )

    except Exception as exc:
        logger.exception(
            "  Failed to extract '%s': %s",
            path.name,
            exc,
        )

        return 0

    cleaned_text = clean_text(
        raw_text
    )

    if not cleaned_text:
        logger.warning(
            "  Skipping empty document: %s",
            path.name,
        )

        return 0

    chunks = chunk_by_sections(
        cleaned_text
    )

    if not chunks:
        logger.warning(
            "  No chunks created for: %s",
            path.name,
        )

        return 0

    logger.info(
        "  → %s chunks",
        len(chunks),
    )

    source_id_base = create_source_id(
        path
    )

    source_name = detect_source_name(
        cleaned_text,
        path,
    )

    structured_chunks = []

    for index, chunk_text in enumerate(
        chunks
    ):

        chunk_id = (
            f"{source_id_base}_chunk_{index + 1}"
        )

        section = detect_section(
            chunk_text
        )

        metadata = {
            "source_id": chunk_id,
            "source_name": source_name,
            "source_type": source_type,
            "category": category,
            "filename": path.name,
            "chunk_index": index + 1,
        }

        if section:
            metadata["section"] = section

        structured_chunks.append(
            {
                "id": chunk_id,
                "text": chunk_text,
                "metadata": metadata,
            }
        )

    # IMPORTANT:
    # rag_service.store_chunks() creates embeddings
    # and stores everything inside ChromaDB.
    store_chunks(
        structured_chunks
    )

    return len(
        structured_chunks
    )


# ---------------------------------------------------------
# DIRECTORY INGESTION
# ---------------------------------------------------------

def ingest_directory(
    directory: Path,
    source_type: str,
) -> tuple[int, int]:
    """
    Recursively ingest supported documents.

    Returns:
        files_processed,
        total_chunks
    """

    if not directory.exists():

        logger.warning(
            "Directory does not exist: %s",
            directory,
        )

        return 0, 0

    files = sorted(
        path
        for path in directory.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    )

    if not files:

        logger.warning(
            "No supported documents found in: %s",
            directory,
        )

        return 0, 0

    files_processed = 0
    total_chunks = 0

    for path in files:

        chunk_count = ingest_file(
            path=path,
            root_directory=directory,
            source_type=source_type,
        )

        if chunk_count > 0:
            files_processed += 1
            total_chunks += chunk_count

    return (
        files_processed,
        total_chunks,
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    """
    Run the complete NyayaSaathi ingestion pipeline.
    """

    logger.info(
        "=" * 60
    )

    logger.info(
        "NyayaSaathi — Legal Document Ingestion"
    )

    logger.info(
        "=" * 60
    )

    logger.info(
        "ChromaDB path: %s",
        settings.CHROMA_PATH,
    )

    logger.info(
        "Collection: %s",
        settings.CHROMA_COLLECTION,
    )

    logger.info("")

    # -----------------------------------------------------
    # LEGAL DOCUMENTS
    # -----------------------------------------------------

    logger.info(
        "[1/2] Ingesting legal documents from: data/legal_documents/"
    )

    legal_files, legal_chunks = ingest_directory(
        LEGAL_DOCS_DIR,
        source_type="statute",
    )

    logger.info("")

    # -----------------------------------------------------
    # JUDGMENTS
    # -----------------------------------------------------

    logger.info(
        "[2/2] Ingesting judgments from: data/judgments/"
    )

    judgment_files, judgment_chunks = ingest_directory(
        JUDGMENTS_DIR,
        source_type="judgment",
    )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    total_files = (
        legal_files
        + judgment_files
    )

    total_chunks = (
        legal_chunks
        + judgment_chunks
    )

    logger.info("")
    logger.info(
        "=" * 60
    )

    logger.info(
        "Ingestion complete."
    )

    logger.info(
        "Files processed: %s",
        total_files,
    )

    logger.info(
        "Legal files: %s",
        legal_files,
    )

    logger.info(
        "Judgment files: %s",
        judgment_files,
    )

    logger.info(
        "Chunks stored/updated: %s",
        total_chunks,
    )

    logger.info(
        "=" * 60
    )


# ---------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()