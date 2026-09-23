"""
pdf_processing.py — PDF text extraction using PyMuPDF (fitz).

Handles text-based PDFs only (no OCR).
Returns extracted text and a list of paragraph dicts.
"""

import re
import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file (given as bytes).

    Returns plain text, or raises ValueError if no text is extractable.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not open PDF: {e}")

    pages_text = []
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages_text.append(text)

    doc.close()

    if not pages_text:
        raise ValueError(
            "Unable to extract readable text from this PDF. "
            "Please upload a text-based (non-scanned) judgment."
        )

    return "\n".join(pages_text)


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from either PDF or TXT bytes.
    Dispatches based on filename extension.
    """
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lower.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1")
    else:
        raise ValueError(f"Unsupported file type: {filename}")
