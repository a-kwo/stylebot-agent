#!/usr/bin/env python3
"""One-time script to restructure the quiz tree:
1. Add Q3 sub-style nodes for all depth-2 dead-ends
2. Add cross-cutting Q4 (color palette) and Q5 (fit/silhouette) nodes
3. Chain all terminal Q3 options -> color -> fit (terminal)

Run: python scripts/restructure_quiz_tree.py
"""

import os
import re
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.quiz_service import QUIZ_TREE

QUIZ_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "services", "quiz_service.py"))

# ── New Q3 sub-style nodes for depth-2 dead-ends ───────────────────

NEW_Q3_NODES = {
    # ── Male dead-ends ──
    "m_om_coast_q3": {
        "prompt": "Which coastal vibe fits you best?",
        "options": [
            {
                "id": "m_om_coast_med",
                "label": "Mediterranean Casual",
                "image_url": "https://images.unsplash.com/photo-placeholder-coast-med?w=400&h=500&fit=crop",
                "style_tags": ["Mediterranean", "linen-shirt", "espadrilles", "sun-faded", "Riviera"],
                "next": "color_m",
            },
            {
                "id": "m_om_coast_neweng",
                "label": "New England Classic",
                "image_url": "https://images.unsplash.com/photo-placeholder-coast-neweng?w=400&h=500&fit=crop",
                "style_tags": ["New-England", "boat-shoes", "cable-knit", "madras", "Cape-Cod"],
                "next": "color_m",
            },
            {
                "id": "m_om_coast_island",
                "label": "Island Linen",
                "image_url": "https://images.unsplash.com/photo-placeholder-coast-island?w=400&h=500&fit=crop",
                "style_tags": ["island", "all-linen", "wide-brim-hat", "barefoot-luxury", "tropical-minimal"],
                "next": "color_m",
            },
        ],
    },
    "m_vt_y2k_q3": {
        "prompt": "Which Y2K flavor do you vibe with?",
        "options": [
            {
                "id": "m_vt_y2k_cyber",
                "label": "Cyber Y2K",
                "image_url": "https://images.unsplash.com/photo-placeholder-y2k-cyber?w=400&h=500&fit=crop",
                "style_tags": ["cyber", "metallic", "futuristic", "tech-inspired", "silver"],
                "next": "color_m",
            },
            {
                "id": "m_vt_y2k_logo",
                "label": "Logo Revival",
                "image_url": "https://images.unsplash.com/photo-placeholder-y2k-logo?w=400&h=500&fit=crop",
                "style_tags": ["logomania", "designer-revival", "bold-branding", "chunky-sneakers", "2000s"],
                "next": "color_m",
            },
            {
                "id": "m_vt_y2k_bling",
                "label": "Bling Era",
                "image_url": "https://images.unsplash.com/photo-placeholder-y2k-bling?w=400&h=500&fit=crop",
                "style_tags": ["bling", "oversized-denim", "flashy", "statement-jewelry", "chrome"],
                "next": "color_m",
            },
        ],
    },
    "m_sc_work_q3": {
        "prompt": "What does your ideal work style look like?",
        "options": [
            {
                "id": "m_sc_work_creative",
                "label": "Creative Office",
                "image_url": "https://images.unsplash.com/photo-placeholder-work-creative?w=400&h=500&fit=crop",
                "style_tags": ["creative-professional", "relaxed-blazer", "no-tie", "sneakers-with-trousers", "design-world"],
                "next": "color_m",
            },
            {
                "id": "m_sc_work_corp",
                "label": "Corporate Casual",
                "image_url": "https://images.unsplash.com/photo-placeholder-work-corp?w=400&h=500&fit=crop",
                "style_tags": ["corporate-casual", "oxford-shirt", "chinos", "loafers", "polished-casual"],
                "next": "color_m",
            },
            {
                "id": "m_sc_work_startup",
                "label": "Startup Minimal",
                "image_url": "https://images.unsplash.com/photo-placeholder-work-startup?w=400&h=500&fit=crop",
                "style_tags": ["startup-casual", "premium-tee", "clean-sneakers", "minimal-accessories", "tech-casual"],
                "next": "color_m",
            },
        ],
    },

    # ── Female dead-ends ──
    "f_sw_tech_q3": {
        "prompt": "Which utility style speaks to you?",
        "options": [
            {
                "id": "f_sw_tech_dark",
                "label": "Dark Utility",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-tech-dark?w=400&h=500&fit=crop",
                "style_tags": ["all-black", "cargo-pants", "utility-vest", "tactical-chic", "dark-functional"],
                "next": "color_f",
            },
            {
                "id": "f_sw_tech_gorp",
                "label": "Urban Gorpcore",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-tech-gorp?w=400&h=500&fit=crop",
                "style_tags": ["gorpcore", "outdoor-brands", "hiking-boots-in-city", "functional-fashion", "earth-tones"],
                "next": "color_f",
            },
            {
                "id": "f_sw_tech_sport",
                "label": "Sporty Tech",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-tech-sport?w=400&h=500&fit=crop",
                "style_tags": ["neon-accents", "performance-fabrics", "futuristic-sneakers", "sport-utility", "tech-sport"],
                "next": "color_f",
            },
        ],
    },
    "f_om_euro_q3": {
        "prompt": "Which European elegance resonates with you?",
        "options": [
            {
                "id": "f_om_euro_riviera",
                "label": "Italian Riviera",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-euro-riviera?w=400&h=500&fit=crop",
                "style_tags": ["Italian-Riviera", "silk-scarf", "oversized-sunglasses", "linen-dress", "Mediterranean"],
                "next": "color_f",
            },
            {
                "id": "f_om_euro_paris",
                "label": "Parisian Classic",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-euro-paris?w=400&h=500&fit=crop",
                "style_tags": ["Parisian", "trench-coat", "ballet-flats", "structured-bag", "understated-chic"],
                "next": "color_f",
            },
            {
                "id": "f_om_euro_english",
                "label": "English Country",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-euro-english?w=400&h=500&fit=crop",
                "style_tags": ["English-country", "Barbour-jacket", "tweed-skirt", "riding-boots", "heritage"],
                "next": "color_f",
            },
        ],
    },
    "f_om_coast_q3": {
        "prompt": "Which refined outdoor style fits your lifestyle?",
        "options": [
            {
                "id": "f_om_coast_hamptons",
                "label": "Hamptons Prep",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-coast-hamp?w=400&h=500&fit=crop",
                "style_tags": ["Hamptons", "white-jeans", "striped-top", "deck-shoes", "coastal-chic"],
                "next": "color_f",
            },
            {
                "id": "f_om_coast_equestrian",
                "label": "Equestrian Chic",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-coast-equestrian?w=400&h=500&fit=crop",
                "style_tags": ["equestrian", "riding-boots", "tailored-jacket", "leather-belt", "horse-country"],
                "next": "color_f",
            },
            {
                "id": "f_om_coast_boho",
                "label": "Seaside Bohemian",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-coast-boho?w=400&h=500&fit=crop",
                "style_tags": ["seaside-boho", "crochet", "flowing-maxi", "sandals", "beachy-relaxed"],
                "next": "color_f",
            },
        ],
    },
    "f_vt_cottage_q3": {
        "prompt": "Which romantic vintage world calls to you?",
        "options": [
            {
                "id": "f_vt_cottage_garden",
                "label": "English Garden",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-cottage-garden?w=400&h=500&fit=crop",
                "style_tags": ["English-garden", "floral-midi", "Peter-Pan-collar", "wicker-basket", "romantic"],
                "next": "color_f",
            },
            {
                "id": "f_vt_cottage_prairie",
                "label": "Prairie Folk",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-cottage-prairie?w=400&h=500&fit=crop",
                "style_tags": ["prairie", "puff-sleeves", "embroidery", "frontier-feminine", "folk"],
                "next": "color_f",
            },
            {
                "id": "f_vt_cottage_fairy",
                "label": "Fairy Vintage",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-cottage-fairy?w=400&h=500&fit=crop",
                "style_tags": ["fairy", "tulle", "pastel", "whimsical", "ethereal"],
                "next": "color_f",
            },
        ],
    },
    "f_vt_80s_q3": {
        "prompt": "Which 80s energy do you channel?",
        "options": [
            {
                "id": "f_vt_80s_power",
                "label": "Power Suit",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-80s-power?w=400&h=500&fit=crop",
                "style_tags": ["power-suit", "oversized-blazer", "structured-shoulders", "bold-earrings", "corporate-glam"],
                "next": "color_f",
            },
            {
                "id": "f_vt_80s_wave",
                "label": "New Wave",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-80s-wave?w=400&h=500&fit=crop",
                "style_tags": ["new-wave", "geometric-prints", "asymmetric", "bold-colors", "art-inspired"],
                "next": "color_f",
            },
            {
                "id": "f_vt_80s_dynasty",
                "label": "Dynasty Glam",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-80s-dynasty?w=400&h=500&fit=crop",
                "style_tags": ["dynasty-glam", "sequins", "dramatic-jewelry", "fur-accents", "opulent"],
                "next": "color_f",
            },
        ],
    },
    "f_vt_y2k_q3": {
        "prompt": "Which Y2K flavor is your vibe?",
        "options": [
            {
                "id": "f_vt_y2k_pop",
                "label": "Pop Princess",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-y2k-pop?w=400&h=500&fit=crop",
                "style_tags": ["pop-princess", "bedazzled", "crop-top", "platform-shoes", "Britney-era"],
                "next": "color_f",
            },
            {
                "id": "f_vt_y2k_paris",
                "label": "It Girl Era",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-y2k-paris?w=400&h=500&fit=crop",
                "style_tags": ["It-girl", "velour-tracksuit", "tiny-bag", "rhinestones", "pink"],
                "next": "color_f",
            },
            {
                "id": "f_vt_y2k_cyber",
                "label": "Cyber Girl",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-y2k-cyber?w=400&h=500&fit=crop",
                "style_tags": ["cyber", "metallic", "futuristic", "holographic", "rave-inspired"],
                "next": "color_f",
            },
        ],
    },
    "f_al_sporty_q3": {
        "prompt": "What kind of sporty fits your energy?",
        "options": [
            {
                "id": "f_al_sporty_gym",
                "label": "Gym Chic",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-sporty-gym?w=400&h=500&fit=crop",
                "style_tags": ["gym-chic", "matching-sets", "neutral-athletic", "seamless", "polished-gym"],
                "next": "color_f",
            },
            {
                "id": "f_al_sporty_track",
                "label": "Track Star",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-sporty-track?w=400&h=500&fit=crop",
                "style_tags": ["track-star", "retro-track", "stripe-detail", "zip-up", "sporty-vintage"],
                "next": "color_f",
            },
            {
                "id": "f_al_sporty_dance",
                "label": "Dance Studio",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-sporty-dance?w=400&h=500&fit=crop",
                "style_tags": ["dance-studio", "leotard-inspired", "legwarmers", "wrap-top", "dance-chic"],
                "next": "color_f",
            },
        ],
    },
    "f_al_outdoor_q3": {
        "prompt": "Which outdoor adventure style is yours?",
        "options": [
            {
                "id": "f_al_outdoor_trail",
                "label": "Trail Hiker",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-outdoor-trail?w=400&h=500&fit=crop",
                "style_tags": ["trail-hiker", "hiking-boots", "cargo-shorts", "moisture-wicking", "nature-ready"],
                "next": "color_f",
            },
            {
                "id": "f_al_outdoor_mountain",
                "label": "Mountain Chic",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-outdoor-mountain?w=400&h=500&fit=crop",
                "style_tags": ["mountain-chic", "puffer-vest", "base-layers", "apres-ski", "elevated-outdoor"],
                "next": "color_f",
            },
            {
                "id": "f_al_outdoor_coastal",
                "label": "Coastal Active",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-outdoor-coastal?w=400&h=500&fit=crop",
                "style_tags": ["coastal-active", "surf-inspired", "rashguard", "board-shorts", "beach-sport"],
                "next": "color_f",
            },
        ],
    },
    "f_al_retro_q3": {
        "prompt": "Which retro sport aesthetic do you love?",
        "options": [
            {
                "id": "f_al_retro_tennis",
                "label": "Retro Tennis",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-retro-tennis?w=400&h=500&fit=crop",
                "style_tags": ["retro-tennis", "pleated-skirt", "polo-shirt", "white-sneakers", "country-club-throwback"],
                "next": "color_f",
            },
            {
                "id": "f_al_retro_velour",
                "label": "Velour Revival",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-retro-velour?w=400&h=500&fit=crop",
                "style_tags": ["velour-tracksuit", "logo-mania", "bedazzled", "pink-sportswear", "2000s-sport"],
                "next": "color_f",
            },
            {
                "id": "f_al_retro_spice",
                "label": "Sporty Spice",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-retro-spice?w=400&h=500&fit=crop",
                "style_tags": ["sporty-spice", "platform-sneakers", "crop-sportswear", "90s-pop", "girl-power"],
                "next": "color_f",
            },
        ],
    },
    "f_sc_office_q3": {
        "prompt": "What does polished look like to you?",
        "options": [
            {
                "id": "f_sc_office_power",
                "label": "Power Professional",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-office-power?w=400&h=500&fit=crop",
                "style_tags": ["power-professional", "tailored-suit", "pointed-heels", "statement-watch", "boardroom"],
                "next": "color_f",
            },
            {
                "id": "f_sc_office_creative",
                "label": "Creative Director",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-office-creative?w=400&h=500&fit=crop",
                "style_tags": ["creative-director", "architectural-pieces", "all-black", "statement-glasses", "design-world"],
                "next": "color_f",
            },
            {
                "id": "f_sc_office_elevated",
                "label": "Elevated Corporate",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-office-elevated?w=400&h=500&fit=crop",
                "style_tags": ["elevated-corporate", "silk-blouse", "pencil-skirt", "pearl-earrings", "polished-feminine"],
                "next": "color_f",
            },
        ],
    },
    "f_sc_soft_q3": {
        "prompt": "Which soft minimal world feels like home?",
        "options": [
            {
                "id": "f_sc_soft_cloud",
                "label": "Cloud Neutral",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-soft-cloud?w=400&h=500&fit=crop",
                "style_tags": ["cloud-neutral", "cream-on-cream", "cashmere", "soft-knits", "ethereal-calm"],
                "next": "color_f",
            },
            {
                "id": "f_sc_soft_organic",
                "label": "Organic Minimal",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-soft-organic?w=400&h=500&fit=crop",
                "style_tags": ["organic-minimal", "natural-linen", "undyed-fabrics", "raw-textures", "sustainable"],
                "next": "color_f",
            },
            {
                "id": "f_sc_soft_japandi",
                "label": "Japandi Living",
                "image_url": "https://images.unsplash.com/photo-placeholder-f-soft-japandi?w=400&h=500&fit=crop",
                "style_tags": ["Japandi", "structured-simplicity", "neutral-palette", "clean-geometric", "zen-inspired"],
                "next": "color_f",
            },
        ],
    },
}

