"""Adaptive visual style quiz for onboarding.

Tree structure:
  - QUIZ_TREE: dict of node_id → {prompt, options[]}
  - Each option: {id, label, image_url, style_tags, next}
      next=None means terminal — quiz ends after this answer
  - Start node is gender-aware: root_m / root_f / root_nb
  - Every path is exactly 5 questions deep:
      Q1 (style family) -> Q2 (sub-style) -> Q3 (variant) -> Q4 (color) -> Q5 (fit)
  - Cross-cutting Q4/Q5 nodes: color_m, color_f, fit_m, fit_f

Image note: all URLs point to AI-generated images in static/quiz_images/.
Run scripts/generate_quiz_images.py to regenerate, then scripts/update_quiz_urls.py to update URLs.
"""

# ── Chat-only questions (used by agent tools) ─────────────────────────────────

CHAT_QUESTIONS = {
    "sneakers": {
        "prompt": "Which sneaker style catches your eye?",
        "options": [
            {
                "id": "retro-runner",
                "label": "Retro Runner",
                "image_url": "/static/quiz_images/chat__sneakers__retro-runner.png",
                "style_tags": ["retro", "sporty"],
            },
            {
                "id": "high-tops",
                "label": "High Tops",
                "image_url": "/static/quiz_images/chat__sneakers__high-tops.png",
                "style_tags": ["streetwear", "bold"],
            },
            {
                "id": "slip-on",
                "label": "Slip-On",
                "image_url": "/static/quiz_images/chat__sneakers__slip-on.png",
                "style_tags": ["casual", "effortless"],
            },
            {
                "id": "designer-sneaker",
                "label": "Designer Sneaker",
                "image_url": "/static/quiz_images/chat__sneakers__designer-sneaker.png",
                "style_tags": ["luxury", "statement"],
            },
        ],
    },
    "formal_wear": {
        "prompt": "Which formal look suits you best?",
        "options": [
            {
                "id": "classic-suit",
                "label": "Classic Suit",
                "image_url": "/static/quiz_images/chat__formal_wear__classic-suit.png",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "modern-slim",
                "label": "Modern Slim Fit",
                "image_url": "/static/quiz_images/chat__formal_wear__modern-slim.png",
                "style_tags": ["modern", "sharp"],
            },
            {
                "id": "relaxed-formal",
                "label": "Relaxed Formal",
                "image_url": "/static/quiz_images/chat__formal_wear__relaxed-formal.png",
                "style_tags": ["relaxed", "smart-casual"],
            },
            {
                "id": "statement-formal",
                "label": "Statement Piece",
                "image_url": "/static/quiz_images/chat__formal_wear__statement-formal.png",
                "style_tags": ["bold", "fashion-forward"],
            },
        ],
    },
    "patterns": {
        "prompt": "Which pattern are you drawn to?",
        "options": [
            {
                "id": "stripes",
                "label": "Stripes",
                "image_url": "/static/quiz_images/chat__patterns__stripes.png",
                "style_tags": ["classic", "nautical"],
            },
            {
                "id": "plaid",
                "label": "Plaid",
                "image_url": "/static/quiz_images/chat__patterns__plaid.png",
                "style_tags": ["heritage", "rugged"],
            },
            {
                "id": "floral",
                "label": "Floral",
                "image_url": "/static/quiz_images/chat__patterns__floral.png",
                "style_tags": ["bohemian", "expressive"],
            },
            {
                "id": "solid",
                "label": "Solid Colors",
                "image_url": "/static/quiz_images/chat__patterns__solid.png",
                "style_tags": ["minimalist", "versatile"],
            },
        ],
    },
    "accessories": {
        "prompt": "Which accessory catches your eye?",
        "options": [
            {
                "id": "minimal-watch",
                "label": "Minimal Watch",
                "image_url": "/static/quiz_images/chat__accessories__minimal-watch.png",
                "style_tags": ["minimalist", "refined"],
            },
            {
                "id": "statement-sunglasses",
                "label": "Statement Sunglasses",
                "image_url": "/static/quiz_images/chat__accessories__statement-sunglasses.png",
                "style_tags": ["bold", "trendy"],
            },
            {
                "id": "leather-bag",
                "label": "Leather Bag",
                "image_url": "/static/quiz_images/chat__accessories__leather-bag.png",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "layered-jewelry",
                "label": "Layered Jewelry",
                "image_url": "/static/quiz_images/chat__accessories__layered-jewelry.png",
                "style_tags": ["bohemian", "expressive"],
            },
        ],
    },
    "dresses": {
        "prompt": "Which dress style do you love?",
        "options": [
            {
                "id": "wrap-dress",
                "label": "Wrap Dress",
                "image_url": "/static/quiz_images/chat__dresses__wrap-dress.png",
                "style_tags": ["classic", "feminine"],
            },
            {
                "id": "maxi-dress",
                "label": "Maxi Dress",
                "image_url": "/static/quiz_images/chat__dresses__maxi-dress.png",
                "style_tags": ["bohemian", "flowy"],
            },
            {
                "id": "shirt-dress",
                "label": "Shirt Dress",
                "image_url": "/static/quiz_images/chat__dresses__shirt-dress.png",
                "style_tags": ["smart-casual", "versatile"],
            },
            {
                "id": "mini-dress",
                "label": "Mini Dress",
                "image_url": "/static/quiz_images/chat__dresses__mini-dress.png",
                "style_tags": ["bold", "trendy"],
            },
        ],
    },
    "activewear": {
        "prompt": "Which activewear look is your go-to?",
        "options": [
            {
                "id": "matching-set",
                "label": "Matching Set",
                "image_url": "/static/quiz_images/chat__activewear__matching-set.png",
                "style_tags": ["put-together", "trendy"],
            },
            {
                "id": "classic-athletic",
                "label": "Classic Athletic",
                "image_url": "/static/quiz_images/chat__activewear__classic-athletic.png",
                "style_tags": ["sporty", "functional"],
            },
            {
                "id": "athleisure",
                "label": "Athleisure",
                "image_url": "/static/quiz_images/chat__activewear__athleisure.png",
                "style_tags": ["athleisure", "casual"],
            },
            {
                "id": "outdoor-active",
                "label": "Outdoor Active",
                "image_url": "/static/quiz_images/chat__activewear__outdoor-active.png",
                "style_tags": ["rugged", "outdoorsy"],
            },
        ],
    },
}


# ── Adaptive onboarding tree ──────────────────────────────────────────────────
#
# Naming convention:
#   root_m / root_f / root_nb   — Q1 by gender
#   m_ / f_ / nb_               — gender prefix for deeper nodes
#   _q2 / _q3                   — question depth within a branch
#   No suffix (or implied)      — terminal (next=None on all options)

