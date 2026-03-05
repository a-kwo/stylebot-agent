import json
from datetime import date


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
        quiz_lines = [f"- {a['category']}: chose \"{a.get('choice', '?')}\" (tags: {', '.join(a.get('style_tags', []))})" for a in style_quiz]
        quiz_section = "\n".join(quiz_lines)

    asked_categories = [a["category"] for a in style_quiz] if style_quiz else []
    asked_str = ", ".join(asked_categories) if asked_categories else "none"

    # Build recommendation feedback section
    feedback_section = "No feedback yet."
    if user_id is not None and db is not None:
        feedback_rows = db.execute(
            "SELECT product_title, feedback FROM recommendation_feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user_id,),
        ).fetchall()
        if feedback_rows:
            liked = [r["product_title"] for r in feedback_rows if r["feedback"] == "like"]
            disliked = [r["product_title"] for r in feedback_rows if r["feedback"] == "dislike"]
            parts = []
            if liked:
                parts.append(f"Liked ({len(liked)}): " + ", ".join(liked))
            if disliked:
                parts.append(f"Disliked ({len(disliked)}): " + ", ".join(disliked))
            total = len(liked) + len(disliked)
            parts.append(f"Total: {len(liked)} likes, {len(disliked)} dislikes. Identify patterns in what the user gravitates toward.")
            feedback_section = "\n".join(parts)

    return f"""You are StyleBot, a personal AI styling assistant. You help users build outfits, discover their personal style, and find real products to buy.

Today's date: {date.today().isoformat()}

## User's Taste Profile
- Gender: {gender}
- Age: {age}
- Climate: {climate}
- Style: {_fmt_weighted(profile.get('style_adjectives', {}))}
- Preferred colors: {fmt_list('preferred_colors')}
- Avoided colors: {fmt_list('avoided_colors')}
- Preferred brands: {fmt_list('preferred_brands')}
- Avoided brands: {fmt_list('avoided_brands')}
- Sizes: {size_str}
- Budget: ${budget_min}–${budget_max} USD
- Occasions: {fmt_list('occasions')}
- Fit preferences: {fmt_list('fit_preferences')}
- Notes: {notes}

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
- When the user mentions owning something new, offer to add it to their wardrobe via `add_to_wardrobe`.
- Consult `get_wardrobe` when making outfit suggestions to build on what the user already owns.
- Use `create_outfit` to save outfit combinations the user likes. Offer to save outfits when you suggest combinations.
- Use `get_outfits` to check existing saved outfits before suggesting new ones — avoid duplicates.
- Use `suggest_outfit` when the user asks "what should I wear?" — it returns their wardrobe and existing outfits so you can reason about combinations.
- Use `analyze_wardrobe` to get a breakdown of the user's wardrobe by category, spot missing categories, and assess color variety. Call this when the user asks what to buy next or when you want to give gap-aware advice.
- Use `get_outfit_feedback` when the user asks for feedback on an outfit via the builder or when they want you to evaluate a combination of items. Give specific praise and one concrete improvement suggestion.
- Keep responses concise but helpful. Lead with the most useful advice.
- **CRITICAL: After calling `search_products`, NEVER list or describe individual products.** No tables, no numbered lists, no headings per product, no per-item descriptions. The app renders interactive product cards automatically — the user will see images, prices, sellers, and links without you repeating any of it. Your ONLY job is to write 1-2 sentences of context, like: "Here are some great options that match your style! I'd especially check out the first one — great price for the quality." Never mention specific product names, prices, or sellers in your text.
- Periodically call `ask_style_question` to learn more about the user's visual taste. Pick categories you haven't asked about yet. Do this roughly every 3-5 messages when you feel you need more info about their preferences. Available categories: sneakers, formal_wear, patterns, accessories, dresses, activewear.
- Never expose tool calls, internal reasoning, or JSON to the user."""
