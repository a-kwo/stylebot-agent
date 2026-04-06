"""Stage-based style quiz with vector scoring.

Structure:
  Stage 0 — Occasion selection (multi-select, not counted as a question)
  Stage 1 — Energy + Cultural reference (Q1-Q4)
  Stage 2 — Silhouette (Q5-Q6)
  Stage 3 — Color relationship (Q8-Q9)

Each answer updates a score vector across four dimension axes:
  energy       — 0.0 (quiet/understated) to 1.0 (expressive/loud)
  cultural_ref — weights across sport_street, prep, clean_basic, utility, vintage_street
  silhouette   — weights for structured, relaxed, oversized
  color        — temperature (-1 cool to 1 warm), range, expression level

The final profile is a set of coordinates, not a category.
"""

# ── Occasion options for Stage 0 ─────────────────────────────────────────────

OCCASIONS = [
    {"id": "work", "label": "Work / Office", "icon": "briefcase"},
    {"id": "casual", "label": "Casual / Everyday", "icon": "coffee"},
    {"id": "going_out", "label": "Going Out / Nightlife", "icon": "music"},
    {"id": "date_night", "label": "Date Night", "icon": "heart"},
    {"id": "active", "label": "Active / Outdoor", "icon": "zap"},
    {"id": "travel", "label": "Travel", "icon": "plane"},
]

# ── Questions ─────────────────────────────────────────────────────────────────
# Each question has:
#   id, stage, prompt, options[]
#   Each option: {id, label, image_url, vector_scores: {dim.sub: value}}
#
# Q3 has "variants" keyed by Q2 answer (branching).
# Q6 prompt is templated with the user's top occasion.

