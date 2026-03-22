"""Post-search product re-ranking based on user profile, wardrobe, and feedback."""

import re
from typing import Optional

DEFAULT_WEIGHTS = {
    "brand_match": 0.25,
    "price_fit": 0.20,
    "color_alignment": 0.20,
    "wardrobe_novelty": 0.20,
    "seller_diversity": 0.15,
}

# Category keywords for detecting product categories from titles
CATEGORY_KEYWORDS = {
    "tops": ["shirt", "tee", "t-shirt", "blouse", "polo", "sweater", "hoodie", "sweatshirt", "top", "henley"],
    "bottoms": ["pants", "jeans", "chinos", "trousers", "shorts", "joggers", "cargo"],
    "shoes": ["shoes", "sneakers", "boots", "loafers", "sandals", "trainers", "mules"],
    "outerwear": ["jacket", "coat", "blazer", "parka", "vest", "windbreaker", "bomber", "overcoat"],
    "accessories": ["watch", "belt", "hat", "cap", "scarf", "sunglasses", "bag", "wallet", "bracelet"],
    "dresses": ["dress", "gown", "romper", "jumpsuit"],
}


def _parse_price(price_str) -> Optional[float]:
    if not price_str:
        return None
    match = re.search(r"[\d]+(?:\.[\d]+)?", str(price_str))
    return float(match.group()) if match else None


def _detect_category(title: str) -> Optional[str]:
    title_lower = title.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in title_lower for kw in keywords):
            return category
    return None


def _extract_colors(title: str) -> list[str]:
    """Extract color words from a product title."""
    common_colors = [
        "black", "white", "navy", "blue", "red", "green", "brown", "tan",
        "grey", "gray", "olive", "cream", "beige", "burgundy", "rust",
        "orange", "yellow", "pink", "purple", "teal", "charcoal", "khaki",
    ]
    title_lower = title.lower()
    return [c for c in common_colors if re.search(r"\b" + c + r"\b", title_lower)]


def _score_brand_match(product: dict, profile: dict) -> float:
    preferred = profile.get("preferred_brands", [])
    avoided = profile.get("avoided_brands", [])

    # Handle both list and dict (weighted) formats
    if isinstance(preferred, dict):
        preferred = list(preferred.keys())
    if isinstance(avoided, dict):
        avoided = list(avoided.keys())

    title_lower = (product.get("title") or "").lower()
    seller_lower = (product.get("seller") or "").lower()
    combined = f"{title_lower} {seller_lower}"

    for brand in preferred:
        if brand.lower() in combined:
            return 1.0

    for brand in avoided:
        if brand.lower() in combined:
            return 0.0

    return 0.5


def _score_price_fit(product: dict, profile: dict, feedback_rows: list[dict] | None) -> float:
    price = _parse_price(product.get("price"))
    if price is None:
        return 0.5

    # Compute sweet spot: median of liked prices, or budget midpoint
    sweet_spot = None

    if feedback_rows:
        liked_prices = []
        for row in feedback_rows:
            if row.get("feedback") == "like":
                p = _parse_price(row.get("price"))
                if p:
                    liked_prices.append(p)
        if liked_prices:
            liked_prices.sort()
            mid = len(liked_prices) // 2
            sweet_spot = liked_prices[mid]

    if sweet_spot is None:
        budget_min = profile.get("budget_min", 0) or 0
        budget_max = profile.get("budget_max", 500) or 500
        sweet_spot = (budget_min + budget_max) / 2

    if sweet_spot == 0:
        return 0.5

    # Score based on distance from sweet spot
    budget_max = profile.get("budget_max", 500) or 500
    budget_min = profile.get("budget_min", 0) or 0
    budget_range = max(budget_max - budget_min, 1)

    distance = abs(price - sweet_spot)
    # Normalize distance relative to budget range
    normalized_distance = min(distance / budget_range, 1.0)
    return max(0.0, 1.0 - normalized_distance)


def _score_color_alignment(product: dict, profile: dict) -> float:
    title = product.get("title") or ""
    product_colors = _extract_colors(title)

    if not product_colors:
        return 0.5

    preferred = profile.get("preferred_colors", [])
    avoided = profile.get("avoided_colors", [])

    if isinstance(preferred, dict):
        preferred = list(preferred.keys())
    if isinstance(avoided, dict):
        avoided = list(avoided.keys())

    preferred_lower = [c.lower() for c in preferred]
    avoided_lower = [c.lower() for c in avoided]

    for color in product_colors:
        if color in avoided_lower:
            return 0.0

    for color in product_colors:
        if color in preferred_lower:
            return 1.0

    return 0.5


def _score_wardrobe_novelty(product: dict, wardrobe_items: list[dict]) -> float:
    if not wardrobe_items:
        return 0.7

    title_lower = (product.get("title") or "").lower()
    seller_lower = (product.get("seller") or "").lower()
    product_category = _detect_category(product.get("title") or "")

    # Check for duplicates
    for item in wardrobe_items:
        item_name = (item.get("name") or "").lower()
        item_brand = (item.get("brand") or "").lower()
        item_color = (item.get("color") or "").lower()

        # Strong duplicate: same name
        name_words = set(item_name.split())
        title_words = set(title_lower.split())
        overlap = len(name_words & title_words)
        if name_words and overlap >= len(name_words) * 0.6:
            return 0.2

        # Brand + color + category match
        if (item_brand and item_brand in f"{title_lower} {seller_lower}"
                and item_color and item_color in title_lower
                and item.get("category") == product_category):
            return 0.3

    # Bonus for missing category
    if product_category:
        owned_categories = {item.get("category") for item in wardrobe_items}
        if product_category not in owned_categories:
            return 1.0

    return 0.6


def _score_seller_diversity(product: dict, index: int, products: list[dict]) -> float:
    seller = (product.get("seller") or "").lower()
    if not seller:
        return 0.5

    # Count how many times this seller appears before this index
    prior_count = sum(
        1 for i, p in enumerate(products)
        if i < index and (p.get("seller") or "").lower() == seller
    )

    if prior_count == 0:
        return 1.0
    elif prior_count == 1:
        return 0.5
    else:
        return 0.2


def rank_products(
    products: list[dict],
    profile: dict,
    wardrobe_items: list[dict],
    feedback_rows: list[dict] | None = None,
    weights: dict | None = None,
) -> list[dict]:
    """Re-rank products by composite personalization score."""
    if not products:
        return []

    w = weights if weights is not None else DEFAULT_WEIGHTS

    scored = []
    for i, product in enumerate(products):
        scores = {
            "brand_match": _score_brand_match(product, profile),
            "price_fit": _score_price_fit(product, profile, feedback_rows),
            "color_alignment": _score_color_alignment(product, profile),
            "wardrobe_novelty": _score_wardrobe_novelty(product, wardrobe_items),
            "seller_diversity": _score_seller_diversity(product, i, products),
        }

        composite = sum(scores[k] * w.get(k, 0) for k in scores)
        product_copy = dict(product)
        product_copy["_rank_score"] = round(composite, 4)
        scored.append((i, product_copy))

    # Stable sort: descending by score, original index as tiebreaker
    scored.sort(key=lambda x: (-x[1]["_rank_score"], x[0]))

    return [item for _, item in scored]
