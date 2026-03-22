"""Feedback-driven style vector refinement.

Computes a feedback vector from liked/disliked products and blends it
with the original quiz vector to create a refined style vector that
evolves with user behavior.
"""

import json

from services.style_translator import CULTURAL_REF_BRANDS, classify_color_temperature

BLEND_QUIZ_WEIGHT = 0.7
BLEND_FEEDBACK_WEIGHT = 0.3
REFINEMENT_THRESHOLD = 5

# Silhouette keywords in product titles
SILHOUETTE_KEYWORDS = {
    "structured": ["slim", "tailored", "fitted", "structured", "sharp"],
    "relaxed": ["relaxed", "easy", "casual", "loose"],
    "oversized": ["oversized", "oversize", "boxy", "wide", "baggy"],
}

# Invert CULTURAL_REF_BRANDS for fast brand → culture lookup
_BRAND_TO_CULTURE: dict[str, str] = {}
for culture, brands in CULTURAL_REF_BRANDS.items():
    for brand in brands:
        _BRAND_TO_CULTURE[brand.lower()] = culture


def _extract_cultural_signal(product: dict) -> dict[str, float]:
    """Map product seller/brand/title to cultural_ref dimension scores."""
    seller = (product.get("seller") or "").lower()
    title = (product.get("product_title") or "").lower()
    combined = f"{seller} {title}"

    signals: dict[str, float] = {}
    for brand_lower, culture in _BRAND_TO_CULTURE.items():
        if brand_lower in combined:
            signals[culture] = signals.get(culture, 0) + 1.0
            break  # one match is enough

    return signals


def _extract_color_signal(product: dict) -> dict:
    """Map product color to color.temperature signal."""
    color = product.get("color")
    if not color:
        return {"temperature": 0}

    temp_class = classify_color_temperature(color)
    if temp_class == "warm":
        return {"temperature": 0.5}
    elif temp_class == "cool":
        return {"temperature": -0.5}
    return {"temperature": 0}


def _extract_silhouette_signal(product: dict) -> dict[str, float]:
    """Parse product title for silhouette keywords."""
    title = (product.get("product_title") or "").lower()
    signals: dict[str, float] = {}

    for sil_type, keywords in SILHOUETTE_KEYWORDS.items():
        if any(kw in title for kw in keywords):
            signals[sil_type] = 1.0

    return signals


def _neutral_vector() -> dict:
    """Return a neutral baseline vector."""
    return {
        "energy": 0.5,
        "cultural_ref": {"sport_street": 0.0, "prep": 0.0, "clean_basic": 0.0, "utility": 0.0},
        "silhouette": {"structured": 0.0, "relaxed": 0.0, "oversized": 0.0},
        "color": {"temperature": 0.0, "range": 0.5, "expression": 0.5},
        "primary_cultural_ref": "none",
        "occasions": [],
    }


def compute_feedback_vector(feedback_rows: list[dict]) -> dict:
    """Compute a style vector from product feedback signals."""
    if not feedback_rows:
        return _neutral_vector()

    cultural_accum: dict[str, float] = {"sport_street": 0.0, "prep": 0.0, "clean_basic": 0.0, "utility": 0.0}
    color_temp_accum = 0.0
    silhouette_accum: dict[str, float] = {"structured": 0.0, "relaxed": 0.0, "oversized": 0.0}
    count = 0

    for row in feedback_rows:
        feedback = row.get("feedback", "")
        multiplier = 1.0 if feedback == "like" else -1.0 if feedback == "dislike" else 0.0
        if multiplier == 0:
            continue

        count += 1

        # Cultural signal
        cultural = _extract_cultural_signal(row)
        for key, val in cultural.items():
            cultural_accum[key] += val * multiplier

        # Color signal
        color = _extract_color_signal(row)
        color_temp_accum += color.get("temperature", 0) * multiplier

        # Silhouette signal
        sil = _extract_silhouette_signal(row)
        for key, val in sil.items():
            silhouette_accum[key] += val * multiplier

    if count == 0:
        return _neutral_vector()

    # Normalize and clamp
    for key in cultural_accum:
        cultural_accum[key] = max(0.0, min(1.0, cultural_accum[key] / count))

    color_temp = max(-1.0, min(1.0, color_temp_accum / count))

    for key in silhouette_accum:
        silhouette_accum[key] = max(0.0, min(1.0, silhouette_accum[key] / count))

    # Determine primary cultural ref
    primary = max(cultural_accum, key=cultural_accum.get)
    if cultural_accum[primary] <= 0:
        primary = "none"

    return {
        "energy": 0.5,  # Energy is hard to extract from product data
        "cultural_ref": cultural_accum,
        "silhouette": silhouette_accum,
        "color": {"temperature": round(color_temp, 3), "range": 0.5, "expression": 0.5},
        "primary_cultural_ref": primary,
        "occasions": [],
    }


