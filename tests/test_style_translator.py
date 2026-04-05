"""Tests for the style vector → search guidance translator."""

import pytest


# ── Helper: build a style vector with defaults ─────────────────────────────

def _make_vector(
    energy=0.5,
    sport_street=0.0,
    prep=0.0,
    clean_basic=0.0,
    utility=0.0,
    vintage_street=0.0,
    primary_cultural_ref="none",
    structured=0.0,
    relaxed=0.0,
    oversized=0.0,
    color_temp=0.0,
    color_range=0.5,
    color_expression=0.5,
    occasions=None,
):
    return {
        "energy": energy,
        "cultural_ref": {
            "sport_street": sport_street,
            "prep": prep,
            "clean_basic": clean_basic,
            "utility": utility,
            "vintage_street": vintage_street,
        },
        "silhouette": {
            "structured": structured,
            "relaxed": relaxed,
            "oversized": oversized,
        },
        "color": {
            "temperature": color_temp,
            "range": color_range,
            "expression": color_expression,
        },
        "primary_cultural_ref": primary_cultural_ref,
        "occasions": occasions or [],
    }


# ── Tests for translate_style_vector ────────────────────────────────────────

class TestTranslateStyleVector:
    """translate_style_vector maps numeric vectors to concrete search guidance."""

    def test_prep_dominant_returns_prep_brands(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(prep=1.0, primary_cultural_ref="prep")
        result = translate_style_vector(vector)

        assert isinstance(result["suggested_brands"], list)
        assert len(result["suggested_brands"]) > 0
        # Should contain classic/prep brands
        brands_lower = [b.lower() for b in result["suggested_brands"]]
        assert any(
            kw in " ".join(brands_lower)
            for kw in ["ralph lauren", "brooks brothers", "j.crew", "polo"]
        ), f"Expected prep brands, got {result['suggested_brands']}"

    def test_prep_dominant_returns_tailored_keywords(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(prep=1.0, primary_cultural_ref="prep")
        result = translate_style_vector(vector)

        keywords_lower = [kw.lower() for kw in result["search_keywords"]]
        assert any(
            "tailor" in kw or "classic" in kw or "prep" in kw
            for kw in keywords_lower
        ), f"Expected tailored/classic keywords, got {result['search_keywords']}"

    def test_sport_street_dominant_returns_street_brands(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(sport_street=1.0, primary_cultural_ref="sport_street")
        result = translate_style_vector(vector)

        brands_lower = [b.lower() for b in result["suggested_brands"]]
        assert any(
            kw in " ".join(brands_lower)
            for kw in ["nike", "jordan", "stussy", "new balance"]
        ), f"Expected street brands, got {result['suggested_brands']}"

    def test_utility_dominant_returns_workwear_brands(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(utility=1.0, primary_cultural_ref="utility")
        result = translate_style_vector(vector)

        brands_lower = [b.lower() for b in result["suggested_brands"]]
        assert any(
            kw in " ".join(brands_lower)
            for kw in ["carhartt", "filson", "red wing", "dickies"]
        ), f"Expected workwear brands, got {result['suggested_brands']}"

    def test_clean_basic_dominant_returns_minimal_brands(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(clean_basic=1.0, primary_cultural_ref="clean_basic")
        result = translate_style_vector(vector)

        brands_lower = [b.lower() for b in result["suggested_brands"]]
        assert any(
            kw in " ".join(brands_lower)
            for kw in ["uniqlo", "cos", "muji", "everlane"]
        ), f"Expected clean basic brands, got {result['suggested_brands']}"

    def test_mixed_weights_blends_both_cultures(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            sport_street=0.6, prep=0.4, primary_cultural_ref="sport_street"
        )
        result = translate_style_vector(vector)

        brands_lower = [b.lower() for b in result["suggested_brands"]]
        brands_str = " ".join(brands_lower)
        # Should have contributions from both cultures
        has_street = any(kw in brands_str for kw in ["nike", "jordan", "stussy", "new balance"])
        has_prep = any(kw in brands_str for kw in ["ralph lauren", "brooks brothers", "j.crew", "polo"])
        assert has_street, "Mixed weights should include street brands"
        assert has_prep, "Mixed weights should include prep brands (weight 0.4 > threshold)"

    def test_low_weight_culture_excluded(self):
        """Cultural refs below 0.2 threshold should not contribute."""
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            sport_street=0.9, utility=0.1, primary_cultural_ref="sport_street"
        )
        result = translate_style_vector(vector)

        # Utility-only brands (not shared with sport_street) should NOT appear
        brands_lower = [b.lower() for b in result["suggested_brands"]]
        brands_str = " ".join(brands_lower)
        assert not any(
            kw in brands_str for kw in ["filson", "red wing", "dickies", "stan ray"]
        ), "Low-weight culture (0.1) should not contribute its unique brands"

    def test_empty_vector_returns_safe_defaults(self):
        from services.style_translator import translate_style_vector

        result = translate_style_vector({})

        assert isinstance(result["suggested_brands"], list)
        assert isinstance(result["search_keywords"], list)
        assert isinstance(result["material_preferences"], list)
        assert isinstance(result["avoid_keywords"], list)
        assert isinstance(result["fit_guidance"], str)
        assert isinstance(result["color_guidance"], str)
        assert isinstance(result["summary"], str)

    def test_none_vector_returns_safe_defaults(self):
        from services.style_translator import translate_style_vector

        result = translate_style_vector(None)

        assert isinstance(result["suggested_brands"], list)
        assert isinstance(result["summary"], str)

    def test_result_has_all_required_keys(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(prep=1.0, primary_cultural_ref="prep")
        result = translate_style_vector(vector)

        required_keys = [
            "search_keywords",
            "suggested_brands",
            "material_preferences",
            "avoid_keywords",
            "fit_guidance",
            "color_guidance",
            "summary",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_structured_silhouette_gives_tailored_fit(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            structured=1.0, prep=1.0, primary_cultural_ref="prep"
        )
        result = translate_style_vector(vector)

        fit_lower = result["fit_guidance"].lower()
        assert any(
            kw in fit_lower for kw in ["tailored", "structured", "slim", "fitted"]
        ), f"Expected tailored fit guidance, got: {result['fit_guidance']}"

    def test_oversized_silhouette_gives_relaxed_fit(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            oversized=1.0, sport_street=1.0, primary_cultural_ref="sport_street"
        )
        result = translate_style_vector(vector)

        fit_lower = result["fit_guidance"].lower()
        assert any(
            kw in fit_lower for kw in ["oversized", "baggy", "loose", "relaxed"]
        ), f"Expected oversized fit guidance, got: {result['fit_guidance']}"

    def test_warm_color_temperature_guidance(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            color_temp=0.8, prep=1.0, primary_cultural_ref="prep"
        )
        result = translate_style_vector(vector)

        color_lower = result["color_guidance"].lower()
        assert any(
            kw in color_lower for kw in ["warm", "earth", "brown", "tan", "rust"]
        ), f"Expected warm color guidance, got: {result['color_guidance']}"

    def test_cool_color_temperature_guidance(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            color_temp=-0.6, prep=1.0, primary_cultural_ref="prep"
        )
        result = translate_style_vector(vector)

        color_lower = result["color_guidance"].lower()
        assert any(
            kw in color_lower for kw in ["cool", "blue", "grey", "navy", "black"]
        ), f"Expected cool color guidance, got: {result['color_guidance']}"

    def test_high_energy_adds_bold_keywords(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            energy=0.9, sport_street=1.0, primary_cultural_ref="sport_street"
        )
        result = translate_style_vector(vector)

        keywords_lower = [kw.lower() for kw in result["search_keywords"]]
        keywords_str = " ".join(keywords_lower)
        assert any(
            kw in keywords_str for kw in ["bold", "statement", "graphic", "loud"]
        ), f"Expected bold/statement keywords for high energy, got: {result['search_keywords']}"

    def test_low_energy_adds_understated_keywords(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(
            energy=0.15, prep=1.0, primary_cultural_ref="prep"
        )
        result = translate_style_vector(vector)

        keywords_lower = [kw.lower() for kw in result["search_keywords"]]
        keywords_str = " ".join(keywords_lower)
        assert any(
            kw in keywords_str
            for kw in ["understated", "minimal", "quiet", "subtle", "clean"]
        ), f"Expected understated keywords for low energy, got: {result['search_keywords']}"

    def test_summary_is_nonempty_string(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(prep=1.0, primary_cultural_ref="prep")
        result = translate_style_vector(vector)

        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 20, "Summary should be a meaningful sentence"


# ── Tests for system prompt integration ─────────────────────────────────────

class TestSystemPromptGuidance:
    """build_system_prompt includes style guidance when vector is present."""

    def test_guidance_section_present_with_vector(self):
        from agent.system_prompt import build_system_prompt

        profile = {
            "style_vector": {
                "energy": 0.6,
                "cultural_ref": {"sport_street": 0.8, "prep": 0.0, "clean_basic": 0.0, "utility": 0.0},
                "silhouette": {"structured": 0.2, "relaxed": 0.6, "oversized": 0.2},
                "color": {"temperature": 0.1, "range": 0.5, "expression": 0.5},
                "primary_cultural_ref": "sport_street",
                "occasions": ["casual"],
            },
            "style_adjectives": {},
        }
        prompt = build_system_prompt(profile, "")

        assert "Search Guidance" in prompt or "search guidance" in prompt.lower(), \
            "System prompt should include search guidance section when style vector present"

    def test_guidance_section_absent_without_vector(self):
        from agent.system_prompt import build_system_prompt

        profile = {"style_vector": {}, "style_adjectives": {}}
        prompt = build_system_prompt(profile, "")

        # Should not have guidance section when no vector
        assert "suggested brands" not in prompt.lower() or "Search Guidance" not in prompt

    def test_guidance_section_absent_with_empty_primary_ref(self):
        from agent.system_prompt import build_system_prompt

        profile = {
            "style_vector": {"primary_cultural_ref": "none"},
            "style_adjectives": {},
        }
        prompt = build_system_prompt(profile, "")

        assert "suggested brands" not in prompt.lower()


# ── Tests for vintage_street cultural reference ──────────────────────────────

class TestVintageStreetCulturalRef:
    """vintage_street dimension returns vintage-appropriate brands, keywords, and system prompt label."""

    def test_vintage_street_brands_returned(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(vintage_street=1.0, primary_cultural_ref="vintage_street")
        result = translate_style_vector(vector)

        brands_lower = [b.lower() for b in result["suggested_brands"]]
        assert any(
            kw in " ".join(brands_lower)
            for kw in ["champion", "levi", "carhartt", "supreme", "dickies"]
        ), f"Expected vintage streetwear brands, got {result['suggested_brands']}"

    def test_vintage_street_keywords_returned(self):
        from services.style_translator import translate_style_vector

        vector = _make_vector(vintage_street=1.0, primary_cultural_ref="vintage_street")
        result = translate_style_vector(vector)

        keywords_lower = [kw.lower() for kw in result["search_keywords"]]
        assert any(
            kw in " ".join(keywords_lower)
            for kw in ["vintage", "90s", "retro", "thrifted"]
        ), f"Expected vintage keywords, got {result['search_keywords']}"

    def test_vintage_street_differs_from_sport_street_brands(self):
        from services.style_translator import translate_style_vector

        sport = translate_style_vector(_make_vector(sport_street=1.0, primary_cultural_ref="sport_street"))
        vintage = translate_style_vector(_make_vector(vintage_street=1.0, primary_cultural_ref="vintage_street"))

        assert set(sport["suggested_brands"]) != set(vintage["suggested_brands"]), (
            "vintage_street and sport_street should produce different brand recommendations"
        )

    def test_vintage_street_label_in_system_prompt(self):
        from agent.system_prompt import build_system_prompt

        profile = {
            "style_vector": {
                "energy": 0.5,
                "cultural_ref": {
                    "sport_street": 0.0, "prep": 0.0, "clean_basic": 0.0,
                    "utility": 0.0, "vintage_street": 1.0,
                },
                "silhouette": {"structured": 0.0, "relaxed": 0.5, "oversized": 0.5},
                "color": {"temperature": 0.0, "range": 0.5, "expression": 0.5},
                "primary_cultural_ref": "vintage_street",
                "occasions": ["casual"],
            },
            "style_adjectives": {},
        }
        prompt = build_system_prompt(profile, "")

        assert "Vintage" in prompt, "System prompt should display 'Vintage/Streetwear' label for vintage_street"
