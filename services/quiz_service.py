"""Quiz question data for onboarding and in-chat style preference questions."""

QUIZ_QUESTIONS = {
    # ── Onboarding categories (8 outfit-based) ───────────────────
    "outfit_everyday": {
        "prompt": "Pick the everyday outfit that feels most like you.",
        "options": [
            {
                "id": "everyday-minimalist",
                "label": "Clean & Minimal",
                "image_url": "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1487222477894-8943e31ef7b2?w=400&h=400&fit=crop",
                "style_tags": ["classic", "polished"],
            },
            {
                "id": "everyday-bohemian",
                "label": "Boho Relaxed",
                "image_url": "https://images.unsplash.com/photo-1479064555552-3ef4979f8908?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=400&h=400&fit=crop",
                "style_tags": ["vintage", "retro"],
            },
            {
                "id": "weekend-smart",
                "label": "Effortless Smart",
                "image_url": "https://images.unsplash.com/photo-1550246140-29f40b909e5a?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "refined"],
            },
            {
                "id": "weekend-edgy",
                "label": "Edgy Layers",
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop",
                "style_tags": ["minimalist", "sophisticated"],
            },
            {
                "id": "goingout-streetlux",
                "label": "Street Luxe",
                "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1611312449408-fcece27cdbb7?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1551537482-f2075a1d41f2?w=400&h=400&fit=crop",
                "style_tags": ["classic", "refined"],
            },
            {
                "id": "winter-rugged",
                "label": "Rugged Outdoors",
                "image_url": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=400&h=400&fit=crop",
                "style_tags": ["classic", "professional"],
            },
            {
                "id": "work-smart-casual",
                "label": "Smart Casual",
                "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=400&h=400&fit=crop",
                "style_tags": ["smart-casual", "modern"],
            },
            {
                "id": "work-creative",
                "label": "Creative Office",
                "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "artsy"],
            },
            {
                "id": "work-minimal",
                "label": "Clean & Understated",
                "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=400&h=400&fit=crop",
                "style_tags": ["edgy", "bold"],
            },
            {
                "id": "dream-vintage",
                "label": "Curated Vintage",
                "image_url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=400&h=400&fit=crop",
                "style_tags": ["vintage", "sophisticated"],
            },
            {
                "id": "dream-classic",
                "label": "Timeless Luxury",
                "image_url": "https://images.unsplash.com/photo-1638247025967-b4e38f787b76?w=400&h=400&fit=crop",
                "style_tags": ["classic", "elegant"],
            },
            {
                "id": "dream-streetwear",
                "label": "Hype Collection",
                "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1490114538077-0a7f8cb49891?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "expressive"],
            },
            {
                "id": "solid",
                "label": "Solid Colors",
                "image_url": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&h=400&fit=crop",
                "style_tags": ["bohemian", "flowy"],
            },
            {
                "id": "shirt-dress",
                "label": "Shirt Dress",
                "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400&h=400&fit=crop",
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
                "image_url": "https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=400&h=400&fit=crop",
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