def blend_vectors(
    quiz_vector: dict,
    feedback_vector: dict,
    quiz_weight: float = BLEND_QUIZ_WEIGHT,
    feedback_weight: float = BLEND_FEEDBACK_WEIGHT,
) -> dict:
    """Blend quiz and feedback vectors into a refined vector."""

    def blend_scalar(a, b):
        return round(quiz_weight * a + feedback_weight * b, 3)

    def blend_dict(a: dict, b: dict) -> dict:
        keys = set(list(a.keys()) + list(b.keys()))
        return {
            k: round(quiz_weight * a.get(k, 0) + feedback_weight * b.get(k, 0), 3)
            for k in keys
        }

    result = {
        "energy": blend_scalar(
            quiz_vector.get("energy", 0.5),
            feedback_vector.get("energy", 0.5),
        ),
        "cultural_ref": blend_dict(
            quiz_vector.get("cultural_ref", {}),
            feedback_vector.get("cultural_ref", {}),
        ),
        "silhouette": blend_dict(
            quiz_vector.get("silhouette", {}),
            feedback_vector.get("silhouette", {}),
        ),
        "color": blend_dict(
            quiz_vector.get("color", {}),
            feedback_vector.get("color", {}),
        ),
        "occasions": quiz_vector.get("occasions", []),
    }

    # Recompute primary_cultural_ref from blended values
    cr = result["cultural_ref"]
    if cr:
        primary = max(cr, key=cr.get)
        result["primary_cultural_ref"] = primary if cr[primary] > 0 else "none"
    else:
        result["primary_cultural_ref"] = "none"

    return result


def maybe_refine_vector(user_id: int, db) -> dict | None:
    """Check if refinement is needed, compute and store if so."""
    try:
        row = db.execute(
            "SELECT style_vector, feedback_vector_count FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    except Exception:
        return None

    if not row:
        return None

    # Parse quiz vector
    style_vector_raw = row["style_vector"] or "{}"
    try:
        quiz_vector = json.loads(style_vector_raw) if isinstance(style_vector_raw, str) else (style_vector_raw or {})
    except Exception:
        quiz_vector = {}

    # Skip if no quiz vector
    if not quiz_vector or quiz_vector.get("primary_cultural_ref", "none") == "none":
        return None

    # Count current feedback
    count_row = db.execute(
        "SELECT COUNT(*) as cnt FROM recommendation_feedback WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    current_count = count_row["cnt"] if count_row else 0
    last_count = row["feedback_vector_count"] or 0

    # Check threshold
    if current_count - last_count < REFINEMENT_THRESHOLD:
        return None

    # Fetch feedback rows
    feedback_rows = db.execute(
        "SELECT product_title, feedback, price, color, seller FROM recommendation_feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
        (user_id,),
    ).fetchall()

    feedback_vector = compute_feedback_vector([dict(r) for r in feedback_rows])
    refined = blend_vectors(quiz_vector, feedback_vector)

    # Store
    db.execute(
        "UPDATE profiles SET refined_style_vector = ?, feedback_vector = ?, feedback_vector_count = ? WHERE user_id = ?",
        (json.dumps(refined), json.dumps(feedback_vector), current_count, user_id),
    )
    db.commit()

    return refined
