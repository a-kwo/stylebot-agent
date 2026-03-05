"""Tests for Part A: Recommendation Quality Improvements

A1: System prompt rewrite — behavioral instructions that force Claude to reference user data
A2: Search query enrichment — prepend gender to search queries as safety net
A3: Wardrobe gap analysis tool — new analyze_wardrobe tool
"""

import json
import sqlite3
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def db():
    """Create a temporary in-memory database with full schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives TEXT DEFAULT '[]',
            preferred_colors TEXT DEFAULT '[]',
            avoided_colors TEXT DEFAULT '[]',
            preferred_brands TEXT DEFAULT '[]',
            avoided_brands TEXT DEFAULT '[]',
            size_tops TEXT, size_bottoms TEXT, size_shoes TEXT,
            budget_min INTEGER DEFAULT 0, budget_max INTEGER DEFAULT 500,
            occasions TEXT DEFAULT '[]', fit_preferences TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            gender TEXT, age INTEGER, climate TEXT,
            onboarded INTEGER DEFAULT 0,
            style_quiz TEXT DEFAULT '[]',
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL, category TEXT NOT NULL,
            color TEXT, brand TEXT, condition TEXT DEFAULT 'good',
            tags TEXT DEFAULT '[]', image_url TEXT, purchase_url TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            role TEXT NOT NULL, content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_title TEXT NOT NULL, feedback TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            summary TEXT NOT NULL, messages_up_to INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL, occasion TEXT, season TEXT,
            notes TEXT DEFAULT '', image_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE outfit_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            outfit_id INTEGER NOT NULL REFERENCES outfits(id) ON DELETE CASCADE,
            wardrobe_id INTEGER NOT NULL REFERENCES wardrobe(id),
            layer_order INTEGER DEFAULT 0
        );
    """)
    conn.execute("INSERT INTO users (username, password_hash) VALUES ('testuser', 'fakehash')")
    conn.execute(
        "INSERT INTO profiles (user_id, gender, age, climate) VALUES (1, 'Male', 28, 'Temperate / 4 seasons')"
    )
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def populated_db(db):
    """DB with wardrobe items and feedback data for richer tests."""
    # Add wardrobe items
    db.executemany(
        "INSERT INTO wardrobe (user_id, name, category, color, brand, tags) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "Navy Slim Chinos", "bottoms", "navy", "J.Crew", '["casual", "work"]'),
            (1, "White Oxford Shirt", "tops", "white", "Brooks Brothers", '["classic", "work"]'),
            (1, "White Sneakers", "shoes", "white", "Common Projects", '["casual", "minimal"]'),
            (1, "Grey Wool Blazer", "outerwear", "grey", "SuitSupply", '["formal", "work"]'),
            (1, "Black Leather Belt", "accessories", "black", "Coach", '["formal", "casual"]'),
        ],
    )
    # Add feedback
    db.executemany(
        "INSERT INTO recommendation_feedback (user_id, product_title, feedback) VALUES (?, ?, ?)",
        [
            (1, "Slim Fit Navy Blazer", "like"),
            (1, "Classic White Sneakers", "like"),
            (1, "Tailored Chinos", "like"),
            (1, "Graphic Print Hoodie", "dislike"),
            (1, "Oversized Cargo Pants", "dislike"),
        ],
    )
    db.commit()
    return db


# ── A1: System Prompt Rewrite ─────────────────────────────────────

