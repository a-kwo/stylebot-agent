import json
import re
from collections import Counter
from datetime import date

from services.style_translator import translate_style_vector


def _build_feedback_patterns(feedback_rows: list[dict]) -> str:
    """Build aggregate feedback patterns from enriched feedback rows."""
    if not feedback_rows:
        return "No feedback yet."

    liked = [r for r in feedback_rows if r.get("feedback") == "like"]
    disliked = [r for r in feedback_rows if r.get("feedback") == "dislike"]

    parts = []

    # Liked summary
    if liked:
        liked_titles = [r["product_title"] for r in liked]
        line = f"Liked ({len(liked)}): {', '.join(liked_titles)}"

        # Price range
        prices = []
        for r in liked:
            p = r.get("price")
            if p:
                match = re.search(r"[\d]+(?:\.[\d]+)?", str(p))
                if match:
                    prices.append(float(match.group()))
        if prices:
            line += f" | Price range: ${min(prices):.0f}–${max(prices):.0f}"

        # Common sellers
        sellers = Counter(r.get("seller") for r in liked if r.get("seller"))
        if sellers:
            top_sellers = sellers.most_common(3)
            seller_str = ", ".join(f"{s} ({c})" for s, c in top_sellers)
            line += f" | Top sellers: {seller_str}"

        # Common colors
        colors = Counter(r.get("color") for r in liked if r.get("color"))
        if colors:
            top_colors = colors.most_common(3)
            color_str = ", ".join(f"{c} ({n})" for c, n in top_colors)
            line += f" | Colors: {color_str}"

        parts.append(line)

    # Disliked summary
    if disliked:
        disliked_titles = [r["product_title"] for r in disliked]
        line = f"Disliked ({len(disliked)}): {', '.join(disliked_titles)}"

        prices = []
        for r in disliked:
            p = r.get("price")
            if p:
                match = re.search(r"[\d]+(?:\.[\d]+)?", str(p))
                if match:
                    prices.append(float(match.group()))
        if prices:
            line += f" | Price range: ${min(prices):.0f}–${max(prices):.0f}"

        parts.append(line)

    total = len(liked) + len(disliked)
    parts.append(f"Total: {len(liked)} likes, {len(disliked)} dislikes. Analyze patterns in what the user gravitates toward.")

    return "\n".join(parts)


def _fmt_weighted(weights: dict) -> str:
    """Render weighted adjectives as a ranked list."""
    if not weights:
        return "none noted"
    if isinstance(weights, list):
        return ", ".join(weights) if weights else "none noted"

    def label(w):
        if w >= 5:
            return "strong"
        elif w >= 3:
            return "moderate"
        return "mild"

    sorted_items = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    return ", ".join(f"{name} ({label(w)})" for name, w in sorted_items)


