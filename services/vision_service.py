"""Google Cloud Vision API image validation and Unsplash replacement search."""

import os

import httpx

VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"
MIN_CONFIDENCE = 0.7

# Maps Google Vision labels/web entities to project style tags.
# Keys are title-case as returned by the Vision API.
VISION_LABEL_TO_STYLE: dict[str, list[str]] = {
    # Fashion styles
    "Street fashion": ["streetwear", "urban"],
    "Streetwear": ["streetwear", "urban"],
    "Formal wear": ["classic", "professional"],
    "Formal": ["classic", "professional"],
    "Business": ["classic", "professional"],
    "Suit": ["classic", "tailored"],
    "Tuxedo": ["classic", "elegant"],
    "Sportswear": ["athleisure", "sporty"],
    "Activewear": ["athleisure", "sporty"],
    "Athletic": ["athleisure", "sporty"],
    "Athleisure": ["athleisure", "casual"],
    "Casual wear": ["casual", "relaxed"],
    "Casual": ["casual", "relaxed"],
    "Smart casual": ["smart-casual", "refined"],
    "Bohemian": ["bohemian", "eclectic"],
    "Boho": ["bohemian", "relaxed"],
    "Vintage": ["vintage", "retro"],
    "Retro": ["vintage", "retro"],
    "Punk": ["edgy", "bold"],
    "Grunge": ["edgy", "bold"],
    "Gothic": ["edgy", "bold"],
    "Avant-garde": ["edgy", "bold"],
    "Minimalism": ["minimalist", "timeless"],
    "Minimalist": ["minimalist", "timeless"],
    "Preppy": ["classic", "polished"],
    "Luxury": ["classic", "elegant"],
    "Haute couture": ["edgy", "bold"],
    "Fashion": ["trendy", "modern"],

    # Garments
    "Jacket": ["edgy", "bold"],
    "Leather jacket": ["edgy", "bold"],
    "Denim jacket": ["casual", "vintage"],
    "Blazer": ["classic", "professional"],
    "Overcoat": ["classic", "refined"],
    "Puffer jacket": ["streetwear", "cozy"],
    "Hoodie": ["streetwear", "casual"],
    "T-shirt": ["casual", "relaxed"],
    "Dress": ["classic", "feminine"],
    "Maxi dress": ["bohemian", "flowy"],
    "Wrap dress": ["classic", "feminine"],
    "Jeans": ["casual", "versatile"],
    "Denim": ["casual", "rugged"],
    "Sneakers": ["streetwear", "casual"],
    "Boots": ["rugged", "edgy"],
    "Heels": ["classic", "elegant"],
    "Watch": ["minimalist", "refined"],
    "Sunglasses": ["bold", "trendy"],
    "Handbag": ["classic", "professional"],
    "Jewelry": ["bohemian", "expressive"],

    # Patterns & textures
    "Plaid": ["heritage", "rugged"],
    "Stripes": ["classic", "nautical"],
    "Floral": ["bohemian", "expressive"],

    # Contexts
    "Outdoor": ["rugged", "outdoorsy"],
    "Urban": ["streetwear", "urban"],
    "Night": ["edgy", "sophisticated"],
    "Summer": ["casual", "relaxed"],
    "Winter": ["cozy", "rugged"],

    # Web entity common values
    "Fashion accessory": ["trendy", "bold"],
    "Men's style": ["classic", "modern"],
    "Women's fashion": ["trendy", "modern"],
    "Outerwear": ["classic", "refined"],
    "Workwear": ["classic", "professional"],
    "Costume": ["edgy", "eclectic"],
    "Shoe": ["casual", "versatile"],
    "Trousers": ["classic", "tailored"],
    "Coat": ["classic", "refined"],
    "Shirt": ["casual", "classic"],
    "Skirt": ["classic", "feminine"],
    "Bag": ["classic", "professional"],
    "Hat": ["bohemian", "eclectic"],
    "Scarf": ["bohemian", "cozy"],
}


