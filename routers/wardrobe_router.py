import json

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from auth import get_current_user
from models import WardrobeItem
from services.image_storage import download_and_store_image

router = APIRouter(prefix="/api/wardrobe", tags=["wardrobe"])

VALID_CATEGORIES = {"tops", "bottoms", "shoes", "outerwear", "accessories", "dresses"}


@router.get("")
def get_wardrobe(
    category: str = None,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
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
    return items


@router.post("", status_code=201)
async def add_wardrobe_item(
    item: WardrobeItem,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    if item.category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")

    cur = db.execute(
        """INSERT INTO wardrobe (user_id, name, category, color, brand, condition, tags, image_url, purchase_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            item.name,
            item.category,
            item.color,
            item.brand,
            item.condition,
            json.dumps(item.tags),
            item.image_url,
            item.purchase_url,
        ),
    )
    db.commit()
    item_id = cur.lastrowid

    # Attempt to download and store image locally (best-effort)
    if item.image_url:
        try:
            local_path = await download_and_store_image(item.image_url, item_id)
            if local_path:
                db.execute(
                    "UPDATE wardrobe SET local_image_path = ? WHERE id = ?",
                    (local_path, item_id),
                )
                db.commit()
        except Exception:
            pass  # image download is best-effort

    return {"id": item_id, "message": "Item added"}


@router.delete("/{item_id}", status_code=204)
def delete_wardrobe_item(
    item_id: int,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    result = db.execute(
        "DELETE FROM wardrobe WHERE id = ? AND user_id = ?", (item_id, user_id)
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, "Item not found")
