TOOLS = [
    {
        "name": "get_profile",
        "description": "Retrieve the user's current taste profile including style preferences, sizes, budget, and notes.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "update_profile",
        "description": (
            "Update the user's taste profile with new information you've learned. "
            "Only call this when you've genuinely learned something new — not every turn. "
            "Array fields (style_adjectives, preferred_colors, etc.) are union-merged; "
            "existing values are never removed. Non-array fields are overwritten. "
            "Use 'notes' for free-text observations about the user (prepended with a timestamp)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "style_adjectives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Words describing their style (e.g. minimalist, preppy, edgy)",
                },
                "preferred_colors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Colors they like",
                },
                "avoided_colors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Colors they dislike or want to avoid",
                },
                "preferred_brands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Brands they like",
                },
                "avoided_brands": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Brands they want to avoid",
                },
                "size_tops": {"type": "string", "description": "Top size (e.g. S, M, L, XL, 38)"},
                "size_bottoms": {"type": "string", "description": "Bottom size (e.g. 32x30, M, 28)"},
                "size_shoes": {"type": "string", "description": "Shoe size (e.g. 10, 42, 8.5)"},
                "budget_min": {"type": "integer", "description": "Minimum budget in USD"},
                "budget_max": {"type": "integer", "description": "Maximum budget in USD"},
                "occasions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Occasions they dress for (e.g. work, casual, formal, gym)",
                },
                "fit_preferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fit preferences (e.g. slim fit, relaxed, oversized, tailored)",
                },
                "notes": {
                    "type": "string",
                    "description": "Free-text note about this user — observations, context, preferences not captured by other fields",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_wardrobe",
        "description": "Retrieve the user's wardrobe items. Optionally filter by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["tops", "bottoms", "shoes", "outerwear", "accessories", "dresses"],
                    "description": "Filter by category (optional)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "add_to_wardrobe",
        "description": (
            "Save an item to the user's wardrobe. Use this when the user mentions they own something, "
            "or when they confirm purchasing a product."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Item name (e.g. 'Navy slim chinos', 'White Oxford shirt')",
                },
                "category": {
                    "type": "string",
                    "enum": ["tops", "bottoms", "shoes", "outerwear", "accessories", "dresses"],
                },
                "color": {"type": "string"},
                "brand": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Descriptive tags (e.g. casual, formal, summer, workwear)",
                },
            },
            "required": ["name", "category"],
        },
    },
    {
        "name": "search_products",
        "description": (
            "Search for real, purchasable clothing and accessories online via Google Shopping. "
            "Use this when the user asks for product recommendations or wants to buy something. "
            "Craft a natural-language query like 'women slim fit chinos navy' for best results. "
            "Respect the user's budget from their profile unless they specify otherwise."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g. 'women slim fit navy chinos', 'men leather chelsea boots black')",
                },
                "min_price": {"type": "number", "description": "Minimum price in USD"},
                "max_price": {"type": "number", "description": "Maximum price in USD"},
                "limit": {
                    "type": "integer",
                    "description": "Max number of results to return (1–10, default 6)",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    },
]