# ── Cross-cutting Q4 (color) and Q5 (fit) nodes ─────────────────

COLOR_NODES = {
    "color_m": {
        "prompt": "Which color palette draws you in?",
        "options": [
            {
                "id": "color_m_earth",
                "label": "Earth & Warm Neutrals",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-m-earth?w=400&h=500&fit=crop",
                "style_tags": ["earth-tones", "warm-neutrals", "brown", "tan", "olive", "cream"],
                "next": "fit_m",
            },
            {
                "id": "color_m_dark",
                "label": "Dark & Moody",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-m-dark?w=400&h=500&fit=crop",
                "style_tags": ["dark-palette", "cool-tones", "black", "navy", "charcoal", "burgundy"],
                "next": "fit_m",
            },
            {
                "id": "color_m_bold",
                "label": "Bold & Vivid",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-m-bold?w=400&h=500&fit=crop",
                "style_tags": ["bold-colors", "statement-color", "vibrant", "red", "cobalt", "emerald"],
                "next": "fit_m",
            },
            {
                "id": "color_m_muted",
                "label": "Soft & Muted",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-m-muted?w=400&h=500&fit=crop",
                "style_tags": ["muted-tones", "pastel", "sage", "dusty-blue", "lavender", "soft-palette"],
                "next": "fit_m",
            },
        ],
    },
    "color_f": {
        "prompt": "Which color palette draws you in?",
        "options": [
            {
                "id": "color_f_earth",
                "label": "Earth & Warm Neutrals",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-f-earth?w=400&h=500&fit=crop",
                "style_tags": ["earth-tones", "warm-neutrals", "brown", "tan", "olive", "cream"],
                "next": "fit_f",
            },
            {
                "id": "color_f_dark",
                "label": "Dark & Moody",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-f-dark?w=400&h=500&fit=crop",
                "style_tags": ["dark-palette", "cool-tones", "black", "navy", "charcoal", "burgundy"],
                "next": "fit_f",
            },
            {
                "id": "color_f_bold",
                "label": "Bold & Vivid",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-f-bold?w=400&h=500&fit=crop",
                "style_tags": ["bold-colors", "statement-color", "vibrant", "red", "cobalt", "emerald"],
                "next": "fit_f",
            },
            {
                "id": "color_f_muted",
                "label": "Soft & Muted",
                "image_url": "https://images.unsplash.com/photo-placeholder-color-f-muted?w=400&h=500&fit=crop",
                "style_tags": ["muted-tones", "pastel", "sage", "dusty-blue", "lavender", "soft-palette"],
                "next": "fit_f",
            },
        ],
    },
}

