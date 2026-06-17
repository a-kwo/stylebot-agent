# StyleBot Agent

An AI personal styling assistant. StyleBot holds a real conversation about what you want to
wear, learns your taste through a visual style quiz and ongoing feedback, and recommends
**real, purchasable products** pulled live from Google Shopping — while keeping track of your
wardrobe, building outfits, and getting smarter about your preferences over time.

Built on a multi-step **agentic loop** (FastAPI + Claude) with a Next.js/React frontend.

---

## What it does

- **Conversational styling agent** — a multi-step loop where Claude autonomously decides which
  of ~12 tools to call to answer a request (search products, read/update your profile, manage
  your wardrobe, build and critique outfits, analyze wardrobe gaps).
- **Real product search** — live, purchasable items via Google Shopping (SerpAPI), filtered by
  your budget and re-ranked against your profile and existing wardrobe.
- **Taste modeling** — a visual onboarding quiz scores you across four numeric style dimensions
  (energy, cultural reference, silhouette, color) to produce a coordinate-based *style vector*
  rather than a single category.
- **Evolving preferences** — the agent reflects on each conversation turn to extract implicit
  preferences, and a feedback-driven refinement system blends your original quiz vector with
  signals from what you like and dislike, so recommendations improve over time.
- **Wardrobe & outfits** — save items, assemble outfits, and get AI feedback on color harmony,
  occasion fit, and style coherence.
- **Persistent memory** — server-side conversation history with automatic summarization to stay
  within context limits.

## Architecture

### Backend (FastAPI + SQLite + Claude)
- `main.py` — app entry; wires routers, serves the built frontend, runs `init_db()` on startup
- `database.py` — SQLite schema and connection management
- `auth.py` — JWT (HS256) auth + bcrypt password hashing
- `agent/` — the agentic core
  - `loop.py` — agentic loop (load history → call Claude → run tools → iterate); sync + SSE streaming
  - `tools.py` / `tool_handlers.py` — tool schemas and their Python implementations
  - `system_prompt.py` — dynamic system prompt built from the user's profile + wardrobe
- `routers/` — `auth`, `chat`, `wardrobe`, `profile`, `quiz`, `outfits`, `image`
- `services/` — domain logic
  - `quiz_v2.py` — stage-based visual quiz with vector scoring
  - `style_translator.py` — turns a style vector into concrete brand/keyword/fit search guidance
  - `vector_refinement.py` — feedback-driven style-vector refinement
  - `product_ranker.py` — post-search re-ranking against profile, wardrobe, and feedback
  - `shopping.py` — Google Shopping search (SerpAPI) with per-user rate limiting
  - `vision_service.py` — Google Cloud Vision image validation + Unsplash fallback
  - `outfit_service.py`, `profile_service.py`, `image_storage.py`

### Frontend (`frontend/` — Next.js + React + TypeScript + Tailwind)
Static-exported and served by the FastAPI app. Pages for landing, login, onboarding, chat,
wardrobe, outfits, and profile, with streaming chat responses and product/quiz card rendering.

## Setup

```bash
# 1. Backend deps
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env        # fill in your keys (see below)

# 3. Build the frontend (output is served by the backend)
cd frontend && npm install && npm run build && cd ..

# 4. Run
uvicorn main:app --reload   # → http://localhost:8000
```

### Environment variables

| Key | Required | Purpose |
|-----|----------|---------|
| `ANTHROPIC_API_KEY` | yes | Claude API |
| `SERPAPI_KEY` | yes | Google Shopping product search |
| `SECRET_KEY` | yes | JWT signing (use a random 32+ char string) |
| `GOOGLE_VISION_API_KEY` | optional | Image validation for quiz/wardrobe images |
| `UNSPLASH_ACCESS_KEY` | optional | Fallback image search |
| `KIE_API_KEY` | optional | Image generation |

## Tech stack

FastAPI · SQLite · Claude (Anthropic API) · SerpAPI · Google Cloud Vision · Next.js · React ·
TypeScript · Tailwind CSS · JWT/bcrypt auth

## Tests

```bash
pytest
```

The codebase follows test-driven development — features and fixes are covered by tests in
`tests/`.
