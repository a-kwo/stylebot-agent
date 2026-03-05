"""Tests for Part B: Visual Outfit Builder

B1: Outfit builder page exists with proper structure
B2: Outfit feedback tool (get_outfit_feedback)
B3: Navigation update (Builder tab in sidebar + mobile nav)
"""

import json
import sqlite3
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FRONTEND_SRC = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")


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
    # Add wardrobe items
    conn.executemany(
        "INSERT INTO wardrobe (user_id, name, category, color, brand, tags) VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "Navy Slim Chinos", "bottoms", "navy", "J.Crew", '["casual", "work"]'),
            (1, "White Oxford Shirt", "tops", "white", "Brooks Brothers", '["classic", "work"]'),
            (1, "White Sneakers", "shoes", "white", "Common Projects", '["casual", "minimal"]'),
            (1, "Grey Wool Blazer", "outerwear", "grey", "SuitSupply", '["formal", "work"]'),
            (1, "Black Leather Belt", "accessories", "black", "Coach", '["formal", "casual"]'),
        ],
    )
    conn.commit()
    yield conn
    conn.close()


# ── B1: Outfit Builder Page ───────────────────────────────────────

class TestB1OutfitBuilderPage:
    """The outfit builder page must exist at frontend/src/app/builder/page.tsx
    with the required structure."""

    def test_builder_page_exists(self):
        """Builder page file must exist."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        assert os.path.isfile(page_path), (
            "frontend/src/app/builder/page.tsx must exist"
        )

    def test_builder_page_has_category_filter(self):
        """Builder page must have category filter buttons."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        # Must have category filtering
        assert "category" in content.lower(), (
            "Builder page must support category filtering"
        )
        for cat in ["tops", "bottoms", "shoes", "outerwear", "accessories"]:
            assert cat in content, (
                f"Builder page must reference category '{cat}'"
            )

    def test_builder_page_has_outfit_slots(self):
        """Builder page must have slots for outfit pieces (top, bottom, shoes, etc.)."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        # Must have slot concepts
        assert "slot" in content.lower() or "canvas" in content.lower(), (
            "Builder page must have outfit slots/canvas concept"
        )

    def test_builder_page_has_save_functionality(self):
        """Builder page must have save outfit functionality."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        # Must call POST /api/outfits or use outfit creation
        assert "save" in content.lower() or "/outfits" in content, (
            "Builder page must have save outfit functionality"
        )

    def test_builder_page_has_ask_stylebot_button(self):
        """Builder page must have an 'Ask StyleBot' button for AI feedback."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        assert "ask stylebot" in content.lower() or "ask style" in content.lower() or "feedback" in content.lower(), (
            "Builder page must have an 'Ask StyleBot' button for AI feedback"
        )

    def test_builder_page_uses_auth_guard(self):
        """Builder page must check authentication."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        assert "useAuth" in content, (
            "Builder page must use useAuth for authentication"
        )

    def test_builder_page_loads_wardrobe(self):
        """Builder page must fetch wardrobe items."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        assert "/wardrobe" in content or "wardrobe" in content.lower(), (
            "Builder page must load wardrobe items"
        )

    def test_builder_page_has_occasion_and_season(self):
        """Builder page must have occasion and season selection for saving."""
        page_path = os.path.join(FRONTEND_SRC, "app", "builder", "page.tsx")
        with open(page_path) as f:
            content = f.read()

        assert "occasion" in content.lower(), (
            "Builder page must have occasion selection"
        )
        assert "season" in content.lower(), (
            "Builder page must have season selection"
        )


# ── B2: Outfit Feedback Tool ─────────────────────────────────────

class TestB2OutfitFeedbackTool:
    """New get_outfit_feedback tool for AI evaluation of outfit combinations."""

    def test_tool_defined(self):
        """TOOLS list must include get_outfit_feedback."""
        from agent.tools import TOOLS

        tool_names = [t["name"] for t in TOOLS]
        assert "get_outfit_feedback" in tool_names, (
            "TOOLS must include 'get_outfit_feedback' tool definition"
        )

    def test_tool_schema_has_item_ids(self):
        """Tool schema must accept wardrobe_item_ids."""
        from agent.tools import TOOLS

        tool = next(t for t in TOOLS if t["name"] == "get_outfit_feedback")
        props = tool["input_schema"]["properties"]
        assert "wardrobe_item_ids" in props, (
            "get_outfit_feedback must accept wardrobe_item_ids"
        )

    def test_tool_schema_has_occasion(self):
        """Tool schema must accept occasion."""
        from agent.tools import TOOLS

        tool = next(t for t in TOOLS if t["name"] == "get_outfit_feedback")
        props = tool["input_schema"]["properties"]
        assert "occasion" in props, (
            "get_outfit_feedback must accept occasion"
        )

    def test_dispatch_handles_get_outfit_feedback(self, db):
        """dispatch_tool must route get_outfit_feedback to its handler."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool(
            "get_outfit_feedback",
            {"wardrobe_item_ids": [1, 2, 3]},
            user_id=1,
            db=db,
        )
        data = json.loads(result)
        assert "error" not in data or "Unknown tool" not in data.get("error", ""), (
            "dispatch_tool must handle 'get_outfit_feedback' tool"
        )

    def test_handler_returns_item_details(self, db):
        """Handler must load and return full item details for the given IDs."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool(
            "get_outfit_feedback",
            {"wardrobe_item_ids": [1, 2, 3]},
            user_id=1,
            db=db,
        )
        data = json.loads(result)

        assert "items" in data, "Result must include 'items' with full wardrobe details"
        assert len(data["items"]) == 3
        names = [i["name"] for i in data["items"]]
        assert "Navy Slim Chinos" in names
        assert "White Oxford Shirt" in names
        assert "White Sneakers" in names

    def test_handler_returns_occasion_and_context(self, db):
        """Handler must pass through occasion and context."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool(
            "get_outfit_feedback",
            {
                "wardrobe_item_ids": [1, 2],
                "occasion": "business casual",
                "context": "office meeting",
            },
            user_id=1,
            db=db,
        )
        data = json.loads(result)

        assert data.get("occasion") == "business casual"
        assert data.get("context") == "office meeting"

    def test_handler_includes_feedback_instruction(self, db):
        """Handler must include instruction for Claude to evaluate the outfit."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool(
            "get_outfit_feedback",
            {"wardrobe_item_ids": [1, 2]},
            user_id=1,
            db=db,
        )
        data = json.loads(result)

        assert "instruction" in data, "Result must include an instruction for Claude"

    def test_system_prompt_mentions_outfit_feedback(self, db):
        """System prompt must instruct Claude on outfit feedback behavior."""
        from agent.system_prompt import build_system_prompt
        from services.profile_service import get_profile, get_wardrobe_summary

        profile = get_profile(1, db)
        wardrobe = get_wardrobe_summary(1, db)
        prompt = build_system_prompt(profile, wardrobe, user_id=1, db=db)

        assert "get_outfit_feedback" in prompt, (
            "System prompt must mention get_outfit_feedback tool"
        )


# ── B3: Navigation Update ────────────────────────────────────────

class TestB3NavigationUpdate:
    """NavBar must include a 'Builder' tab in both desktop sidebar and mobile nav."""

    def test_navbar_has_builder_link(self):
        """NavBar must include a link to /builder."""
        navbar_path = os.path.join(FRONTEND_SRC, "components", "NavBar.tsx")
        with open(navbar_path) as f:
            content = f.read()

        assert "/builder" in content, (
            "NavBar must include a link to /builder"
        )

    def test_navbar_has_builder_label(self):
        """NavBar must show 'Builder' as the label."""
        navbar_path = os.path.join(FRONTEND_SRC, "components", "NavBar.tsx")
        with open(navbar_path) as f:
            content = f.read()

        assert "Builder" in content, (
            "NavBar must include 'Builder' label"
        )

    def test_builder_in_nav_items_array(self):
        """The navItems array must include a Builder entry."""
        navbar_path = os.path.join(FRONTEND_SRC, "components", "NavBar.tsx")
        with open(navbar_path) as f:
            content = f.read()

        # Check that builder is in the navItems list (used by both desktop and mobile)
        assert "'/builder'" in content or '"/builder"' in content, (
            "navItems must include '/builder' href"
        )