FIT_NODES = {
    "fit_m": {
        "prompt": "What silhouette feels most you?",
        "options": [
            {
                "id": "fit_m_slim",
                "label": "Slim & Tailored",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-m-slim?w=400&h=500&fit=crop",
                "style_tags": ["slim-fit", "fitted", "tailored", "structured", "defined"],
                "next": None,
            },
            {
                "id": "fit_m_relaxed",
                "label": "Relaxed & Oversized",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-m-relaxed?w=400&h=500&fit=crop",
                "style_tags": ["relaxed-fit", "oversized", "wide-leg", "dropped-shoulder", "volume"],
                "next": None,
            },
            {
                "id": "fit_m_classic",
                "label": "Classic & Balanced",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-m-classic?w=400&h=500&fit=crop",
                "style_tags": ["classic-fit", "proportioned", "versatile", "balanced", "traditional"],
                "next": None,
            },
            {
                "id": "fit_m_layered",
                "label": "Layered & Experimental",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-m-layered?w=400&h=500&fit=crop",
                "style_tags": ["layered", "proportion-play", "deconstructed", "mixed-silhouettes", "experimental"],
                "next": None,
            },
        ],
    },
    "fit_f": {
        "prompt": "What silhouette feels most you?",
        "options": [
            {
                "id": "fit_f_slim",
                "label": "Slim & Tailored",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-f-slim?w=400&h=500&fit=crop",
                "style_tags": ["slim-fit", "fitted", "tailored", "structured", "defined"],
                "next": None,
            },
            {
                "id": "fit_f_relaxed",
                "label": "Relaxed & Oversized",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-f-relaxed?w=400&h=500&fit=crop",
                "style_tags": ["relaxed-fit", "oversized", "wide-leg", "dropped-shoulder", "volume"],
                "next": None,
            },
            {
                "id": "fit_f_classic",
                "label": "Classic & Balanced",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-f-classic?w=400&h=500&fit=crop",
                "style_tags": ["classic-fit", "proportioned", "versatile", "balanced", "traditional"],
                "next": None,
            },
            {
                "id": "fit_f_layered",
                "label": "Layered & Experimental",
                "image_url": "https://images.unsplash.com/photo-placeholder-fit-f-layered?w=400&h=500&fit=crop",
                "style_tags": ["layered", "proportion-play", "deconstructed", "mixed-silhouettes", "experimental"],
                "next": None,
            },
        ],
    },
}