QUIZ_TREE = {

    # ═══════════════════════════════════════════════════════════════
    # Q1 — ROOT (gender-specific images, same 5 broad styles)
    # ═══════════════════════════════════════════════════════════════

    "root_m": {
        "prompt": "Which of these looks closest to how you naturally dress?",
        "options": [
            {
                "id": "root_m_street",
                "label": "Streetwear",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_casual.png",
                "style_tags": ["streetwear"],
                "next": "m_sw_q2",
            },
            {
                "id": "root_m_oldmoney",
                "label": "Old Money",
                "image_url": "/static/quiz_images/tree__m_om_ital_q3__m_om_ital_sprezza.png",
                "style_tags": ["classic", "refined"],
                "next": "m_om_q2",
            },
            {
                "id": "root_m_vintage",
                "label": "Vintage",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["vintage"],
                "next": "m_vt_q2",
            },
            {
                "id": "root_m_ath",
                "label": "Athleisure",
                "image_url": "/static/quiz_images/tree__m_al_perf_q3__m_al_perf_mono.png",
                "style_tags": ["athleisure"],
                "next": "m_al_q2",
            },
            {
                "id": "root_m_smart",
                "label": "Smart & Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["minimalist", "smart-casual"],
                "next": "m_sc_q2",
            },
        ],
    },

    "root_f": {
        "prompt": "Which of these looks closest to how you naturally dress?",
        "options": [
            {
                "id": "root_f_street",
                "label": "Streetwear",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["streetwear"],
                "next": "f_sw_q2",
            },
            {
                "id": "root_f_oldmoney",
                "label": "Old Money",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_casual.png",
                "style_tags": ["classic", "refined"],
                "next": "f_om_q2",
            },
            {
                "id": "root_f_vintage",
                "label": "Vintage",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["vintage"],
                "next": "f_vt_q2",
            },
            {
                "id": "root_f_ath",
                "label": "Athleisure",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_pilates.png",
                "style_tags": ["athleisure"],
                "next": "f_al_q2",
            },
            {
                "id": "root_f_smart",
                "label": "Smart & Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["minimalist", "smart-casual"],
                "next": "f_sc_q2",
            },
        ],
    },

    "root_nb": {
        "prompt": "Which of these looks closest to how you naturally dress?",
        "options": [
            {
                "id": "root_nb_street",
                "label": "Streetwear",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["streetwear"],
                "next": "m_sw_q2",
            },
            {
                "id": "root_nb_oldmoney",
                "label": "Old Money",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["classic", "refined"],
                "next": "m_om_q2",
            },
            {
                "id": "root_nb_vintage",
                "label": "Vintage",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["vintage"],
                "next": "m_vt_q2",
            },
            {
                "id": "root_nb_ath",
                "label": "Athleisure",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_power.png",
                "style_tags": ["athleisure"],
                "next": "m_al_q2",
            },
            {
                "id": "root_nb_smart",
                "label": "Smart & Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["minimalist", "smart-casual"],
                "next": "m_sc_q2",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # MEN'S STREETWEAR BRANCH
    # ═══════════════════════════════════════════════════════════════

    "m_sw_q2": {
        "prompt": "What's your streetwear energy?",
        "options": [
            {
                "id": "m_sw_skate",
                "label": "Skate / Surf",
                "image_url": "/static/quiz_images/tree__f_sw_q2__f_sw_tech.png",
                "style_tags": ["skate", "casual", "laid-back"],
                "next": "m_sw_skate_q3",
            },
            {
                "id": "m_sw_tech",
                "label": "Techwear / Utility",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_chic.png",
                "style_tags": ["techwear", "utility", "functional"],
                "next": "m_sw_tech_q3",
            },
            {
                "id": "m_sw_hiphop",
                "label": "Hip-Hop / Oversized",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_elevated.png",
                "style_tags": ["oversized", "urban", "bold"],
                "next": "m_sw_hiphop_q3",
            },
            {
                "id": "m_sw_hype",
                "label": "Hype / Sneakerhead",
                "image_url": "/static/quiz_images/tree__m_sw_q2__m_sw_hype.png",
                "style_tags": ["hype", "sneakerhead", "statement"],
                "next": "m_sw_hype_q3",
            },
        ],
    },

    # ── Men's Skate Q3 ────────────────────────────────────────────
    "m_sw_skate_q3": {
        "prompt": "Which skate aesthetic fits your vibe best?",
        "options": [
            {
                "id": "m_sw_skate_90s",
                "label": "90s Old-School",
                "image_url": "/static/quiz_images/tree__m_vt_q2__m_vt_70s.png",
                "style_tags": ["vintage-skate", "90s", "baggy", "graphic-tees", "Vans"],
                "next": "color_m",
            },
            {
                "id": "m_sw_skate_modern",
                "label": "Modern Minimalist Skate",
                "image_url": "/static/quiz_images/tree__m_sw_skate_q3__m_sw_skate_modern.png",
                "style_tags": ["skate", "earth-tones", "understated", "clean-lines"],
                "next": "color_m",
            },
            {
                "id": "m_sw_skate_surf",
                "label": "Surf-Skate Crossover",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_paris.png",
                "style_tags": ["surf", "beach-casual", "loose-denim", "bright-accents"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Techwear Q3 ─────────────────────────────────────────
    "m_sw_tech_q3": {
        "prompt": "Which technical aesthetic speaks to you?",
        "options": [
            {
                "id": "m_sw_tech_dark",
                "label": "Dark Techwear",
                "image_url": "/static/quiz_images/tree__m_sc_q2__m_sc_japan.png",
                "style_tags": ["techwear", "all-black", "cargo", "ACRONYM", "tactical"],
                "next": "color_m",
            },
            {
                "id": "m_sw_tech_gorpcore",
                "label": "Gorpcore",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_outdoor.png",
                "style_tags": ["gorpcore", "outdoor-brands", "earth-tones", "functional", "Arc'teryx"],
                "next": "color_m",
            },
            {
                "id": "m_sw_tech_sport",
                "label": "Soft Sporty",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_power.png",
                "style_tags": ["sporty", "Nike", "Adidas", "technical", "off-court"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Hip-Hop Q3 ──────────────────────────────────────────
    "m_sw_hiphop_q3": {
        "prompt": "What's the soul of your oversized look?",
        "options": [
            {
                "id": "m_sw_hiphop_classic",
                "label": "Classic Hip-Hop",
                "image_url": "/static/quiz_images/tree__m_sw_hiphop_q3__m_sw_hiphop_classic.png",
                "style_tags": ["hip-hop", "90s", "Timberlands", "puffer", "gold-chain", "retro"],
                "next": "color_m",
            },
            {
                "id": "m_sw_hiphop_luxe",
                "label": "Luxury Streetwear",
                "image_url": "/static/quiz_images/tree__m_sw_hiphop_q3__m_sw_hiphop_luxe.png",
                "style_tags": ["luxury-streetwear", "dark", "layered", "elevated", "Rick-Owens"],
                "next": "color_m",
            },
            {
                "id": "m_sw_hiphop_tonal",
                "label": "Clean & Tonal",
                "image_url": "/static/quiz_images/tree__m_sc_euro_q3__m_sc_euro_relaxed.png",
                "style_tags": ["tonal", "neutral-palette", "oversized", "subtle-branding", "clean"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Hype Q3 ─────────────────────────────────────────────
    "m_sw_hype_q3": {
        "prompt": "Around the sneakers, you build...",
        "options": [
            {
                "id": "m_sw_hype_neutral",
                "label": "Neutral Canvas",
                "image_url": "/static/quiz_images/tree__m_sw_hype_q3__m_sw_hype_neutral.png",
                "style_tags": ["neutral", "minimalist-fit", "sneaker-focused", "understated"],
                "next": "color_m",
            },
            {
                "id": "m_sw_hype_coord",
                "label": "Coordinated Colorways",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_disco.png",
                "style_tags": ["color-coordinated", "matching-sets", "bold-colorblocking", "hype"],
                "next": "color_m",
            },
            {
                "id": "m_sw_hype_loud",
                "label": "Full Statement",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["graphic-heavy", "loud-patterns", "statement", "maximalist"],
                "next": "color_m",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # MEN'S OLD MONEY BRANCH
    # ═══════════════════════════════════════════════════════════════

    "m_om_q2": {
        "prompt": "Which old money tradition resonates with you?",
        "options": [
            {
                "id": "m_om_brit",
                "label": "British Heritage",
                "image_url": "/static/quiz_images/tree__m_om_q2__m_om_brit.png",
                "style_tags": ["heritage", "British", "tailored"],
                "next": "m_om_brit_q3",
            },
            {
                "id": "m_om_ital",
                "label": "Italian Tailoring",
                "image_url": "/static/quiz_images/tree__m_om_q2__m_om_ital.png",
                "style_tags": ["Italian", "tailored", "elegant"],
                "next": "m_om_ital_q3",
            },
            {
                "id": "m_om_prep",
                "label": "American Prep",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_office.png",
                "style_tags": ["preppy", "collegiate", "American"],
                "next": "m_om_prep_q3",
            },
            {
                "id": "m_om_coastal",
                "label": "Coastal / Nautical",
                "image_url": "/static/quiz_images/tree__f_om_q2__f_om_coastal.png",
                "style_tags": ["coastal", "nautical", "linen", "navy", "relaxed-elegance"],
                "next": "m_om_coast_q3",
            },
        ],
    },

    # ── Men's British Q3 ──────────────────────────────────────────
    "m_om_brit_q3": {
        "prompt": "Your British style — country or city?",
        "options": [
            {
                "id": "m_om_brit_country",
                "label": "Country Estate",
                "image_url": "/static/quiz_images/tree__m_al_outdoor_q3__m_al_outdoor_expedition.png",
                "style_tags": ["tweed", "Barbour", "Hunter-boots", "heritage-outerwear", "country"],
                "next": "color_m",
            },
            {
                "id": "m_om_brit_city",
                "label": "City Gent",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_academia.png",
                "style_tags": ["three-piece", "pocket-square", "brogues", "polished", "Savile-Row"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Italian Q3 ──────────────────────────────────────────
    "m_om_ital_q3": {
        "prompt": "Your Italian dressing style...",
        "options": [
            {
                "id": "m_om_ital_sprezza",
                "label": "Sprezzatura",
                "image_url": "/static/quiz_images/tree__m_om_ital_q3__m_om_ital_sprezza.png",
                "style_tags": ["sprezzatura", "unlined-blazer", "deliberate-imperfection", "Mediterranean", "effortless-elegance"],
                "next": "color_m",
            },
            {
                "id": "m_om_ital_milan",
                "label": "Modern Milan",
                "image_url": "/static/quiz_images/tree__m_vt_8090_q3__m_vt_8090_sport.png",
                "style_tags": ["modern-luxury", "sleek", "dark-palette", "Milan", "minimal-luxury"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Prep Q3 ─────────────────────────────────────────────
    "m_om_prep_q3": {
        "prompt": "Classic Ivy League or updated prep?",
        "options": [
            {
                "id": "m_om_prep_ivy",
                "label": "Classic Ivy",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_ivy.png",
                "style_tags": ["Ivy-League", "OCBD", "navy-blazer", "khakis", "boat-shoes", "timeless"],
                "next": "color_m",
            },
            {
                "id": "m_om_prep_modern",
                "label": "Modern Prep",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_office.png",
                "style_tags": ["modern-prep", "updated-silhouettes", "unexpected-colors", "elevated-basics"],
                "next": "color_m",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # MEN'S VINTAGE BRANCH
    # ═══════════════════════════════════════════════════════════════

    "m_vt_q2": {
        "prompt": "Which era pulls you in most?",
        "options": [
            {
                "id": "m_vt_70s",
                "label": "70s — Rock & Disco",
                "image_url": "/static/quiz_images/tree__m_vt_q2__m_vt_70s.png",
                "style_tags": ["70s", "vintage"],
                "next": "m_vt_70s_q3",
            },
            {
                "id": "m_vt_8090",
                "label": "80s / 90s — Sports & Street",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["80s", "90s", "retro"],
                "next": "m_vt_8090_q3",
            },
            {
                "id": "m_vt_americana",
                "label": "Americana / Workwear",
                "image_url": "/static/quiz_images/tree__m_al_outdoor_q3__m_al_outdoor_expedition.png",
                "style_tags": ["Americana", "workwear", "heritage"],
                "next": "m_vt_work_q3",
            },
            {
                "id": "m_vt_y2k",
                "label": "Y2K / Early 2000s",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["Y2K", "2000s", "logomania", "low-rise", "chrome"],
                "next": "m_vt_y2k_q3",
            },
        ],
    },

    # ── Men's 70s Q3 ──────────────────────────────────────────────
    "m_vt_70s_q3": {
        "prompt": "Your 70s energy is...",
        "options": [
            {
                "id": "m_vt_70s_rock",
                "label": "Rock & Roll",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["rock", "band-tees", "flares", "Chelsea-boots", "leather-jacket"],
                "next": "color_m",
            },
            {
                "id": "m_vt_70s_boho",
                "label": "Boho / Folk",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_folk.png",
                "style_tags": ["bohemian", "folk", "loose-linen", "earth-tones", "fringe"],
                "next": "color_m",
            },
            {
                "id": "m_vt_70s_disco",
                "label": "Disco Glam",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_disco.png",
                "style_tags": ["disco", "satin", "wide-leg", "retro-prints", "statement-accessories"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's 80s/90s Q3 ──────────────────────────────────────────
    "m_vt_8090_q3": {
        "prompt": "Your 80s/90s flavor...",
        "options": [
            {
                "id": "m_vt_8090_hiphop",
                "label": "Old-School Hip-Hop",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_casual.png",
                "style_tags": ["old-school", "tracksuit", "bucket-hat", "vintage-Adidas", "90s-hip-hop"],
                "next": "color_m",
            },
            {
                "id": "m_vt_8090_grunge",
                "label": "Grunge",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_grunge.png",
                "style_tags": ["grunge", "flannel", "ripped-denim", "boots", "layering", "90s"],
                "next": "color_m",
            },
            {
                "id": "m_vt_8090_sport",
                "label": "Sports / Collegiate",
                "image_url": "/static/quiz_images/tree__m_vt_8090_q3__m_vt_8090_sport.png",
                "style_tags": ["varsity-jacket", "collegiate", "retro-tees", "court-sneakers", "sporty"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Americana Q3 ────────────────────────────────────────
    "m_vt_work_q3": {
        "prompt": "Your workwear influence leans toward...",
        "options": [
            {
                "id": "m_vt_work_americana",
                "label": "Classic Americana",
                "image_url": "/static/quiz_images/tree__m_al_outdoor_q3__m_al_outdoor_expedition.png",
                "style_tags": ["Americana", "Levi's", "Carhartt", "work-boots", "utilitarian", "raw-denim"],
                "next": "color_m",
            },
            {
                "id": "m_vt_work_selvedge",
                "label": "Japanese Selvedge",
                "image_url": "/static/quiz_images/tree__m_vt_work_q3__m_vt_work_selvedge.png",
                "style_tags": ["selvedge-denim", "Japanese-workwear", "indigo", "slow-fashion", "sashiko"],
                "next": "color_m",
            },
            {
                "id": "m_vt_work_military",
                "label": "Military Surplus",
                "image_url": "/static/quiz_images/tree__m_vt_work_q3__m_vt_work_military.png",
                "style_tags": ["military", "field-jacket", "cargo", "surplus", "functional"],
                "next": "color_m",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # MEN'S ATHLEISURE BRANCH
    # ═══════════════════════════════════════════════════════════════

    "m_al_q2": {
        "prompt": "What drives your athleisure look?",
        "options": [
            {
                "id": "m_al_perf",
                "label": "Performance First",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_sporty.png",
                "style_tags": ["performance", "functional", "training"],
                "next": "m_al_perf_q3",
            },
            {
                "id": "m_al_fashion",
                "label": "Fashion-Forward Sport",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_power.png",
                "style_tags": ["fashion-sport", "design-led", "luxury-sport"],
                "next": "m_al_fashion_q3",
            },
            {
                "id": "m_al_outdoor",
                "label": "Outdoor / Adventure",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_outdoor.png",
                "style_tags": ["outdoor", "adventure", "technical"],
                "next": "m_al_outdoor_q3",
            },
        ],
    },

    # ── Men's Performance Q3 ──────────────────────────────────────
    "m_al_perf_q3": {
        "prompt": "Your performance style is...",
        "options": [
            {
                "id": "m_al_perf_mono",
                "label": "Clean Monochrome",
                "image_url": "/static/quiz_images/tree__m_al_perf_q3__m_al_perf_mono.png",
                "style_tags": ["monochrome", "single-brand", "clean", "Nike", "Adidas", "minimal-sport"],
                "next": "color_m",
            },
            {
                "id": "m_al_perf_mixed",
                "label": "Mixed Performance",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_sporty.png",
                "style_tags": ["multi-brand", "elite-gear", "function-maximalist", "technical-layers"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Fashion Sport Q3 ────────────────────────────────────
    "m_al_fashion_q3": {
        "prompt": "Your fashion sport energy...",
        "options": [
            {
                "id": "m_al_fashion_luxury",
                "label": "Luxury Sport",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_power.png",
                "style_tags": ["luxury-sport", "Lululemon", "Vuori", "premium-basics", "elevated-casual"],
                "next": "color_m",
            },
            {
                "id": "m_al_fashion_hype",
                "label": "Hype Sport",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["Jordan", "collab-pieces", "streetwear-sport", "hype", "limited-edition"],
                "next": "color_m",
            },
            {
                "id": "m_al_fashion_retro",
                "label": "Y2K Sport Revival",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["retro-sport", "vintage-Adidas", "Fila", "track-jacket", "throwback-athletic"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Outdoor Q3 ──────────────────────────────────────────
    "m_al_outdoor_q3": {
        "prompt": "Your outdoor aesthetic...",
        "options": [
            {
                "id": "m_al_outdoor_gorpcore",
                "label": "Gorpcore",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_outdoor.png",
                "style_tags": ["gorpcore", "Arc'teryx", "Salomon", "Patagonia", "outdoor-in-the-city"],
                "next": "color_m",
            },
            {
                "id": "m_al_outdoor_trail",
                "label": "Trail Runner",
                "image_url": "/static/quiz_images/tree__m_al_outdoor_q3__m_al_outdoor_trail.png",
                "style_tags": ["trail", "minimal-tech", "movement-focused", "trail-shoes", "lightweight"],
                "next": "color_m",
            },
            {
                "id": "m_al_outdoor_expedition",
                "label": "Expedition Ready",
                "image_url": "/static/quiz_images/tree__m_al_outdoor_q3__m_al_outdoor_expedition.png",
                "style_tags": ["expedition", "insulated-layers", "waterproof", "heavy-duty", "mountaineer"],
                "next": "color_m",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # MEN'S SMART CASUAL / MODERN MINIMAL BRANCH
    # ═══════════════════════════════════════════════════════════════

    "m_sc_q2": {
        "prompt": "What's the foundation of your refined look?",
        "options": [
            {
                "id": "m_sc_quiet",
                "label": "Quiet Luxury",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["quiet-luxury", "elevated-fabrics", "neutral-palette"],
                "next": "m_sc_quiet_q3",
            },
            {
                "id": "m_sc_euro",
                "label": "European Contemporary",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_ivy.png",
                "style_tags": ["European", "contemporary", "COS", "Arket", "architectural"],
                "next": "m_sc_euro_q3",
            },
            {
                "id": "m_sc_japan",
                "label": "Japanese Minimalism",
                "image_url": "/static/quiz_images/tree__m_sc_q2__m_sc_japan.png",
                "style_tags": ["Japanese", "minimalist", "natural-fabrics"],
                "next": "m_sc_japan_q3",
            },
            {
                "id": "m_sc_work",
                "label": "Smart-Casual Workwear",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_office.png",
                "style_tags": ["smart-casual", "business-casual", "tailored", "professional", "versatile"],
                "next": "m_sc_work_q3",
            },
        ],
    },

    # ── Men's Quiet Luxury Q3 ─────────────────────────────────────
    "m_sc_quiet_q3": {
        "prompt": "Your quiet luxury is led by...",
        "options": [
            {
                "id": "m_sc_quiet_tonal",
                "label": "Tonal Neutrals",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["tonal-dressing", "camel", "cream", "navy", "head-to-toe-neutral"],
                "next": "color_m",
            },
            {
                "id": "m_sc_quiet_texture",
                "label": "Subtle Texture",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["cashmere", "suede", "twill", "material-led", "tactile-luxury"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's European Q3 ─────────────────────────────────────────
    "m_sc_euro_q3": {
        "prompt": "Your European minimal is...",
        "options": [
            {
                "id": "m_sc_euro_structured",
                "label": "Structured",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_academia.png",
                "style_tags": ["structured", "clean-lines", "fitted", "architectural", "precise"],
                "next": "color_m",
            },
            {
                "id": "m_sc_euro_relaxed",
                "label": "Relaxed Volume",
                "image_url": "/static/quiz_images/tree__m_sc_euro_q3__m_sc_euro_relaxed.png",
                "style_tags": ["wide-leg", "dropped-shoulder", "oversized-precise", "relaxed-tailoring"],
                "next": "color_m",
            },
        ],
    },

    # ── Men's Japanese Q3 ─────────────────────────────────────────
    "m_sc_japan_q3": {
        "prompt": "Your Japanese aesthetic specifically...",
        "options": [
            {
                "id": "m_sc_japan_muji",
                "label": "Pure Minimalism",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["Muji", "Uniqlo", "quality-basics", "functional-minimalism", "refined"],
                "next": "color_m",
            },
            {
                "id": "m_sc_japan_avantgarde",
                "label": "Avant-Garde",
                "image_url": "/static/quiz_images/tree__f_sw_luxe_q3__f_sw_luxe_logo.png",
                "style_tags": ["CDG", "Yohji", "deconstructed", "asymmetric", "dark", "avant-garde"],
                "next": "color_m",
            },
            {
                "id": "m_sc_japan_wabi",
                "label": "Wabi-Sabi",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["wabi-sabi", "natural-dyes", "artisan", "imperfect-texture", "slow-fashion"],
                "next": "color_m",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # WOMEN'S STREETWEAR BRANCH
    # ═══════════════════════════════════════════════════════════════

    "f_sw_q2": {
        "prompt": "What's your streetwear vibe?",
        "options": [
            {
                "id": "f_sw_tomboy",
                "label": "Tomboy / Skate",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_grunge.png",
                "style_tags": ["tomboy", "skate", "oversized"],
                "next": "f_sw_tomboy_q3",
            },
            {
                "id": "f_sw_luxe",
                "label": "Luxe Street",
                "image_url": "/static/quiz_images/tree__f_sw_luxe_q3__f_sw_luxe_quiet.png",
                "style_tags": ["luxury-streetwear", "elevated", "designer"],
                "next": "f_sw_luxe_q3",
            },
            {
                "id": "f_sw_y2k",
                "label": "Y2K / Baddie",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["Y2K", "baddie", "bold"],
                "next": "f_sw_y2k_q3",
            },
            {
                "id": "f_sw_tech",
                "label": "Techwear / Utility",
                "image_url": "/static/quiz_images/tree__f_sw_q2__f_sw_tech.png",
                "style_tags": ["techwear", "utility", "dark", "functional", "technical-fabrics"],
                "next": "f_sw_tech_q3",
            },
        ],
    },

    # ── Women's Tomboy Q3 ─────────────────────────────────────────
    "f_sw_tomboy_q3": {
        "prompt": "Your tomboy style leans toward...",
        "options": [
            {
                "id": "f_sw_tomboy_skate",
                "label": "90s Skate",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["90s-skate", "baggy-cargos", "graphic-tee", "chunky-sneakers", "relaxed"],
                "next": "color_f",
            },
            {
                "id": "f_sw_tomboy_tailored",
                "label": "Tailored Menswear",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_casual.png",
                "style_tags": ["menswear-inspired", "oversized-blazer", "wide-trousers", "androgynous", "tailored"],
                "next": "color_f",
            },
        ],
    },

    # ── Women's Luxe Street Q3 ────────────────────────────────────
    "f_sw_luxe_q3": {
        "prompt": "Your luxe streetwear is...",
        "options": [
            {
                "id": "f_sw_luxe_logo",
                "label": "Logomania",
                "image_url": "/static/quiz_images/tree__f_sw_luxe_q3__f_sw_luxe_logo.png",
                "style_tags": ["logomania", "Gucci", "Fendi", "prominent-branding", "luxury-logos"],
                "next": "color_f",
            },
            {
                "id": "f_sw_luxe_quiet",
                "label": "Quiet Hype",
                "image_url": "/static/quiz_images/tree__f_sw_luxe_q3__f_sw_luxe_quiet.png",
                "style_tags": ["quiet-hype", "understated-luxury", "tonal", "clean", "premium-streetwear"],
                "next": "color_f",
            },
            {
                "id": "f_sw_luxe_art",
                "label": "Streetwear Art",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["statement-graphics", "art-driven", "collab-pieces", "creative", "expressive"],
                "next": "color_f",
            },
        ],
    },

    # ── Women's Y2K Q3 ────────────────────────────────────────────
    "f_sw_y2k_q3": {
        "prompt": "Your Y2K energy...",
        "options": [
            {
                "id": "f_sw_y2k_classic",
                "label": "Classic Revival",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["Y2K", "low-rise", "butterfly-clips", "shiny-fabrics", "2000s-nostalgia"],
                "next": "color_f",
            },
            {
                "id": "f_sw_y2k_baddie",
                "label": "Modern Baddie",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["baddie", "bodycon", "polished", "powerful", "glam"],
                "next": "color_f",
            },
            {
                "id": "f_sw_y2k_soft",
                "label": "Soft Y2K",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_y2k.png",
                "style_tags": ["soft-Y2K", "pastel", "baby-tee", "mini-skirt", "feminine", "coquette"],
                "next": "color_f",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # WOMEN'S OLD MONEY BRANCH
    # ═══════════════════════════════════════════════════════════════

    "f_om_q2": {
        "prompt": "Your old money energy is...",
        "options": [
            {
                "id": "f_om_quiet",
                "label": "Quiet Luxury",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["quiet-luxury", "The-Row", "Bottega"],
                "next": "f_om_quiet_q3",
            },
            {
                "id": "f_om_prep",
                "label": "Heritage Prep",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_casual.png",
                "style_tags": ["heritage-prep", "collegiate", "plaid"],
                "next": "f_om_prep_q3",
            },
            {
                "id": "f_om_euro",
                "label": "European Aristocrat",
                "image_url": "/static/quiz_images/tree__f_om_q2__f_om_euro.png",
                "style_tags": ["silk-scarf", "structured-bag", "timeless", "European", "classic-chic"],
                "next": "f_om_euro_q3",
            },
            {
                "id": "f_om_coastal",
                "label": "Coastal / Equestrian",
                "image_url": "/static/quiz_images/tree__f_om_q2__f_om_coastal.png",
                "style_tags": ["coastal", "equestrian", "cream-knits", "riding-boots", "nautical", "classic"],
                "next": "f_om_coast_q3",
            },
        ],
    },

    # ── Women's Quiet Luxury Q3 ───────────────────────────────────
    "f_om_quiet_q3": {
        "prompt": "Your quiet luxury specifically...",
        "options": [
            {
                "id": "f_om_quiet_tonal",
                "label": "Monochrome Neutral",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_soft.png",
                "style_tags": ["monochrome", "camel", "cream", "grey", "head-to-toe-tonal", "The-Row"],
                "next": "color_f",
            },
            {
                "id": "f_om_quiet_sculptural",
                "label": "Sculptural Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_mono.png",
                "style_tags": ["sculptural", "interesting-silhouette", "quality-fabric", "logo-free", "Bottega"],
                "next": "color_f",
            },
        ],
    },

    # ── Women's Prep Q3 ───────────────────────────────────────────
    "f_om_prep_q3": {
        "prompt": "Your prep aesthetic...",
        "options": [
            {
                "id": "f_om_prep_ivy",
                "label": "Classic Ivy",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_ivy.png",
                "style_tags": ["Ivy-League", "plaid-blazer", "loafers", "pearl-earrings", "collegiate"],
                "next": "color_f",
            },
            {
                "id": "f_om_prep_academia",
                "label": "Dark Academia",
                "image_url": "/static/quiz_images/tree__f_om_prep_q3__f_om_prep_academia.png",
                "style_tags": ["dark-academia", "tweed", "oxford-shoes", "vintage-scholarly", "moody"],
                "next": "color_f",
            },
            {
                "id": "f_om_prep_modern",
                "label": "Modern Prep",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["modern-prep", "sleek", "elevated-basics", "Ralph-Lauren", "refined-casual"],
                "next": "color_f",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # WOMEN'S VINTAGE BRANCH
    # ═══════════════════════════════════════════════════════════════

    "f_vt_q2": {
        "prompt": "Which vintage era speaks to you?",
        "options": [
            {
                "id": "f_vt_70s",
                "label": "70s — Boho & Disco",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_folk.png",
                "style_tags": ["70s", "bohemian"],
                "next": "f_vt_70s_q3",
            },
            {
                "id": "f_vt_90s",
                "label": "90s — Grunge & Minimal",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_grunge.png",
                "style_tags": ["90s", "grunge", "minimalism"],
                "next": "f_vt_90s_q3",
            },
            {
                "id": "f_vt_cottage",
                "label": "Cottagecore / Romantic",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_cottage.png",
                "style_tags": ["cottagecore", "romantic", "prairie-dress", "florals", "lace", "pastoral"],
                "next": "f_vt_cottage_q3",
            },
            {
                "id": "f_vt_80s",
                "label": "80s Power",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_80s.png",
                "style_tags": ["80s", "power-dressing", "shoulder-pads", "bold-prints", "statement-earrings"],
                "next": "f_vt_80s_q3",
            },
            {
                "id": "f_vt_y2k",
                "label": "Y2K / Early 2000s",
                "image_url": "/static/quiz_images/tree__f_vt_q2__f_vt_y2k.png",
                "style_tags": ["Y2K", "low-rise", "denim-skirt", "rhinestones", "2000s"],
                "next": "f_vt_y2k_q3",
            },
        ],
    },

    # ── Women's 70s Q3 ────────────────────────────────────────────
    "f_vt_70s_q3": {
        "prompt": "Your 70s look is...",
        "options": [
            {
                "id": "f_vt_70s_folk",
                "label": "Folk / Boho",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_folk.png",
                "style_tags": ["folk", "fringe", "embroidery", "free-spirited", "earth-tones", "bohemian"],
                "next": "color_f",
            },
            {
                "id": "f_vt_70s_disco",
                "label": "Disco Glamour",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_disco.png",
                "style_tags": ["disco", "satin", "sequins", "platforms", "wide-leg", "glam"],
                "next": "color_f",
            },
            {
                "id": "f_vt_70s_chic",
                "label": "70s Chic",
                "image_url": "/static/quiz_images/tree__f_vt_70s_q3__f_vt_70s_chic.png",
                "style_tags": ["70s-cool", "tailored-flares", "printed-blouses", "chic-simplicity"],
                "next": "color_f",
            },
        ],
    },

    # ── Women's 90s Q3 ────────────────────────────────────────────
    "f_vt_90s_q3": {
        "prompt": "Your 90s style...",
        "options": [
            {
                "id": "f_vt_90s_grunge",
                "label": "Grunge",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_grunge.png",
                "style_tags": ["grunge", "slip-dress-over-tee", "combat-boots", "flannel", "layering"],
                "next": "color_f",
            },
            {
                "id": "f_vt_90s_minimal",
                "label": "Minimalist 90s",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["Calvin-Klein", "slip-dress", "spaghetti-straps", "clean", "90s-minimal"],
                "next": "color_f",
            },
            {
                "id": "f_vt_90s_casual",
                "label": "90s Casual",
                "image_url": "/static/quiz_images/tree__f_vt_90s_q3__f_vt_90s_casual.png",
                "style_tags": ["denim-everything", "crop-top", "white-sneakers", "casual-90s", "relaxed"],
                "next": "color_f",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # WOMEN'S ATHLEISURE BRANCH
    # ═══════════════════════════════════════════════════════════════

    "f_al_q2": {
        "prompt": "What's your athleisure look?",
        "options": [
            {
                "id": "f_al_fashion",
                "label": "High-Fashion Sport",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_pilates.png",
                "style_tags": ["luxury-sport", "Alo", "Lululemon"],
                "next": "f_al_fashion_q3",
            },
            {
                "id": "f_al_sporty",
                "label": "Sporty Girl",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_sporty.png",
                "style_tags": ["sporty", "matching-sets", "functional-cute", "casual-athletic"],
                "next": "f_al_sporty_q3",
            },
            {
                "id": "f_al_outdoor",
                "label": "Active Outdoor",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_outdoor.png",
                "style_tags": ["outdoor", "trail", "technical", "adventure", "functional"],
                "next": "f_al_outdoor_q3",
            },
            {
                "id": "f_al_retro",
                "label": "Y2K Sport Revival",
                "image_url": "/static/quiz_images/tree__f_al_q2__f_al_retro.png",
                "style_tags": ["retro-sport", "vintage-Adidas", "crop-sweatshirt", "throwback-athletic", "Y2K-sport"],
                "next": "f_al_retro_q3",
            },
        ],
    },

    # ── Women's Fashion Sport Q3 ──────────────────────────────────
    "f_al_fashion_q3": {
        "prompt": "Your high-fashion sport vibe...",
        "options": [
            {
                "id": "f_al_fashion_pilates",
                "label": "Pilates Princess",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_pilates.png",
                "style_tags": ["pilates", "soft-neutrals", "seamless", "refined-sport", "Alo", "Skims"],
                "next": "color_f",
            },
            {
                "id": "f_al_fashion_power",
                "label": "Power Lift",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_power.png",
                "style_tags": ["power-lift", "bold-colors", "high-waist", "statement-sports-bra", "strong"],
                "next": "color_f",
            },
            {
                "id": "f_al_fashion_tennis",
                "label": "Tennis / Country Club",
                "image_url": "/static/quiz_images/tree__f_al_fashion_q3__f_al_fashion_tennis.png",
                "style_tags": ["tennis", "country-club", "polo", "pleated-skirt", "retro-sport-luxury"],
                "next": "color_f",
            },
        ],
    },


    # ═══════════════════════════════════════════════════════════════
    # WOMEN'S SMART CASUAL / MODERN MINIMAL BRANCH
    # ═══════════════════════════════════════════════════════════════

    "f_sc_q2": {
        "prompt": "Your minimal look is built on...",
        "options": [
            {
                "id": "f_sc_paris",
                "label": "Parisian Chic",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_paris.png",
                "style_tags": ["Parisian", "effortless", "French-girl"],
                "next": "f_sc_paris_q3",
            },
            {
                "id": "f_sc_modern",
                "label": "Contemporary Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_modern.png",
                "style_tags": ["contemporary", "Toteme", "COS", "architectural"],
                "next": "f_sc_modern_q3",
            },
            {
                "id": "f_sc_office",
                "label": "Office Sophisticate",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_office.png",
                "style_tags": ["tailored", "professional", "office-chic", "power-dressing", "polished"],
                "next": "f_sc_office_q3",
            },
            {
                "id": "f_sc_soft",
                "label": "Soft Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_q2__f_sc_soft.png",
                "style_tags": ["soft-minimal", "loose-silhouettes", "neutral-fabrics", "calm-palette", "relaxed"],
                "next": "f_sc_soft_q3",
            },
        ],
    },

    # ── Women's Parisian Q3 ───────────────────────────────────────
    "f_sc_paris_q3": {
        "prompt": "Your Parisian style is...",
        "options": [
            {
                "id": "f_sc_paris_casual",
                "label": "Casual Parisian",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_casual.png",
                "style_tags": ["Breton-stripe", "trench-coat", "pointed-flats", "effortlessly-undone", "French-casual"],
                "next": "color_f",
            },
            {
                "id": "f_sc_paris_elevated",
                "label": "Elevated Parisian",
                "image_url": "/static/quiz_images/tree__f_sc_paris_q3__f_sc_paris_elevated.png",
                "style_tags": ["silk-blouse", "wide-leg-trousers", "statement-earring", "French-chic", "polished"],
                "next": "color_f",
            },
        ],
    },

    # ── Women's Contemporary Minimal Q3 ──────────────────────────
    "f_sc_modern_q3": {
        "prompt": "Your contemporary minimal is...",
        "options": [
            {
                "id": "f_sc_modern_mono",
                "label": "Monochrome & Sculptural",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_mono.png",
                "style_tags": ["monochrome", "sculptural-cuts", "single-color-outfit", "architectural", "Toteme"],
                "next": "color_f",
            },
            {
                "id": "f_sc_modern_relaxed",
                "label": "Relaxed Precision",
                "image_url": "/static/quiz_images/tree__f_sc_modern_q3__f_sc_modern_relaxed.png",
                "style_tags": ["wide-silhouette", "dropped-shoulder", "tailored-casual", "relaxed-precise", "COS"],
                "next": "color_f",
            },
        ],
    },
    "m_om_coast_q3": {
        "prompt": "Which coastal vibe fits you best?",
        "options": [
            {
                "id": "m_om_coast_med",
                "label": "Mediterranean Casual",
                "image_url": "/static/quiz_images/tree__m_om_coast_q3__m_om_coast_med.png",
                "style_tags": ["Mediterranean", "linen-shirt", "espadrilles", "sun-faded", "Riviera"],
                "next": "color_m",
            },
            {
                "id": "m_om_coast_neweng",
                "label": "New England Classic",
                "image_url": "/static/quiz_images/tree__m_om_coast_q3__m_om_coast_neweng.png",
                "style_tags": ["New-England", "boat-shoes", "cable-knit", "madras", "Cape-Cod"],
                "next": "color_m",
            },
            {
                "id": "m_om_coast_island",
                "label": "Island Linen",
                "image_url": "/static/quiz_images/tree__m_om_coast_q3__m_om_coast_island.png",
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
                "image_url": "/static/quiz_images/tree__m_vt_y2k_q3__m_vt_y2k_cyber.png",
                "style_tags": ["cyber", "metallic", "futuristic", "tech-inspired", "silver"],
                "next": "color_m",
            },
            {
                "id": "m_vt_y2k_logo",
                "label": "Logo Revival",
                "image_url": "/static/quiz_images/tree__m_vt_y2k_q3__m_vt_y2k_logo.png",
                "style_tags": ["logomania", "designer-revival", "bold-branding", "chunky-sneakers", "2000s"],
                "next": "color_m",
            },
            {
                "id": "m_vt_y2k_bling",
                "label": "Bling Era",
                "image_url": "/static/quiz_images/tree__m_vt_y2k_q3__m_vt_y2k_bling.png",
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
                "image_url": "/static/quiz_images/tree__m_sc_work_q3__m_sc_work_creative.png",
                "style_tags": ["creative-professional", "relaxed-blazer", "no-tie", "sneakers-with-trousers", "design-world"],
                "next": "color_m",
            },
            {
                "id": "m_sc_work_corp",
                "label": "Corporate Casual",
                "image_url": "/static/quiz_images/tree__m_sc_work_q3__m_sc_work_corp.png",
                "style_tags": ["corporate-casual", "oxford-shirt", "chinos", "loafers", "polished-casual"],
                "next": "color_m",
            },
            {
                "id": "m_sc_work_startup",
                "label": "Startup Minimal",
                "image_url": "/static/quiz_images/tree__m_sc_work_q3__m_sc_work_startup.png",
                "style_tags": ["startup-casual", "premium-tee", "clean-sneakers", "minimal-accessories", "tech-casual"],
                "next": "color_m",
            },
        ],
    },
    "f_sw_tech_q3": {
        "prompt": "Which utility style speaks to you?",
        "options": [
            {
                "id": "f_sw_tech_dark",
                "label": "Dark Utility",
                "image_url": "/static/quiz_images/tree__f_sw_tech_q3__f_sw_tech_dark.png",
                "style_tags": ["all-black", "cargo-pants", "utility-vest", "tactical-chic", "dark-functional"],
                "next": "color_f",
            },
            {
                "id": "f_sw_tech_gorp",
                "label": "Urban Gorpcore",
                "image_url": "/static/quiz_images/tree__f_sw_tech_q3__f_sw_tech_gorp.png",
                "style_tags": ["gorpcore", "outdoor-brands", "hiking-boots-in-city", "functional-fashion", "earth-tones"],
                "next": "color_f",
            },
            {
                "id": "f_sw_tech_sport",
                "label": "Sporty Tech",
                "image_url": "/static/quiz_images/tree__f_sw_tech_q3__f_sw_tech_sport.png",
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
                "image_url": "/static/quiz_images/tree__f_om_euro_q3__f_om_euro_riviera.png",
                "style_tags": ["Italian-Riviera", "silk-scarf", "oversized-sunglasses", "linen-dress", "Mediterranean"],
                "next": "color_f",
            },
            {
                "id": "f_om_euro_paris",
                "label": "Parisian Classic",
                "image_url": "/static/quiz_images/tree__f_om_euro_q3__f_om_euro_paris.png",
                "style_tags": ["Parisian", "trench-coat", "ballet-flats", "structured-bag", "understated-chic"],
                "next": "color_f",
            },
            {
                "id": "f_om_euro_english",
                "label": "English Country",
                "image_url": "/static/quiz_images/tree__f_om_euro_q3__f_om_euro_english.png",
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
                "image_url": "/static/quiz_images/tree__f_om_coast_q3__f_om_coast_hamptons.png",
                "style_tags": ["Hamptons", "white-jeans", "striped-top", "deck-shoes", "coastal-chic"],
                "next": "color_f",
            },
            {
                "id": "f_om_coast_equestrian",
                "label": "Equestrian Chic",
                "image_url": "/static/quiz_images/tree__f_om_coast_q3__f_om_coast_equestrian.png",
                "style_tags": ["equestrian", "riding-boots", "tailored-jacket", "leather-belt", "horse-country"],
                "next": "color_f",
            },
            {
                "id": "f_om_coast_boho",
                "label": "Seaside Bohemian",
                "image_url": "/static/quiz_images/tree__f_om_coast_q3__f_om_coast_boho.png",
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
                "image_url": "/static/quiz_images/tree__f_vt_cottage_q3__f_vt_cottage_garden.png",
                "style_tags": ["English-garden", "floral-midi", "Peter-Pan-collar", "wicker-basket", "romantic"],
                "next": "color_f",
            },
            {
                "id": "f_vt_cottage_prairie",
                "label": "Prairie Folk",
                "image_url": "/static/quiz_images/tree__f_vt_cottage_q3__f_vt_cottage_prairie.png",
                "style_tags": ["prairie", "puff-sleeves", "embroidery", "frontier-feminine", "folk"],
                "next": "color_f",
            },
            {
                "id": "f_vt_cottage_fairy",
                "label": "Fairy Vintage",
                "image_url": "/static/quiz_images/tree__f_vt_cottage_q3__f_vt_cottage_fairy.png",
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
                "image_url": "/static/quiz_images/tree__f_vt_80s_q3__f_vt_80s_power.png",
                "style_tags": ["power-suit", "oversized-blazer", "structured-shoulders", "bold-earrings", "corporate-glam"],
                "next": "color_f",
            },
            {
                "id": "f_vt_80s_wave",
                "label": "New Wave",
                "image_url": "/static/quiz_images/tree__f_vt_80s_q3__f_vt_80s_wave.png",
                "style_tags": ["new-wave", "geometric-prints", "asymmetric", "bold-colors", "art-inspired"],
                "next": "color_f",
            },
            {
                "id": "f_vt_80s_dynasty",
                "label": "Dynasty Glam",
                "image_url": "/static/quiz_images/tree__f_vt_80s_q3__f_vt_80s_dynasty.png",
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
                "image_url": "/static/quiz_images/tree__f_vt_y2k_q3__f_vt_y2k_pop.png",
                "style_tags": ["pop-princess", "bedazzled", "crop-top", "platform-shoes", "Britney-era"],
                "next": "color_f",
            },
            {
                "id": "f_vt_y2k_paris",
                "label": "It Girl Era",
                "image_url": "/static/quiz_images/tree__f_vt_y2k_q3__f_vt_y2k_paris.png",
                "style_tags": ["It-girl", "velour-tracksuit", "tiny-bag", "rhinestones", "pink"],
                "next": "color_f",
            },
            {
                "id": "f_vt_y2k_cyber",
                "label": "Cyber Girl",
                "image_url": "/static/quiz_images/tree__f_vt_y2k_q3__f_vt_y2k_cyber.png",
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
                "image_url": "/static/quiz_images/tree__f_al_sporty_q3__f_al_sporty_gym.png",
                "style_tags": ["gym-chic", "matching-sets", "neutral-athletic", "seamless", "polished-gym"],
                "next": "color_f",
            },
            {
                "id": "f_al_sporty_track",
                "label": "Track Star",
                "image_url": "/static/quiz_images/tree__f_al_sporty_q3__f_al_sporty_track.png",
                "style_tags": ["track-star", "retro-track", "stripe-detail", "zip-up", "sporty-vintage"],
                "next": "color_f",
            },
            {
                "id": "f_al_sporty_dance",
                "label": "Dance Studio",
                "image_url": "/static/quiz_images/tree__f_al_sporty_q3__f_al_sporty_dance.png",
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
                "image_url": "/static/quiz_images/tree__f_al_outdoor_q3__f_al_outdoor_trail.png",
                "style_tags": ["trail-hiker", "hiking-boots", "cargo-shorts", "moisture-wicking", "nature-ready"],
                "next": "color_f",
            },
            {
                "id": "f_al_outdoor_mountain",
                "label": "Mountain Chic",
                "image_url": "/static/quiz_images/tree__f_al_outdoor_q3__f_al_outdoor_mountain.png",
                "style_tags": ["mountain-chic", "puffer-vest", "base-layers", "apres-ski", "elevated-outdoor"],
                "next": "color_f",
            },
            {
                "id": "f_al_outdoor_coastal",
                "label": "Coastal Active",
                "image_url": "/static/quiz_images/tree__f_al_outdoor_q3__f_al_outdoor_coastal.png",
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
                "image_url": "/static/quiz_images/tree__f_al_retro_q3__f_al_retro_tennis.png",
                "style_tags": ["retro-tennis", "pleated-skirt", "polo-shirt", "white-sneakers", "country-club-throwback"],
                "next": "color_f",
            },
            {
                "id": "f_al_retro_velour",
                "label": "Velour Revival",
                "image_url": "/static/quiz_images/tree__f_al_retro_q3__f_al_retro_velour.png",
                "style_tags": ["velour-tracksuit", "logo-mania", "bedazzled", "pink-sportswear", "2000s-sport"],
                "next": "color_f",
            },
            {
                "id": "f_al_retro_spice",
                "label": "Sporty Spice",
                "image_url": "/static/quiz_images/tree__f_al_retro_q3__f_al_retro_spice.png",
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
                "image_url": "/static/quiz_images/tree__f_sc_office_q3__f_sc_office_power.png",
                "style_tags": ["power-professional", "tailored-suit", "pointed-heels", "statement-watch", "boardroom"],
                "next": "color_f",
            },
            {
                "id": "f_sc_office_creative",
                "label": "Creative Director",
                "image_url": "/static/quiz_images/tree__f_sc_office_q3__f_sc_office_creative.png",
                "style_tags": ["creative-director", "architectural-pieces", "all-black", "statement-glasses", "design-world"],
                "next": "color_f",
            },
            {
                "id": "f_sc_office_elevated",
                "label": "Elevated Corporate",
                "image_url": "/static/quiz_images/tree__f_sc_office_q3__f_sc_office_elevated.png",
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
                "image_url": "/static/quiz_images/tree__f_sc_soft_q3__f_sc_soft_cloud.png",
                "style_tags": ["cloud-neutral", "cream-on-cream", "cashmere", "soft-knits", "ethereal-calm"],
                "next": "color_f",
            },
            {
                "id": "f_sc_soft_organic",
                "label": "Organic Minimal",
                "image_url": "/static/quiz_images/tree__f_sc_soft_q3__f_sc_soft_organic.png",
                "style_tags": ["organic-minimal", "natural-linen", "undyed-fabrics", "raw-textures", "sustainable"],
                "next": "color_f",
            },
            {
                "id": "f_sc_soft_japandi",
                "label": "Japandi Living",
                "image_url": "/static/quiz_images/tree__f_sc_soft_q3__f_sc_soft_japandi.png",
                "style_tags": ["Japandi", "structured-simplicity", "neutral-palette", "clean-geometric", "zen-inspired"],
                "next": "color_f",
            },
        ],
    },
    "color_m": {
        "prompt": "Which color palette draws you in?",
        "options": [
            {
                "id": "color_m_earth",
                "label": "Earth & Warm Neutrals",
                "image_url": "/static/quiz_images/tree__color_m__color_m_earth.png",
                "style_tags": ["earth-tones", "warm-neutrals", "brown", "tan", "olive", "cream"],
                "next": "fit_m",
            },
            {
                "id": "color_m_dark",
                "label": "Dark & Moody",
                "image_url": "/static/quiz_images/tree__color_m__color_m_dark.png",
                "style_tags": ["dark-palette", "cool-tones", "black", "navy", "charcoal", "burgundy"],
                "next": "fit_m",
            },
            {
                "id": "color_m_bold",
                "label": "Bold & Vivid",
                "image_url": "/static/quiz_images/tree__color_m__color_m_bold.png",
                "style_tags": ["bold-colors", "statement-color", "vibrant", "red", "cobalt", "emerald"],
                "next": "fit_m",
            },
            {
                "id": "color_m_muted",
                "label": "Soft & Muted",
                "image_url": "/static/quiz_images/tree__color_m__color_m_muted.png",
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
                "image_url": "/static/quiz_images/tree__color_f__color_f_earth.png",
                "style_tags": ["earth-tones", "warm-neutrals", "brown", "tan", "olive", "cream"],
                "next": "fit_f",
            },
            {
                "id": "color_f_dark",
                "label": "Dark & Moody",
                "image_url": "/static/quiz_images/tree__color_f__color_f_dark.png",
                "style_tags": ["dark-palette", "cool-tones", "black", "navy", "charcoal", "burgundy"],
                "next": "fit_f",
            },
            {
                "id": "color_f_bold",
                "label": "Bold & Vivid",
                "image_url": "/static/quiz_images/tree__color_f__color_f_bold.png",
                "style_tags": ["bold-colors", "statement-color", "vibrant", "red", "cobalt", "emerald"],
                "next": "fit_f",
            },
            {
                "id": "color_f_muted",
                "label": "Soft & Muted",
                "image_url": "/static/quiz_images/tree__color_f__color_f_muted.png",
                "style_tags": ["muted-tones", "pastel", "sage", "dusty-blue", "lavender", "soft-palette"],
                "next": "fit_f",
            },
        ],
    },
    "fit_m": {
        "prompt": "What silhouette feels most you?",
        "options": [
            {
                "id": "fit_m_slim",
                "label": "Slim & Tailored",
                "image_url": "/static/quiz_images/tree__fit_m__fit_m_slim.png",
                "style_tags": ["slim-fit", "fitted", "tailored", "structured", "defined"],
                "next": None,
            },
            {
                "id": "fit_m_relaxed",
                "label": "Relaxed & Oversized",
                "image_url": "/static/quiz_images/tree__fit_m__fit_m_relaxed.png",
                "style_tags": ["relaxed-fit", "oversized", "wide-leg", "dropped-shoulder", "volume"],
                "next": None,
            },
            {
                "id": "fit_m_classic",
                "label": "Classic & Balanced",
                "image_url": "/static/quiz_images/tree__fit_m__fit_m_classic.png",
                "style_tags": ["classic-fit", "proportioned", "versatile", "balanced", "traditional"],
                "next": None,
            },
            {
                "id": "fit_m_layered",
                "label": "Layered & Experimental",
                "image_url": "/static/quiz_images/tree__fit_m__fit_m_layered.png",
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
                "image_url": "/static/quiz_images/tree__fit_f__fit_f_slim.png",
                "style_tags": ["slim-fit", "fitted", "tailored", "structured", "defined"],
                "next": None,
            },
            {
                "id": "fit_f_relaxed",
                "label": "Relaxed & Oversized",
                "image_url": "/static/quiz_images/tree__fit_f__fit_f_relaxed.png",
                "style_tags": ["relaxed-fit", "oversized", "wide-leg", "dropped-shoulder", "volume"],
                "next": None,
            },
            {
                "id": "fit_f_classic",
                "label": "Classic & Balanced",
                "image_url": "/static/quiz_images/tree__fit_f__fit_f_classic.png",
                "style_tags": ["classic-fit", "proportioned", "versatile", "balanced", "traditional"],
                "next": None,
            },
            {
                "id": "fit_f_layered",
                "label": "Layered & Experimental",
                "image_url": "/static/quiz_images/tree__fit_f__fit_f_layered.png",
                "style_tags": ["layered", "proportion-play", "deconstructed", "mixed-silhouettes", "experimental"],
                "next": None,
            },
        ],
    },
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_quiz_tree(gender: str | None) -> dict:
    """Return the full quiz tree with the appropriate start node for the given gender."""
    start_map = {
        "Man": "root_m",
        "male": "root_m",
        "Woman": "root_f",
        "female": "root_f",
        "Non-binary": "root_nb",
        "non-binary": "root_nb",
        "Prefer not to say": "root_nb",
        "prefer-not-to-say": "root_nb",
    }
    start = start_map.get(gender or "", "root_nb")
    return {"start": start, "nodes": QUIZ_TREE}


def get_chat_question(category: str) -> dict | None:
    """Return a single quiz question for in-chat use, or None if category unknown."""
    if category not in CHAT_QUESTIONS:
        return None
    q = CHAT_QUESTIONS[category].copy()
    q["category"] = category
    return q