def build_system_prompt(profile: dict, wardrobe_summary: str, user_id: int = None, db=None) -> str:
    def fmt_list(key: str) -> str:
        vals = profile.get(key, [])
        if isinstance(vals, str):
            try:
                vals = json.loads(vals)
            except Exception:
                vals = []
        return ", ".join(vals) if vals else "none noted"

    sizes = []
    if profile.get("size_tops"):
        sizes.append(f"tops {profile['size_tops']}")
    if profile.get("size_bottoms"):
        sizes.append(f"bottoms {profile['size_bottoms']}")
    if profile.get("size_shoes"):
        sizes.append(f"shoes {profile['size_shoes']}")
    size_str = ", ".join(sizes) if sizes else "unknown"

    budget_min = profile.get("budget_min", 0)
    budget_max = profile.get("budget_max", 500)
    notes = profile.get("notes") or "none"

    wardrobe_section = wardrobe_summary if wardrobe_summary else "No wardrobe items recorded yet."

    gender = profile.get("gender") or "unknown"
    age = profile.get("age") or "unknown"
    climate = profile.get("climate") or "unknown"

    # Parse style vector — prefer refined over raw quiz vector
    refined_raw = profile.get("refined_style_vector", "{}")
    if isinstance(refined_raw, str):
        try:
            refined_vector = json.loads(refined_raw)
        except Exception:
            refined_vector = {}
    else:
        refined_vector = refined_raw or {}

    style_vector_raw = profile.get("style_vector", "{}")
    if isinstance(style_vector_raw, str):
        try:
            style_vector = json.loads(style_vector_raw)
        except Exception:
            style_vector = {}
    else:
        style_vector = style_vector_raw or {}

    # Use refined vector if available
    if refined_vector and refined_vector.get("primary_cultural_ref", "none") != "none":
        style_vector = refined_vector

    vector_section = "Not completed yet."
    if style_vector and style_vector.get("primary_cultural_ref", "none") != "none":
        energy = style_vector.get("energy", 0.5)
        energy_label = "quiet" if energy < 0.3 else "expressive" if energy > 0.7 else "balanced"

        cr = style_vector.get("cultural_ref", {})
        primary_cr = style_vector.get("primary_cultural_ref", "unknown")
        cr_labels = {"sport_street": "Sport/Street", "prep": "Old-Money/Prep", "clean_basic": "Clean Basic", "utility": "Workwear", "vintage_street": "Vintage/Streetwear"}

        sil = style_vector.get("silhouette", {})
        color = style_vector.get("color", {})
        temp = color.get("temperature", 0)
        temp_label = "cool" if temp < -0.3 else "warm" if temp > 0.3 else "neutral"
        expr = color.get("expression", 0.5)
        expr_label = "accent only" if expr < 0.3 else "full commitment" if expr > 0.7 else "focal point"

        vector_section = f"""Energy: {energy:.2f} ({energy_label})
Primary cultural reference: {cr_labels.get(primary_cr, primary_cr)}
Cultural weights: {', '.join(f'{k}: {v:.2f}' for k, v in cr.items() if v > 0)}
Silhouette: structured={sil.get('structured', 0):.2f}, relaxed={sil.get('relaxed', 0):.2f}, oversized={sil.get('oversized', 0):.2f}
Color temperature: {temp:.2f} ({temp_label}), range: {color.get('range', 0.5):.2f}, expression: {expr:.2f} ({expr_label})"""

    # Build search guidance from style vector
    guidance_section = ""
    if style_vector and style_vector.get("primary_cultural_ref", "none") != "none":
        guidance = translate_style_vector(style_vector)
        if guidance.get("aesthetic_brief"):
            guidance_section = f"""
## Search Guidance (from style profile)

**Aesthetic Brief** — use this as your creative direction when forming search queries:
{guidance['aesthetic_brief']}

When calling search_products:
- Reason from this brief to form specific, descriptive queries (e.g., "heavyweight washed graphic tee 90s" not just "vintage tee")
- Vary item types, colors, and price points across different search calls in a session — don't search the same category or colorway twice unless explicitly asked
- Don't inject brand names into queries mechanically — let the aesthetic guide what you search for; only name a brand when it uniquely matches the brief

Reference context (for brand/keyword ideas, not for direct use in queries):
- Brands aligned with this style: {', '.join(guidance['suggested_brands'])}
- Materials: {', '.join(guidance['material_preferences'])}
- Fit: {guidance['fit_guidance']}
- Color: {guidance['color_guidance']}"""

    # Parse style quiz answers
    style_quiz_raw = profile.get("style_quiz", "[]")
    if isinstance(style_quiz_raw, str):
        try:
            style_quiz = json.loads(style_quiz_raw)
        except Exception:
            style_quiz = []
    else:
        style_quiz = style_quiz_raw if style_quiz_raw else []

    quiz_section = "None yet."
    if style_quiz:
        quiz_lines = []
        for a in style_quiz:
            if "category" in a:
                # V1 format
                quiz_lines.append(f"- {a['category']}: chose \"{a.get('choice', '?')}\" (tags: {', '.join(a.get('style_tags', []))})")
            elif "question_id" in a:
                # V2 format
                quiz_lines.append(f"- {a['question_id']}: chose \"{a.get('option_id', '?')}\"")
        quiz_section = "\n".join(quiz_lines) if quiz_lines else "None yet."

    asked_categories = [a["category"] for a in style_quiz if "category" in a] if style_quiz else []
    asked_str = ", ".join(asked_categories) if asked_categories else "none"

    # Build recommendation feedback section
    feedback_section = "No feedback yet."
    if user_id is not None and db is not None:
        try:
            feedback_rows = db.execute(
                """SELECT product_title, feedback, price, category, seller, color, search_query, image_url
                   FROM recommendation_feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 20""",
                (user_id,),
            ).fetchall()
        except Exception:
            # Fallback for DBs without enriched columns
            feedback_rows = db.execute(
                "SELECT product_title, feedback FROM recommendation_feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
                (user_id,),
            ).fetchall()
        if feedback_rows:
            feedback_section = _build_feedback_patterns(
                [dict(r) for r in feedback_rows]
            )

    return f"""You are StyleBot, a personal AI styling assistant. You help users build outfits, discover their personal style, and find real products to buy.

Today's date: {date.today().isoformat()}

## User's Taste Profile
- Gender: {gender}
- Age: {age}
- Climate: {climate}
- Style: {_fmt_weighted(profile.get('style_adjectives', {}))}
- Preferred colors: {_fmt_weighted(profile.get('preferred_colors', {}))}
- Avoided colors: {_fmt_weighted(profile.get('avoided_colors', {}))}
- Preferred brands: {_fmt_weighted(profile.get('preferred_brands', {}))}
- Avoided brands: {_fmt_weighted(profile.get('avoided_brands', {}))}
- Sizes: {size_str}
- Budget: ${budget_min}–${budget_max} USD
- Occasions: {_fmt_weighted(profile.get('occasions', {}))}
- Fit preferences: {_fmt_weighted(profile.get('fit_preferences', {}))}
- Notes: {notes}

## Style Vector (from onboarding quiz)
{vector_section}
{guidance_section}

## Style Quiz Answers
{quiz_section}
Categories already asked: {asked_str}

## User's Wardrobe
{wardrobe_section}

## Recommendation Feedback
{feedback_section}

## Your Behavior
- Be warm, specific, and actionable. Give concrete outfit suggestions, not vague advice.
- **Name specific wardrobe items** in your suggestions. Say "Your Navy Slim Chinos would pair great with..." not "Try navy pants." Reference items the user actually owns.
- **Explain why** suggestions match the user's style or preferences. Reference their style adjectives, color preferences, or feedback patterns. Example: "Since you lean minimalist and love earth tones, this linen shirt fits right in."
- **Analyze feedback patterns.** Look at liked and disliked items to identify what the user gravitates toward. Example: "You've liked 3 structured blazers and disliked graphic tees — you clearly gravitate toward clean, tailored pieces."
- **Spot wardrobe gaps proactively.** If you notice missing categories or lack of variety, mention it. Example: "You've got 5 tops but no outerwear — want me to find a jacket?" Use `analyze_wardrobe` when the user asks "what should I buy?" or when a gap is obvious.
- **Suggest wardrobe combinations unprompted.** When items in the wardrobe pair well together, point it out without being asked.
- **Always pass budget** as `min_price`/`max_price` on `search_products` calls. Use the user's profile budget unless they specify otherwise.
- **Build profile-aware search queries.** Include gender, preferred brands, fit preferences, and size when calling `search_products`.
- When you learn something new about the user's preferences, sizes, or style, call `update_profile` to save it. Only call it once per turn and only when something genuinely new was shared.
- When the user mentions owning something new, offer to add it to their wardrobe via `add_to_wardrobe`. **Always pass `image_url`** (and `purchase_url`) from the product references when adding items from search results — without it the wardrobe shows a blank placeholder.
- Consult `get_wardrobe` when making outfit suggestions to build on what the user already owns.
- Use `create_outfit` to save outfit combinations the user likes. Offer to save outfits when you suggest combinations.
- Use `get_outfits` to check existing saved outfits before suggesting new ones — avoid duplicates.
- Use `suggest_outfit` when the user asks "what should I wear?" — it returns their wardrobe and existing outfits so you can reason about combinations.
- Use `analyze_wardrobe` to get a breakdown of the user's wardrobe by category, spot missing categories, and assess color variety. Call this when the user asks what to buy next or when you want to give gap-aware advice.
- Use `get_outfit_feedback` when the user asks for feedback on an outfit via the builder or when they want you to evaluate a combination of items. Give specific praise and one concrete improvement suggestion.
- Keep responses concise but helpful. Lead with the most useful advice.
- **CRITICAL: After calling `search_products`, NEVER list or describe individual products.** No tables, no numbered lists, no headings per product, no per-item descriptions. The app renders interactive product cards automatically — the user will see images, prices, sellers, and links without you repeating any of it. Your ONLY job is to write 1-2 short sentences of context. Let the product images do the talking. Never mention specific product names, prices, or sellers in your text.
- Keep your text responses concise when showing products. The visual content (product cards, images) should be the focus, not your text.
- Periodically call `ask_style_question` to learn more about the user's visual taste. Pick categories you haven't asked about yet. Do this roughly every 3-5 messages when you feel you need more info about their preferences. Available categories: sneakers, formal_wear, patterns, accessories, dresses, activewear.
- Never expose tool calls, internal reasoning, or JSON to the user."""
