"""Tests for wardrobe image URL handling.

Verifies that:
1. add_to_wardrobe stores image_url when Claude passes it
2. Auto-enrichment populates image_url from recent search results (in-memory)
3. Fallback enrichment from conversation history (DB) fills image_url
4. The tool description and system prompt instruct Claude to pass image_url
"""

import json
import sqlite3
import pytest

from agent.tool_handlers import (
    dispatch_tool,
    set_recent_search_products,
    _enrich_from_recent_search,
    _enrich_from_conversation_history,
)
from agent.tools import TOOLS


@pytest.fixture
def db():
    """In-memory SQLite database with wardrobe + conversations tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            color TEXT,
            brand TEXT,
            condition TEXT,
            tags TEXT DEFAULT '[]',
            image_url TEXT,
            local_image_path TEXT,
            purchase_url TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE profiles (
            user_id INTEGER PRIMARY KEY,
            gender TEXT, age TEXT, climate TEXT,
            style_adjectives TEXT DEFAULT '[]',
            preferred_colors TEXT DEFAULT '[]',
            avoided_colors TEXT DEFAULT '[]',
            preferred_brands TEXT DEFAULT '[]',
            avoided_brands TEXT DEFAULT '[]',
            size_tops TEXT, size_bottoms TEXT, size_shoes TEXT,
            budget_min INTEGER DEFAULT 0, budget_max INTEGER DEFAULT 500,
            occasions TEXT DEFAULT '[]',
            fit_preferences TEXT DEFAULT '[]',
            notes TEXT,
            style_quiz TEXT DEFAULT '[]'
        )
    """)
    conn.execute("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "INSERT INTO profiles (user_id) VALUES (?)", (1,)
    )
    conn.commit()
    yield conn
    conn.close()


def _insert_meta_products(db, user_id, products):
    """Helper: insert a meta record with product data into conversations."""
    meta = [{"type": "products", "products": products}]
    db.execute(
        "INSERT INTO conversations (user_id, role, content) VALUES (?, 'meta', ?)",
        (user_id, json.dumps(meta)),
    )
    db.commit()


class TestAddToWardrobeStoresImageUrl:
    """When Claude passes image_url to add_to_wardrobe, it must be stored."""

    def test_image_url_stored_when_provided(self, db):
        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Steve Madden Icebox",
            "category": "shoes",
            "image_url": "https://example.com/shoe.jpg",
        }, user_id=1, db=db))

        assert result["status"] == "added"
        row = db.execute("SELECT image_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["image_url"] == "https://example.com/shoe.jpg"

    def test_purchase_url_stored_when_provided(self, db):
        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Nike Air Max",
            "category": "shoes",
            "image_url": "https://example.com/nike.jpg",
            "purchase_url": "https://shop.com/nike",
        }, user_id=1, db=db))

        row = db.execute("SELECT purchase_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["purchase_url"] == "https://shop.com/nike"


class TestAutoEnrichmentInMemory:
    """When Claude omits image_url, enrichment from in-memory buffer should fill it."""

    def test_enrichment_exact_match(self):
        products = [
            {"title": "Steve Madden Icebox", "image_url": "https://img.com/shoe.jpg", "item_url": "https://shop.com/shoe"},
        ]
        result = _enrich_from_recent_search("Steve Madden Icebox", products)
        assert result is not None
        assert result["image_url"] == "https://img.com/shoe.jpg"

    def test_enrichment_from_global_buffer(self, db):
        set_recent_search_products([
            {"title": "Steve Madden Icebox Sneaker", "image_url": "https://img.com/shoe.jpg", "item_url": "https://shop.com/shoe"},
        ])
        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Steve Madden Icebox Sneaker",
            "category": "shoes",
        }, user_id=1, db=db))

        row = db.execute("SELECT image_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["image_url"] == "https://img.com/shoe.jpg"

        set_recent_search_products([])


class TestEnrichmentFromConversationHistory:
    """When in-memory buffer is empty, enrichment should fall back to DB history."""

    def test_enrichment_finds_product_in_history(self, db):
        """After server restart (empty buffer), image_url should come from stored search results."""
        set_recent_search_products([])  # simulate server restart

        # Simulate a previous search_products result stored in conversation history
        _insert_meta_products(db, user_id=1, products=[
            {
                "title": "Men's Lace Up Graffiti Sneakers",
                "image_url": "https://img.com/graffiti.jpg",
                "item_url": "https://shop.com/graffiti",
                "price": "$49.99",
            },
            {
                "title": "Nike Air Force 1",
                "image_url": "https://img.com/af1.jpg",
                "item_url": "https://shop.com/af1",
                "price": "$110.00",
            },
        ])

        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Men's Lace Up Graffiti Sneakers",
            "category": "shoes",
        }, user_id=1, db=db))

        row = db.execute("SELECT image_url, purchase_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["image_url"] == "https://img.com/graffiti.jpg"
        assert row["purchase_url"] == "https://shop.com/graffiti"

    def test_enrichment_fuzzy_match_from_history(self, db):
        """Fuzzy matching should work against conversation history products."""
        set_recent_search_products([])

        _insert_meta_products(db, user_id=1, products=[
            {
                "title": "Steve Madden Icebox Men's Sneaker - White/Multi",
                "image_url": "https://img.com/icebox.jpg",
                "item_url": "https://shop.com/icebox",
            },
        ])

        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Steve Madden Icebox",
            "category": "shoes",
        }, user_id=1, db=db))

        row = db.execute("SELECT image_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["image_url"] == "https://img.com/icebox.jpg"

    def test_no_match_returns_none(self, db):
        """When no products match at all, image_url stays None."""
        set_recent_search_products([])

        _insert_meta_products(db, user_id=1, products=[
            {"title": "Completely Different Product", "image_url": "https://img.com/other.jpg"},
        ])

        result = json.loads(dispatch_tool("add_to_wardrobe", {
            "name": "Random Unknown Shoe",
            "category": "shoes",
        }, user_id=1, db=db))

        row = db.execute("SELECT image_url FROM wardrobe WHERE id = ?", (result["id"],)).fetchone()
        assert row["image_url"] is None

    def test_direct_function_call(self, db):
        """_enrich_from_conversation_history returns correct data."""
        _insert_meta_products(db, user_id=1, products=[
            {"title": "Nike Dunk Low", "image_url": "https://img.com/dunk.jpg", "item_url": "https://shop.com/dunk"},
        ])

        result = _enrich_from_conversation_history(1, "Nike Dunk Low", db)
        assert result is not None
        assert result["image_url"] == "https://img.com/dunk.jpg"
        assert result["item_url"] == "https://shop.com/dunk"


class TestToolDescriptionRequiresImageUrl:
    """The add_to_wardrobe tool description must instruct Claude to pass image_url."""

    def _get_add_tool(self):
        return next(t for t in TOOLS if t["name"] == "add_to_wardrobe")

    def test_description_mentions_image_url_requirement(self):
        tool = self._get_add_tool()
        desc = tool["description"].lower()
        assert "image_url" in desc

    def test_description_emphasizes_always_passing_image(self):
        tool = self._get_add_tool()
        desc = tool["description"].lower()
        assert any(word in desc for word in ["always", "must", "required"])


class TestSystemPromptImageGuidance:
    """System prompt must instruct Claude to pass image_url when adding from search."""

    def test_system_prompt_mentions_image_url_for_wardrobe(self):
        from agent.system_prompt import build_system_prompt
        prompt = build_system_prompt(
            profile={"gender": "male", "age": "25", "climate": "temperate"},
            wardrobe_summary="",
        )
        assert "image_url" in prompt.lower()
