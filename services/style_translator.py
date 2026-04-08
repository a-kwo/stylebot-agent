"""Translate a numeric style vector into concrete search guidance.

Maps energy, cultural reference, silhouette, and color dimensions to
brand suggestions, search keywords, material preferences, and fit guidance
that Claude can use directly when building product searches.
"""

from typing import Optional

# ── Cultural reference → brands ──────────────────────────────────────────────

CULTURAL_REF_BRANDS: dict[str, list[str]] = {
    "sport_street": [
        "Nike", "Jordan", "New Balance", "Stussy",
        "Carhartt WIP", "Palace", "ASICS", "Adidas",
    ],
    "prep": [
        "Ralph Lauren", "Brooks Brothers", "J.Crew",
        "Polo Ralph Lauren", "Vineyard Vines", "Todd Snyder", "Gant",
    ],
    "clean_basic": [
        "Uniqlo", "COS", "Everlane", "Muji",
        "Arket", "H&M Premium", "ASOS Design",
    ],
    "utility": [
        "Carhartt", "Filson", "Red Wing", "Dickies",
        "Stan Ray", "Patagonia", "Norse Projects",
    ],
    "vintage_street": [
        "Champion", "Levi's", "Carhartt", "Vintage Nike", "Stussy",
        "Supreme", "Dickies",
    ],
}

# ── Cultural reference → search keywords ─────────────────────────────────────

CULTURAL_REF_KEYWORDS: dict[str, list[str]] = {
    "sport_street": [
        "streetwear", "sneakers", "joggers", "hoodie",
        "athletic", "urban", "graphic tee",
    ],
    "prep": [
        "preppy", "classic", "tailored", "blazer",
        "oxford shirt", "chinos", "loafers",
    ],
    "clean_basic": [
        "minimal", "basics", "clean lines", "essentials",
        "neutral wardrobe", "capsule wardrobe",
    ],
    "utility": [
        "workwear", "utility", "field jacket", "cargo pants",
        "boots", "heritage", "rugged",
    ],
    "vintage_street": [
        "vintage streetwear", "90s", "retro", "thrifted",
        "deadstock", "archive", "vintage tee",
    ],
}

# ── Cultural reference → materials ───────────────────────────────────────────

CULTURAL_REF_MATERIALS: dict[str, list[str]] = {
    "sport_street": [
        "cotton jersey", "nylon", "mesh", "fleece", "polyester blend",
    ],
    "prep": [
        "oxford cloth", "cotton twill", "wool", "cashmere",
        "linen", "pique cotton",
    ],
    "clean_basic": [
        "cotton", "linen", "organic cotton", "jersey",
        "soft knit", "modal",
    ],
    "utility": [
        "canvas", "denim", "waxed cotton", "ripstop",
        "flannel", "heavy cotton twill",
    ],
    "vintage_street": [
        "heavyweight cotton", "washed denim", "vintage fleece",
        "brushed cotton", "distressed fabric",
    ],
}

# ── Energy level → keyword modifiers ─────────────────────────────────────────

ENERGY_MODIFIERS: dict[str, list[str]] = {
    "low": ["understated", "minimal", "quiet", "subtle", "clean"],
    "mid": ["balanced", "versatile", "smart", "considered"],
    "high": ["bold", "statement", "graphic", "loud", "eye-catching"],
}

# ── Silhouette → fit guidance ────────────────────────────────────────────────

SILHOUETTE_FIT_MAP: dict[str, str] = {
    "structured": "tailored, structured fit — slim through the body with sharp shoulders",
    "relaxed": "relaxed, easy fit — slightly loose but intentional, not sloppy",
    "oversized": "oversized, loose fit — dropped shoulders, wide legs, generous proportions",
}

# ── Color temperature → color guidance ───────────────────────────────────────

