"""
citation_service.py — Validates that cited sources actually exist in the retrieved context.

This is one of NyayaSaathi's key responsible-AI features.
The LLM must not be allowed to invent citations.
"""

import logging
import re

logger = logging.getLogger(__name__)


def validate_provisions(
    provisions: list[dict],
    retrieved_chunks: list[dict],
) -> list[dict]:
    """
    Verify each LLM-generated legal provision against retrieved context.

    A provision is verified only when:
    1. Its source matches a retrieved legal source, AND
    2. Its section exists in the retrieved text.

    If no section number can be extracted, meaningful text overlap
    is used as a fallback.
    """

    retrieved_sources = [
        c.get("metadata", {}).get("source_name", "").strip().lower()
        for c in retrieved_chunks
    ]

    retrieved_texts = [
        c.get("text", "").lower()
        for c in retrieved_chunks
    ]

    all_retrieved_text = " ".join(retrieved_texts)

    validated = []

    for provision in provisions:
        source = provision.get("source", "").strip().lower()
        section = provision.get("section", "").strip()
        original_text = provision.get("originalText", "").strip()

        source_in_context = any(
            source == retrieved_source
            or source in retrieved_source
            or retrieved_source in source
            for retrieved_source in retrieved_sources
            if retrieved_source and source
        )

        section_match = re.search(
            r"(?:section|sec\.?)\s*(\d+[a-zA-Z]?)",
            section,
            re.IGNORECASE,
        )

        section_in_context = False

        if section_match:
            section_number = re.escape(section_match.group(1))

            section_pattern = re.compile(
                rf"\b(?:section|sec\.?)\s*{section_number}\b",
                re.IGNORECASE,
            )

            section_in_context = bool(
                section_pattern.search(all_retrieved_text)
            )

        text_overlap = False

        if original_text:
            words = {
                word.lower()
                for word in re.findall(r"\b[a-zA-Z]{5,}\b", original_text)
            }

            if words:
                matching_words = {
                    word
                    for word in words
                    if word in all_retrieved_text
                }

                overlap_ratio = len(matching_words) / len(words)
                text_overlap = overlap_ratio >= 0.40

        if section_match:
            verified = source_in_context and section_in_context
        else:
            verified = source_in_context and text_overlap

        if not verified:
            logger.warning(
                "Citation verification failed: %s / %s "
                "(source_match=%s, section_match=%s, text_overlap=%s)",
                provision.get("source"),
                provision.get("section"),
                source_in_context,
                section_in_context,
                text_overlap,
            )

        validated.append(
            {
                **provision,
                "_verified": verified,
            }
        )

    return validated

def validate_judgment_paragraphs(
    paragraphs: list[dict],
    extracted_paragraphs: list[dict],
) -> list[dict]:
    """
    Validate paragraph citations returned by the LLM.

    Security / grounding rule:
    - The LLM may choose a paragraph ID.
    - The LLM is NOT trusted to provide the paragraph text.
    - If the ID exists in the extracted judgment, the exact original
      paragraph number and text are restored from the uploaded document.
    - Invalid paragraph IDs are removed.
    """

    paragraph_map = {
        paragraph.get("id"): paragraph
        for paragraph in extracted_paragraphs
        if paragraph.get("id")
    }

    validated = []

    for paragraph in paragraphs:
        para_id = paragraph.get("id", "").strip()

        original_paragraph = paragraph_map.get(para_id)

        if not original_paragraph:
            logger.warning(
                "LLM referenced paragraph ID '%s' "
                "that was not present in the extracted judgment. Skipping.",
                para_id,
            )
            continue

        validated.append(
            {
                "id": original_paragraph["id"],
                "number": original_paragraph["number"],
                "text": original_paragraph["text"],
            }
        )

    return validated