QUESTIONS = {
    # ── Stage 1: Energy + Cultural Reference ──────────────────────────────────

    "q1_energy": {
        "id": "q1_energy",
        "stage": 1,
        "prompt": "Which of these looks feels most like you?",
        "subtitle": "Pick the energy level you gravitate toward",
        "options": [
            {
                "id": "understated",
                "label": "Understated",
                "image_url": "/static/quiz_images/v2__q1__understated.jpg",
                "vector_scores": {"energy": 0.15},
            },
            {
                "id": "balanced",
                "label": "Balanced",
                "image_url": "/static/quiz_images/v2__q1__balanced.jpg",
                "vector_scores": {"energy": 0.5},
            },
            {
                "id": "expressive",
                "label": "Expressive",
                "image_url": "/static/quiz_images/v2__q1__expressive.jpg",
                "vector_scores": {"energy": 0.85},
            },
        ],
    },

    "q2_cultural": {
        "id": "q2_cultural",
        "stage": 1,
        "prompt": "Which world does your style live in?",
        "subtitle": "The culture that best represents how you dress",
        "options": [
            {
                "id": "vintage_street",
                "label": "Vintage/Streetwear",
                "image_url": "/static/quiz_images/v2__q2__vintage-streetwear.jpg",
                "vector_scores": {"cultural_ref.vintage_street": 1.0},
            },
            {
                "id": "prep",
                "label": "Old-Money / Prep",
                "image_url": "/static/quiz_images/v2__q2__prep.jpg",
                "vector_scores": {"cultural_ref.prep": 1.0},
            },
            {
                "id": "clean_basic",
                "label": "Clean Basic",
                "image_url": "/static/quiz_images/v2__q2__clean-basic.jpg",
                "vector_scores": {"cultural_ref.clean_basic": 1.0},
            },
            {
                "id": "utility",
                "label": "Workwear",
                "image_url": "/static/quiz_images/v2__q2__utility.jpg",
                "vector_scores": {"cultural_ref.utility": 1.0},
            },
        ],
    },

    # Q3 branches based on Q2 — shows 3 looks within chosen cultural space,
    # varying in energy to cross-validate both dimensions.
    "q3_refine": {
        "id": "q3_refine",
        "stage": 1,
        "prompt": "Now within that world — where do you sit?",
        "subtitle": "Same cultural space, different energy levels",
        "branch_on": "q2_cultural",
        "variants": {
            "vintage_street": [
                {
                    "id": "ss_subtle",
                    "label": "Balanced Vintage Streetwear",
                    "image_url": "/static/quiz_images/v2_q3_vintage-balanced.jpg",
                    "vector_scores": {"energy": 0.2, "cultural_ref.vintage_street": 0.5},
                },
                {
                    "id": "ss_core",
                    "label": "Core Vintage Streetwear",
                    "image_url": "/static/quiz_images/v2_q3_vintage-core.jpg",
                    "vector_scores": {"energy": 0.55, "cultural_ref.vintage_street": 0.5},
                },
                {
                    "id": "ss_loud",
                    "label": "Statement Vintage Streetwear",
                    "image_url": "/static/quiz_images/v2_q3_vintage-statement.jpg",
                    "vector_scores": {"energy": 0.9, "cultural_ref.vintage_street": 0.5},
                },
            ],
            "prep": [
                {
                    "id": "prep_quiet",
                    "label": "Quiet Everyday",
                    "image_url": "/static/quiz_images/v2__q3__prep-quiet.jpg",
                    "vector_scores": {"energy": 0.15, "cultural_ref.prep": 0.5},
                },
                {
                    "id": "prep_classic",
                    "label": "Classic Prep",
                    "image_url": "/static/quiz_images/v2__q3__prep-classic.png",
                    "vector_scores": {"energy": 0.45, "cultural_ref.prep": 0.5},
                },
                {
                    "id": "prep_bold",
                    "label": "Formal Prep",
                    "image_url": "/static/quiz_images/v2__q3__prep-bold.png",
                    "vector_scores": {"energy": 0.8, "cultural_ref.prep": 0.5},
                },
            ],
            "utility": [
                {
                    "id": "util_clean",
                    "label": "Soft",
                    "image_url": "/static/quiz_images/v2__q3__util-clean.png",
                    "vector_scores": {"energy": 0.15, "cultural_ref.utility": 0.5},
                },
                {
                    "id": "util_rugged",
                    "label": "Rugged",
                    "image_url": "/static/quiz_images/v2__q3__util-rugged.png",
                    "vector_scores": {"energy": 0.45, "cultural_ref.utility": 0.5},
                },
                {
                    "id": "util_techwear",
                    "label": "Vintage",
                    "image_url": "/static/quiz_images/v2__q3__util-techwear.png",
                    "vector_scores": {"energy": 0.85, "cultural_ref.utility": 0.5},
                },
            ],
        },
    },

    "q4_social_energy": {
        "id": "q4_social_energy",
        "stage": 1,
        "prompt": "You're heading out for the night. Which vibe?",
        "subtitle": "How much do you want to stand out?",
        "options": [
            {
                "id": "everyday",
                "label": "Everyday",
                "image_url": "/static/quiz_images/v2__q4__everyday.png",
                "vector_scores": {"energy": 0.1},
            },
            {
                "id": "slightly_elevated",
                "label": "Slightly Elevated",
                "image_url": "/static/quiz_images/v2__q4__slightly-elevated.png",
                "vector_scores": {"energy": 0.3},
            },
            {
                "id": "smart_casual",
                "label": "Smart Casual",
                "image_url": "/static/quiz_images/v2__q4__smart-casual.png",
                "vector_scores": {"energy": 0.5},
            },
            {
                "id": "classy",
                "label": "Classy",
                "image_url": "/static/quiz_images/v2__q4__classy.png",
                "vector_scores": {"energy": 0.7},
            },
            {
                "id": "formal",
                "label": "Formal",
                "image_url": "/static/quiz_images/v2__q4__formal.png",
                "vector_scores": {"energy": 0.9},
            },
        ],
    },

    # ── Stage 2: Silhouette ───────────────────────────────────────────────────

    "q5_silhouette": {
        "id": "q5_silhouette",
        "stage": 2,
        "prompt": "Same style, different fit. Which feels right?",
        "subtitle": "Identical aesthetic and color — just the fit changes",
        "options": [
            {
                "id": "structured",
                "label": "Tailored / Structured",
                "image_url": "/static/quiz_images/v2__q5__structured.jpg",
                "vector_scores": {"silhouette.structured": 1.0},
            },
            {
                "id": "relaxed",
                "label": "Relaxed",
                "image_url": "/static/quiz_images/v2__q5__relaxed.jpg",
                "vector_scores": {"silhouette.relaxed": 1.0},
            },
            {
                "id": "oversized",
                "label": "Baggy",
                "image_url": "/static/quiz_images/v2__q5__oversized.jpg",
                "vector_scores": {"silhouette.oversized": 1.0},
            },
        ],
    },

    "q6_silhouette_occasion": {
        "id": "q6_silhouette_occasion",
        "stage": 2,
        "prompt": "Now imagine dressing for {occasion}. Same question — which fit?",
        "subtitle": "Grounding your silhouette preference in real life",
        "occasion_template": True,
        "options": [
            {
                "id": "occ_structured",
                "label": "Tailored / Structured",
                "image_url": "/static/quiz_images/v2__q6__structured.jpg",
                "vector_scores": {"silhouette.structured": 0.5},
            },
            {
                "id": "occ_relaxed",
                "label": "Loose / Slightly Baggy",
                "image_url": "/static/quiz_images/v2__q6__relaxed.jpg",
                "vector_scores": {"silhouette.relaxed": 0.5},
            },
            {
                "id": "occ_oversized",
                "label": "Baggy + Cropped",
                "image_url": "/static/quiz_images/v2__q6__oversized.jpg",
                "vector_scores": {"silhouette.oversized": 0.5},
            },
        ],
    },

    # ── Stage 3: Color ────────────────────────────────────────────────────────

    "q8_color": {
        "id": "q8_color",
        "stage": 3,
        "prompt": "Which color palette are you drawn to?",
        "subtitle": "Your instinctive color preference",
        "options": [
            {
                "id": "neutral_mono",
                "label": "Neutral",
                "image_url": "/static/quiz_images/v2__q8__neutral-mono.jpg",
                "vector_scores": {"color.temperature": 0.0, "color.range": 0.1},
            },
            {
                "id": "warm_earth",
                "label": "Warm Earth Tones",
                "image_url": "/static/quiz_images/v2__q8__warm-earth.jpg",
                "vector_scores": {"color.temperature": 0.8, "color.range": 0.4},
            },
            {
                "id": "cool_bold",
                "label": "Cool Colors",
                "image_url": "/static/quiz_images/v2__q8__cool-bold.jpg",
                "vector_scores": {"color.temperature": -0.6, "color.range": 0.6},
            },
            {
                "id": "mixed_pattern",
                "label": "Bright Colors",
                "image_url": "/static/quiz_images/v2__q8__mixed-pattern.jpg",
                "vector_scores": {"color.temperature": 0.3, "color.range": 1.0},
            },
        ],
    },

    "q9_color_expression": {
        "id": "q9_color_expression",
        "stage": 3,
        "prompt": "How do you use color in your outfits?",
        "subtitle": "Color as a supporting player vs. the main act",
        "options": [
            {
                "id": "color_accent",
                "label": "Accent",
                "image_url": "/static/quiz_images/v2__q9__accent.jpg",
                "vector_scores": {"color.expression": 0.2},
            },
            {
                "id": "color_focal",
                "label": "Focal Point",
                "image_url": "/static/quiz_images/v2__q9__focal.jpg",
                "vector_scores": {"color.expression": 0.6},
            },
            {
                "id": "color_full",
                "label": "Whole Outfit",
                "image_url": "/static/quiz_images/v2__q9__full.jpg",
                "vector_scores": {"color.expression": 1.0},
            },
        ],
    },
}

