import json
import os
from typing import Any

import anthropic

from agent.tools import TOOLS
from agent.tool_handlers import dispatch_tool
from agent.system_prompt import build_system_prompt
from services.profile_service import get_profile, get_wardrobe_summary

MAX_ITERATIONS = 10
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def _load_history(user_id: int, db) -> list[dict]:
    rows = db.execute(
        "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id ASC",
        (user_id,),
    ).fetchall()

    messages = []
    for row in rows:
        try:
            content = json.loads(row["content"])
        except Exception:
            content = row["content"]
        messages.append({"role": row["role"], "content": content})
    return messages


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


def run_agent_turn(user_id: int, user_message: str, db) -> list[dict]:
    # Build system prompt from current profile + wardrobe
    profile = get_profile(user_id, db)
    wardrobe_summary = get_wardrobe_summary(user_id, db)
    system_prompt = build_system_prompt(profile, wardrobe_summary)

    # Load full conversation history
    messages = _load_history(user_id, db)

    # Append and persist the new user message
    messages.append({"role": "user", "content": user_message})
    _persist(user_id, "user", user_message, db)

    # Collect product results across all tool calls in this turn
    product_results: list[dict] = []

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

            blocks = _parse_final_blocks(response.content)
            if product_results:
                blocks.append({"type": "products", "items": product_results})
            return blocks

        elif response.stop_reason == "tool_use":
            assistant_content = _to_serializable(response.content)
            tool_results = []

            for block in response.content:
                if not (hasattr(block, "type") and block.type == "tool_use"):
                    continue

                result_str = dispatch_tool(block.name, block.input, user_id, db)

                # Collect eBay products for the final response block
                try:
                    result_data = json.loads(result_str)
                    if block.name == "search_products" and "products" in result_data:
                        product_results.extend(result_data["products"])
                except Exception:
                    pass

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            _persist(user_id, "assistant", assistant_content, db)
            _persist(user_id, "user", tool_results, db)

        else:
            break

    return [{"type": "text", "content": "I ran into an issue processing your request. Please try again."}]
