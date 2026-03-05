from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
from services.outfit_service import (
    create_outfit, get_outfit, get_outfits, update_outfit, delete_outfit,
)

router = APIRouter(prefix="/api/outfits", tags=["outfits"])


class OutfitCreateRequest(BaseModel):
    name: str
    occasion: str | None = None
    season: str | None = None
    notes: str = ""
    wardrobe_item_ids: list[int] = []


class OutfitUpdateRequest(BaseModel):
    name: str | None = None
    occasion: str | None = None
    season: str | None = None
    notes: str | None = None
    image_url: str | None = None
    wardrobe_item_ids: list[int] | None = None


@router.get("")
def list_outfits(
    occasion: str = None,
    season: str = None,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    return get_outfits(user_id, db, occasion=occasion, season=season)


@router.get("/{outfit_id}")
def read_outfit(
    outfit_id: int,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    outfit = get_outfit(outfit_id, user_id, db)
    if not outfit:
        raise HTTPException(404, "Outfit not found")
    return outfit


@router.post("", status_code=201)
def create(
    req: OutfitCreateRequest,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    if not req.name.strip():
        raise HTTPException(400, "Name is required")
    return create_outfit(
        user_id, req.name.strip(), req.occasion, req.season,
        req.notes, req.wardrobe_item_ids, db,
    )


@router.put("/{outfit_id}")
def update(
    outfit_id: int,
    req: OutfitUpdateRequest,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    updates = req.model_dump(exclude_none=True)
    result = update_outfit(outfit_id, user_id, updates, db)
    if not result:
        raise HTTPException(404, "Outfit not found")
    return result


@router.delete("/{outfit_id}", status_code=204)
def delete(
    outfit_id: int,
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    if not delete_outfit(outfit_id, user_id, db):
        raise HTTPException(404, "Outfit not found")
