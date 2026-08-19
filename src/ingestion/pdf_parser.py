"""
PDF parsing pipeline using pymupdf4llm.
Extracts markdown text and diagram images from basketball rulebooks.
Filters out tiny decorative images (logos, icons, separators) to keep
only meaningful diagrams worth captioning.
"""

import logging
import re
import shutil
from pathlib import Path

import pymupdf4llm
from PIL import Image

from src.config import PROJECT_ROOT, IMAGES_DIR, PARSED_DIR, PDF_LEAGUE_MAP, IMAGE_CACHE_PATH

logger = logging.getLogger(__name__)

# ── Image filtering thresholds ────────────────────────────────────────────
MIN_IMAGE_FILE_SIZE = 5 * 1024    # 5 KB   — skip truly tiny icons / dots
MIN_IMAGE_DIMENSION = 100         # pixels — both width AND height must exceed
MAX_ASPECT_RATIO = 3.5            # reject thin separator bars / banners


def _is_meaningful_image(img_path: Path) -> bool:
    """Return True if the image is large enough to be a real diagram."""
    try:
        # Quick file-size check first (no need to decode the image)
        if img_path.stat().st_size < MIN_IMAGE_FILE_SIZE:
            return False
        # Pixel-dimension and aspect-ratio check
        with Image.open(img_path) as im:
            w, h = im.size
            if w < MIN_IMAGE_DIMENSION or h < MIN_IMAGE_DIMENSION:
                return False
            # Reject extremely narrow / wide images (separator bars, banners)
            ratio = max(w, h) / max(min(w, h), 1)
            if ratio > MAX_ASPECT_RATIO:
                return False
        return True
    except Exception:
        return False


def clean_output() -> None:
    """
    Delete all previously extracted images, parsed markdown, and caption cache
    so the pipeline starts fresh.
    """
    for subdir in (IMAGES_DIR, PARSED_DIR):
        if subdir.exists():
            shutil.rmtree(subdir)
            logger.info(f"  Cleaned {subdir}")
    if IMAGE_CACHE_PATH.exists():
        IMAGE_CACHE_PATH.unlink()
        logger.info(f"  Cleaned {IMAGE_CACHE_PATH}")
    # Re-create empty directories
    for league in PDF_LEAGUE_MAP.values():
        (IMAGES_DIR / league).mkdir(parents=True, exist_ok=True)
    PARSED_DIR.mkdir(parents=True, exist_ok=True)


def get_pdf_paths() -> list[tuple[Path, str]]:
    """Return list of (pdf_path, league) for all rulebooks found in project root."""
    found = []
    for filename, league in PDF_LEAGUE_MAP.items():
        pdf_path = PROJECT_ROOT / filename
        if pdf_path.exists():
            found.append((pdf_path, league))
        else:
            logger.warning(f"PDF not found: {pdf_path}")
    return found


def parse_pdf(pdf_path: Path, league: str) -> list[dict]:
    """
    Parse a single PDF into per-page markdown chunks with image extraction.

    Images smaller than the filtering thresholds are deleted from disk and
    their markdown references are stripped so they never reach the captioner.

    Returns list of dicts:
        {
            "league": str,
            "page_number": int,
            "markdown": str,          # markdown text for this page
            "images": [str, ...],     # file paths to extracted images (filtered)
            "source_pdf": str,
        }
    """
    image_dir = IMAGES_DIR / league
    image_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Parsing {pdf_path.name} (league={league}) ...")

    # Extract markdown with images saved to disk, chunked per-page
    page_chunks = pymupdf4llm.to_markdown(
        str(pdf_path),
        page_chunks=True,
        write_images=True,
        image_path=str(image_dir),
        image_format="png",
        dpi=200,
    )

    total_raw = 0
    total_kept = 0
    results = []

    for chunk in page_chunks:
        page_num = chunk.get("metadata", {}).get("page", 0) + 1  # 0-indexed -> 1-indexed
        md_text = chunk.get("text", "")

        # Collect image paths referenced in this page's markdown
        raw_images = _extract_image_refs(md_text, image_dir)
        total_raw += len(raw_images)

        # Filter out tiny / decorative images
        kept_images = []
        removed_names = set()
        for img in raw_images:
            if _is_meaningful_image(Path(img)):
                kept_images.append(img)
            else:
                removed_names.add(Path(img).name)
                # Delete the junk file from disk
                try:
                    Path(img).unlink(missing_ok=True)
                except OSError:
                    pass

        total_kept += len(kept_images)

        # Strip markdown references to removed images so downstream
        # processing never sees them
        if removed_names:
            md_text = _strip_image_refs(md_text, removed_names)

        results.append({
            "league": league,
            "page_number": page_num,
            "markdown": md_text,
            "images": kept_images,
            "source_pdf": pdf_path.name,
        })

    logger.info(
        f"  -> {len(results)} pages, "
        f"{total_kept} diagram images kept "
        f"({total_raw - total_kept} tiny/decorative images discarded)"
    )

    # Save full markdown for inspection
    full_md = "\n\n---\n\n".join(r["markdown"] for r in results)
    out_path = PARSED_DIR / f"{league}.md"
    out_path.write_text(full_md, encoding="utf-8")
    logger.info(f"  -> Saved parsed markdown to {out_path}")

    return results


def _extract_image_refs(markdown_text: str, image_dir: Path) -> list[str]:
    """Extract image file paths from markdown ![...](...) references."""
    pattern = r"!\[.*?\]\((.*?)\)"
    matches = re.findall(pattern, markdown_text)
    valid_paths = []
    for match in matches:
        # pymupdf4llm writes paths relative to the image_path directory
        img_path = Path(match)
        if not img_path.is_absolute():
            img_path = image_dir / img_path.name
        if img_path.exists():
            valid_paths.append(str(img_path))
        else:
            # Try resolving relative to project root
            alt_path = PROJECT_ROOT / match
            if alt_path.exists():
                valid_paths.append(str(alt_path))
            else:
                logger.debug(f"Image ref not found on disk: {match}")
    return valid_paths


def _strip_image_refs(markdown_text: str, names_to_remove: set[str]) -> str:
    """Remove ![...](...) lines whose filename is in *names_to_remove*."""
    def _keep(m: re.Match) -> str:
        ref = m.group(1)
        if Path(ref).name in names_to_remove:
            return ""          # drop the whole reference
        return m.group(0)      # keep it

    return re.sub(r"!\[.*?\]\((.*?)\)\n?", _keep, markdown_text)


def parse_all_pdfs() -> dict[str, list[dict]]:
    """Parse all available rulebook PDFs. Returns {league: [page_chunks]}."""
    all_results = {}
    for pdf_path, league in get_pdf_paths():
        all_results[league] = parse_pdf(pdf_path, league)
    return all_results
