"""Quiz question data for onboarding and in-chat style preference questions."""

QUIZ_QUESTIONS = {
    # ── Onboarding categories (8 outfit-based) ───────────────────
    "outfit_everyday": {
        "prompt": "Pick the everyday outfit that feels most like you.",
        "options": [
            {
                "id": "everyday-minimalist",
                "label": "Clean & Minimal",
                "image_url": "https://images.unsplash.com/photo-1666358085605-b3b717d5a210?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "timeless"],
            },
            {
                "id": "everyday-streetwear",
                "label": "Street-Ready",
                "image_url": "https://images.unsplash.com/photo-1523398002811-999ca8dec234?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "urban"],
            },
            {
                "id": "everyday-classic",
                "label": "Classic & Polished",
                "image_url": "https://images.unsplash.com/photo-1667243142746-deb10f212300?w=400&h=400&fit=crop",
                "style_tags": ["classic", "polished"],
            },
            {
                "id": "everyday-bohemian",
                "label": "Boho Relaxed",
                "image_url": "https://images.unsplash.com/photo-1718737654958-9b49716693bb?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "relaxed"],
            },
        ],
    },
    "outfit_weekend": {
        "prompt": "It's Saturday — which outfit are you reaching for?",
        "options": [
            {
                "id": "weekend-athleisure",
                "label": "Athleisure Vibes",
                "image_url": "https://images.unsplash.com/photo-1618355281951-a174b87198e2?w=400&h=400&fit=crop",
                "style_tags": ["athleisure", "casual"],
            },
            {
                "id": "weekend-vintage",
                "label": "Vintage Finds",
                "image_url": "https://images.unsplash.com/photo-1593458778871-3c08120770e4?w=400&h=400&fit=crop",
                "style_tags": ["vintage", "retro"],
            },
            {
                "id": "weekend-smart",
                "label": "Effortless Smart",
                "image_url": "https://images.unsplash.com/photo-1588189408846-30ad110a0f4c?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "refined"],
            },
            {
                "id": "weekend-edgy",
                "label": "Edgy Layers",
                "image_url": "https://images.unsplash.com/photo-1608680480325-d3ec3cdf7e60?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "bold"],
            },
        ],
    },
    "outfit_going_out": {
        "prompt": "You're heading out tonight — which look do you choose?",
        "options": [
            {
                "id": "goingout-sleek",
                "label": "Sleek & Dark",
                "image_url": "https://images.unsplash.com/photo-1593032470861-4509830938cb?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "sophisticated"],
            },
            {
                "id": "goingout-streetlux",
                "label": "Street Luxe",
                "image_url": "https://images.unsplash.com/photo-1556766129-37f0e1e17847?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "bold"],
            },
            {
                "id": "goingout-classic",
                "label": "Classic Night Out",
                "image_url": "https://images.unsplash.com/photo-1610652492500-ded49ceeb378?w=400&h=400&fit=crop",
                "style_tags": ["classic", "elegant"],
            },
            {
                "id": "goingout-eclectic",
                "label": "Eclectic Mix",
                "image_url": "https://images.unsplash.com/photo-1764698192655-2beff44ad6cc?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "eclectic"],
            },
        ],
    },
    "outfit_date": {
        "prompt": "First date outfit — what's your go-to?",
        "options": [
            {
                "id": "date-smart-casual",
                "label": "Smart Casual",
                "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "tailored"],
            },
            {
                "id": "date-effortless",
                "label": "Effortless Cool",
                "image_url": "https://images.unsplash.com/photo-1544441893-675973e31985?w=400&h=400&fit=crop",
                "style_tags": ["vintage", "casual"],
            },
            {
                "id": "date-edgy",
                "label": "Edgy Statement",
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "modern"],
            },
            {
                "id": "date-bohemian",
                "label": "Romantic Boho",
                "image_url": "https://images.unsplash.com/photo-1725114028309-3b6b4aed3278?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "chic"],
            },
        ],
    },
    "outfit_summer": {
        "prompt": "Peak summer — which full outfit do you picture?",
        "options": [
            {
                "id": "summer-minimal",
                "label": "Breezy Minimal",
                "image_url": "https://images.unsplash.com/photo-1604006852748-903fccbc4019?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "relaxed"],
            },
            {
                "id": "summer-streetwear",
                "label": "Bold Summer Street",
                "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "trendy"],
            },
            {
                "id": "summer-classic",
                "label": "Preppy Summer",
                "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&h=400&fit=crop",
                "style_tags": ["classic", "sporty"],
            },
            {
                "id": "summer-boho",
                "label": "Festival Ready",
                "image_url": "https://images.unsplash.com/photo-1647211102988-0571f7440219?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "adventurous"],
            },
        ],
    },
    "outfit_winter": {
        "prompt": "Cold weather look — what's your layering style?",
        "options": [
            {
                "id": "winter-minimalist",
                "label": "Sleek Layers",
                "image_url": "https://images.unsplash.com/photo-1709614268006-96be7984bf05?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "polished"],
            },
            {
                "id": "winter-street",
                "label": "Street Puffer",
                "image_url": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "cozy"],
            },
            {
                "id": "winter-classic",
                "label": "Tailored Overcoat",
                "image_url": "https://images.unsplash.com/photo-1592878849122-facb97520f9e?w=400&h=400&fit=crop",
                "style_tags": ["classic", "refined"],
            },
            {
                "id": "winter-rugged",
                "label": "Rugged Outdoors",
                "image_url": "https://images.unsplash.com/photo-1646061392496-bacaa3fe68a8?w=400&h=400&fit=crop",
                "style_tags": ["rugged", "athleisure"],
            },
        ],
    },
    "outfit_work": {
        "prompt": "Walking into the office — which look do you own?",
        "options": [
            {
                "id": "work-classic",
                "label": "Sharp Tailoring",
                "image_url": "https://images.unsplash.com/photo-1763598461615-610264129bea?w=400&h=400&fit=crop",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "work-smart-casual",
                "label": "Smart Casual",
                "image_url": "https://images.unsplash.com/photo-1723277171985-07c20f1876e1?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "modern"],
            },
            {
                "id": "work-creative",
                "label": "Creative Office",
                "image_url": "https://images.unsplash.com/photo-1696960181436-1b6d9576354e?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "artsy"],
            },
            {
                "id": "work-minimal",
                "label": "Clean & Understated",
                "image_url": "https://images.unsplash.com/photo-1708295923811-9b025f4f5fcc?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "timeless"],
            },
        ],
    },
    "outfit_dream": {
        "prompt": "Dream wardrobe — if money were no object, which vibe?",
        "options": [
            {
                "id": "dream-avant-garde",
                "label": "Avant-Garde",
                "image_url": "https://images.unsplash.com/photo-1568936829638-715cab9b5142?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "bold"],
            },
            {
                "id": "dream-vintage",
                "label": "Curated Vintage",
                "image_url": "https://images.unsplash.com/photo-1681377629414-cc21664505f1?w=400&h=400&fit=crop",
                "style_tags": ["vintage", "sophisticated"],
            },
            {
                "id": "dream-classic",
                "label": "Timeless Luxury",
                "image_url": "https://images.unsplash.com/photo-1614416943242-9e18ce1ea19b?w=400&h=400&fit=crop",
                "style_tags": ["classic", "elegant"],
            },
            {
                "id": "dream-streetwear",
                "label": "Hype Collection",
                "image_url": "https://images.unsplash.com/photo-1765560217763-aaa285ffd313?w=400&h=400&fit=crop",
                "style_tags": ["streetwear", "urban"],
            },
        ],
    },
    # ── Chat-only categories ───────────────────────────────────
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

ONBOARDING_CATEGORIES = [
    "outfit_everyday", "outfit_weekend", "outfit_going_out", "outfit_date",
    "outfit_summer", "outfit_winter", "outfit_work", "outfit_dream",
]


def get_onboarding_questions() -> list[dict]:
    """Return the 8 onboarding quiz questions with full option data."""
    questions = []
    for cat in ONBOARDING_CATEGORIES:
        q = QUIZ_QUESTIONS[cat].copy()
        q["category"] = cat
        questions.append(q)
    return questions


def get_chat_question(category: str) -> dict | None:
    """Return a single quiz question for in-chat use, or None if category unknown."""
    if category not in QUIZ_QUESTIONS:
        return None
    q = QUIZ_QUESTIONS[category].copy()
    q["category"] = category
    return q
