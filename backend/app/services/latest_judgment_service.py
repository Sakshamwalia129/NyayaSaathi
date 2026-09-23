"""
latest_judgment_service.py

Supreme Court of India Latest Judgments updater.

Responsibilities:
- Fetch latest judgments from the official Supreme Court website
- Extract official metadata
- Resolve SCI view-pdf URLs to the official sci-get-pdf endpoint
- Download judgment PDFs safely
- Prevent duplicate storage
- Retry previously failed judgments automatically
- Extract judgment text
- Reuse NyayaSaathi's existing Judgment Simplifier pipeline
- Store AI headline and summary in PostgreSQL

V1: Supreme Court of India only.
"""

import hashlib
import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.database_models import LatestJudgment
from app.services import llm_service
from app.utils.pdf_processing import extract_text_from_pdf
from app.utils.text_processing import clean_text, split_into_paragraphs


logger = logging.getLogger(__name__)


# =============================================================
# CONFIGURATION
# =============================================================

SCI_BASE_URL = "https://www.sci.gov.in"
SCI_LATEST_URL = "https://www.sci.gov.in/"

ALLOWED_DOMAINS = {
    "sci.gov.in",
    "www.sci.gov.in",
    "api.sci.gov.in",
}

REQUEST_TIMEOUT = 30
MAX_PDF_SIZE = 25 * 1024 * 1024  # 25 MB

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
}


# =============================================================
# URL VALIDATION
# =============================================================

def _is_allowed_url(url: str) -> bool:
    """
    Accept only HTTPS URLs belonging to approved
    Supreme Court of India domains.
    """

    try:
        parsed = urlparse(url)

        return (
            parsed.scheme == "https"
            and parsed.hostname in ALLOWED_DOMAINS
        )

    except Exception:
        return False


# =============================================================
# GENERAL UTILITIES
# =============================================================

def _normalize_text(value: str | None) -> str:
    """
    Collapse repeated whitespace and trim text.
    """

    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def _sha256(data: bytes) -> str:
    """
    Calculate SHA-256 hash for PDF bytes.
    """

    return hashlib.sha256(data).hexdigest()