COLOR_TEMP_MAP: dict[str, dict] = {
    "cool": {
        "guidance": "Cool-toned palette — navy, charcoal, grey, black, slate blue, forest green",
        "keywords": ["navy", "charcoal", "grey", "black", "blue", "cool tones"],
    },
    "neutral": {
        "guidance": "Neutral palette — mix of warm and cool tones, versatile color range",
        "keywords": ["neutral", "versatile", "balanced tones"],
    },
    "warm": {
        "guidance": "Warm-toned palette — brown, tan, rust, olive, cream, earth tones",
        "keywords": ["earth tones", "brown", "tan", "warm tones", "rust", "olive"],
    },
}

# ── Color temperature classification for wardrobe items ──────────────────────

COLOR_TEMPERATURE_MAP: dict[str, str] = {
    # Warm
    "brown": "warm", "tan": "warm", "rust": "warm", "olive": "warm",
    "cream": "warm", "beige": "warm", "orange": "warm", "yellow": "warm",
    "gold": "warm", "camel": "warm", "khaki": "warm", "terracotta": "warm",
    "coral": "warm", "peach": "warm", "burgundy": "warm", "maroon": "warm",
    "sand": "warm", "copper": "warm", "amber": "warm", "sienna": "warm",
    # Cool
    "navy": "cool", "blue": "cool", "charcoal": "cool", "grey": "cool",
    "gray": "cool", "slate": "cool", "teal": "cool", "lavender": "cool",
    "purple": "cool", "indigo": "cool", "plum": "cool", "mauve": "cool",
    "silver": "cool", "ice": "cool", "cobalt": "cool", "mint": "cool",
    "emerald": "cool", "forest": "cool", "steel": "cool",
    # Neutral
    "black": "neutral", "white": "neutral", "ivory": "neutral",
    "taupe": "neutral", "mushroom": "neutral",
}


def classify_color_temperature(color: Optional[str]) -> str:
    """Classify a color name as warm, cool, or neutral.

    Direct lookup first, then substring fallback for multi-word colors
    like "dark navy" or "light brown".
    """
    if not color:
        return "neutral"

    color_lower = color.lower().strip()

    # Direct lookup
    if color_lower in COLOR_TEMPERATURE_MAP:
        return COLOR_TEMPERATURE_MAP[color_lower]

    # Substring fallback: check if any known color is in the string
    for known_color, temp in COLOR_TEMPERATURE_MAP.items():
        if known_color in color_lower:
            return temp

    return "neutral"


# ── Threshold for including a cultural reference ─────────────────────────────

BLEND_THRESHOLD = 0.2


