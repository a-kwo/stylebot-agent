# CLAUDE.md — StyleBot Agent

AI-powered personal styling assistant with persistent user profiles, wardrobe tracking, and real product search via Google Shopping (SerpAPI). Built on FastAPI + SQLite + Claude with a multi-step agentic loop.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env                 # fill in ANTHROPIC_API_KEY, SERPAPI_KEY, SECRET_KEY (+ optional keys)
cd frontend && npm install && npm run build && cd ..   # build the static frontend the backend serves
uvicorn main:app --reload
# → http://localhost:8000
```

## Architecture

### Backend
- `main.py` — FastAPI app; wires routers, serves static files, calls `init_db()` on startup
- `database.py` — SQLite via `sqlite3`; `init_db()` creates tables, `get_db()` yields connections
- `auth.py` — JWT (HS256, 7-day TTL) + bcrypt passwords; `get_current_user()` FastAPI dependency
- `models.py` — Pydantic request/response schemas

### Routers (`routers/`)
- `auth_router.py` — `POST /auth/register`, `POST /auth/login`
- `chat_router.py` — `POST /chat` (protected), SSE streaming endpoint, `GET /conversations`
- `wardrobe_router.py` — `GET/POST /wardrobe`, `DELETE /wardrobe/{id}`
- `profile_router.py` — `GET /profile`; `quiz_router` for the visual style quiz
- `outfits_router.py` — outfit CRUD and suggestions
- `image_router.py` — wardrobe/quiz image upload and serving

### Agent (`agent/`)
- `loop.py` — Core agentic loop: loads history → calls Claude → executes tools → iterates (max 10 turns)
- `tools.py` — Tool JSON schemas passed to Claude API
- `tool_handlers.py` — Python functions that execute each tool; `dispatch_tool()` routes by name
- `system_prompt.py` — Builds dynamic system prompt from user's profile + wardrobe summary

### Services (`services/`)
- `profile_service.py` — Profile read/write; array fields union-merged, `notes` prepended with timestamp
- `shopping.py` — Google Shopping search via SerpAPI with per-user rate limiting
- `quiz_v2.py` — Stage-based visual style quiz with vector scoring
- `style_translator.py` — Maps a numeric style vector to brand/keyword/fit/material search guidance
- `vector_refinement.py` — Blends quiz vector with like/dislike feedback into a refined style vector
- `product_ranker.py` — Re-ranks search results against profile, wardrobe, and feedback
- `vision_service.py` — Google Cloud Vision image validation + Unsplash fallback
- `outfit_service.py`, `image_storage.py`, `quiz_service.py` — outfit logic, image storage, legacy quiz

### Frontend (`frontend/` — Next.js + React + TypeScript + Tailwind)
- Static-exported (`frontend/out/`, gitignored) and served by the FastAPI app
- Pages (`frontend/src/app/`): landing, login, onboarding, chat, wardrobe, outfits, profile, builder
- Chat uses SSE streaming; renders product and quiz cards inline
- Legacy vanilla-JS frontend remains under `static/` as a fallback (served if `frontend/out/` is absent)

## Development workflow

- **Test-driven development (TDD)**: All bug fixes and new features MUST follow this strict process:
  1. **Write tests first** — Write unit/integration tests that cover the expected behavior for the fix or feature.
  2. **Verify tests fail** — Run the tests and confirm they fail (red phase). If tests pass before any implementation, the tests are not testing the right thing — revise them.
  3. **Implement the change** — Write the minimum code needed to make the failing tests pass.
  4. **Verify tests pass** — Run the tests again and confirm they all pass (green phase).
  5. **Do not skip steps** — Never implement a fix or feature without first having a failing test that proves the need for the change.

## Key conventions

- **Model**: `claude-sonnet-4-6` (defined in `agent/loop.py`)
- **Database**: `stylebot.db` created in project root on first run
- **Auth**: JWT stored in `localStorage["stylebot_token"]`, sent as `Authorization: Bearer <token>`
- **Conversation history**: Server-side in `conversations` table. Client sends only new message.
- **Agent loop**: Supports both a synchronous endpoint and an SSE streaming endpoint (`stream_agent_turn`).
- **Array profile fields**: Union-merged on update — values are added, never removed.
- **Shopping rate limit**: 50 calls/user/hour in-memory guard (resets on server restart).
- **Product results**: Collected from all `search_products` tool calls in a turn, returned as a single `{"type": "products"}` block appended after text blocks.