def _build_official_id(
    case_title: str,
    case_number: str | None,
    diary_number: str | None,
    pdf_url: str,
) -> str:
    """
    Build a deterministic unique ID for a judgment.
    """

    identity = "|".join(
        [
            _normalize_text(case_title).lower(),
            _normalize_text(case_number).lower(),
            _normalize_text(diary_number).lower(),
            pdf_url.strip().lower(),
        ]
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


# =============================================================
# DATE PARSING
# =============================================================

def _parse_date(value: str | None) -> datetime | None:
    """
    Parse common date/time formats used by SCI.
    """

    if not value:
        return None

    value = _normalize_text(value)

    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M",
        "%d-%b-%Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            )

        except ValueError:
            continue

    return None


# =============================================================
# FETCH SCI HOMEPAGE
# =============================================================

def fetch_latest_listing() -> str:
    """
    Fetch the Supreme Court of India homepage.

    The homepage contains the Latest Judgements section.
    """

    response = requests.get(
        SCI_LATEST_URL,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.text


# =============================================================
# DISCOVER LATEST JUDGMENTS
# =============================================================

def discover_judgments(
    html: str,
) -> list[dict]:
    """
    Discover judgments from the official SCI
    Latest Judgements section.

    Official link format:

    /view-pdf/?diary_no=...
    &type=j
    &order_date=...
    &from=latest_judgements_order
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    discovered = []
    seen_urls = set()

    for link in soup.find_all(
        "a",
        href=True,
    ):
        href = link.get(
            "href",
            "",
        ).strip()

        # Only Latest Judgment viewer links.
        # This excludes notices, circulars and other homepage PDFs.
        if "view-pdf/" not in href:
            continue

        if "type=j" not in href:
            continue

        if "from=latest_judgements_order" not in href:
            continue

        official_url = urljoin(
            SCI_BASE_URL,
            href,
        )

        if not _is_allowed_url(
            official_url
        ):
            continue

        if official_url in seen_urls:
            continue

        seen_urls.add(
            official_url
        )

        # -----------------------------------------------------
        # Complete visible metadata
        # -----------------------------------------------------

        full_text = _normalize_text(
            link.get_text(
                " ",
                strip=True,
            )
        )

        # -----------------------------------------------------
        # Uploaded timestamp
        # -----------------------------------------------------

        upload_match = re.search(
            r"Uploaded\s+On\s+"
            r"(\d{1,2}-\d{1,2}-\d{4}"
            r"\s+\d{1,2}:\d{2}:\d{2})",
            full_text,
            flags=re.IGNORECASE,
        )

        uploaded_at = None

        if upload_match:
            uploaded_at = _parse_date(
                upload_match.group(1)
            )

        # -----------------------------------------------------
        # Remove uploaded timestamp from metadata text
        # -----------------------------------------------------

        metadata_text = re.sub(
            r"\(?\s*Uploaded\s+On\s+"
            r"\d{1,2}-\d{1,2}-\d{4}"
            r"\s+\d{1,2}:\d{2}:\d{2}\s*\)?",
            "",
            full_text,
            flags=re.IGNORECASE,
        )

        metadata_text = _normalize_text(
            metadata_text
        )

        # -----------------------------------------------------
        # Diary number
        # -----------------------------------------------------

        diary_match = re.search(
            r"Diary\s+Number\s+"
            r"(\d+)\s*/\s*(\d{4})",
            metadata_text,
            flags=re.IGNORECASE,
        )

        diary_number = None

        if diary_match:
            diary_number = (
                f"{diary_match.group(1)}/"
                f"{diary_match.group(2)}"
            )

        # -----------------------------------------------------
        # Judgment date
        # -----------------------------------------------------

        date_match = re.search(
            r"\b("
            r"\d{1,2}-[A-Za-z]{3}-\d{4}"
            r")\b",
            metadata_text,
        )

        judgment_date = None

        if date_match:
            judgment_date = _parse_date(
                date_match.group(1)
            )

        # -----------------------------------------------------
        # Case number
        # -----------------------------------------------------

        case_number = None

        case_match = re.search(
            r"-\s*"
            r"(.+?\bNo\.?\s*[\w./()\-]+)"
            r"\s*-\s*Diary\s+Number",
            metadata_text,
            flags=re.IGNORECASE,
        )

        if case_match:
            case_number = _normalize_text(
                case_match.group(1)
            )

        # -----------------------------------------------------
        # Case title
        # -----------------------------------------------------

        case_title = metadata_text

        if case_number:
            marker = f" - {case_number}"

            if marker in case_title:
                case_title = case_title.split(
                    marker,
                    1,
                )[0]

        else:
            case_title = re.split(
                r"\s+-\s+Diary\s+Number",
                case_title,
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]

        case_title = re.sub(
            r"\s*-\s*"
            r"\d{1,2}-[A-Za-z]{3}-\d{4}"
            r"\s*$",
            "",
            case_title,
        )

        case_title = _normalize_text(
            case_title
        )

        if not case_title:
            case_title = (
                "Supreme Court Judgment"
            )

        # -----------------------------------------------------
        # Stable unique ID
        # -----------------------------------------------------

        official_id = _build_official_id(
            case_title=case_title,
            case_number=case_number,
            diary_number=diary_number,
            pdf_url=official_url,
        )

        discovered.append(
            {
                "official_id": official_id,
                "case_title": case_title,
                "case_number": case_number,
                "diary_number": diary_number,
                "judgment_date": judgment_date,
                "uploaded_at": uploaded_at,
                "official_pdf_url": official_url,
                "source_url": SCI_LATEST_URL,
                "metadata_json": {
                    "raw_text": full_text,
                    "source": (
                        "Supreme Court of India"
                    ),
                },
            }
        )

    # Latest uploaded judgment first.
    discovered.sort(
        key=lambda item: (
            item["uploaded_at"]
            or datetime.min
        ),
        reverse=True,
    )

    logger.info(
        "SCI discovery found %s latest judgments.",
        len(discovered),
    )

    return discovered


# =============================================================
# RESOLVE SCI PDF DOWNLOAD URL
# =============================================================

def _resolve_pdf_url(
    viewer_url: str,
) -> str:
    """
    Convert SCI's public /view-pdf/ URL into the
    /sci-get-pdf/ endpoint used by SCI's own viewer.
    """

    if not _is_allowed_url(
        viewer_url
    ):
        raise ValueError(
            "Rejected non-official Supreme Court URL."
        )

    parsed = urlparse(
        viewer_url
    )

    if parsed.path.rstrip("/") == "/view-pdf":

        resolved_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"/sci-get-pdf/"
        )

        if parsed.query:
            resolved_url += (
                f"?{parsed.query}"
            )

    else:
        resolved_url = viewer_url

    if not _is_allowed_url(
        resolved_url
    ):
        raise ValueError(
            "Resolved Supreme Court PDF URL "
            "is not approved."
        )

    return resolved_url


# =============================================================
# DOWNLOAD OFFICIAL JUDGMENT PDF
# =============================================================

def download_pdf(
    pdf_url: str,
) -> bytes:
    """
    Download an official Supreme Court judgment PDF.

    SCI Latest Judgment links point to /view-pdf/.
    The official viewer loads the underlying document using
    /sci-get-pdf/ with the same query parameters.
    """

    download_url = _resolve_pdf_url(
        pdf_url
    )

    response = requests.get(
        download_url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        stream=True,
        allow_redirects=True,
    )

    response.raise_for_status()

    # ---------------------------------------------------------
    # Redirect safety
    # ---------------------------------------------------------

    if not _is_allowed_url(
        response.url
    ):
        raise ValueError(
            "Supreme Court PDF request redirected "
            "to a non-approved domain."
        )

    content_type = (
        response.headers
        .get(
            "Content-Type",
            "",
        )
        .lower()
    )

    data = bytearray()

    for chunk in response.iter_content(
        chunk_size=1024 * 128,
    ):
        if not chunk:
            continue

        data.extend(
            chunk
        )

        if len(data) > MAX_PDF_SIZE:
            raise ValueError(
                "Judgment PDF exceeds "
                "the 25 MB limit."
            )

    pdf_bytes = bytes(
        data
    )

    if not pdf_bytes:
        raise ValueError(
            "Downloaded judgment PDF is empty."
        )

    # ---------------------------------------------------------
    # Strict PDF validation
    # ---------------------------------------------------------

    if not pdf_bytes.startswith(
        b"%PDF"
    ):
        raise ValueError(
            "SCI sci-get-pdf endpoint did not "
            "return a valid PDF. "
            f"Content-Type: {content_type}"
        )

    return pdf_bytes


# =============================================================
# AI CONTENT GENERATION
# =============================================================

def generate_ai_content(
    pdf_bytes: bytes,
) -> dict:
    """
    Reuse NyayaSaathi's existing Judgment Simplifier pipeline.

    AI analysis is based only on text extracted from the
    official Supreme Court judgment.
    """

    raw_text = extract_text_from_pdf(
        pdf_bytes
    )

    text = clean_text(
        raw_text
    )

    paragraphs = split_into_paragraphs(
        text
    )

    if not paragraphs:
        raise ValueError(
            "No usable judgment paragraphs "
            "were extracted."
        )

    analysis = (
        llm_service
        .generate_judgment_response(
            judgment_text=text,
            paragraphs=paragraphs,
        )
    )

    headline = _normalize_text(
        analysis.get(
            "caseTitle"
        )
    )

    if not headline:
        headline = (
            "Supreme Court Judgment"
        )

    summary = _normalize_text(
        analysis.get(
            "brief"
        )
    )

    if not summary:
        summary = _normalize_text(
            analysis.get(
                "decision"
            )
        )

    if not summary:
        summary = (
            "AI summary could not be generated."
        )

    return {
        "headline": headline,
        "summary": summary,
    }


# =============================================================
# PROCESS ONE JUDGMENT
# =============================================================

def process_judgment(
    db: Session,
    metadata: dict,
) -> dict:
    """
    Download, analyze and store one judgment.

    Behaviour:
    - processed record -> duplicate / skip
    - pending record   -> duplicate / skip
    - failed record    -> retry processing
    - new record       -> create and process
    """

    official_id = metadata[
        "official_id"
    ]

    # ---------------------------------------------------------
    # Check whether this judgment already exists
    # ---------------------------------------------------------

    existing = (
        db.query(
            LatestJudgment
        )
        .filter(
            LatestJudgment.official_id
            == official_id
        )
        .first()
    )

    # ---------------------------------------------------------
    # Existing processed/pending judgment -> skip
    # ---------------------------------------------------------

    if (
        existing
        and existing.processing_status
        != "failed"
    ):
        return {
            "status": "duplicate",
            "id": existing.id,
            "official_id": official_id,
        }

    # ---------------------------------------------------------
    # Existing failed judgment -> reuse same DB row and retry
    # ---------------------------------------------------------

    if existing:
        record = existing

        logger.info(
            "Retrying previously failed SCI judgment %s "
            "(database id=%s).",
            official_id,
            record.id,
        )

        # Refresh official metadata in case SCI metadata changed.
        record.case_title = metadata[
            "case_title"
        ]
        record.case_number = metadata.get(
            "case_number"
        )
        record.diary_number = metadata.get(
            "diary_number"
        )
        record.judgment_date = metadata.get(
            "judgment_date"
        )
        record.uploaded_at = metadata.get(
            "uploaded_at"
        )
        record.official_pdf_url = metadata[
            "official_pdf_url"
        ]
        record.source_url = metadata.get(
            "source_url"
        )
        record.metadata_json = metadata.get(
            "metadata_json"
        )

        record.processing_status = (
            "pending"
        )
        record.processing_error = (
            None
        )

        db.commit()
        db.refresh(
            record
        )

    # ---------------------------------------------------------
    # New judgment -> create pending record
    # ---------------------------------------------------------

    else:
        record = LatestJudgment(
            official_id=official_id,
            case_title=metadata[
                "case_title"
            ],
            case_number=metadata.get(
                "case_number"
            ),
            diary_number=metadata.get(
                "diary_number"
            ),
            judgment_date=metadata.get(
                "judgment_date"
            ),
            uploaded_at=metadata.get(
                "uploaded_at"
            ),
            official_pdf_url=metadata[
                "official_pdf_url"
            ],
            source_url=metadata.get(
                "source_url"
            ),
            metadata_json=metadata.get(
                "metadata_json"
            ),
            processing_status="pending",
        )

        db.add(
            record
        )

        db.commit()
        db.refresh(
            record
        )

    try:

        # -----------------------------------------------------
        # Download official PDF
        # -----------------------------------------------------

        pdf_bytes = download_pdf(
            record.official_pdf_url
        )

        # -----------------------------------------------------
        # Calculate document hash
        # -----------------------------------------------------

        pdf_hash = _sha256(
            pdf_bytes
        )

        # -----------------------------------------------------
        # Duplicate protection using actual PDF bytes
        # -----------------------------------------------------

        duplicate_pdf = (
            db.query(
                LatestJudgment
            )
            .filter(
                LatestJudgment.pdf_sha256
                == pdf_hash,
                LatestJudgment.id
                != record.id,
            )
            .first()
        )

        if duplicate_pdf:

            # If this was a retried failed record, it is safe to
            # remove it because the same official PDF already
            # exists in another database row.
            db.delete(
                record
            )

            db.commit()

            return {
                "status": "duplicate",
                "id": duplicate_pdf.id,
                "official_id": (
                    duplicate_pdf.official_id
                ),
            }

        record.pdf_sha256 = (
            pdf_hash
        )

        # -----------------------------------------------------
        # Generate grounded AI headline + summary
        # -----------------------------------------------------

        ai_content = generate_ai_content(
            pdf_bytes
        )

        record.ai_headline = (
            ai_content[
                "headline"
            ]
        )

        record.ai_summary = (
            ai_content[
                "summary"
            ]
        )

        record.processing_status = (
            "processed"
        )

        record.processing_error = (
            None
        )

        db.commit()
        db.refresh(
            record
        )

        logger.info(
            "Successfully processed SCI judgment %s "
            "(database id=%s).",
            official_id,
            record.id,
        )

        return {
            "status": "processed",
            "id": record.id,
            "official_id": official_id,
        }

    except Exception as exc:

        logger.exception(
            "Failed processing SCI judgment %s",
            official_id,
        )

        # Roll back any failed transaction state first.
        try:
            db.rollback()
        except Exception:
            pass

        # Re-fetch the row after rollback so failure status can
        # still be stored reliably.
        failed_record = (
            db.query(
                LatestJudgment
            )
            .filter(
                LatestJudgment.official_id
                == official_id
            )
            .first()
        )

        if failed_record:
            failed_record.processing_status = (
                "failed"
            )

            failed_record.processing_error = (
                str(exc)[:2000]
            )

            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception(
                    "Could not save failed status for SCI "
                    "judgment %s.",
                    official_id,
                )

        return {
            "status": "failed",
            "id": (
                failed_record.id
                if failed_record
                else None
            ),
            "official_id": official_id,
            "error": str(exc),
        }


# =============================================================
# MAIN UPDATE FUNCTION
# =============================================================

def update_latest_judgments(
    db: Session,
    limit: int = 5,
) -> dict:
    """
    Discover and process Supreme Court judgments.

    Safe to run repeatedly.

    Behaviour:
    - processed judgments are skipped as duplicates
    - pending judgments are skipped
    - failed judgments are automatically retried
    - newly discovered judgments are processed normally

    Duplicate protection:
    1. Stable official ID
    2. SHA-256 hash of actual judgment PDF

    The limit applies to actual processing attempts,
    including retries of previously failed judgments.
    """

    html = fetch_latest_listing()

    candidates = discover_judgments(
        html
    )

    results = []

    attempted = 0
    retried = 0

    for metadata in candidates:

        existing = (
            db.query(
                LatestJudgment
            )
            .filter(
                LatestJudgment.official_id
                == metadata[
                    "official_id"
                ]
            )
            .first()
        )

        # -----------------------------------------------------
        # Already successfully processed or currently pending
        # -----------------------------------------------------

        if (
            existing
            and existing.processing_status
            != "failed"
        ):

            results.append(
                {
                    "status": "duplicate",
                    "id": existing.id,
                    "official_id": (
                        existing.official_id
                    ),
                }
            )

            continue

        # -----------------------------------------------------
        # Limit applies to new processing + failed retries
        # -----------------------------------------------------

        if attempted >= limit:
            break

        is_retry = bool(
            existing
            and existing.processing_status
            == "failed"
        )

        if is_retry:
            retried += 1

        result = process_judgment(
            db,
            metadata,
        )

        if is_retry:
            result["retried"] = True

        results.append(
            result
        )

        attempted += 1

    return {
        "success": True,

        "discovered": len(
            candidates
        ),

        # Keep this key for compatibility with existing logs/API.
        "new_attempted": attempted,

        # New field showing how many attempts were retries.
        "retried": retried,

        "processed": sum(
            1
            for item in results
            if item["status"]
            == "processed"
        ),

        "duplicates": sum(
            1
            for item in results
            if item["status"]
            == "duplicate"
        ),

        "failed": sum(
            1
            for item in results
            if item["status"]
            == "failed"
        ),

        "results": results,
    }