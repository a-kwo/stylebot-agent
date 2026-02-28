import json

from fastapi import APIRouter, Depends

from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

ARRAY_FIELDS = [
    "style_adjectives", "preferred_colors", "avoided_colors",
    "preferred_brands", "avoided_brands", "occasions", "fit_preferences",
]


@router.get("")
def get_profile(user_id: int = Depends(get_current_user), db=Depends(get_db)):
    row = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {}

    profile = dict(row)
    for field in ARRAY_FIELDS:
        try:
            profile[field] = json.loads(profile.get(field) or "[]")
        except Exception:
            profile[field] = []

    return profile
