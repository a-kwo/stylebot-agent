"""Tests for programmatic search query enhancement."""

import pytest


# ── Tests for _enhance_query ─────────────────────────────────────────────────

class TestEnhanceQuery:
    """_enhance_query auto-injects profile data into search queries."""

    def test_avoided_brand_produces_warning(self):
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": ["Shein", "Temu"], "preferred_brands": [], "fit_preferences": []}
        result = _enhance_query("Shein summer dress", profile, None, None)

        assert len(result["warnings"]) > 0
        assert any("Shein" in w for w in result["warnings"])

    def test_avoided_brand_case_insensitive(self):
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": ["shein"], "preferred_brands": [], "fit_preferences": []}
        result = _enhance_query("SHEIN summer dress", profile, None, None)

        assert len(result["warnings"]) > 0

    def test_preferred_brands_not_auto_appended_to_generic_query(self):
        """Preferred brands should be reference context only — not auto-injected into queries.
        Claude reads brand preferences from the system prompt and decides when to use them."""
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": [], "preferred_brands": ["COS", "Arket"], "fit_preferences": []}
        result = _enhance_query("navy blazer", profile, None, None)

        query_lower = result["query"].lower()
        assert "cos" not in query_lower and "arket" not in query_lower, \
            f"Preferred brands should not be auto-appended to queries, got: {result['query']}"

    def test_preferred_brands_not_appended_when_brand_in_query(self):
        """Don't append preferred brands if the query already mentions a brand."""
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": [], "preferred_brands": ["COS", "Arket"], "fit_preferences": []}
        result = _enhance_query("Nike air max sneakers", profile, None, None)

        # Query already has "Nike" — should NOT append COS/Arket
        query_lower = result["query"].lower()
        assert "cos" not in query_lower and "arket" not in query_lower, \
            f"Should not append preferred brands when query already has a brand: {result['query']}"

    def test_budget_injected_when_no_explicit_prices(self):
        from agent.tool_handlers import _enhance_query

        profile = {
            "avoided_brands": [], "preferred_brands": [], "fit_preferences": [],
            "budget_min": 50, "budget_max": 200,
        }
        result = _enhance_query("leather boots", profile, None, None)

        assert result["min_price"] == 50
        assert result["max_price"] == 200

    def test_explicit_prices_not_overridden(self):
        from agent.tool_handlers import _enhance_query

        profile = {
            "avoided_brands": [], "preferred_brands": [], "fit_preferences": [],
            "budget_min": 50, "budget_max": 200,
        }
        result = _enhance_query("leather boots", profile, 20, 100)

        assert result["min_price"] == 20
        assert result["max_price"] == 100

    def test_partial_explicit_price_preserved(self):
        """If Claude passes only min_price, don't override it but fill max from profile."""
        from agent.tool_handlers import _enhance_query

        profile = {
            "avoided_brands": [], "preferred_brands": [], "fit_preferences": [],
            "budget_min": 50, "budget_max": 200,
        }
        result = _enhance_query("boots", profile, 30, None)

        assert result["min_price"] == 30
        assert result["max_price"] == 200

    def test_empty_profile_passes_through(self):
        from agent.tool_handlers import _enhance_query

        profile = {}
        result = _enhance_query("navy blazer", profile, None, None)

        assert result["query"] == "navy blazer"
        assert result["min_price"] is None
        assert result["max_price"] is None
        assert result["warnings"] == []

    def test_fit_preference_appended(self):
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": [], "preferred_brands": [], "fit_preferences": ["slim fit"]}
        result = _enhance_query("mens chinos", profile, None, None)

        assert "slim fit" in result["query"].lower(), \
            f"Expected 'slim fit' in query, got: {result['query']}"

    def test_fit_preference_not_duplicated(self):
        from agent.tool_handlers import _enhance_query

        profile = {"avoided_brands": [], "preferred_brands": [], "fit_preferences": ["slim fit"]}
        result = _enhance_query("slim fit chinos", profile, None, None)

        # Should not add "slim fit" again
        assert result["query"].lower().count("slim fit") == 1

    def test_returns_all_required_keys(self):
        from agent.tool_handlers import _enhance_query

        profile = {}
        result = _enhance_query("test query", profile, None, None)

        assert "query" in result
        assert "min_price" in result
        assert "max_price" in result
        assert "warnings" in result
