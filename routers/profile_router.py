import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
from services.quiz_service import get_onboarding_questions
from services.profile_service import update_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])

quiz_router = APIRouter(prefix="/api/quiz", tags=["quiz"])


class OnboardRequest(BaseModel):
    gender: str
    age: int
    climate: str


class QuizAnswer(BaseModel):
    category: str
    choice: str
    style_tags: list[str] = []


class StyleQuizRequest(BaseModel):
    answers: list[QuizAnswer]

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
def quiz_onboarding():
    return get_onboarding_questions()


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
