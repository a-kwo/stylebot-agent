import json
import os
from typing import Any, Generator

import anthropic

from agent.tools import TOOLS
from agent.tool_handlers import dispatch_tool, set_recent_search_products
from agent.system_prompt import build_system_prompt
from services.profile_service import get_profile, update_profile, get_wardrobe_summary
from services.vector_refinement import maybe_refine_vector

MAX_ITERATIONS = 10
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


def _build_search_summary(products: list[dict]) -> str:
    """Build the tool result Claude sees after search_products.

    Includes a compact product reference list so Claude can pass image_url
    and purchase_url when calling add_to_wardrobe.
    """
    count = len(products)
    refs = [
        {"title": p.get("title", ""), "image_url": p.get("image_url", ""), "item_url": p.get("item_url", "")}
        for p in products
    ]
    return json.dumps({
        "status": (
            f"Found {count} products. They are being displayed to the user as interactive cards "
            f"with images, prices, and buy links. Do NOT list or describe individual products. "
            f"Just write 1-2 sentences of context. "
            f"IMPORTANT: If the user asks to add any of these to their wardrobe, you MUST pass "
            f"the image_url and item_url (as purchase_url) from the product references below."
        ),
        "products": refs,
    })

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


SUMMARIZE_THRESHOLD = 30


def _load_history(user_id: int, db) -> list[dict]:
    summary_row = db.execute(
        "SELECT summary, messages_up_to FROM conversation_summaries WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    messages = []
    if summary_row:
        messages.append({
            "role": "user",
            "content": "[Previous conversation summary follows]",
        })
        messages.append({
            "role": "assistant",
            "content": f"I remember our previous conversations. Here's what I know:\n\n{summary_row['summary']}",
        })
        rows = db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? AND id > ? ORDER BY id ASC",
            (user_id, summary_row["messages_up_to"]),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()

    for row in rows:
        # Skip meta records (products/quizzes) — they're for the frontend only
        if row["role"] == "meta":
            continue
        try:
            content = json.loads(row["content"])
        except Exception:
            content = row["content"]

        # Sanitize old tool_result content: strip product data so Claude
        # doesn't see and mimic verbose product listings from history
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    try:
                        inner = json.loads(block.get("content", "{}"))
                        if isinstance(inner, dict) and "products" in inner:
                            count = len(inner["products"])
                            block["content"] = json.dumps({
                                "status": f"Found {count} products. They were displayed to the user as interactive cards.",
                            })
                    except Exception:
                        pass

        messages.append({"role": row["role"], "content": content})
    return messages


def _maybe_summarize(user_id: int, db):
    try:
        summary_row = db.execute(
            "SELECT summary, messages_up_to FROM conversation_summaries WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

        cutoff_id = summary_row["messages_up_to"] if summary_row else 0
        previous_summary = summary_row["summary"] if summary_row else ""

        count_row = db.execute(
            "SELECT COUNT(*) as cnt FROM conversations WHERE user_id = ? AND id > ?",
            (user_id, cutoff_id),
        ).fetchone()

        if count_row["cnt"] < SUMMARIZE_THRESHOLD:
            return

        rows = db.execute(
            "SELECT id, role, content FROM conversations WHERE user_id = ? AND id > ? ORDER BY id ASC",
            (user_id, cutoff_id),
        ).fetchall()

        max_id = rows[-1]["id"]

        msg_lines = []
        for row in rows:
            try:
                content = json.loads(row["content"])
                if isinstance(content, list):
                    text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                    text = " ".join(text_parts).strip()
                else:
                    text = str(content)
            except Exception:
                text = row["content"]
            if text:
                msg_lines.append(f"{row['role'].upper()}: {text[:500]}")

        conversation_text = "\n".join(msg_lines)

        prompt = f"""Produce a concise summary of this conversation that captures:
1. Key style preferences discovered
2. Products discussed (liked/disliked)
3. Important context about the user's lifestyle, events, or needs
4. Any decisions made

{"Previous summary to incorporate:\n" + previous_summary if previous_summary else ""}

New messages to summarize:
{conversation_text}

Write a clear, paragraph-form summary (max 300 words). Focus on information useful for future styling conversations."""

        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        summary = response.content[0].text.strip()
        db.execute(
            "INSERT INTO conversation_summaries (user_id, summary, messages_up_to) VALUES (?, ?, ?)",
            (user_id, summary, max_id),
        )
        db.commit()
    except Exception:
        pass


def _persist(user_id: int, role: str, content: Any, db):
    db.execute(
        "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, json.dumps(content)),
    )
    db.commit()


def _to_serializable(content: list) -> list:
    result = []
    for block in content:
        if hasattr(block, "type"):
            if block.type == "text":
                result.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                result.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
    return result


def _parse_final_blocks(content: list) -> list[dict]:
    blocks = []
    for block in content:
        if hasattr(block, "type") and block.type == "text" and block.text.strip():
            blocks.append({"type": "text", "content": block.text})
        elif isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text", "").strip()
            if text:
                blocks.append({"type": "text", "content": text})
    return blocks


REFLECTION_PROMPT = """Analyze this conversation turn and extract any implicit style preferences or profile updates the user revealed — things they didn't state as explicit requests but that reveal taste, lifestyle, or preferences.

User message: {user_message}
Assistant response: {assistant_response}

Respond with JSON only (no markdown fencing):
{{
  "profile_updates": {{
    "style_adjectives": [],
    "preferred_colors": [],
    "avoided_colors": [],
    "preferred_brands": [],
    "avoided_brands": [],
    "occasions": [],
    "fit_preferences": [],
    "notes": ""
  }},
  "has_updates": false,
  "behavioral_signals": {{
    "price_reaction": null,
    "category_interest": [],
    "engagement_level": null
  }}
}}

Rules:
- Only include fields where you genuinely detected something new. Leave arrays empty and notes as "" if nothing was found.
- Set has_updates to true only if at least one field has content.
- For notes, write a brief observation (prefix not needed, it will be added automatically).
- Do NOT repeat things the agent already explicitly saved via update_profile.
- Be conservative — only extract clear signals, not guesses.

Behavioral signals (detect from tone and context, not explicit statements):
- price_reaction: null if unclear. "budget_conscious" if the user balks at prices, asks for cheaper options, or emphasizes deals. "comfortable" if they accept prices without concern. "willing_to_splurge" if they actively seek premium/luxury items.
- category_interest: list of clothing categories (e.g. "outerwear", "sneakers", "blazers") the user showed genuine interest in this turn. Empty if none.
- engagement_level: null if unclear. "high" if the user is enthusiastic, asks follow-up questions, or explores options eagerly. "low" if responses are short, disengaged, or dismissive. Do NOT set "medium" — leave null instead."""


def _reflect_on_turn(user_id: int, user_message: str, assistant_text: str, db):
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": REFLECTION_PROMPT.format(
                    user_message=user_message,
                    assistant_response=assistant_text,
                ),
            }],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)

        # Process standard profile updates
        if data.get("has_updates"):
            updates = data.get("profile_updates", {})
            if updates.get("notes"):
                updates["notes"] = f"[reflection] {updates['notes']}"
            updates = {k: v for k, v in updates.items() if v}
            if updates:
                update_profile(user_id, updates, db)

        # Process behavioral signals (backward compatible — missing key is fine)
        behavioral = data.get("behavioral_signals")
        if behavioral:
            notes_parts = []

            price_reaction = behavioral.get("price_reaction")
            if price_reaction:
                notes_parts.append(f"[behavioral] Price sensitivity: {price_reaction}")

            category_interest = behavioral.get("category_interest", [])
            if category_interest:
                notes_parts.append(f"[behavioral] Showed interest in: {', '.join(category_interest)}")

            engagement = behavioral.get("engagement_level")
            if engagement and engagement != "medium":
                notes_parts.append(f"[behavioral] Engagement level: {engagement}")

            for note in notes_parts:
                update_profile(user_id, {"notes": note}, db)
    except Exception:
        pass


