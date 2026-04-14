import json

from services.profile_service import get_profile, update_profile
from services.shopping import search_products as shopping_search, filter_results
from services.style_translator import classify_color_temperature, CULTURAL_REF_BRANDS
from services.product_ranker import rank_products
from services.quiz_service import get_chat_question
from services.outfit_service import (
    create_outfit as svc_create_outfit,
    get_outfits as svc_get_outfits,
    get_outfit as svc_get_outfit,
)

# Recent search results buffer — populated by the agent loop after search_products,
# consumed by _add_to_wardrobe to auto-enrich items with image/purchase URLs.
_recent_search_products: list[dict] = []


def set_recent_search_products(products: list[dict]) -> None:
    """Called by the agent loop after search_products to cache results."""
    global _recent_search_products
    _recent_search_products = list(products)


def _fuzzy_match_products(item_name: str, products: list[dict]) -> dict | None:
    """Fuzzy-match item_name against a product list and return the best match."""
    if not products or not item_name:
        return None

    name_lower = item_name.lower().strip()

    # Exact title match first
    for p in products:
        if p.get("title", "").lower().strip() == name_lower:
            return {"image_url": p.get("image_url", ""), "item_url": p.get("item_url", "")}

    # Substring match (item name in title or title in item name)
    for p in products:
        title_lower = p.get("title", "").lower().strip()
        if name_lower in title_lower or title_lower in name_lower:
            return {"image_url": p.get("image_url", ""), "item_url": p.get("item_url", "")}

    # Word overlap match — if most words in the item name appear in a product title
    name_words = set(name_lower.split())
    best_match = None
    best_overlap = 0
    for p in products:
        title_words = set(p.get("title", "").lower().split())
        overlap = len(name_words & title_words)
        if overlap > best_overlap and overlap >= len(name_words) * 0.5:
            best_overlap = overlap
            best_match = p

    if best_match:
        return {"image_url": best_match.get("image_url", ""), "item_url": best_match.get("item_url", "")}

    return None


def _enrich_from_recent_search(item_name: str, products: list[dict] | None = None) -> dict | None:
    """Fuzzy-match item_name against recent search products and return image_url + item_url."""
    search_list = products if products is not None else _recent_search_products
    return _fuzzy_match_products(item_name, search_list)


def _enrich_from_conversation_history(user_id: int, item_name: str, db) -> dict | None:
    """Fallback: search stored conversation meta records for product image URLs.

    This handles the case where the in-memory buffer is empty (e.g. server restart)
    but the user is referencing a product from a previous search.
    """
    try:
        rows = db.execute(
            "SELECT content FROM conversations WHERE user_id = ? AND role = 'meta' ORDER BY id DESC LIMIT 10",
            (user_id,),
        ).fetchall()
    except Exception:
        return None

    all_products = []
    for row in rows:
        try:
            meta = json.loads(row["content"])
            if isinstance(meta, list):
                for block in meta:
                    if isinstance(block, dict) and block.get("type") == "products":
                        all_products.extend(block.get("products", []))
        except Exception:
            continue

    return _fuzzy_match_products(item_name, all_products)


def dispatch_tool(tool_name: str, tool_input: dict, user_id: int, db) -> str:
    try:
        if tool_name == "get_profile":
            return _get_profile(user_id, db)
        elif tool_name == "update_profile":
            return _update_profile(user_id, tool_input, db)
        elif tool_name == "get_wardrobe":
            return _get_wardrobe(user_id, tool_input, db)
        elif tool_name == "add_to_wardrobe":
            return _add_to_wardrobe(user_id, tool_input, db)
        elif tool_name == "search_products":
            return _search_products(user_id, tool_input, db=db)
        elif tool_name == "create_outfit":
            return _create_outfit(user_id, tool_input, db)
        elif tool_name == "get_outfits":
            return _get_outfits(user_id, tool_input, db)
        elif tool_name == "suggest_outfit":
            return _suggest_outfit(user_id, tool_input, db)
        elif tool_name == "get_outfit_feedback":
            return _get_outfit_feedback(user_id, tool_input, db)
        elif tool_name == "analyze_wardrobe":
            return _analyze_wardrobe(user_id, db)
        elif tool_name == "ask_style_question":
            return _ask_style_question(tool_input)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _get_profile(user_id: int, db) -> str:
    profile = get_profile(user_id, db)
    return json.dumps(profile)


def _update_profile(user_id: int, updates: dict, db) -> str:
    updated = update_profile(user_id, updates, db)
    return json.dumps({"status": "updated", "profile": updated})


