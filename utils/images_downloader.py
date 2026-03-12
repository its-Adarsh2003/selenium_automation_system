import os
import uuid
import logging
from typing import List, Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s %(message)s",
)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _guess_extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    if "." in name:
        ext = name.split(".")[-1].lower()
        if ext in {"jpg", "jpeg", "png", "gif", "webp"}:
            return "." + ext
    return ".jpg"


def download_single_image(url: str, output_dir: str = "images") -> Optional[str]:
    if not url:
        logger.warning("Empty image URL, skipping.")
        return None

    _ensure_dir(output_dir)

    try:
        logger.info("Downloading image from %s", url)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        ext = _guess_extension_from_url(url)
        filename = f"{uuid.uuid4().hex}{ext}"
        path = os.path.join(output_dir, filename)

        with open(path, "wb") as f:
            f.write(resp.content)

        logger.info("Saved image to %s", path)
        return path

    except Exception as e:
        logger.error("Failed to download image from %s: %s", url, e)
        return None


def download_images_parallel(
    image_urls: List[str],
    output_dir: str = "images",
    max_workers: int = 8,
) -> List[Optional[str]]:
    _ensure_dir(output_dir)
    results: List[Optional[str]] = [None] * len(image_urls)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(download_single_image, url, output_dir): idx
            for idx, url in enumerate(image_urls)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                logger.error("Unexpected error for %s: %s", image_urls[idx], e)
                results[idx] = None

    return results