# ── Original synchronous endpoint (kept for backward compatibility) ──

def run_agent_turn(user_id: int, user_message: str, db) -> list[dict]:
    profile = get_profile(user_id, db)
    wardrobe_summary = get_wardrobe_summary(user_id, db)
    system_prompt = build_system_prompt(profile, wardrobe_summary, user_id, db)

    messages = _load_history(user_id, db)
    messages.append({"role": "user", "content": user_message})
    _persist(user_id, "user", user_message, db)

    product_results: list[dict] = []
    quiz_results: list[dict] = []

    for _ in range(MAX_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            serialized = _to_serializable(response.content)
            _persist(user_id, "assistant", serialized, db)

            # Persist products/quizzes separately so they don't pollute
            # Claude's message history but are recoverable by the frontend
            if product_results or quiz_results:
                meta: list[dict] = []
                if product_results:
                    meta.append({"type": "products", "products": product_results})
                for quiz in quiz_results:
                    meta.append({"type": "quiz", "quiz": quiz})
                _persist(user_id, "meta", meta, db)

            blocks = _parse_final_blocks(response.content)
            if product_results:
                blocks.append({"type": "products", "items": product_results})
            for quiz in quiz_results:
                blocks.append({"type": "quiz", "quiz": quiz})

            assistant_text = " ".join(
                b.text for b in response.content
                if hasattr(b, "type") and b.type == "text"
            )
            _reflect_on_turn(user_id, user_message, assistant_text, db)
            maybe_refine_vector(user_id, db)
            _maybe_summarize(user_id, db)

            return blocks

        elif response.stop_reason == "tool_use":
            assistant_content = _to_serializable(response.content)
            tool_results = []

            for block in response.content:
                if not (hasattr(block, "type") and block.type == "tool_use"):
                    continue

                result_str = dispatch_tool(block.name, block.input, user_id, db)

                # What Claude sees in the tool result
                claude_result = result_str

                try:
                    result_data = json.loads(result_str)
                    if block.name == "search_products" and "products" in result_data:
                        product_results.extend(result_data["products"])
                        set_recent_search_products(result_data["products"])
                        claude_result = _build_search_summary(result_data["products"])
                    elif block.name == "ask_style_question" and "quiz" in result_data:
                        quiz_results.append(result_data["quiz"])
                except Exception:
                    pass

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": claude_result,
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            _persist(user_id, "assistant", assistant_content, db)
            _persist(user_id, "user", tool_results, db)

        else:
            break

    return [{"type": "text", "content": "I ran into an issue processing your request. Please try again."}]


# ── SSE streaming endpoint ──────────────────────────────────────

def stream_agent_turn(user_id: int, user_message: str, db) -> Generator[str, None, None]:
    """Yields SSE-formatted events: token, tool_status, products, quiz, done."""

    def sse(event: str, data: Any) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    profile = get_profile(user_id, db)
    wardrobe_summary = get_wardrobe_summary(user_id, db)
    system_prompt = build_system_prompt(profile, wardrobe_summary, user_id, db)

    messages = _load_history(user_id, db)
    messages.append({"role": "user", "content": user_message})
    _persist(user_id, "user", user_message, db)

    product_results: list[dict] = []
    quiz_results: list[dict] = []
    full_assistant_text = ""
    has_streamed_text = False

    for _ in range(MAX_ITERATIONS):
        # Check if this iteration might be a tool-use round or final text
        # We'll stream the response and handle both cases
        try:
            stream_ctx = client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )
        except Exception as e:
            yield sse("error", {"message": f"Failed to connect to AI: {e}"})
            yield sse("done", {})
            return

        try:
          with stream_ctx as stream:
            collected_content = []
            current_text = ""

            for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "text":
                        # Add separator between text from different iterations
                        if has_streamed_text:
                            yield sse("token", {"text": "\n\n"})
                        current_text = ""
                    elif event.content_block.type == "tool_use":
                        yield sse("tool_status", {
                            "tool": event.content_block.name,
                            "status": "calling",
                        })
                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        current_text += event.delta.text
                        has_streamed_text = True
                        yield sse("token", {"text": event.delta.text})

            # Get the final message
            response = stream.get_final_message()
        except Exception as e:
            yield sse("error", {"message": f"AI error: {e}"})
            yield sse("done", {})
            return

        if response.stop_reason == "end_turn":
            serialized = _to_serializable(response.content)
            _persist(user_id, "assistant", serialized, db)

            if product_results or quiz_results:
                meta: list[dict] = []
                if product_results:
                    meta.append({"type": "products", "products": product_results})
                for quiz in quiz_results:
                    meta.append({"type": "quiz", "quiz": quiz})
                _persist(user_id, "meta", meta, db)

            # Send any collected products/quizzes
            if product_results:
                yield sse("products", {"items": product_results})
            for quiz in quiz_results:
                yield sse("quiz", quiz)

            yield sse("done", {})

            # Post-turn work (non-blocking from client perspective)
            assistant_text = " ".join(
                b.text for b in response.content
                if hasattr(b, "type") and b.type == "text"
            )
            _reflect_on_turn(user_id, user_message, assistant_text, db)
            maybe_refine_vector(user_id, db)
            _maybe_summarize(user_id, db)
            return

        elif response.stop_reason == "tool_use":
            assistant_content = _to_serializable(response.content)
            tool_results = []

            for block in response.content:
                if not (hasattr(block, "type") and block.type == "tool_use"):
                    continue

                yield sse("tool_status", {
                    "tool": block.name,
                    "status": "executing",
                })

                result_str = dispatch_tool(block.name, block.input, user_id, db)

                # What Claude sees in the tool result
                claude_result = result_str

                try:
                    result_data = json.loads(result_str)
                    if block.name == "search_products" and "products" in result_data:
                        product_results.extend(result_data["products"])
                        set_recent_search_products(result_data["products"])
                        claude_result = _build_search_summary(result_data["products"])
                    elif block.name == "ask_style_question" and "quiz" in result_data:
                        quiz_results.append(result_data["quiz"])
                except Exception:
                    pass

                yield sse("tool_status", {
                    "tool": block.name,
                    "status": "done",
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": claude_result,
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            _persist(user_id, "assistant", assistant_content, db)
            _persist(user_id, "user", tool_results, db)

        else:
            break

    yield sse("error", {"message": "I ran into an issue processing your request. Please try again."})
    yield sse("done", {})
