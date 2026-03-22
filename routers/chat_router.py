import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from database import get_db
from auth import get_current_user
from models import ChatRequest, ChatResponse, FeedbackRequest, ResponseBlock
from agent.loop import run_agent_turn, stream_agent_turn

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")

    blocks = run_agent_turn(user_id, req.message.strip(), db)
    return ChatResponse(blocks=[ResponseBlock(**b) for b in blocks])


@router.get("/chat/stream")
def chat_stream(
    message: str = Query(..., min_length=1),
    user_id: int = Depends(get_current_user),
):
    from database import get_connection

    def generate():
        import json as _json
        db = get_connection()
        try:
            for chunk in stream_agent_turn(user_id, message.strip(), db):
                yield chunk
        except Exception as e:
            yield f"event: error\ndata: {_json.dumps({'message': str(e)})}\n\n"
            yield f"event: done\ndata: {{}}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, user_id: int = Depends(get_current_user), db=Depends(get_db)):
    if req.feedback not in ("like", "dislike"):
        raise HTTPException(400, "Feedback must be 'like' or 'dislike'")
    db.execute(
        """INSERT INTO recommendation_feedback
           (user_id, product_title, feedback, price, category, seller, color, search_query, image_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, req.product_title, req.feedback,
         req.price, req.category, req.seller, req.color, req.search_query, req.image_url),
    )
    db.commit()
    return {"status": "ok"}


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