class TestA1SystemPromptBehavior:
    """The system prompt must contain explicit behavioral instructions
    that force Claude to reference specific wardrobe items, explain
    reasoning, and analyze feedback patterns."""

    def test_prompt_instructs_naming_wardrobe_items(self, populated_db):
        """Prompt must instruct Claude to name specific wardrobe items."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        assert "name" in prompt.lower() and "wardrobe" in prompt.lower() and "specific" in prompt.lower(), (
            "System prompt must instruct Claude to name specific wardrobe items in suggestions"
        )

    def test_prompt_instructs_explaining_why(self, populated_db):
        """Prompt must instruct Claude to explain WHY suggestions match."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        # Must instruct to explain reasoning
        prompt_lower = prompt.lower()
        assert "why" in prompt_lower or "explain" in prompt_lower or "reason" in prompt_lower, (
            "System prompt must instruct Claude to explain WHY suggestions match the user's style"
        )
        # Must reference style/preferences/profile as basis for explanation
        assert "style" in prompt_lower or "preference" in prompt_lower or "profile" in prompt_lower, (
            "System prompt must reference user style/preferences as basis for explanations"
        )

    def test_prompt_instructs_feedback_pattern_analysis(self, populated_db):
        """Prompt must instruct Claude to analyze feedback patterns."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        prompt_lower = prompt.lower()
        assert "pattern" in prompt_lower, (
            "System prompt must instruct Claude to analyze feedback patterns"
        )

    def test_prompt_instructs_wardrobe_gap_spotting(self, populated_db):
        """Prompt must instruct Claude to spot wardrobe gaps proactively."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        prompt_lower = prompt.lower()
        assert "gap" in prompt_lower or "missing" in prompt_lower, (
            "System prompt must instruct Claude to spot wardrobe gaps"
        )

    def test_prompt_instructs_budget_on_search(self, populated_db):
        """Prompt must instruct Claude to always pass budget as min/max price."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        prompt_lower = prompt.lower()
        assert "min_price" in prompt_lower and "max_price" in prompt_lower, (
            "System prompt must instruct Claude to always pass budget as min_price/max_price on search_products"
        )

    def test_feedback_section_includes_counts(self, populated_db):
        """Feedback section must show counts like 'Liked (3): ...'."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        # Should show counts in feedback section
        assert "Liked (3)" in prompt, (
            "Feedback section must show count like 'Liked (3): ...'"
        )
        assert "Disliked (2)" in prompt, (
            "Feedback section must show count like 'Disliked (2): ...'"
        )

    def test_feedback_section_includes_pattern_instruction(self, populated_db):
        """Feedback section must include instruction to identify patterns."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        assert "pattern" in prompt.lower() and "identify" in prompt.lower(), (
            "Feedback section must include instruction to identify patterns"
        )

    def test_prompt_instructs_wardrobe_combos(self, populated_db):
        """Prompt must instruct Claude to suggest wardrobe combos unprompted."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        prompt_lower = prompt.lower()
        assert "combo" in prompt_lower or "pair" in prompt_lower or "combination" in prompt_lower, (
            "System prompt must instruct Claude to suggest wardrobe combos unprompted"
        )


# ── A2: Search Query Enrichment ───────────────────────────────────

class TestA2SearchQueryEnrichment:
    """search_products handler must prepend gender to query if missing."""

    def test_search_products_receives_db(self, populated_db):
        """dispatch_tool must pass db to _search_products."""
        from agent.tool_handlers import dispatch_tool
        import agent.tool_handlers as th

        # Monkey-patch _search_products to capture args
        captured = {}
        original = th._search_products

        def mock_search(user_id, tool_input, db=None):
            captured["db"] = db
            captured["user_id"] = user_id
            captured["tool_input"] = tool_input
            return json.dumps({"products": []})

        th._search_products = mock_search
        try:
            dispatch_tool("search_products", {"query": "navy chinos"}, user_id=1, db=populated_db)
            assert captured.get("db") is not None, (
                "dispatch_tool must pass db to _search_products"
            )
        finally:
            th._search_products = original

    def test_search_prepends_gender_when_missing(self, populated_db):
        """When the query doesn't contain gender, it should be prepended."""
        import agent.tool_handlers as th

        # Monkey-patch at the module level where it's imported
        captured = {}
        original = th.shopping_search

        def mock_search(user_id, query, min_price=None, max_price=None, limit=6):
            captured["query"] = query
            return []

        th.shopping_search = mock_search
        try:
            th._search_products(1, {"query": "slim chinos navy"}, db=populated_db)
            assert "male" in captured["query"].lower() or "men" in captured["query"].lower(), (
                "Gender should be prepended to search query when missing"
            )
        finally:
            th.shopping_search = original

    def test_search_does_not_duplicate_gender(self, populated_db):
        """When the query already contains gender, it should NOT be prepended again."""
        import agent.tool_handlers as th

        captured = {}
        original = th.shopping_search

        def mock_search(user_id, query, min_price=None, max_price=None, limit=6):
            captured["query"] = query
            return []

        th.shopping_search = mock_search
        try:
            th._search_products(1, {"query": "men slim chinos navy"}, db=populated_db)
            query_lower = captured["query"].lower()
            # Count occurrences of gender terms
            gender_count = query_lower.count("men") + query_lower.count("male")
            assert gender_count <= 1, (
                f"Gender was duplicated in query: '{captured['query']}'"
            )
        finally:
            th.shopping_search = original


