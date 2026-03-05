import json


def create_outfit(user_id: int, name: str, occasion: str, season: str,
                  notes: str, wardrobe_item_ids: list[int], db) -> dict:
    cur = db.execute(
        "INSERT INTO outfits (user_id, name, occasion, season, notes) VALUES (?, ?, ?, ?, ?)",
        (user_id, name, occasion, season, notes),
    )
    outfit_id = cur.lastrowid

    for order, wid in enumerate(wardrobe_item_ids):
        # Verify item belongs to user
        row = db.execute(
            "SELECT id FROM wardrobe WHERE id = ? AND user_id = ?", (wid, user_id)
        ).fetchone()
        if row:
            db.execute(
                "INSERT INTO outfit_items (outfit_id, wardrobe_id, layer_order) VALUES (?, ?, ?)",
                (outfit_id, wid, order),
            )
    db.commit()
    return get_outfit(outfit_id, user_id, db)


def get_outfit(outfit_id: int, user_id: int, db) -> dict | None:
    row = db.execute(
        "SELECT * FROM outfits WHERE id = ? AND user_id = ?", (outfit_id, user_id)
    ).fetchone()
    if not row:
        return None

    outfit = dict(row)
    items = db.execute(
        """SELECT oi.layer_order, w.id, w.name, w.category, w.color, w.brand, w.tags, w.image_url
           FROM outfit_items oi
           JOIN wardrobe w ON w.id = oi.wardrobe_id
           WHERE oi.outfit_id = ?
           ORDER BY oi.layer_order""",
        (outfit_id,),
    ).fetchall()

    outfit["items"] = []
    for item in items:
        d = dict(item)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except Exception:
            d["tags"] = []
        outfit["items"].append(d)

    return outfit


def get_outfits(user_id: int, db, occasion: str = None, season: str = None) -> list[dict]:
    query = "SELECT * FROM outfits WHERE user_id = ?"
    params: list = [user_id]

    if occasion:
        query += " AND occasion = ?"
        params.append(occasion)
    if season:
        query += " AND season = ?"
        params.append(season)

    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()

    outfits = []
    for row in rows:
        outfit = get_outfit(row["id"], user_id, db)
        if outfit:
            outfits.append(outfit)
    return outfits


def update_outfit(outfit_id: int, user_id: int, updates: dict, db) -> dict | None:
    row = db.execute(
        "SELECT * FROM outfits WHERE id = ? AND user_id = ?", (outfit_id, user_id)
    ).fetchone()
    if not row:
        return None

    allowed = {"name", "occasion", "season", "notes", "image_url"}
    sets = []
    vals = []
    for key in allowed:
        if key in updates:
            sets.append(f"{key} = ?")
            vals.append(updates[key])

    if sets:
        vals.append(outfit_id)
        db.execute(f"UPDATE outfits SET {', '.join(sets)} WHERE id = ?", vals)

    # Update items if provided
    if "wardrobe_item_ids" in updates:
        db.execute("DELETE FROM outfit_items WHERE outfit_id = ?", (outfit_id,))
        for order, wid in enumerate(updates["wardrobe_item_ids"]):
            exists = db.execute(
                "SELECT id FROM wardrobe WHERE id = ? AND user_id = ?", (wid, user_id)
            ).fetchone()
            if exists:
                db.execute(
                    "INSERT INTO outfit_items (outfit_id, wardrobe_id, layer_order) VALUES (?, ?, ?)",
                    (outfit_id, wid, order),
                )

    db.commit()
    return get_outfit(outfit_id, user_id, db)


def delete_outfit(outfit_id: int, user_id: int, db) -> bool:
    result = db.execute(
        "DELETE FROM outfits WHERE id = ? AND user_id = ?", (outfit_id, user_id)
    )
    db.commit()
    return result.rowcount > 0
