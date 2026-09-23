"""
text_processing.py — Text cleaning and chunking utilities.
"""

import re


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize text."""
    text = re.sub(r"\n{3,}", "\n\n", text)     # Collapse 3+ newlines → 2
    text = re.sub(r"[ \t]{2,}", " ", text)       # Collapse multiple spaces
    text = text.strip()
    return text


def split_into_paragraphs(text: str) -> list[dict]:
    """
    Split text into paragraphs, assigning each an ID.

    Returns a list of dicts: {"id": "para1", "number": "Paragraph 1", "text": "..."}
    """
    # Split on double newlines (typical paragraph boundary)
    raw_paras = re.split(r"\n\s*\n", text)

    paragraphs = []
    para_counter = 1
    for raw in raw_paras:
        cleaned = raw.strip()
        if len(cleaned) < 30:
            continue  # Skip very short fragments

        para_id = f"para{para_counter}"
        paragraphs.append(
            {
                "id": para_id,
                "number": f"Paragraph {para_counter}",
                "text": cleaned,
            }
        )
        para_counter += 1

    return paragraphs


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    Args:
        text:       Input text.
        chunk_size: Target words per chunk.
        overlap:    Overlapping words between chunks.

    Returns:
        List of text chunk strings.
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # slide with overlap

    return [c for c in chunks if len(c.strip()) > 50]


def chunk_by_sections(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """
    Attempt section-aware chunking.

    Splits first on 'Section N' or 'CHAPTER N' boundaries.
    Falls back to word-based chunking if no sections found.
    """
    section_pattern = re.compile(
        r"(?=\n(?:Section|SECTION|Sec\.|Chapter|CHAPTER|Article|ARTICLE)\s+\d+)",
        re.IGNORECASE,
    )
    sections = section_pattern.split(text)

    if len(sections) <= 1:
        # No section boundaries found — use word-based chunking
        return chunk_text(text, chunk_size, overlap)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        words = section.split()
        if len(words) <= chunk_size:
            chunks.append(section)
        else:
            # Section is too large — sub-chunk it
            chunks.extend(chunk_text(section, chunk_size, overlap))

    return [c for c in chunks if len(c.strip()) > 50]