def translate_style_vector(style_vector: dict | None) -> dict:
    """Translate a numeric style vector into concrete search guidance.

    Args:
        style_vector: The style vector dict from the V2 quiz, or None/empty.

    Returns:
        Dict with keys: search_keywords, suggested_brands, material_preferences,
        avoid_keywords, fit_guidance, color_guidance, summary.
    """
    empty_result = {
        "search_keywords": [],
        "suggested_brands": [],
        "material_preferences": [],
        "avoid_keywords": [],
        "fit_guidance": "",
        "color_guidance": "",
        "summary": "",
    }

    if not style_vector:
        return empty_result

    # ── Gather cultural refs above threshold ─────────────────────────────
    cultural_ref = style_vector.get("cultural_ref", {})
    active_refs = {
        k: v for k, v in cultural_ref.items() if v >= BLEND_THRESHOLD
    }

    if not active_refs:
        return empty_result

    # Normalize weights so they sum to 1
    total_weight = sum(active_refs.values())

    # ── Blend brands across active cultures ──────────────────────────────
    brands: list[str] = []
    keywords: list[str] = []
    materials: list[str] = []

    for ref, weight in sorted(active_refs.items(), key=lambda x: -x[1]):
        proportion = weight / total_weight
        ref_brands = CULTURAL_REF_BRANDS.get(ref, [])
        ref_keywords = CULTURAL_REF_KEYWORDS.get(ref, [])
        ref_materials = CULTURAL_REF_MATERIALS.get(ref, [])

        # Take a proportional slice of brands (at least 2 if active)
        n_brands = max(2, int(len(ref_brands) * proportion))
        brands.extend(ref_brands[:n_brands])

        n_keywords = max(2, int(len(ref_keywords) * proportion))
        keywords.extend(ref_keywords[:n_keywords])

        n_materials = max(2, int(len(ref_materials) * proportion))
        materials.extend(ref_materials[:n_materials])

    # Deduplicate while preserving order
    brands = list(dict.fromkeys(brands))
    keywords = list(dict.fromkeys(keywords))
    materials = list(dict.fromkeys(materials))

    # ── Energy modifiers ─────────────────────────────────────────────────
    energy = style_vector.get("energy", 0.5)
    if energy < 0.3:
        energy_band = "low"
    elif energy > 0.7:
        energy_band = "high"
    else:
        energy_band = "mid"

    energy_keywords = ENERGY_MODIFIERS.get(energy_band, [])
    keywords = energy_keywords + keywords  # prepend energy keywords

    # ── Avoid keywords (opposite energy) ─────────────────────────────────
    avoid_keywords: list[str] = []
    if energy < 0.3:
        avoid_keywords = ["loud prints", "neon colors", "oversized graphics"]
    elif energy > 0.7:
        avoid_keywords = ["plain basics", "muted tones only"]

    # Add avoids based on absent cultural refs, but skip any keyword that
    # overlaps with the active refs' own keywords (e.g. "streetwear" ⊂ "vintage streetwear")
    active_kw_words: set[str] = set()
    for kw in keywords:
        active_kw_words.update(kw.lower().split())

    absent_refs = set(CULTURAL_REF_KEYWORDS.keys()) - set(active_refs.keys())
    for ref in absent_refs:
        ref_kw = CULTURAL_REF_KEYWORDS.get(ref, [])
        if ref_kw:
            candidate = ref_kw[0]
            candidate_words = set(candidate.lower().split())
            if not candidate_words.intersection(active_kw_words):
                avoid_keywords.append(candidate)

    # ── Silhouette → fit guidance ────────────────────────────────────────
    silhouette = style_vector.get("silhouette", {})
    dominant_sil = max(
        ["structured", "relaxed", "oversized"],
        key=lambda s: silhouette.get(s, 0),
        default="relaxed",
    )
    fit_guidance = SILHOUETTE_FIT_MAP.get(dominant_sil, SILHOUETTE_FIT_MAP["relaxed"])

    # ── Color guidance ───────────────────────────────────────────────────
    color = style_vector.get("color", {})
    temp = color.get("temperature", 0)
    if temp < -0.3:
        temp_band = "cool"
    elif temp > 0.3:
        temp_band = "warm"
    else:
        temp_band = "neutral"

    color_info = COLOR_TEMP_MAP.get(temp_band, COLOR_TEMP_MAP["neutral"])
    color_guidance = color_info["guidance"]

    # Append expression note
    expression = color.get("expression", 0.5)
    if expression < 0.3:
        color_guidance += ". Use color sparingly — as small accents only."
    elif expression > 0.7:
        color_guidance += ". Go bold with color — full tonal looks or color blocking."

    # ── Summary ──────────────────────────────────────────────────────────
    primary_ref = style_vector.get("primary_cultural_ref", "none")
    primary_label = {
        "sport_street": "sport/street",
        "prep": "old-money/prep",
        "clean_basic": "clean basic",
        "utility": "workwear/utility",
        "vintage_street": "vintage/streetwear",
    }.get(primary_ref, primary_ref)

    energy_label = {"low": "understated", "mid": "balanced", "high": "expressive"}.get(
        energy_band, "balanced"
    )

    summary = (
        f"This user has an {energy_label} energy with a {primary_label} cultural reference. "
        f"They prefer {fit_guidance.split('—')[0].strip().lower()} silhouettes. "
        f"{color_info['guidance'].split('—')[0].strip()}."
    )

    return {
        "search_keywords": keywords,
        "suggested_brands": brands,
        "material_preferences": materials,
        "avoid_keywords": avoid_keywords,
        "fit_guidance": fit_guidance,
        "color_guidance": color_guidance,
        "summary": summary,
    }
