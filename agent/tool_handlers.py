import json

from services.profile_service import get_profile, update_profile
from services.shopping import search_products as shopping_search


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
            return _search_products(user_id, tool_input)
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

    cur = db.execute(
        """INSERT INTO wardrobe (user_id, name, category, color, brand, tags)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            name,
            category,
            tool_input.get("color"),
            tool_input.get("brand"),
            json.dumps(tool_input.get("tags", [])),
        ),
    )
    db.commit()
    return json.dumps({"status": "added", "id": cur.lastrowid, "name": name})


def _search_products(user_id: int, tool_input: dict) -> str:
    query = tool_input.get("query", "").strip()
    if not query:
        return json.dumps({"error": "query is required"})

    results = shopping_search(
        user_id=user_id,
        query=query,
        min_price=tool_input.get("min_price"),
        max_price=tool_input.get("max_price"),
        limit=tool_input.get("limit", 6),
    )
    return json.dumps({"products": results})
