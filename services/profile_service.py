import json
from datetime import date

WEIGHTED_FIELDS = ["style_adjectives"]
ARRAY_FIELDS = [
    "preferred_colors", "avoided_colors",
    "preferred_brands", "avoided_brands", "occasions", "fit_preferences",
]
SCALAR_FIELDS = ["size_tops", "size_bottoms", "size_shoes", "budget_min", "budget_max"]


def _migrate_weighted(raw: str) -> dict:
    """Auto-migrate old array format to weighted dict format."""
    try:
        data = json.loads(raw or "[]")
    except Exception:
        return {}
    if isinstance(data, list):
        return {v: 1 for v in data}
    if isinstance(data, dict):
        return data
    return {}


def get_profile(user_id: int, db) -> dict:
    row = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {}

    profile = dict(row)
    for field in WEIGHTED_FIELDS:
        profile[field] = _migrate_weighted(profile.get(field) or "[]")
    for field in ARRAY_FIELDS:
        try:
            profile[field] = json.loads(profile.get(field) or "[]")
        except Exception:
            profile[field] = []
    return profile


def update_profile(user_id: int, updates: dict, db) -> dict:
    current = get_profile(user_id, db)

    set_clauses = []
    params = []

    # Weighted fields: increment weights instead of union-append
    for field in WEIGHTED_FIELDS:
        if field in updates and updates[field]:
            current_weights = current.get(field, {})
            if not isinstance(current_weights, dict):
                current_weights = _migrate_weighted(json.dumps(current_weights))
            new_vals = updates[field] if isinstance(updates[field], list) else list(updates[field])
            for v in new_vals:
                current_weights[v] = current_weights.get(v, 0) + 1
            set_clauses.append(f"{field} = ?")
            params.append(json.dumps(current_weights))

    for field in ARRAY_FIELDS:
        if field in updates and updates[field]:
            current_vals = current.get(field, [])
            if not isinstance(current_vals, list):
                current_vals = []
            merged = list(dict.fromkeys(current_vals + [v for v in updates[field] if v not in current_vals]))
            set_clauses.append(f"{field} = ?")
            params.append(json.dumps(merged))

    for field in SCALAR_FIELDS:
        if field in updates and updates[field] is not None:
            set_clauses.append(f"{field} = ?")
            params.append(updates[field])

    if "notes" in updates and updates["notes"]:
        existing = current.get("notes") or ""
        new_entry = f"[{date.today().isoformat()}] {updates['notes']}"
        notes = f"{new_entry}\n{existing}".strip() if existing else new_entry
        set_clauses.append("notes = ?")
        params.append(notes)

    if set_clauses:
        set_clauses.append("updated_at = datetime('now')")
        sql = f"UPDATE profiles SET {', '.join(set_clauses)} WHERE user_id = ?"
        params.append(user_id)
        db.execute(sql, params)
        db.commit()

    return get_profile(user_id, db)


def get_wardrobe_summary(user_id: int, db) -> str:
    rows = db.execute(
        "SELECT name, category, color, brand FROM wardrobe WHERE user_id = ? ORDER BY category, name",
        (user_id,),
    ).fetchall()

    if not rows:
        return ""

    by_category: dict[str, list[str]] = {}
    for row in rows:
        cat = row["category"]
        parts = [row["name"]]
        if row["color"]:
            parts.append(f"({row['color']})")
        if row["brand"]:
            parts.append(f"by {row['brand']}")
        by_category.setdefault(cat, []).append(" ".join(parts))

    return "\n".join(
        f"{cat.capitalize()}: {', '.join(items)}"
        for cat, items in sorted(by_category.items())
    )
