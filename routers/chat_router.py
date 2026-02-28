import json

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from auth import get_current_user
from models import ChatRequest, ChatResponse, ResponseBlock
from agent.loop import run_agent_turn

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    blocks = run_agent_turn(user_id, req.message.strip(), db)
    return ChatResponse(blocks=[ResponseBlock(**b) for b in blocks])


@router.get("/conversations")
def get_conversations(user_id: int = Depends(get_current_user), db=Depends(get_db)):
    rows = db.execute(
        "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    ).fetchall()

    result = []
    for row in rows:
        try:
            content = json.loads(row["content"])
        except Exception:
            content = row["content"]
        result.append({"role": row["role"], "content": content})

    return result
