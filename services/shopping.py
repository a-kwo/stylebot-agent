import os
import re
import time
from typing import Optional

import httpx

SERPAPI_URL = "https://serpapi.com/search.json"

# Per-user rate limit: store timestamps of recent calls
_rate_limit: dict[int, list[float]] = {}
CALLS_PER_HOUR = 50


def _check_rate_limit(user_id: int) -> bool:
    now = time.time()
    hour_ago = now - 3600
    calls = [t for t in _rate_limit.get(user_id, []) if t > hour_ago]
    _rate_limit[user_id] = calls
    if len(calls) >= CALLS_PER_HOUR:
        return False
    _rate_limit[user_id].append(now)
    return True


def _parse_price(price_str: str) -> Optional[float]:
    """Extract a numeric price from a string like '$29.99' or '29.99'."""
    match = re.search(r"[\d]+(?:\.[\d]+)?", price_str or "")
    if match:
        return float(match.group())
    return None


def search_products(
    user_id: int,
    query: str,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    limit: int = 6,
) -> list[dict]:
    if not _check_rate_limit(user_id):
        raise ValueError("Rate limit exceeded — please wait a moment before searching again.")

    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise ValueError("SERPAPI_KEY is not configured.")

    params: dict = {
        "engine": "google_shopping",
        "q": query,
        "api_key": api_key,
        "num": min(limit, 10),
    }

    if min_price is not None:
        params["tbs"] = f"mr:1,price:1,ppr_min:{min_price}"
        if max_price is not None:
            params["tbs"] = f"mr:1,price:1,ppr_min:{min_price},ppr_max:{max_price}"
    elif max_price is not None:
        params["tbs"] = f"mr:1,price:1,ppr_max:{max_price}"

    resp = httpx.get(SERPAPI_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    items = []
    for result in data.get("shopping_results", []):
        price = _parse_price(result.get("price", ""))

        items.append({
            "title": result.get("title", ""),
            "price": str(price) if price else "",
            "currency": "USD",
            "image_url": result.get("thumbnail", ""),
            "item_url": result.get("link", ""),
            "seller": result.get("source", ""),
        })

        if len(items) >= limit:
            break

    return items


def filter_results(
    items: list[dict],
    avoided_brands: list[str],
    avoided_colors: list[str],
) -> list[dict]:
    """Filter search results to remove products matching avoided brands or colors.

    Brand matching: case-insensitive substring against title + seller.
    Color matching: word-boundary regex against title only (prevents
    "blue" from matching "bluetooth").
    """
    if not avoided_brands and not avoided_colors:
        return items

    # Pre-compile color patterns with word boundaries
    color_patterns = []
    for color in avoided_colors:
        if color:
            pattern = re.compile(r"\b" + re.escape(color) + r"\b", re.IGNORECASE)
            color_patterns.append(pattern)

    avoided_brands_lower = [b.lower() for b in avoided_brands if b]

    filtered = []
    for item in items:
        title = (item.get("title") or "").lower()
        seller = (item.get("seller") or "").lower()
        combined = f"{title} {seller}"

        # Check avoided brands (substring match on title + seller)
        if any(brand in combined for brand in avoided_brands_lower):
            continue

        # Check avoided colors (word boundary match on title only)
        title_raw = item.get("title") or ""
        if any(p.search(title_raw) for p in color_patterns):
            continue

        filtered.append(item)

    return filtered