# ── A3: Wardrobe Gap Analysis Tool ────────────────────────────────

class TestA3WardrobeGapTool:
    """New analyze_wardrobe tool must exist in tool definitions, handler,
    and system prompt."""

    def test_analyze_wardrobe_tool_defined(self):
        """TOOLS list must include analyze_wardrobe."""
        from agent.tools import TOOLS

        tool_names = [t["name"] for t in TOOLS]
        assert "analyze_wardrobe" in tool_names, (
            "TOOLS must include 'analyze_wardrobe' tool definition"
        )

    def test_analyze_wardrobe_tool_schema(self):
        """analyze_wardrobe tool must have proper input schema."""
        from agent.tools import TOOLS

        tool = next(t for t in TOOLS if t["name"] == "analyze_wardrobe")
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"

    def test_dispatch_handles_analyze_wardrobe(self, populated_db):
        """dispatch_tool must route analyze_wardrobe to its handler."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("analyze_wardrobe", {}, user_id=1, db=populated_db)
        data = json.loads(result)
        assert "error" not in data or "Unknown tool" not in data.get("error", ""), (
            "dispatch_tool must handle 'analyze_wardrobe' tool"
        )

    def test_analyze_wardrobe_returns_category_counts(self, populated_db):
        """Result must include item count by category."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("analyze_wardrobe", {}, user_id=1, db=populated_db)
        data = json.loads(result)

        assert "categories" in data, "Result must include 'categories' with counts"
        cats = data["categories"]
        assert cats.get("tops") == 1
        assert cats.get("bottoms") == 1
        assert cats.get("shoes") == 1
        assert cats.get("outerwear") == 1
        assert cats.get("accessories") == 1

    def test_analyze_wardrobe_returns_missing_categories(self, populated_db):
        """Result must list categories with zero items."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("analyze_wardrobe", {}, user_id=1, db=populated_db)
        data = json.loads(result)

        assert "missing_categories" in data, "Result must include 'missing_categories'"
        # populated_db has no dresses
        assert "dresses" in data["missing_categories"]

    def test_analyze_wardrobe_returns_color_variety(self, populated_db):
        """Result must include color variety info."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("analyze_wardrobe", {}, user_id=1, db=populated_db)
        data = json.loads(result)

        assert "colors" in data, "Result must include 'colors'"
        assert isinstance(data["colors"], list)
        assert "white" in data["colors"]
        assert "navy" in data["colors"]

    def test_analyze_wardrobe_returns_total_count(self, populated_db):
        """Result must include total item count."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("analyze_wardrobe", {}, user_id=1, db=populated_db)
        data = json.loads(result)

        assert "total_items" in data
        assert data["total_items"] == 5

    def test_system_prompt_mentions_analyze_wardrobe(self, populated_db):
        """System prompt must instruct Claude when to use analyze_wardrobe."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, populated_db)
        wardrobe = get_wardrobe_summary(1, populated_db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=populated_db)

        assert "analyze_wardrobe" in prompt, (
            "System prompt must mention analyze_wardrobe tool"
        )
