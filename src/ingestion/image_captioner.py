"""
VLM-based image captioning via OpenRouter.
Calls qwen2.5-vl-72b-instruct to generate detailed factual descriptions
of basketball rulebook diagrams. Results are cached to disk.
"""

import base64
import json
import logging
import os
import time
from pathlib import Path

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    VLM_MODEL,
    IMAGE_CACHE_PATH,
)

logger = logging.getLogger(__name__)

# Minimum image file size in bytes — skip tiny decorative images
MIN_IMAGE_SIZE_BYTES = 5 * 1024  # 5KB


def _get_vlm_client() -> OpenAI:
    """Create OpenRouter-compatible OpenAI client for VLM calls."""
    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )


def _load_cache() -> dict:
    """Load the image caption cache from disk."""
    if IMAGE_CACHE_PATH.exists():
        with open(IMAGE_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    """Persist the image caption cache to disk."""
    IMAGE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(IMAGE_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _encode_image_base64(image_path: str) -> tuple[str, str]:
    """Read an image file and return (base64_string, mime_type)."""
    ext = Path(image_path).suffix.lower().lstrip(".")
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return b64, mime_type


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: logger.warning(f"  VLM call failed, retrying (attempt {rs.attempt_number})..."),
)
def _call_vlm(client: OpenAI, image_path: str) -> str:
    """Call the VLM to caption a single image."""
    b64, mime_type = _encode_image_base64(image_path)

    response = client.chat.completions.create(
        model=VLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a sports rules diagram analyst. Describe exactly what is depicted "
                    "in this basketball rulebook image: player positions, court markings, "
                    "measurements, dimensions, referee signals, arrows, labels, zones. "
                    "Be precise, factual, and thorough. Do not speculate — describe only "
                    "what is visually present."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this basketball rulebook diagram in detail."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                    },
                ],
            },
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()


def caption_images(image_paths: list[str]) -> dict[str, str]:
    """
    Caption a list of images, using cache where available.

    Returns dict: {image_path: caption}
    """
    cache = _load_cache()
    client = _get_vlm_client()
    results = {}
    new_captions = 0

    for img_path in image_paths:
        # Normalize path for cache key
        cache_key = os.path.normpath(img_path)

        # Check file size — skip tiny images
        try:
            file_size = os.path.getsize(img_path)
            if file_size < MIN_IMAGE_SIZE_BYTES:
                logger.debug(f"  Skipping small image ({file_size}B): {img_path}")
                continue
        except OSError:
            logger.warning(f"  Cannot access image: {img_path}")
            continue

        # Check cache
        if cache_key in cache:
            results[img_path] = cache[cache_key]["caption"]
            logger.debug(f"  Cache hit: {Path(img_path).name}")
            continue

        # Call VLM
        logger.info(f"  Captioning: {Path(img_path).name} ...")
        try:
            caption = _call_vlm(client, img_path)
            cache[cache_key] = {
                "caption": caption,
                "model": VLM_MODEL,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            results[img_path] = caption
            new_captions += 1
        except Exception as e:
            logger.error(f"  Failed to caption {img_path}: {e}")
            results[img_path] = ""

    if new_captions > 0:
        _save_cache(cache)
        logger.info(f"  -> Cached {new_captions} new captions")

    return results


def inject_captions_into_markdown(markdown: str, captions: dict[str, str]) -> str:
    """
    Find image references in markdown and inject VLM captions below each.
    Transforms:
        ![img](path/to/image.png)
    Into:
        ![img](path/to/image.png)
        **[Figure Description]:** <caption text>
    """
    import re

    def _replace_match(match):
        full_match = match.group(0)
        img_ref = match.group(1)
        # Try to find a caption for this image
        for img_path, caption in captions.items():
            if Path(img_ref).name == Path(img_path).name and caption:
                return f"{full_match}\n\n**[Figure Description]:** {caption}"
        return full_match

    pattern = r"!\[.*?\]\((.*?)\)"
    return re.sub(pattern, _replace_match, markdown)