# ── Mapping: dead-end Q2 option IDs → new Q3 node IDs ──────────

DEAD_END_TO_Q3 = {
    # Male
    "m_om_coastal": "m_om_coast_q3",
    "m_vt_y2k": "m_vt_y2k_q3",
    "m_sc_work": "m_sc_work_q3",
    # Female
    "f_sw_tech": "f_sw_tech_q3",
    "f_om_euro": "f_om_euro_q3",
    "f_om_coastal": "f_om_coast_q3",
    "f_vt_cottage": "f_vt_cottage_q3",
    "f_vt_80s": "f_vt_80s_q3",
    "f_vt_y2k": "f_vt_y2k_q3",
    "f_al_sporty": "f_al_sporty_q3",
    "f_al_outdoor": "f_al_outdoor_q3",
    "f_al_retro": "f_al_retro_q3",
    "f_sc_office": "f_sc_office_q3",
    "f_sc_soft": "f_sc_soft_q3",
}

# ── Mapping: Q3 node prefix → color node ─────────────────────────

def get_color_node(node_id: str) -> str:
    if node_id.startswith("f_"):
        return "color_f"
    return "color_m"  # male + NB share male tree


def apply_transformations():
    """Apply all transformations to quiz_service.py."""
    with open(QUIZ_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    changes = 0

    # 1. Fix dead-end Q2 options: update next: None → new Q3 node
    for opt_id, q3_node in DEAD_END_TO_Q3.items():
        # Pattern: find the option block containing this ID and replace its next: None
        # We look for "id": "opt_id" ... "next": None within the same option dict
        pattern = re.compile(
            r'("id":\s*"' + re.escape(opt_id) + r'".*?"next":\s*)None',
            re.DOTALL,
        )
        new_content, n = pattern.subn(r'\1"' + q3_node + '"', content, count=1)
        if n:
            content = new_content
            changes += 1
            print(f"  Updated dead-end: {opt_id} -> {q3_node}")
        else:
            print(f"  WARNING: Could not find dead-end option {opt_id}")

    # 2. Fix existing Q3 terminal options: update next: None → color node
    for node_id in QUIZ_TREE:
        if "_q3" not in node_id:
            continue
        color_node = get_color_node(node_id)
        node = QUIZ_TREE[node_id]
        for opt in node["options"]:
            if opt["next"] is not None:
                continue
            opt_id = opt["id"]
            pattern = re.compile(
                r'("id":\s*"' + re.escape(opt_id) + r'".*?"next":\s*)None',
                re.DOTALL,
            )
            new_content, n = pattern.subn(r'\1"' + color_node + '"', content, count=1)
            if n:
                content = new_content
                changes += 1
            else:
                print(f"  WARNING: Could not find Q3 terminal {opt_id}")

    print(f"\n  Updated {changes} 'next: None' references")

    # 3. Append new nodes before the closing "}" of QUIZ_TREE
    # Find the last "}" that closes QUIZ_TREE (it's the "}" right before the Public API section)
    insert_marker = "\n}\n\n\n# ── Public API"
    if insert_marker not in content:
        # Try alternate spacing
        insert_marker = "}\n\n\n# ── Public API"
        if insert_marker not in content:
            print("  ERROR: Cannot find QUIZ_TREE closing brace + Public API marker")
            sys.exit(1)

    all_new_nodes = {}
    all_new_nodes.update(NEW_Q3_NODES)
    all_new_nodes.update(COLOR_NODES)
    all_new_nodes.update(FIT_NODES)

    new_node_lines = []
    for node_id, node_data in all_new_nodes.items():
        new_node_lines.append(f'    "{node_id}": {{')
        new_node_lines.append(f'        "prompt": "{node_data["prompt"]}",')
        new_node_lines.append(f'        "options": [')
        for opt in node_data["options"]:
            new_node_lines.append(f'            {{')
            new_node_lines.append(f'                "id": "{opt["id"]}",')
            new_node_lines.append(f'                "label": "{opt["label"]}",')
            new_node_lines.append(f'                "image_url": "{opt["image_url"]}",')
            tags_str = ", ".join(f'"{t}"' for t in opt["style_tags"])
            new_node_lines.append(f'                "style_tags": [{tags_str}],')
            if opt["next"] is None:
                new_node_lines.append(f'                "next": None,')
            else:
                new_node_lines.append(f'                "next": "{opt["next"]}",')
            new_node_lines.append(f'            }},')
        new_node_lines.append(f'        ],')
        new_node_lines.append(f'    }},')

    new_block = "\n".join(new_node_lines)

    content = content.replace(
        insert_marker,
        f"\n{new_block}\n}}\n\n\n# ── Public API",
        1,
    )

    print(f"  Appended {len(all_new_nodes)} new nodes")

    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  Done! Updated {QUIZ_FILE}")


if __name__ == "__main__":
    print("Restructuring quiz tree...\n")
    apply_transformations()
