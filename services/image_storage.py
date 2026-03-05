"""Download and persist product images locally for wardrobe items."""

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import httpx

UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "wardrobe"


def _extension_from_response(url: str, content_type: str) -> str:
    """Determine file extension from content-type header or URL."""
    ct_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    for ct, ext in ct_map.items():
        if ct in content_type:
            return ext
    # Fallback: try URL path
    path = urlparse(url).path
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if path.lower().endswith(ext):
            return ext
    return ".jpg"


async def download_and_store_image(url: str, item_id: int) -> str | None:
    """Download image from url and save to uploads/wardrobe/.

    Returns the relative path (e.g. /uploads/wardrobe/42_abc123.png) on success,
    or None on any failure.
    """
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )

        if resp.status_code != 200:
            return None

        content_type = resp.headers.get("content-type", "")
        ext = _extension_from_response(url, content_type)
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        filename = f"{item_id}_{url_hash}{ext}"
        filepath = UPLOAD_DIR / filename

        filepath.write_bytes(resp.content)
        return f"/uploads/wardrobe/{filename}"

    except Exception:
        return None
