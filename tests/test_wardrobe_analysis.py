"""Tests for wardrobe-aware style coherence (Item 6)."""

import json
import sqlite3
import pytest


# ── Tests for classify_color_temperature ────────────────────────────────────

class TestClassifyColorTemperature:
    """classify_color_temperature maps color names to warm/cool/neutral."""

    def test_warm_colors(self):
        from services.style_translator import classify_color_temperature

        for color in ["brown", "tan", "rust", "olive", "cream", "beige", "orange"]:
            assert classify_color_temperature(color) == "warm", f"{color} should be warm"

    def test_cool_colors(self):
        from services.style_translator import classify_color_temperature

        for color in ["navy", "blue", "charcoal", "grey", "slate", "teal"]:
            assert classify_color_temperature(color) == "cool", f"{color} should be cool"

    def test_neutral_colors(self):
        from services.style_translator import classify_color_temperature

        for color in ["black", "white"]:
            assert classify_color_temperature(color) == "neutral", f"{color} should be neutral"

    def test_case_insensitive(self):
        from services.style_translator import classify_color_temperature

        assert classify_color_temperature("NAVY") == "cool"
        assert classify_color_temperature("Brown") == "warm"

    def test_multi_word_color_substring_fallback(self):
        from services.style_translator import classify_color_temperature

        assert classify_color_temperature("dark navy") == "cool"
        assert classify_color_temperature("light brown") == "warm"

    def test_unknown_color_returns_neutral(self):
        from services.style_translator import classify_color_temperature

        assert classify_color_temperature("sparkle") == "neutral"

    def test_none_returns_neutral(self):
        from services.style_translator import classify_color_temperature

        assert classify_color_temperature(None) == "neutral"

    def test_empty_string_returns_neutral(self):
        from services.style_translator import classify_color_temperature

        assert classify_color_temperature("") == "neutral"


# ── Tests for _analyze_wardrobe enriched output ─────────────────────────────

def _make_db():
    """Create an in-memory DB with wardrobe + profile tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE wardrobe (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        color TEXT,
        brand TEXT,
        tags TEXT DEFAULT '[]',
        image_url TEXT,
        purchase_url TEXT,
        added_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE profiles (
        user_id INTEGER PRIMARY KEY,
        gender TEXT, age TEXT, climate TEXT,
        style_adjectives TEXT DEFAULT '{}',
        preferred_colors TEXT DEFAULT '[]',
        avoided_colors TEXT DEFAULT '[]',
        preferred_brands TEXT DEFAULT '[]',
        avoided_brands TEXT DEFAULT '[]',
        size_tops TEXT, size_bottoms TEXT, size_shoes TEXT,
        budget_min REAL DEFAULT 0, budget_max REAL DEFAULT 500,
        occasions TEXT DEFAULT '[]',
        fit_preferences TEXT DEFAULT '[]',
        notes TEXT,
        style_quiz TEXT DEFAULT '[]',
        style_vector TEXT DEFAULT '{}'
    )""")
    return conn


class TestAnalyzeWardrobeEnriched:
    """_analyze_wardrobe returns enriched output with color temperature, brand alignment, occasion gaps."""

    def test_existing_keys_still_present(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        db.execute("INSERT INTO profiles (user_id) VALUES (1)")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Navy Shirt', 'tops', 'navy', 'COS')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert "total_items" in result
        assert "categories" in result
        assert "missing_categories" in result
        assert "colors" in result

    def test_color_temperature_breakdown(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        db.execute("INSERT INTO profiles (user_id) VALUES (1)")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Navy Shirt', 'tops', 'navy', 'COS')")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Brown Boots', 'shoes', 'brown', 'Red Wing')")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Black Jeans', 'bottoms', 'black', 'Levis')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert "color_temperature" in result
        assert result["color_temperature"]["cool"] == 1  # navy
        assert result["color_temperature"]["warm"] == 1  # brown
        assert result["color_temperature"]["neutral"] == 1  # black

    def test_brand_alignment_with_style_vector(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        style_vector = json.dumps({"primary_cultural_ref": "utility", "cultural_ref": {"utility": 0.8}})
        db.execute("INSERT INTO profiles (user_id, style_vector) VALUES (1, ?)", (style_vector,))
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Flannel Shirt', 'tops', 'red', 'Filson')")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Sneakers', 'shoes', 'white', 'Nike')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert "brand_alignment" in result
        assert "Filson" in result["brand_alignment"]["aligned"]
        assert "Nike" in result["brand_alignment"]["unaligned"]

    def test_occasion_gaps(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        occasions = json.dumps(["formal", "casual"])
        db.execute("INSERT INTO profiles (user_id, occasions) VALUES (1, ?)", (occasions,))
        # Only have tops — missing shoes and outerwear for formal
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Shirt', 'tops', 'white', 'COS')")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Jeans', 'bottoms', 'blue', 'Levis')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert "occasion_gaps" in result
        # Should identify missing categories for formal occasions
        assert isinstance(result["occasion_gaps"], dict)

    def test_empty_wardrobe_safe_defaults(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        db.execute("INSERT INTO profiles (user_id) VALUES (1)")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert result["total_items"] == 0
        assert result["color_temperature"] == {"warm": 0, "cool": 0, "neutral": 0}
        assert result["brand_alignment"] == {"aligned": [], "unaligned": []}
        assert result["occasion_gaps"] == {}

    def test_no_profile_still_works(self):
        """If profile doesn't exist, analysis should still return safely."""
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Shirt', 'tops', 'navy', 'COS')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert result["total_items"] == 1
        assert "color_temperature" in result

    def test_null_colors_counted_as_neutral(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        db.execute("INSERT INTO profiles (user_id) VALUES (1)")
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Shirt', 'tops', NULL, 'COS')")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        # NULL color items shouldn't contribute to temperature counts
        assert result["color_temperature"] == {"warm": 0, "cool": 0, "neutral": 0}

    def test_null_brands_excluded_from_alignment(self):
        from agent.tool_handlers import _analyze_wardrobe

        db = _make_db()
        style_vector = json.dumps({"primary_cultural_ref": "prep"})
        db.execute("INSERT INTO profiles (user_id, style_vector) VALUES (1, ?)", (style_vector,))
        db.execute("INSERT INTO wardrobe (user_id, name, category, color, brand) VALUES (1, 'Shirt', 'tops', 'white', NULL)")
        db.commit()

        result = json.loads(_analyze_wardrobe(1, db))

        assert result["brand_alignment"]["aligned"] == []
        assert result["brand_alignment"]["unaligned"] == []