def _get_wardrobe(user_id: int, tool_input: dict, db) -> str:
    category = tool_input.get("category")
    if category:
        rows = db.execute(
            "SELECT * FROM wardrobe WHERE user_id = ? AND category = ? ORDER BY added_at DESC",
            (user_id, category),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM wardrobe WHERE user_id = ? ORDER BY added_at DESC",
            (user_id,),
        ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        try:
            item["tags"] = json.loads(item.get("tags") or "[]")
        except Exception:
            item["tags"] = []
        items.append(item)
    return json.dumps(items)


def _add_to_wardrobe(user_id: int, tool_input: dict, db) -> str:
    name = tool_input.get("name", "").strip()
    category = tool_input.get("category", "").strip()

    if not name or not category:
        return json.dumps({"error": "name and category are required"})

    valid_categories = {"tops", "bottoms", "shoes", "outerwear", "accessories", "dresses"}
    if category not in valid_categories:
        return json.dumps({"error": f"Invalid category: {category}"})

    image_url = tool_input.get("image_url")
    purchase_url = tool_input.get("purchase_url")

    # Auto-enrich from recent search results if Claude didn't pass image/purchase URLs
    if not image_url:
        match = _enrich_from_recent_search(name)
        # Fallback: check stored conversation history (survives server restarts)
        if not match:
            match = _enrich_from_conversation_history(user_id, name, db)
        if match:
            image_url = match.get("image_url") or image_url
            purchase_url = purchase_url or match.get("item_url")

    cur = db.execute(
        """INSERT INTO wardrobe (user_id, name, category, color, brand, tags, image_url, purchase_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            name,
            category,
            tool_input.get("color"),
            tool_input.get("brand"),
            json.dumps(tool_input.get("tags", [])),
            image_url,
            purchase_url,
        ),
    )
    db.commit()
    return json.dumps({"status": "added", "id": cur.lastrowid, "name": name})


def _enhance_query(
    query: str,
    profile: dict,
    explicit_min: float | None,
    explicit_max: float | None,
) -> dict:
    """Auto-inject profile data into a search query.

    Returns dict with: query, min_price, max_price, warnings.
    """
    warnings: list[str] = []
    enhanced_query = query

    # Check for avoided brands
    avoided_brands = profile.get("avoided_brands", [])
    if isinstance(avoided_brands, str):
        try:
            avoided_brands = json.loads(avoided_brands)
        except Exception:
            avoided_brands = []
    if isinstance(avoided_brands, dict):
        avoided_brands = list(avoided_brands.keys())
    for brand in avoided_brands:
        if brand.lower() in query.lower():
            warnings.append(
                f"Warning: '{brand}' is in the user's avoided brands list. Consider alternative brands."
            )

    # Append fit preference if not already present
    fit_preferences = profile.get("fit_preferences", [])
    if isinstance(fit_preferences, str):
        try:
            fit_preferences = json.loads(fit_preferences)
        except Exception:
            fit_preferences = []
    if isinstance(fit_preferences, dict):
        fit_preferences = sorted(fit_preferences.keys(), key=lambda f: fit_preferences[f], reverse=True)
    if fit_preferences:
        dominant_fit = fit_preferences[0]
        if dominant_fit.lower() not in enhanced_query.lower():
            enhanced_query = f"{enhanced_query} {dominant_fit}"

    # Inject budget as price params if not explicitly provided
    min_price = explicit_min
    max_price = explicit_max

    budget_min = profile.get("budget_min")
    budget_max = profile.get("budget_max")

    if min_price is None and budget_min and budget_min > 0:
        min_price = budget_min
    if max_price is None and budget_max and budget_max > 0:
        max_price = budget_max

    return {
        "query": enhanced_query,
        "min_price": min_price,
        "max_price": max_price,
        "warnings": warnings,
    }


def _search_products(user_id: int, tool_input: dict, db=None) -> str:
    query = tool_input.get("query", "").strip()
    if not query:
        return json.dumps({"error": "query is required"})

    # Enhance query with profile data
    explicit_min = tool_input.get("min_price")
    explicit_max = tool_input.get("max_price")
    enhancement_warnings = []
    avoided_brands = []
    avoided_colors = []
    profile = {}
    requested_limit = tool_input.get("limit", 6)

    if db is not None:
        try:
            profile = get_profile(user_id, db)

            # Prepend gender if not already present
            gender = (profile.get("gender") or "").strip().lower()
            if gender and gender not in ("unknown", "prefer not to say"):
                gender_terms = {"male": ["male", "men", "man", "mens", "men's"],
                                "female": ["female", "women", "woman", "womens", "women's"],
                                "non-binary": []}
                search_terms = gender_terms.get(gender, [])
                query_lower = query.lower()
                if search_terms and not any(term in query_lower for term in search_terms):
                    prefix = "mens" if gender == "male" else "womens" if gender == "female" else ""
                    if prefix:
                        query = f"{prefix} {query}"

            # Auto-inject brands, budget, fit preferences
            enhanced = _enhance_query(query, profile, explicit_min, explicit_max)
            query = enhanced["query"]
            explicit_min = enhanced["min_price"]
            explicit_max = enhanced["max_price"]
            enhancement_warnings = enhanced["warnings"]

            # Collect avoided lists for post-filtering
            avoided_brands = profile.get("avoided_brands", [])
            if isinstance(avoided_brands, str):
                try:
                    avoided_brands = json.loads(avoided_brands)
                except Exception:
                    avoided_brands = []
            if isinstance(avoided_brands, dict):
                avoided_brands = list(avoided_brands.keys())
            avoided_colors = profile.get("avoided_colors", [])
            if isinstance(avoided_colors, str):
                try:
                    avoided_colors = json.loads(avoided_colors)
                except Exception:
                    avoided_colors = []
            if isinstance(avoided_colors, dict):
                avoided_colors = list(avoided_colors.keys())
        except Exception:
            pass  # Don't break search if profile lookup fails

    results = shopping_search(
        user_id=user_id,
        query=query,
        min_price=explicit_min,
        max_price=explicit_max,
        limit=requested_limit,
    )

    # Post-filter results to remove avoided brands/colors
    if avoided_brands or avoided_colors:
        results = filter_results(results, avoided_brands, avoided_colors)

        # If too many filtered, retry with larger limit
        if len(results) < requested_limit // 2 and requested_limit <= 6:
            expanded = shopping_search(
                user_id=user_id,
                query=query,
                min_price=explicit_min,
                max_price=explicit_max,
                limit=min(requested_limit * 2, 10),
            )
            results = filter_results(expanded, avoided_brands, avoided_colors)[:requested_limit]

    # Re-rank results based on user preferences, wardrobe, and feedback
    if db is not None:
        try:
            wardrobe_items = db.execute(
                "SELECT name, category, color, brand FROM wardrobe WHERE user_id = ?",
                (user_id,),
            ).fetchall()
            feedback_rows = db.execute(
                "SELECT product_title, feedback, price, color, seller FROM recommendation_feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
                (user_id,),
            ).fetchall()
            results = rank_products(
                results,
                profile,
                [dict(r) for r in wardrobe_items],
                [dict(r) for r in feedback_rows],
            )
        except Exception:
            pass  # Don't break search if ranking fails

    response = {
        "products": results,
        "display_note": (
            "These products will be displayed to the user as interactive cards with images, "
            "prices, and links. Do NOT list, number, or describe individual products in your "
            "response. Just write 1-2 sentences of context about the results overall."
        ),
    }
    if enhancement_warnings:
        response["warnings"] = enhancement_warnings
    return json.dumps(response)


def _create_outfit(user_id: int, tool_input: dict, db) -> str:
    name = tool_input.get("name", "").strip()
    if not name:
        return json.dumps({"error": "name is required"})

    wardrobe_item_ids = tool_input.get("wardrobe_item_ids", [])
    if not wardrobe_item_ids:
        return json.dumps({"error": "wardrobe_item_ids is required (list of wardrobe item IDs)"})

    outfit = svc_create_outfit(
        user_id=user_id,
        name=name,
        occasion=tool_input.get("occasion"),
        season=tool_input.get("season"),
        notes=tool_input.get("notes", ""),
        wardrobe_item_ids=wardrobe_item_ids,
        db=db,
    )
    return json.dumps({"status": "created", "outfit": outfit})


def _get_outfits(user_id: int, tool_input: dict, db) -> str:
    outfits = svc_get_outfits(
        user_id=user_id,
        db=db,
        occasion=tool_input.get("occasion"),
        season=tool_input.get("season"),
    )
    return json.dumps({"outfits": outfits, "count": len(outfits)})


def _suggest_outfit(user_id: int, tool_input: dict, db) -> str:
    # Gather wardrobe and existing outfits for the AI to reason over
    wardrobe_rows = db.execute(
        "SELECT * FROM wardrobe WHERE user_id = ? ORDER BY added_at DESC",
        (user_id,),
    ).fetchall()

    items = []
    for row in wardrobe_rows:
        item = dict(row)
        try:
            item["tags"] = json.loads(item.get("tags") or "[]")
        except Exception:
            item["tags"] = []
        items.append(item)

    outfits = svc_get_outfits(user_id, db)

    return json.dumps({
        "wardrobe_items": items,
        "existing_outfits": outfits,
        "occasion": tool_input.get("occasion"),
        "season": tool_input.get("season"),
        "constraints": tool_input.get("constraints"),
        "instruction": "Use the wardrobe items above to suggest a complete outfit. Respond with specific item names and IDs.",
    })


def _get_outfit_feedback(user_id: int, tool_input: dict, db) -> str:
    item_ids = tool_input.get("wardrobe_item_ids", [])
    if not item_ids:
        return json.dumps({"error": "wardrobe_item_ids is required"})

    placeholders = ",".join("?" for _ in item_ids)
    rows = db.execute(
        f"SELECT * FROM wardrobe WHERE user_id = ? AND id IN ({placeholders})",
        [user_id] + item_ids,
    ).fetchall()

    items = []
    for row in rows:
        item = dict(row)
        try:
            item["tags"] = json.loads(item.get("tags") or "[]")
        except Exception:
            item["tags"] = []
        items.append(item)

    return json.dumps({
        "items": items,
        "occasion": tool_input.get("occasion"),
        "context": tool_input.get("context"),
        "instruction": (
            "Evaluate this outfit combination. Give specific praise and one concrete "
            "improvement suggestion. Consider color harmony, occasion appropriateness, "
            "style coherence, and suggest swaps from the user's wardrobe if applicable."
        ),
    })


def _analyze_wardrobe(user_id: int, db) -> str:
    all_categories = {"tops", "bottoms", "shoes", "outerwear", "accessories", "dresses"}

    rows = db.execute(
        "SELECT category, color, brand, tags FROM wardrobe WHERE user_id = ? ORDER BY category",
        (user_id,),
    ).fetchall()

    # Count by category
    category_counts: dict[str, int] = {cat: 0 for cat in all_categories}
    colors = []
    color_temp_counts = {"warm": 0, "cool": 0, "neutral": 0}
    brands = []

    for row in rows:
        cat = row["category"]
        if cat in category_counts:
            category_counts[cat] += 1
        color = row["color"]
        if color and color not in colors:
            colors.append(color)
        # Color temperature
        if color:
            temp = classify_color_temperature(color)
            color_temp_counts[temp] += 1
        # Collect brands
        brand = row["brand"]
        if brand and brand not in brands:
            brands.append(brand)

    missing = [cat for cat, count in sorted(category_counts.items()) if count == 0]

    # ── Brand alignment with style vector ────────────────────────────────
    aligned_brands = []
    unaligned_brands = []

    # Load profile for style vector and occasions (gracefully handle missing table/columns)
    try:
        profile_row = db.execute(
            "SELECT style_vector, occasions FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    except Exception:
        profile_row = None

    if profile_row and brands:
        style_vector_raw = profile_row["style_vector"] or "{}"
        try:
            style_vector = json.loads(style_vector_raw) if isinstance(style_vector_raw, str) else (style_vector_raw or {})
        except Exception:
            style_vector = {}

        primary_ref = style_vector.get("primary_cultural_ref")
        if primary_ref and primary_ref in CULTURAL_REF_BRANDS:
            ref_brands_lower = [b.lower() for b in CULTURAL_REF_BRANDS[primary_ref]]
            for brand in brands:
                if brand.lower() in ref_brands_lower:
                    aligned_brands.append(brand)
                else:
                    unaligned_brands.append(brand)

    # ── Occasion gaps ────────────────────────────────────────────────────
    OCCASION_REQUIRED_CATEGORIES: dict[str, list[str]] = {
        "formal": ["tops", "bottoms", "shoes", "outerwear"],
        "casual": ["tops", "bottoms", "shoes"],
        "business": ["tops", "bottoms", "shoes", "outerwear"],
        "date": ["tops", "bottoms", "shoes"],
        "active": ["tops", "bottoms", "shoes"],
        "travel": ["tops", "bottoms", "shoes", "outerwear"],
    }

    occasion_gaps: dict[str, list[str]] = {}
    if profile_row:
        occasions_raw = profile_row["occasions"] or "[]"
        try:
            occasions = json.loads(occasions_raw) if isinstance(occasions_raw, str) else (occasions_raw or [])
        except Exception:
            occasions = []

        owned_categories = {cat for cat, count in category_counts.items() if count > 0}
        for occasion in occasions:
            occ_lower = occasion.lower()
            required = OCCASION_REQUIRED_CATEGORIES.get(occ_lower, [])
            gaps = [cat for cat in required if cat not in owned_categories]
            if gaps:
                occasion_gaps[occasion] = gaps

    return json.dumps({
        "total_items": len(rows),
        "categories": category_counts,
        "missing_categories": missing,
        "colors": colors,
        "color_temperature": color_temp_counts,
        "brand_alignment": {"aligned": aligned_brands, "unaligned": unaligned_brands},
        "occasion_gaps": occasion_gaps,
    })


def _ask_style_question(tool_input: dict) -> str:
    category = tool_input.get("category", "").strip()
    if not category:
        return json.dumps({"error": "category is required"})

    question = get_chat_question(category)
    if question is None:
        return json.dumps({"error": f"Unknown category: {category}"})

    return json.dumps({"quiz": question})
