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
                "image_url": {
                    "type": "string",
                    "description": "URL of the product image (from search results or user-provided)",
                },
                "purchase_url": {
                    "type": "string",
                    "description": "URL where the product can be purchased",
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
    {
        "name": "create_outfit",
        "description": (
            "Create a new outfit from the user's wardrobe items. Use this when the user asks "
            "you to put together an outfit or save a combination of items they like."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A descriptive name for the outfit (e.g. 'Casual Friday', 'Date Night Look')",
                },
                "occasion": {
                    "type": "string",
                    "description": "When this outfit is for (e.g. work, casual, date, formal, gym)",
                },
                "season": {
                    "type": "string",
                    "enum": ["spring", "summer", "fall", "winter", "all-season"],
                    "description": "What season this outfit suits",
                },
                "notes": {
                    "type": "string",
                    "description": "Any styling notes or tips for this outfit",
                },
                "wardrobe_item_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "IDs of wardrobe items to include in the outfit (get these from get_wardrobe)",
                },
            },
            "required": ["name", "wardrobe_item_ids"],
        },
    },
    {
        "name": "get_outfits",
        "description": "Retrieve the user's saved outfits. Optionally filter by occasion or season.",
        "input_schema": {
            "type": "object",
            "properties": {
                "occasion": {
                    "type": "string",
                    "description": "Filter by occasion (e.g. work, casual, date)",
                },
                "season": {
                    "type": "string",
                    "enum": ["spring", "summer", "fall", "winter", "all-season"],
                    "description": "Filter by season",
                },
            },
            "required": [],
        },
    },
    {
        "name": "suggest_outfit",
        "description": (
            "Suggest an outfit from the user's wardrobe for a given occasion, season, or context. "
            "Looks at their wardrobe items and saved outfits to recommend a combination. "
            "Use this when the user asks 'what should I wear?' or similar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "occasion": {
                    "type": "string",
                    "description": "What the outfit is for (e.g. work, casual, date night, interview)",
                },
                "season": {
                    "type": "string",
                    "description": "Current season or weather context",
                },
                "constraints": {
                    "type": "string",
                    "description": "Any constraints (e.g. 'must include my new blazer', 'no heels')",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_outfit_feedback",
        "description": (
            "Get AI feedback on an outfit combination. Takes wardrobe item IDs and returns "
            "the full item details for Claude to evaluate color harmony, occasion appropriateness, "
            "style coherence, and suggest swaps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wardrobe_item_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "IDs of wardrobe items that form the outfit",
                },
                "occasion": {
                    "type": "string",
                    "description": "What occasion the outfit is for (e.g. work, casual, date)",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context (e.g. 'outdoor event', 'office meeting')",
                },
            },
            "required": ["wardrobe_item_ids"],
        },
    },
    {
        "name": "analyze_wardrobe",
        "description": (
            "Analyze the user's wardrobe to identify gaps, category distribution, and color variety. "
            "Use this when the user asks 'what should I buy next?' or when you want to give gap-aware advice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "ask_style_question",
        "description": (
            "Ask the user a visual style preference question. Use this every 3-5 messages "
            "to learn more about their taste. Pick a category you haven't asked about yet."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category to ask about (e.g. sneakers, formal_wear, patterns, accessories, dresses, activewear)",
                },
            },
            "required": ["category"],
        },
    },
]
