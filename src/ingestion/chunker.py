"""
Chunking strategies for basketball rulebook documents.
Config 1: Markdown structure-aware (header-based splitting).
Config 2: Recursive character splitting with token-aware boundaries.
"""

import hashlib
import logging
import re
from typing import Optional

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)

# Headers to split on for markdown-aware chunking
MARKDOWN_HEADERS = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

# Regex patterns to extract article/section identifiers from text
SECTION_PATTERNS = [
    re.compile(r"(Article\s+\d+[\s:–\-].*?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(Rule\s+(?:No\.?\s*)?\d+[\s:–\-].*?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(Section\s+[IVXLC]+[\s:–\-].*?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(RULE\s+NO\.\s*\d+[\s:–\-].*?)(?:\n|$)", re.IGNORECASE),
    re.compile(r"(Chapter\s+\d+[\s:–\-].*?)(?:\n|$)", re.IGNORECASE),
]


def _generate_chunk_id(league: str, text: str, index: int) -> str:
    """Generate a deterministic unique ID for a chunk."""
    content_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{league}_{index:04d}_{content_hash}"


def _extract_section_from_headers(header_metadata: dict) -> str:
    """Build article_or_section from markdown header hierarchy."""
    parts = []
    for key in ["h1", "h2", "h3"]:
        if key in header_metadata and header_metadata[key]:
            parts.append(header_metadata[key].strip())
    return " > ".join(parts) if parts else ""


def _extract_section_from_text(text: str) -> str:
    """Fallback: extract article/section from body text via regex."""
    for pattern in SECTION_PATTERNS:
        match = pattern.search(text[:500])  # only scan start of chunk
        if match:
            return match.group(1).strip()
    return ""


def _detect_images_in_chunk(text: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Detect image references and captions in a chunk."""
    img_pattern = re.compile(r"!\[.*?\]\((.*?)\)")
    caption_pattern = re.compile(r"\*\*\[Figure Description\]:\*\*\s*(.*?)(?:\n\n|\Z)", re.DOTALL)

    img_match = img_pattern.search(text)
    caption_match = caption_pattern.search(text)

    has_image = img_match is not None
    image_path = img_match.group(1) if img_match else None
    image_caption = caption_match.group(1).strip() if caption_match else None

    return has_image, image_path, image_caption


def _build_chunk_metadata(
    text: str,
    league: str,
    source_pdf: str,
    page_number: int,
    index: int,
    section_override: str = "",
) -> dict:
    """Build the unified metadata payload for a chunk."""
    has_image, image_path, image_caption = _detect_images_in_chunk(text)

    section = section_override or _extract_section_from_text(text) or f"Page {page_number}"

    return {
        "chunk_id": _generate_chunk_id(league, text, index),
        "league": league,
        "article_or_section": section,
        "has_image": has_image,
        "image_path": image_path,
        "image_caption": image_caption,
        "source_pdf": source_pdf,
        "page_number": page_number,
    }


def chunk_markdown_aware(
    pages: list[dict],
    league: str,
) -> list[dict]:
    """
    Config 1: Markdown structure-aware chunking.
    Splits on #/##/### headers to keep legal clauses intact.

    Args:
        pages: list of page dicts from pdf_parser (with 'markdown', 'source_pdf', 'page_number')

    Returns:
        list of {"text": str, "metadata": dict}
    """
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=MARKDOWN_HEADERS,
        strip_headers=False,
    )

    all_chunks = []
    chunk_index = 0

    for page in pages:
        md_text = page["markdown"]
        source_pdf = page["source_pdf"]
        page_num = page["page_number"]

        splits = splitter.split_text(md_text)

        for split in splits:
            text = split.page_content.strip()
            if not text or len(text) < 20:
                continue

            header_meta = split.metadata if hasattr(split, "metadata") else {}
            section = _extract_section_from_headers(header_meta)

            metadata = _build_chunk_metadata(
                text, league, source_pdf, page_num, chunk_index, section_override=section
            )
            all_chunks.append({"text": text, "metadata": metadata})
            chunk_index += 1

    logger.info(f"  Markdown-aware chunking: {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks


def chunk_recursive(
    pages: list[dict],
    league: str,
    chunk_size: int = 2000,
    chunk_overlap: int = 200,
) -> list[dict]:
    """
    Config 2: Recursive character splitting with overlap.
    Uses character counts (approx ~512 tokens at 4 chars/token).

    Args:
        pages: list of page dicts from pdf_parser
        chunk_size: max characters per chunk (default 2000 ≈ 512 tokens)
        chunk_overlap: overlap in characters (default 200 ≈ 50 tokens)

    Returns:
        list of {"text": str, "metadata": dict}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    all_chunks = []
    chunk_index = 0

    # Track last seen section header for inheritance
    current_section = ""

    for page in pages:
        md_text = page["markdown"]
        source_pdf = page["source_pdf"]
        page_num = page["page_number"]

        # Update current section from page content
        section_from_text = _extract_section_from_text(md_text)
        if section_from_text:
            current_section = section_from_text

        splits = splitter.split_text(md_text)

        for split_text in splits:
            text = split_text.strip()
            if not text or len(text) < 20:
                continue

            # Check if this chunk has its own section header
            chunk_section = _extract_section_from_text(text) or current_section

            metadata = _build_chunk_metadata(
                text, league, source_pdf, page_num, chunk_index, section_override=chunk_section
            )
            all_chunks.append({"text": text, "metadata": metadata})
            chunk_index += 1

    logger.info(f"  Recursive chunking: {len(all_chunks)} chunks from {len(pages)} pages")
    return all_chunks
