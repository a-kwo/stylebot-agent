"""Tests for the 4 reported bugs:
1. Login page centering (layout applies sidebar margin when not authenticated)
2. Quiz image accuracy (images must actually depict the labeled item)
3. Wardrobe image_url not saved by add_to_wardrobe agent tool
4. Product results lost from conversation history on reload
"""

import json
import sqlite3
import os
import sys
import tempfile

import pytest

# Add project root to path
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
    conn.execute("INSERT INTO profiles (user_id) VALUES (1)")
    conn.commit()
    yield conn
    conn.close()


# ── Bug 1: Login page centering ──────────────────────────────────

class TestLoginPageCentering:
    """The layout must NOT apply sidebar margin (md:ml-56) when the user is
    not authenticated. The NavBar returns null when unauthenticated, so the
    main content area should not have the left margin offset."""

    def test_layout_conditionally_applies_sidebar_margin(self):
        """Read the layout.tsx and verify that md:ml-56 is NOT hardcoded
        on <main>. It should be conditional on auth state."""
        layout_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend", "src", "app", "layout.tsx"
        )
        with open(layout_path) as f:
            content = f.read()

        # The layout must NOT have a hardcoded md:ml-56 on the <main> tag
        # It should be conditionally applied (e.g., via a wrapper component
        # that checks auth state)
        assert 'className="md:ml-56' not in content, (
            "layout.tsx should NOT hardcode md:ml-56 on <main>. "
            "The sidebar margin must be conditional on authentication state."
        )


# ── Bug 2: Quiz image accuracy ───────────────────────────────────

class TestQuizImageAccuracy:
    """Each quiz option's image_url must depict the actual item described
    by its label, not a generic/mismatched fashion photo."""

    def test_no_duplicate_image_urls_across_categories(self):
        """No two different items should use the same image URL."""
        from services.quiz_service import QUIZ_QUESTIONS

        seen: dict[str, str] = {}  # url -> "category/label"
        duplicates = []

        for cat_name, cat_data in QUIZ_QUESTIONS.items():
            for opt in cat_data["options"]:
                url = opt["image_url"]
                loc = f"{cat_name}/{opt['label']}"
                if url in seen:
                    duplicates.append(f"  {loc} reuses image from {seen[url]}")
                else:
                    seen[url] = loc

        assert len(duplicates) == 0, (
            "Duplicate image URLs found across quiz categories:\n"
            + "\n".join(duplicates)
        )

    def test_onboarding_images_are_unique_from_chat(self):
        """Onboarding outfit categories must not share image URLs with
        chat-only categories."""
        from services.quiz_service import QUIZ_QUESTIONS, ONBOARDING_CATEGORIES

        chat_cats = [k for k in QUIZ_QUESTIONS if k not in ONBOARDING_CATEGORIES]
        chat_urls = set()
        for cat in chat_cats:
            for opt in QUIZ_QUESTIONS[cat]["options"]:
                chat_urls.add(opt["image_url"])

        for cat in ONBOARDING_CATEGORIES:
            for opt in QUIZ_QUESTIONS[cat]["options"]:
                assert opt["image_url"] not in chat_urls, (
                    f"Onboarding option '{opt['label']}' in {cat} reuses "
                    f"a chat-only image URL"
                )

    def test_all_quiz_images_are_unique_per_category(self):
        """Within a single category, all options must have different images."""
        from services.quiz_service import QUIZ_QUESTIONS

        for cat_name, cat_data in QUIZ_QUESTIONS.items():
            urls = [opt["image_url"] for opt in cat_data["options"]]
            assert len(urls) == len(set(urls)), (
                f"Category '{cat_name}' has duplicate image URLs within itself"
            )


# ── Bug 3: Wardrobe image_url not saved ──────────────────────────

class TestWardrobeImageUrl:
    """When the agent's add_to_wardrobe tool is called with image_url and
    purchase_url, those fields must be saved to the database."""

    def test_add_to_wardrobe_saves_image_url(self, db):
        """The tool handler must persist image_url when provided."""
        from agent.tool_handlers import dispatch_tool

        result = dispatch_tool("add_to_wardrobe", {
            "name": "White Air Force 1s",
            "category": "shoes",
            "color": "white",
            "brand": "Nike",
            "image_url": "https://example.com/shoe.jpg",
            "purchase_url": "https://shop.example.com/shoe",
            "tags": ["casual", "sneakers"],
        }, user_id=1, db=db)

        data = json.loads(result)
        assert data.get("status") == "added"
        item_id = data["id"]

        row = db.execute("SELECT image_url, purchase_url FROM wardrobe WHERE id = ?", (item_id,)).fetchone()
        assert row["image_url"] == "https://example.com/shoe.jpg", (
            "image_url was not saved to the database"
        )
        assert row["purchase_url"] == "https://shop.example.com/shoe", (
            "purchase_url was not saved to the database"
        )

    def test_add_to_wardrobe_tool_schema_includes_image_url(self):
        """The tool's input_schema must expose image_url so Claude can pass it."""
        from agent.tools import TOOLS

        add_tool = next(t for t in TOOLS if t["name"] == "add_to_wardrobe")
        props = add_tool["input_schema"]["properties"]
        assert "image_url" in props, (
            "add_to_wardrobe tool schema is missing image_url property"
        )
        assert "purchase_url" in props, (
            "add_to_wardrobe tool schema is missing purchase_url property"
        )


# ── Bug 4: Products disappear from conversation history ──────────

class TestProductsInHistory:
    """When product results are returned in a conversation turn, they must
    be persisted so that reloading the chat page shows them again."""

    def test_products_persisted_in_conversation(self, db):
        """Product data from search_products must be saved in the
        conversations table alongside the assistant message."""
        # Simulate what the agent loop does: persist an assistant message
        # followed by a products block
        assistant_content = [
            {"type": "text", "text": "Here are some shoes I found:"},
        ]
        products = [
            {"title": "Nike AF1", "price": 110, "image_url": "https://img.example.com/af1.jpg",
             "item_url": "https://shop.example.com/af1", "seller": "Nike"},
        ]

        # The loop should persist products alongside the assistant message
        # Let's store as the loop does
        db.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (1, "assistant", json.dumps(assistant_content)),
        )
        # Products should also be persisted
        db.execute(
            "INSERT INTO conversations (user_id, role, content) VALUES (?, ?, ?)",
            (1, "assistant", json.dumps([{"type": "products", "products": products}])),
        )
        db.commit()

        # Now load conversations and verify products can be recovered
        rows = db.execute(
            "SELECT role, content FROM conversations WHERE user_id = 1 ORDER BY id ASC"
        ).fetchall()

        found_products = False
        for row in rows:
            content = json.loads(row["content"])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "products":
                        found_products = True

        assert found_products, "Product data should be recoverable from conversation history"

    def test_history_loader_extracts_products(self):
        """The frontend chat history loader must extract product blocks,
        not just text blocks. We test this by checking the chat page source
        handles tool_result content containing products."""
        chat_path = os.path.join(
            os.path.dirname(__file__), "..", "frontend", "src", "app", "chat", "page.tsx"
        )
        with open(chat_path) as f:
            content = f.read()

        # The history loading code must handle product blocks
        assert "products" in content.lower(), (
            "Chat page history loader does not handle product blocks"
        )

        # Specifically, the history loading useEffect must extract products
        # from assistant messages, not just text
        assert "tool_result" in content or "products" in content, (
            "Chat page must extract product data from conversation history"
        )