def analyze_image(
    image_url: str,
    features: list[str] | None = None,
) -> dict:
    """Call Google Cloud Vision API for a single image. Returns the first response."""
    api_key = os.environ.get("GOOGLE_VISION_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_VISION_API_KEY is not configured.")

    if features is None:
        features = ["LABEL_DETECTION", "WEB_DETECTION"]

    payload = {
        "requests": [
            {
                "image": {"source": {"imageUri": image_url}},
                "features": [{"type": f, "maxResults": 20} for f in features],
            }
        ]
    }

    resp = httpx.post(
        f"{VISION_API_URL}?key={api_key}",
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["responses"][0]


def analyze_images_batch(
    image_urls: list[str],
    features: list[str] | None = None,
) -> list[dict]:
    """Batch-analyze up to 16 images in a single API call."""
    api_key = os.environ.get("GOOGLE_VISION_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_VISION_API_KEY is not configured.")

    if features is None:
        features = ["LABEL_DETECTION", "WEB_DETECTION"]

    payload = {
        "requests": [
            {
                "image": {"source": {"imageUri": url}},
                "features": [{"type": f, "maxResults": 20} for f in features],
            }
            for url in image_urls
        ]
    }

    resp = httpx.post(
        f"{VISION_API_URL}?key={api_key}",
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["responses"]


def extract_style_signals(vision_response: dict) -> set[str]:
    """Extract style tags from a Vision API response using the label mapping."""
    signals: set[str] = set()

    for annotation in vision_response.get("labelAnnotations", []):
        desc = annotation.get("description", "")
        score = annotation.get("score", 0)
        if score < MIN_CONFIDENCE:
            continue
        for tag in VISION_LABEL_TO_STYLE.get(desc, []):
            signals.add(tag)

    web_detection = vision_response.get("webDetection", {})
    for entity in web_detection.get("webEntities", []):
        desc = entity.get("description", "")
        score = entity.get("score", 0)
        if score < MIN_CONFIDENCE:
            continue
        for tag in VISION_LABEL_TO_STYLE.get(desc, []):
            signals.add(tag)

    return signals


def score_image_match(
    image_url: str,
    expected_tags: list[str],
    expected_label: str,
    threshold: float = 0.5,
) -> dict:
    """Score how well an image matches its expected style tags.

    Returns dict with match_score, matched_tags, missing_tags, inferred_tags,
    raw_labels, and verdict (PASS/PARTIAL/FAIL).
    """
    vision_response = analyze_image(image_url)
    inferred_tags = extract_style_signals(vision_response)

    raw_labels = [
        a.get("description", "")
        for a in vision_response.get("labelAnnotations", [])
    ]

    matched = [t for t in expected_tags if t in inferred_tags]
    missing = [t for t in expected_tags if t not in inferred_tags]

    score = len(matched) / len(expected_tags) if expected_tags else 0

    if score >= threshold:
        verdict = "PASS"
    elif score > 0:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        "match_score": score,
        "matched_tags": matched,
        "missing_tags": missing,
        "inferred_tags": inferred_tags,
        "raw_labels": raw_labels,
        "verdict": verdict,
    }


def search_replacement_image(
    style_tags: list[str],
    label: str,
    category: str,
) -> str | None:
    """Search Unsplash for a replacement image that matches the style tags.

    Returns the best-matching image URL or None if no good match found.
    """
    unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not unsplash_key:
        raise ValueError("UNSPLASH_ACCESS_KEY is not configured.")

    query = f"{label} {' '.join(style_tags)} outfit fashion"

    resp = httpx.get(
        UNSPLASH_API_URL,
        params={
            "query": query,
            "per_page": 10,
            "orientation": "squarish",
        },
        headers={"Authorization": f"Client-ID {unsplash_key}"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    if not results:
        return None

    best_url = None
    best_score = -1

    for photo in results:
        url = photo.get("urls", {}).get("regular", "")
        if not url:
            continue

        try:
            result = score_image_match(url, style_tags, label)
            if result["match_score"] > best_score:
                best_score = result["match_score"]
                best_url = url
        except Exception:
            continue

    return best_url
