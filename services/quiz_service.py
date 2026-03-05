"""Adaptive visual style quiz for onboarding.

Tree structure:
  - QUIZ_TREE: dict of node_id → {prompt, options[]}
  - Each option: {id, label, image_url, style_tags, next}
      next=None means terminal — quiz ends after this answer
  - Start node is gender-aware: root_m / root_f / root_nb
  - Depth varies by path (2–4 questions); no path exceeds 5

Image note: all URLs are Unsplash. If any thumbnail looks wrong,
swap the photo ID — format is always ?w=400&h=500&fit=crop.
"""

# ── Chat-only questions (used by agent tools) ─────────────────────────────────

CHAT_QUESTIONS = {
    "sneakers": {
        "prompt": "Which sneaker style catches your eye?",
        "options": [
            {
                "id": "retro-runner",
                "label": "Retro Runner",
                "image_url": "https://images.unsplash.com/photo-1552346154-21d32810aba3?w=400&h=400&fit=crop",
                "style_tags": ["retro", "sporty"],
            },
            {
                "id": "high-tops",
                "label": "High Tops",
                "image_url": "https://images.unsplash.com/photo-1446214814726-e6074845b4ce?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "bold"],
            },
            {
                "id": "slip-on",
                "label": "Slip-On",
                "image_url": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=400&h=400&fit=crop",
                "style_tags": ["casual", "effortless"],
            },
            {
                "id": "designer-sneaker",
                "label": "Designer Sneaker",
                "image_url": "https://images.unsplash.com/photo-1593032470861-4509830938cb?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=400&h=400&fit=crop",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "modern-slim",
                "label": "Modern Slim Fit",
                "image_url": "https://images.unsplash.com/photo-1617137968427-85924c800a22?w=400&h=400&fit=crop",
                "style_tags": ["modern", "sharp"],
            },
            {
                "id": "relaxed-formal",
                "label": "Relaxed Formal",
                "image_url": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=400&h=400&fit=crop",
                "style_tags": ["relaxed", "smart-casual"],
            },
            {
                "id": "statement-formal",
                "label": "Statement Piece",
                "image_url": "https://images.unsplash.com/photo-1580657018950-c7f7d6a6d990?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1621951753163-ee63e7fc147e?w=400&h=400&fit=crop",
                "style_tags": ["classic", "nautical"],
            },
            {
                "id": "plaid",
                "label": "Plaid",
                "image_url": "https://images.unsplash.com/photo-1608063615781-e2ef8c73d114?w=400&h=400&fit=crop",
                "style_tags": ["heritage", "rugged"],
            },
            {
                "id": "floral",
                "label": "Floral",
                "image_url": "https://images.unsplash.com/photo-1575062258018-37b8821ce9b7?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "expressive"],
            },
            {
                "id": "solid",
                "label": "Solid Colors",
                "image_url": "https://images.unsplash.com/photo-1592878858320-cec76c56da82?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "refined"],
            },
            {
                "id": "statement-sunglasses",
                "label": "Statement Sunglasses",
                "image_url": "https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=400&h=400&fit=crop",
                "style_tags": ["bold", "trendy"],
            },
            {
                "id": "leather-bag",
                "label": "Leather Bag",
                "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400&h=400&fit=crop",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "layered-jewelry",
                "label": "Layered Jewelry",
                "image_url": "https://images.unsplash.com/photo-1738754835779-cae7fb8907a2?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400&h=400&fit=crop",
                "style_tags": ["classic", "feminine"],
            },
            {
                "id": "maxi-dress",
                "label": "Maxi Dress",
                "image_url": "https://images.unsplash.com/photo-1738261544450-dac9cc4e5631?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "flowy"],
            },
            {
                "id": "shirt-dress",
                "label": "Shirt Dress",
                "image_url": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "versatile"],
            },
            {
                "id": "mini-dress",
                "label": "Mini Dress",
                "image_url": "https://images.unsplash.com/photo-1495385794356-15371f348c31?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1592878798022-3be8fcd44b1b?w=400&h=400&fit=crop",
                "style_tags": ["put-together", "trendy"],
            },
            {
                "id": "classic-athletic",
                "label": "Classic Athletic",
                "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=400&fit=crop",
                "style_tags": ["sporty", "functional"],
            },
            {
                "id": "athleisure",
                "label": "Athleisure",
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=400&fit=crop",
                "style_tags": ["athleisure", "casual"],
            },
            {
                "id": "outdoor-active",
                "label": "Outdoor Active",
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=400&h=500&fit=crop",
                "style_tags": ["streetwear"],
                "next": "m_sw_q2",
            },
            {
                "id": "root_m_oldmoney",
                "label": "Old Money",
                "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=500&fit=crop",
                "style_tags": ["classic", "refined"],
                "next": "m_om_q2",
            },
            {
                "id": "root_m_vintage",
                "label": "Vintage",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["vintage"],
                "next": "m_vt_q2",
            },
            {
                "id": "root_m_ath",
                "label": "Athleisure",
                "image_url": "https://images.unsplash.com/photo-1618355281951-a174b87198e2?w=400&h=500&fit=crop",
                "style_tags": ["athleisure"],
                "next": "m_al_q2",
            },
            {
                "id": "root_m_smart",
                "label": "Smart & Minimal",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop",
                "style_tags": ["streetwear"],
                "next": "f_sw_q2",
            },
            {
                "id": "root_f_oldmoney",
                "label": "Old Money",
                "image_url": "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&h=500&fit=crop",
                "style_tags": ["classic", "refined"],
                "next": "f_om_q2",
            },
            {
                "id": "root_f_vintage",
                "label": "Vintage",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["vintage"],
                "next": "f_vt_q2",
            },
            {
                "id": "root_f_ath",
                "label": "Athleisure",
                "image_url": "https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=400&h=500&fit=crop",
                "style_tags": ["athleisure"],
                "next": "f_al_q2",
            },
            {
                "id": "root_f_smart",
                "label": "Smart & Minimal",
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=500&fit=crop",
                "style_tags": ["streetwear"],
                "next": "m_sw_q2",
            },
            {
                "id": "root_nb_oldmoney",
                "label": "Old Money",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
                "style_tags": ["classic", "refined"],
                "next": "m_om_q2",
            },
            {
                "id": "root_nb_vintage",
                "label": "Vintage",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["vintage"],
                "next": "m_vt_q2",
            },
            {
                "id": "root_nb_ath",
                "label": "Athleisure",
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=500&fit=crop",
                "style_tags": ["athleisure"],
                "next": "m_al_q2",
            },
            {
                "id": "root_nb_smart",
                "label": "Smart & Minimal",
                "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=500&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=500&fit=crop",
                "style_tags": ["skate", "casual", "laid-back"],
                "next": "m_sw_skate_q3",
            },
            {
                "id": "m_sw_tech",
                "label": "Techwear / Utility",
                "image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=500&fit=crop",
                "style_tags": ["techwear", "utility", "functional"],
                "next": "m_sw_tech_q3",
            },
            {
                "id": "m_sw_hiphop",
                "label": "Hip-Hop / Oversized",
                "image_url": "https://images.unsplash.com/photo-1544441893-675973e31985?w=400&h=500&fit=crop",
                "style_tags": ["oversized", "urban", "bold"],
                "next": "m_sw_hiphop_q3",
            },
            {
                "id": "m_sw_hype",
                "label": "Hype / Sneakerhead",
                "image_url": "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=400&h=500&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400&h=500&fit=crop",
                "style_tags": ["vintage-skate", "90s", "baggy", "graphic-tees", "Vans"],
                "next": None,
            },
            {
                "id": "m_sw_skate_modern",
                "label": "Modern Minimalist Skate",
                "image_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400&h=500&fit=crop",
                "style_tags": ["skate", "earth-tones", "understated", "clean-lines"],
                "next": None,
            },
            {
                "id": "m_sw_skate_surf",
                "label": "Surf-Skate Crossover",
                "image_url": "https://images.unsplash.com/photo-1551524559-8af4e6624178?w=400&h=500&fit=crop",
                "style_tags": ["surf", "beach-casual", "loose-denim", "bright-accents"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400&h=500&fit=crop",
                "style_tags": ["techwear", "all-black", "cargo", "ACRONYM", "tactical"],
                "next": None,
            },
            {
                "id": "m_sw_tech_gorpcore",
                "label": "Gorpcore",
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=500&fit=crop",
                "style_tags": ["gorpcore", "outdoor-brands", "earth-tones", "functional", "Arc'teryx"],
                "next": None,
            },
            {
                "id": "m_sw_tech_sport",
                "label": "Soft Sporty",
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=500&fit=crop",
                "style_tags": ["sporty", "Nike", "Adidas", "technical", "off-court"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1552374196-1ab2a1c593e8?w=400&h=500&fit=crop",
                "style_tags": ["hip-hop", "90s", "Timberlands", "puffer", "gold-chain", "retro"],
                "next": None,
            },
            {
                "id": "m_sw_hiphop_luxe",
                "label": "Luxury Streetwear",
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=500&fit=crop",
                "style_tags": ["luxury-streetwear", "dark", "layered", "elevated", "Rick-Owens"],
                "next": None,
            },
            {
                "id": "m_sw_hiphop_tonal",
                "label": "Clean & Tonal",
                "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=500&fit=crop",
                "style_tags": ["tonal", "neutral-palette", "oversized", "subtle-branding", "clean"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1617137968427-85924c800a22?w=400&h=500&fit=crop",
                "style_tags": ["neutral", "minimalist-fit", "sneaker-focused", "understated"],
                "next": None,
            },
            {
                "id": "m_sw_hype_coord",
                "label": "Coordinated Colorways",
                "image_url": "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=400&h=500&fit=crop",
                "style_tags": ["color-coordinated", "matching-sets", "bold-colorblocking", "hype"],
                "next": None,
            },
            {
                "id": "m_sw_hype_loud",
                "label": "Full Statement",
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=500&fit=crop",
                "style_tags": ["graphic-heavy", "loud-patterns", "statement", "maximalist"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1598808503746-f34c53b9323e?w=400&h=500&fit=crop",
                "style_tags": ["heritage", "British", "tailored"],
                "next": "m_om_brit_q3",
            },
            {
                "id": "m_om_ital",
                "label": "Italian Tailoring",
                "image_url": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=400&h=500&fit=crop",
                "style_tags": ["Italian", "tailored", "elegant"],
                "next": "m_om_ital_q3",
            },
            {
                "id": "m_om_prep",
                "label": "American Prep",
                "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop",
                "style_tags": ["preppy", "collegiate", "American"],
                "next": "m_om_prep_q3",
            },
            {
                "id": "m_om_coastal",
                "label": "Coastal / Nautical",
                "image_url": "https://images.unsplash.com/photo-1604006852748-903fccbc4019?w=400&h=500&fit=crop",
                "style_tags": ["coastal", "nautical", "linen", "navy", "relaxed-elegance"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=400&h=500&fit=crop",
                "style_tags": ["tweed", "Barbour", "Hunter-boots", "heritage-outerwear", "country"],
                "next": None,
            },
            {
                "id": "m_om_brit_city",
                "label": "City Gent",
                "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400&h=500&fit=crop",
                "style_tags": ["three-piece", "pocket-square", "brogues", "polished", "Savile-Row"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=500&fit=crop",
                "style_tags": ["sprezzatura", "unlined-blazer", "deliberate-imperfection", "Mediterranean", "effortless-elegance"],
                "next": None,
            },
            {
                "id": "m_om_ital_milan",
                "label": "Modern Milan",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=500&fit=crop",
                "style_tags": ["modern-luxury", "sleek", "dark-palette", "Milan", "minimal-luxury"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop",
                "style_tags": ["Ivy-League", "OCBD", "navy-blazer", "khakis", "boat-shoes", "timeless"],
                "next": None,
            },
            {
                "id": "m_om_prep_modern",
                "label": "Modern Prep",
                "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop",
                "style_tags": ["modern-prep", "updated-silhouettes", "unexpected-colors", "elevated-basics"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400&h=500&fit=crop",
                "style_tags": ["70s", "vintage"],
                "next": "m_vt_70s_q3",
            },
            {
                "id": "m_vt_8090",
                "label": "80s / 90s — Sports & Street",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["80s", "90s", "retro"],
                "next": "m_vt_8090_q3",
            },
            {
                "id": "m_vt_americana",
                "label": "Americana / Workwear",
                "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=400&h=500&fit=crop",
                "style_tags": ["Americana", "workwear", "heritage"],
                "next": "m_vt_work_q3",
            },
            {
                "id": "m_vt_y2k",
                "label": "Y2K / Early 2000s",
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=500&fit=crop",
                "style_tags": ["Y2K", "2000s", "logomania", "low-rise", "chrome"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop",
                "style_tags": ["rock", "band-tees", "flares", "Chelsea-boots", "leather-jacket"],
                "next": None,
            },
            {
                "id": "m_vt_70s_boho",
                "label": "Boho / Folk",
                "image_url": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=500&fit=crop",
                "style_tags": ["bohemian", "folk", "loose-linen", "earth-tones", "fringe"],
                "next": None,
            },
            {
                "id": "m_vt_70s_disco",
                "label": "Disco Glam",
                "image_url": "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=400&h=500&fit=crop",
                "style_tags": ["disco", "satin", "wide-leg", "retro-prints", "statement-accessories"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=400&h=500&fit=crop",
                "style_tags": ["old-school", "tracksuit", "bucket-hat", "vintage-Adidas", "90s-hip-hop"],
                "next": None,
            },
            {
                "id": "m_vt_8090_grunge",
                "label": "Grunge",
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop",
                "style_tags": ["grunge", "flannel", "ripped-denim", "boots", "layering", "90s"],
                "next": None,
            },
            {
                "id": "m_vt_8090_sport",
                "label": "Sports / Collegiate",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=500&fit=crop",
                "style_tags": ["varsity-jacket", "collegiate", "retro-tees", "court-sneakers", "sporty"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=400&h=500&fit=crop",
                "style_tags": ["Americana", "Levi's", "Carhartt", "work-boots", "utilitarian", "raw-denim"],
                "next": None,
            },
            {
                "id": "m_vt_work_selvedge",
                "label": "Japanese Selvedge",
                "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&h=500&fit=crop",
                "style_tags": ["selvedge-denim", "Japanese-workwear", "indigo", "slow-fashion", "sashiko"],
                "next": None,
            },
            {
                "id": "m_vt_work_military",
                "label": "Military Surplus",
                "image_url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=500&fit=crop",
                "style_tags": ["military", "field-jacket", "cargo", "surplus", "functional"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=500&fit=crop",
                "style_tags": ["performance", "functional", "training"],
                "next": "m_al_perf_q3",
            },
            {
                "id": "m_al_fashion",
                "label": "Fashion-Forward Sport",
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=500&fit=crop",
                "style_tags": ["fashion-sport", "design-led", "luxury-sport"],
                "next": "m_al_fashion_q3",
            },
            {
                "id": "m_al_outdoor",
                "label": "Outdoor / Adventure",
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=500&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1618355281951-a174b87198e2?w=400&h=500&fit=crop",
                "style_tags": ["monochrome", "single-brand", "clean", "Nike", "Adidas", "minimal-sport"],
                "next": None,
            },
            {
                "id": "m_al_perf_mixed",
                "label": "Mixed Performance",
                "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=500&fit=crop",
                "style_tags": ["multi-brand", "elite-gear", "function-maximalist", "technical-layers"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=500&fit=crop",
                "style_tags": ["luxury-sport", "Lululemon", "Vuori", "premium-basics", "elevated-casual"],
                "next": None,
            },
            {
                "id": "m_al_fashion_hype",
                "label": "Hype Sport",
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=500&fit=crop",
                "style_tags": ["Jordan", "collab-pieces", "streetwear-sport", "hype", "limited-edition"],
                "next": None,
            },
            {
                "id": "m_al_fashion_retro",
                "label": "Y2K Sport Revival",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["retro-sport", "vintage-Adidas", "Fila", "track-jacket", "throwback-athletic"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=500&fit=crop",
                "style_tags": ["gorpcore", "Arc'teryx", "Salomon", "Patagonia", "outdoor-in-the-city"],
                "next": None,
            },
            {
                "id": "m_al_outdoor_trail",
                "label": "Trail Runner",
                "image_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=500&fit=crop",
                "style_tags": ["trail", "minimal-tech", "movement-focused", "trail-shoes", "lightweight"],
                "next": None,
            },
            {
                "id": "m_al_outdoor_expedition",
                "label": "Expedition Ready",
                "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=400&h=500&fit=crop",
                "style_tags": ["expedition", "insulated-layers", "waterproof", "heavy-duty", "mountaineer"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
                "style_tags": ["quiet-luxury", "elevated-fabrics", "neutral-palette"],
                "next": "m_sc_quiet_q3",
            },
            {
                "id": "m_sc_euro",
                "label": "European Contemporary",
                "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop",
                "style_tags": ["European", "contemporary", "COS", "Arket", "architectural"],
                "next": "m_sc_euro_q3",
            },
            {
                "id": "m_sc_japan",
                "label": "Japanese Minimalism",
                "image_url": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=400&h=500&fit=crop",
                "style_tags": ["Japanese", "minimalist", "natural-fabrics"],
                "next": "m_sc_japan_q3",
            },
            {
                "id": "m_sc_work",
                "label": "Smart-Casual Workwear",
                "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop",
                "style_tags": ["smart-casual", "business-casual", "tailored", "professional", "versatile"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
                "style_tags": ["tonal-dressing", "camel", "cream", "navy", "head-to-toe-neutral"],
                "next": None,
            },
            {
                "id": "m_sc_quiet_texture",
                "label": "Subtle Texture",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
                "style_tags": ["cashmere", "suede", "twill", "material-led", "tactile-luxury"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400&h=500&fit=crop",
                "style_tags": ["structured", "clean-lines", "fitted", "architectural", "precise"],
                "next": None,
            },
            {
                "id": "m_sc_euro_relaxed",
                "label": "Relaxed Volume",
                "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=500&fit=crop",
                "style_tags": ["wide-leg", "dropped-shoulder", "oversized-precise", "relaxed-tailoring"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
                "style_tags": ["Muji", "Uniqlo", "quality-basics", "functional-minimalism", "refined"],
                "next": None,
            },
            {
                "id": "m_sc_japan_avantgarde",
                "label": "Avant-Garde",
                "image_url": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop",
                "style_tags": ["CDG", "Yohji", "deconstructed", "asymmetric", "dark", "avant-garde"],
                "next": None,
            },
            {
                "id": "m_sc_japan_wabi",
                "label": "Wabi-Sabi",
                "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=500&fit=crop",
                "style_tags": ["wabi-sabi", "natural-dyes", "artisan", "imperfect-texture", "slow-fashion"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop",
                "style_tags": ["tomboy", "skate", "oversized"],
                "next": "f_sw_tomboy_q3",
            },
            {
                "id": "f_sw_luxe",
                "label": "Luxe Street",
                "image_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400&h=500&fit=crop",
                "style_tags": ["luxury-streetwear", "elevated", "designer"],
                "next": "f_sw_luxe_q3",
            },
            {
                "id": "f_sw_y2k",
                "label": "Y2K / Baddie",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["Y2K", "baddie", "bold"],
                "next": "f_sw_y2k_q3",
            },
            {
                "id": "f_sw_tech",
                "label": "Techwear / Utility",
                "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=500&fit=crop",
                "style_tags": ["techwear", "utility", "dark", "functional", "technical-fabrics"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop",
                "style_tags": ["90s-skate", "baggy-cargos", "graphic-tee", "chunky-sneakers", "relaxed"],
                "next": None,
            },
            {
                "id": "f_sw_tomboy_tailored",
                "label": "Tailored Menswear",
                "image_url": "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&h=500&fit=crop",
                "style_tags": ["menswear-inspired", "oversized-blazer", "wide-trousers", "androgynous", "tailored"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=500&fit=crop",
                "style_tags": ["logomania", "Gucci", "Fendi", "prominent-branding", "luxury-logos"],
                "next": None,
            },
            {
                "id": "f_sw_luxe_quiet",
                "label": "Quiet Hype",
                "image_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400&h=500&fit=crop",
                "style_tags": ["quiet-hype", "understated-luxury", "tonal", "clean", "premium-streetwear"],
                "next": None,
            },
            {
                "id": "f_sw_luxe_art",
                "label": "Streetwear Art",
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=500&fit=crop",
                "style_tags": ["statement-graphics", "art-driven", "collab-pieces", "creative", "expressive"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["Y2K", "low-rise", "butterfly-clips", "shiny-fabrics", "2000s-nostalgia"],
                "next": None,
            },
            {
                "id": "f_sw_y2k_baddie",
                "label": "Modern Baddie",
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop",
                "style_tags": ["baddie", "bodycon", "polished", "powerful", "glam"],
                "next": None,
            },
            {
                "id": "f_sw_y2k_soft",
                "label": "Soft Y2K",
                "image_url": "https://images.unsplash.com/photo-1495385794356-15371f348c31?w=400&h=500&fit=crop",
                "style_tags": ["soft-Y2K", "pastel", "baby-tee", "mini-skirt", "feminine", "coquette"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
                "style_tags": ["quiet-luxury", "The-Row", "Bottega"],
                "next": "f_om_quiet_q3",
            },
            {
                "id": "f_om_prep",
                "label": "Heritage Prep",
                "image_url": "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&h=500&fit=crop",
                "style_tags": ["heritage-prep", "collegiate", "plaid"],
                "next": "f_om_prep_q3",
            },
            {
                "id": "f_om_euro",
                "label": "European Aristocrat",
                "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=500&fit=crop",
                "style_tags": ["silk-scarf", "structured-bag", "timeless", "European", "classic-chic"],
                "next": None,
            },
            {
                "id": "f_om_coastal",
                "label": "Coastal / Equestrian",
                "image_url": "https://images.unsplash.com/photo-1604006852748-903fccbc4019?w=400&h=500&fit=crop",
                "style_tags": ["coastal", "equestrian", "cream-knits", "riding-boots", "nautical", "classic"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1611312449408-fcece27cdbb7?w=400&h=500&fit=crop",
                "style_tags": ["monochrome", "camel", "cream", "grey", "head-to-toe-tonal", "The-Row"],
                "next": None,
            },
            {
                "id": "f_om_quiet_sculptural",
                "label": "Sculptural Minimal",
                "image_url": "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=400&h=500&fit=crop",
                "style_tags": ["sculptural", "interesting-silhouette", "quality-fabric", "logo-free", "Bottega"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=500&fit=crop",
                "style_tags": ["Ivy-League", "plaid-blazer", "loafers", "pearl-earrings", "collegiate"],
                "next": None,
            },
            {
                "id": "f_om_prep_academia",
                "label": "Dark Academia",
                "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400&h=500&fit=crop",
                "style_tags": ["dark-academia", "tweed", "oxford-shoes", "vintage-scholarly", "moody"],
                "next": None,
            },
            {
                "id": "f_om_prep_modern",
                "label": "Modern Prep",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
                "style_tags": ["modern-prep", "sleek", "elevated-basics", "Ralph-Lauren", "refined-casual"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=500&fit=crop",
                "style_tags": ["70s", "bohemian"],
                "next": "f_vt_70s_q3",
            },
            {
                "id": "f_vt_90s",
                "label": "90s — Grunge & Minimal",
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop",
                "style_tags": ["90s", "grunge", "minimalism"],
                "next": "f_vt_90s_q3",
            },
            {
                "id": "f_vt_cottage",
                "label": "Cottagecore / Romantic",
                "image_url": "https://images.unsplash.com/photo-1490114538077-0a7f8cb49891?w=400&h=500&fit=crop",
                "style_tags": ["cottagecore", "romantic", "prairie-dress", "florals", "lace", "pastoral"],
                "next": None,
            },
            {
                "id": "f_vt_80s",
                "label": "80s Power",
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=500&fit=crop",
                "style_tags": ["80s", "power-dressing", "shoulder-pads", "bold-prints", "statement-earrings"],
                "next": None,
            },
            {
                "id": "f_vt_y2k",
                "label": "Y2K / Early 2000s",
                "image_url": "https://images.unsplash.com/photo-1495385794356-15371f348c31?w=400&h=500&fit=crop",
                "style_tags": ["Y2K", "low-rise", "denim-skirt", "rhinestones", "2000s"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=500&fit=crop",
                "style_tags": ["folk", "fringe", "embroidery", "free-spirited", "earth-tones", "bohemian"],
                "next": None,
            },
            {
                "id": "f_vt_70s_disco",
                "label": "Disco Glamour",
                "image_url": "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=400&h=500&fit=crop",
                "style_tags": ["disco", "satin", "sequins", "platforms", "wide-leg", "glam"],
                "next": None,
            },
            {
                "id": "f_vt_70s_chic",
                "label": "70s Chic",
                "image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&h=500&fit=crop",
                "style_tags": ["70s-cool", "tailored-flares", "printed-blouses", "chic-simplicity"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=500&fit=crop",
                "style_tags": ["grunge", "slip-dress-over-tee", "combat-boots", "flannel", "layering"],
                "next": None,
            },
            {
                "id": "f_vt_90s_minimal",
                "label": "Minimalist 90s",
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
                "style_tags": ["Calvin-Klein", "slip-dress", "spaghetti-straps", "clean", "90s-minimal"],
                "next": None,
            },
            {
                "id": "f_vt_90s_casual",
                "label": "90s Casual",
                "image_url": "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=400&h=500&fit=crop",
                "style_tags": ["denim-everything", "crop-top", "white-sneakers", "casual-90s", "relaxed"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=400&h=500&fit=crop",
                "style_tags": ["luxury-sport", "Alo", "Lululemon"],
                "next": "f_al_fashion_q3",
            },
            {
                "id": "f_al_sporty",
                "label": "Sporty Girl",
                "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400&h=500&fit=crop",
                "style_tags": ["sporty", "matching-sets", "functional-cute", "casual-athletic"],
                "next": None,
            },
            {
                "id": "f_al_outdoor",
                "label": "Active Outdoor",
                "image_url": "https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400&h=500&fit=crop",
                "style_tags": ["outdoor", "trail", "technical", "adventure", "functional"],
                "next": None,
            },
            {
                "id": "f_al_retro",
                "label": "Y2K Sport Revival",
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=500&fit=crop",
                "style_tags": ["retro-sport", "vintage-Adidas", "crop-sweatshirt", "throwback-athletic", "Y2K-sport"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=400&h=500&fit=crop",
                "style_tags": ["pilates", "soft-neutrals", "seamless", "refined-sport", "Alo", "Skims"],
                "next": None,
            },
            {
                "id": "f_al_fashion_power",
                "label": "Power Lift",
                "image_url": "https://images.unsplash.com/photo-1483721310020-03333e577078?w=400&h=500&fit=crop",
                "style_tags": ["power-lift", "bold-colors", "high-waist", "statement-sports-bra", "strong"],
                "next": None,
            },
            {
                "id": "f_al_fashion_tennis",
                "label": "Tennis / Country Club",
                "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=500&fit=crop",
                "style_tags": ["tennis", "country-club", "polo", "pleated-skirt", "retro-sport-luxury"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1551524559-8af4e6624178?w=400&h=500&fit=crop",
                "style_tags": ["Parisian", "effortless", "French-girl"],
                "next": "f_sc_paris_q3",
            },
            {
                "id": "f_sc_modern",
                "label": "Contemporary Minimal",
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=500&fit=crop",
                "style_tags": ["contemporary", "Toteme", "COS", "architectural"],
                "next": "f_sc_modern_q3",
            },
            {
                "id": "f_sc_office",
                "label": "Office Sophisticate",
                "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=500&fit=crop",
                "style_tags": ["tailored", "professional", "office-chic", "power-dressing", "polished"],
                "next": None,
            },
            {
                "id": "f_sc_soft",
                "label": "Soft Minimal",
                "image_url": "https://images.unsplash.com/photo-1611312449408-fcece27cdbb7?w=400&h=500&fit=crop",
                "style_tags": ["soft-minimal", "loose-silhouettes", "neutral-fabrics", "calm-palette", "relaxed"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&h=500&fit=crop",
                "style_tags": ["Breton-stripe", "trench-coat", "pointed-flats", "effortlessly-undone", "French-casual"],
                "next": None,
            },
            {
                "id": "f_sc_paris_elevated",
                "label": "Elevated Parisian",
                "image_url": "https://images.unsplash.com/photo-1544441893-675973e31985?w=400&h=500&fit=crop",
                "style_tags": ["silk-blouse", "wide-leg-trousers", "statement-earring", "French-chic", "polished"],
                "next": None,
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
                "image_url": "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=400&h=500&fit=crop",
                "style_tags": ["monochrome", "sculptural-cuts", "single-color-outfit", "architectural", "Toteme"],
                "next": None,
            },
            {
                "id": "f_sc_modern_relaxed",
                "label": "Relaxed Precision",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=500&fit=crop",
                "style_tags": ["wide-silhouette", "dropped-shoulder", "tailored-casual", "relaxed-precise", "COS"],
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
        "Woman": "root_f",
        "Non-binary": "root_nb",
        "Prefer not to say": "root_nb",
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
