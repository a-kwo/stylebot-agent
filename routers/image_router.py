import time
import ipaddress
from collections import OrderedDict
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from auth import get_current_user

router = APIRouter(prefix="/api/images", tags=["images"])

# Simple LRU cache: url -> (content_type, body, timestamp)
_cache: OrderedDict[str, tuple[str, bytes, float]] = OrderedDict()
_CACHE_MAX = 100
_CACHE_TTL = 600  # 10 minutes


def _is_private_ip(hostname: str) -> bool:
    try:
        addr = ipaddress.ip_address(hostname)
        return addr.is_private or addr.is_loopback or addr.is_reserved
    except ValueError:
        return False


def _cache_get(url: str) -> tuple[str, bytes] | None:
    entry = _cache.get(url)
    if entry is None:
        return None
    content_type, body, ts = entry
    if time.time() - ts > _CACHE_TTL:
        _cache.pop(url, None)
        return None
    _cache.move_to_end(url)
    return content_type, body


def _cache_put(url: str, content_type: str, body: bytes) -> None:
    _cache[url] = (content_type, body, time.time())
    _cache.move_to_end(url)
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)


@router.get("/proxy")
async def proxy_image(
    url: str = Query(..., description="External image URL to proxy"),
):
    # Validate URL scheme
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(400, "Only http/https URLs are allowed")
    if not parsed.hostname:
        raise HTTPException(400, "Invalid URL")

    # Block private/internal IPs
    if _is_private_ip(parsed.hostname):
        raise HTTPException(400, "Private IP addresses are not allowed")

    # Check cache
    cached = _cache_get(url)
    if cached:
        content_type, body = cached
        return Response(content=body, media_type=content_type)

    # Fetch upstream
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "image/*,*/*;q=0.8",
                },
            )
    except httpx.TimeoutException:
        raise HTTPException(504, "Upstream image request timed out")
    except httpx.RequestError:
        raise HTTPException(502, "Failed to fetch upstream image")

    if resp.status_code != 200:
        raise HTTPException(502, f"Upstream returned status {resp.status_code}")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    body = resp.content

    # Only cache reasonable sizes (< 5MB)
    if len(body) < 5 * 1024 * 1024:
        _cache_put(url, content_type, body)

    return Response(content=body, media_type=content_type)