# ── Question flow order ───────────────────────────────────────────────────────

QUESTION_ORDER = [
    "q1_energy",
    "q2_cultural",
    "q3_refine",
    "q4_social_energy",
    "q5_silhouette",
    "q6_silhouette_occasion",
    "q8_color",
    "q9_color_expression",
]

STAGES = [
    {"id": 0, "label": "Occasions", "question_count": 0},
    {"id": 1, "label": "Energy & Culture", "question_count": 4},
    {"id": 2, "label": "Silhouette", "question_count": 2},
    {"id": 3, "label": "Color", "question_count": 2},
]

OCCASION_LABELS = {o["id"]: o["label"] for o in OCCASIONS}


# ── Public API ────────────────────────────────────────────────────────────────

def get_quiz_v2() -> dict:
    """Return the full V2 quiz definition for the frontend."""
    return {
        "occasions": OCCASIONS,
        "questions": QUESTIONS,
        "question_order": QUESTION_ORDER,
        "stages": STAGES,
        "occasion_labels": OCCASION_LABELS,
    }


def compute_style_vector(answers: list[dict], selected_occasions: list[str]) -> dict:
    """Compute a style vector from quiz answers.

    Args:
        answers: List of {question_id, option_id, vector_scores} dicts.
        selected_occasions: List of occasion IDs from Stage 0.

    Returns:
        Style vector dict with all dimension scores.
    """
    # Known nested groups — keys starting with these prefixes + underscore
    # should be normalized to dot notation (e.g. cultural_ref_prep → cultural_ref.prep)
    _NESTED_GROUPS = ("cultural_ref", "silhouette", "color")

    # Accumulate raw scores
    raw: dict[str, list[float]] = {}

    for answer in answers:
        scores = answer.get("vector_scores", {})
        for key, value in scores.items():
            # Normalize underscore keys to dot notation
            if "." not in key:
                for group in _NESTED_GROUPS:
                    prefix = group + "_"
                    if key.startswith(prefix) and key != group:
                        key = group + "." + key[len(prefix):]
                        break
            raw.setdefault(key, []).append(value)

    # Average each dimension
    vector: dict = {
        "energy": 0.5,
        "cultural_ref": {
            "sport_street": 0.0,
            "prep": 0.0,
            "clean_basic": 0.0,
            "utility": 0.0,
            "vintage_street": 0.0,
        },
        "silhouette": {
            "structured": 0.0,
            "relaxed": 0.0,
            "oversized": 0.0,
        },
        "color": {
            "temperature": 0.0,
            "range": 0.5,
            "expression": 0.5,
        },
        "occasions": selected_occasions,
        "primary_cultural_ref": "none",
    }

    # Fill in averaged values
    for key, values in raw.items():
        avg = sum(values) / len(values)
        if "." in key:
            group, sub = key.split(".", 1)
            if group in vector and isinstance(vector[group], dict):
                vector[group][sub] = round(avg, 3)
        else:
            vector[key] = round(avg, 3)

    # Determine primary cultural reference
    cr = vector["cultural_ref"]
    if any(v > 0 for v in cr.values()):
        vector["primary_cultural_ref"] = max(cr, key=cr.get)

    return vector
