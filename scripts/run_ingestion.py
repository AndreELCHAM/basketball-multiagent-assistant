"""
End-to-end ingestion pipeline:
1. Parse all rulebook PDFs → markdown + images
2. Caption extracted images via VLM
3. Inject captions back into markdown
4. Save enriched parsed data for chunking
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR, PARSED_DIR, IMAGE_CACHE_PATH
from src.ingestion.pdf_parser import parse_all_pdfs, clean_output
from src.ingestion.image_captioner import caption_images, inject_captions_into_markdown

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("Basketball Rulebook Ingestion Pipeline")
    logger.info("=" * 60)

    # Step 0: Clean previous outputs for a fresh start
    logger.info("\n--- Step 0: Cleaning previous outputs ---")
    clean_output()

    # Step 1: Parse PDFs
    logger.info("\n--- Step 1: Parsing PDFs ---")
    all_pages = parse_all_pdfs()

    total_pages = sum(len(pages) for pages in all_pages.values())
    total_images = sum(
        sum(len(p["images"]) for p in pages)
        for pages in all_pages.values()
    )
    logger.info(f"\nParsing complete: {len(all_pages)} rulebooks, {total_pages} pages, {total_images} images")

    # Step 2: Caption images
    logger.info("\n--- Step 2: Captioning images via VLM ---")
    all_image_paths = []
    for league, pages in all_pages.items():
        for page in pages:
            all_image_paths.extend(page["images"])

    logger.info(f"Found {len(all_image_paths)} total images to process")

    if all_image_paths:
        captions = caption_images(all_image_paths)
        captioned_count = sum(1 for c in captions.values() if c)
        logger.info(f"Captioned {captioned_count}/{len(all_image_paths)} images")
    else:
        captions = {}
        logger.info("No images to caption")

    # Step 3: Inject captions into markdown and save enriched versions
    logger.info("\n--- Step 3: Enriching markdown with captions ---")
    enriched_data = {}

    for league, pages in all_pages.items():
        enriched_pages = []
        for page in pages:
            enriched_md = inject_captions_into_markdown(page["markdown"], captions)
            enriched_pages.append({
                **page,
                "markdown": enriched_md,
            })
        enriched_data[league] = enriched_pages

        # Save enriched markdown
        out_path = PARSED_DIR / f"{league}_enriched.md"
        full_md = "\n\n---\n\n".join(p["markdown"] for p in enriched_pages)
        out_path.write_text(full_md, encoding="utf-8")
        logger.info(f"  Saved enriched markdown: {out_path.name}")

    # Step 4: Save structured data for chunking
    logger.info("\n--- Step 4: Saving structured page data ---")
    structured_path = DATA_DIR / "parsed_pages.json"

    # Convert to JSON-serializable format
    json_data = {}
    for league, pages in enriched_data.items():
        json_data[league] = [
            {
                "league": p["league"],
                "page_number": p["page_number"],
                "markdown": p["markdown"],
                "images": p["images"],
                "source_pdf": p["source_pdf"],
            }
            for p in pages
        ]

    with open(structured_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    logger.info(f"  Saved structured data to {structured_path}")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    for league, pages in enriched_data.items():
        img_count = sum(len(p["images"]) for p in pages)
        logger.info(f"  {league}: {len(pages)} pages, {img_count} images")
    logger.info(f"  Image cache: {IMAGE_CACHE_PATH}")
    logger.info(f"  Parsed data: {structured_path}")


if __name__ == "__main__":
    main()
