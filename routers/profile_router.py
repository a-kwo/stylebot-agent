import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
from services.quiz_service import get_quiz_tree, get_chat_question
from services.quiz_v2 import get_quiz_v2, compute_style_vector
from services.profile_service import update_profile, _migrate_weighted, WEIGHTED_FIELDS as _PROFILE_WEIGHTED_FIELDS

router = APIRouter(prefix="/api/profile", tags=["profile"])

quiz_router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class OnboardRequest(BaseModel):
    gender: str
    age: int
    climate: str = ''


class QuizAnswer(BaseModel):
    category: str
    choice: str
    style_tags: list[str] = []


class StyleQuizRequest(BaseModel):
    answers: list[QuizAnswer]


class StyleQuizV2Answer(BaseModel):
    question_id: str
    option_id: str
    vector_scores: dict[str, float] = {}


class StyleQuizV2Request(BaseModel):
    answers: list[StyleQuizV2Answer]
    selected_occasions: list[str] = []

@router.get("")
def get_profile(user_id: int = Depends(get_current_user), db=Depends(get_db)):
    row = db.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {}

    profile = dict(row)
    for field in _PROFILE_WEIGHTED_FIELDS:
        profile[field] = _migrate_weighted(profile.get(field) or "[]")

    return profile


@router.get("/onboarding-status")
def onboarding_status(user_id: int = Depends(get_current_user), db=Depends(get_db)):
    row = db.execute("SELECT onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    return {"onboarded": bool(row and row["onboarded"])}


@router.post("/onboard")
def onboard(body: OnboardRequest, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    db.execute(
        "UPDATE profiles SET gender = ?, age = ?, climate = ?, updated_at = datetime('now') WHERE user_id = ?",
        (body.gender, body.age, body.climate, user_id),
    )
    db.commit()
    return {"ok": True}


@quiz_router.get("/onboarding")
def quiz_onboarding(user_id: int = Depends(get_current_user), db=Depends(get_db)):
    row = db.execute("SELECT gender FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    gender = row["gender"] if row else None
    return get_quiz_tree(gender)


@router.post("/style-quiz")
def submit_style_quiz(body: StyleQuizRequest, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    answers = [a.model_dump() for a in body.answers]

    # Save quiz answers
    db.execute(
        "UPDATE profiles SET style_quiz = ?, onboarded = 1, updated_at = datetime('now') WHERE user_id = ?",
        (json.dumps(answers), user_id),
    )
    db.commit()

    # Merge all style_tags into style_adjectives
    all_tags = []
    for a in answers:
        all_tags.extend(a.get("style_tags", []))
    if all_tags:
        update_profile(user_id, {"style_adjectives": all_tags}, db)

    return {"ok": True}


@router.post("/quiz-answer")
def submit_quiz_answer(body: QuizAnswer, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    # Load existing quiz answers
    row = db.execute("SELECT style_quiz FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    existing = []
    if row and row["style_quiz"]:
        try:
            existing = json.loads(row["style_quiz"])
        except Exception:
            existing = []

    answer = body.model_dump()
    existing.append(answer)

    db.execute(
        "UPDATE profiles SET style_quiz = ?, updated_at = datetime('now') WHERE user_id = ?",
        (json.dumps(existing), user_id),
    )
    db.commit()

    # Merge style tags
    if body.style_tags:
        update_profile(user_id, {"style_adjectives": body.style_tags}, db)

    return {"ok": True}


# ── V2 Quiz endpoints ────────────────────────────────────────────────────────

@quiz_router.get("/v2")
def quiz_v2():
    """Return the full V2 quiz definition."""
    return get_quiz_v2()


@router.post("/style-quiz-v2")
def submit_style_quiz_v2(body: StyleQuizV2Request, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    """Submit V2 quiz answers, compute style vector, save to profile."""
    answers = [a.model_dump() for a in body.answers]

    # Compute style vector
    vector = compute_style_vector(answers, body.selected_occasions)

    # Save quiz answers + vector + occasions, mark onboarded
    db.execute(
        """UPDATE profiles
           SET style_quiz = ?, style_vector = ?, occasions = ?,
               onboarded = 1, updated_at = datetime('now')
           WHERE user_id = ?""",
        (json.dumps(answers), json.dumps(vector), json.dumps(body.selected_occasions), user_id),
    )
    db.commit()

    # Map vector to style adjectives for backward compatibility
    style_tags = _vector_to_tags(vector)
    if style_tags:
        update_profile(user_id, {"style_adjectives": style_tags}, db)

    return {"ok": True, "style_vector": vector}


def _vector_to_tags(vector: dict) -> list[str]:
    """Derive style adjective tags from a style vector for backward compat."""
    tags = []

    # Energy
    energy = vector.get("energy", 0.5)
    if energy < 0.3:
        tags.append("understated")
    elif energy > 0.7:
        tags.append("expressive")
        tags.append("bold")
    else:
        tags.append("balanced")

    # Cultural ref
    primary = vector.get("primary_cultural_ref", "")
    tag_map = {
        "sport_street": ["streetwear", "sporty"],
        "prep": ["classic", "refined"],
        "clean_basic": ["clean", "basic", "minimal"],
        "utility": ["workwear", "functional"],
        "vintage_street": ["vintage", "retro"],
    }
    tags.extend(tag_map.get(primary, []))

    # Silhouette
    sil = vector.get("silhouette", {})
    max_sil = max(
        ["structured", "relaxed", "oversized"],
        key=lambda k: sil.get(k, 0),
        default="relaxed",
    )
    tags.append(max_sil)

    # Color
    color = vector.get("color", {})
    if color.get("range", 0.5) < 0.3:
        tags.append("monochrome")
    elif color.get("range", 0.5) > 0.7:
        tags.append("colorful")
    if color.get("temperature", 0) > 0.5:
        tags.append("warm-tones")
    elif color.get("temperature", 0) < -0.3:
        tags.append("cool-tones")

    return tags
