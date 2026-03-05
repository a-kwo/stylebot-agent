import json

from services.profile_service import get_profile, update_profile
from services.shopping import search_products as shopping_search
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


def _enrich_from_recent_search(item_name: str, products: list[dict] | None = None) -> dict | None:
    """Fuzzy-match item_name against recent search products and return image_url + item_url."""
    search_list = products if products is not None else _recent_search_products
    if not search_list or not item_name:
        return None

    name_lower = item_name.lower().strip()

    # Exact title match first
    for p in search_list:
        if p.get("title", "").lower().strip() == name_lower:
            return {"image_url": p.get("image_url", ""), "item_url": p.get("item_url", "")}

    # Substring match (item name in title or title in item name)
    for p in search_list:
        title_lower = p.get("title", "").lower().strip()
        if name_lower in title_lower or title_lower in name_lower:
            return {"image_url": p.get("image_url", ""), "item_url": p.get("item_url", "")}

    # Word overlap match — if most words in the item name appear in a product title
    name_words = set(name_lower.split())
    best_match = None
    best_overlap = 0
    for p in search_list:
        title_words = set(p.get("title", "").lower().split())
        overlap = len(name_words & title_words)
        if overlap > best_overlap and overlap >= len(name_words) * 0.5:
            best_overlap = overlap
            best_match = p

    if best_match:
        return {"image_url": best_match.get("image_url", ""), "item_url": best_match.get("item_url", "")}

    return None


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


def _search_products(user_id: int, tool_input: dict, db=None) -> str:
    query = tool_input.get("query", "").strip()
    if not query:
        return json.dumps({"error": "query is required"})

    # Prepend gender to query if not already present (safety net)
    if db is not None:
        try:
            profile = get_profile(user_id, db)
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
        except Exception:
            pass  # Don't break search if profile lookup fails

    results = shopping_search(
        user_id=user_id,
        query=query,
        min_price=tool_input.get("min_price"),
        max_price=tool_input.get("max_price"),
        limit=tool_input.get("limit", 6),
    )
    return json.dumps({
        "products": results,
        "display_note": (
            "These products will be displayed to the user as interactive cards with images, "
            "prices, and links. Do NOT list, number, or describe individual products in your "
            "response. Just write 1-2 sentences of context about the results overall."
        ),
    })


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
        "SELECT category, color FROM wardrobe WHERE user_id = ? ORDER BY category",
        (user_id,),
    ).fetchall()

    # Count by category
    category_counts: dict[str, int] = {cat: 0 for cat in all_categories}
    colors = []
    for row in rows:
        cat = row["category"]
        if cat in category_counts:
            category_counts[cat] += 1
        color = row["color"]
        if color and color not in colors:
            colors.append(color)

    missing = [cat for cat, count in sorted(category_counts.items()) if count == 0]

    return json.dumps({
        "total_items": len(rows),
        "categories": category_counts,
        "missing_categories": missing,
        "colors": colors,
    })


def _ask_style_question(tool_input: dict) -> str:
    category = tool_input.get("category", "").strip()
    if not category:
        return json.dumps({"error": "category is required"})

    question = get_chat_question(category)
    if question is None:
        return json.dumps({"error": f"Unknown category: {category}"})

    return json.dumps({"quiz": question})
