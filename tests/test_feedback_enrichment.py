"""Tests for enriched feedback storage and pattern analysis."""

import sqlite3
import pytest


# ── Helper: create an in-memory DB with the feedback table ──────────────────

def _make_db():
    """Create an in-memory SQLite DB with the recommendation_feedback table."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_title TEXT NOT NULL,
            feedback TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


# ── Tests for DB migration ──────────────────────────────────────────────────

class TestFeedbackMigration:
    """_migrate_feedback adds new columns to existing table."""

    def test_migration_adds_new_columns(self):
        from database import _migrate_feedback

        conn = _make_db()
        _migrate_feedback(conn)

        # Verify new columns exist by inserting a row with them
        conn.execute(
            """INSERT INTO recommendation_feedback
               (user_id, product_title, feedback, price, category, seller, color, search_query, image_url)
               VALUES (1, 'Test Shirt', 'like', '$49.99', 'tops', 'Nordstrom', 'navy', 'navy shirt', 'http://img.jpg')"""
        )
        conn.commit()

        row = conn.execute("SELECT * FROM recommendation_feedback WHERE id = 1").fetchone()
        assert row["price"] == "$49.99"
        assert row["category"] == "tops"
        assert row["seller"] == "Nordstrom"
        assert row["color"] == "navy"
        assert row["search_query"] == "navy shirt"
        assert row["image_url"] == "http://img.jpg"

    def test_migration_is_idempotent(self):
        from database import _migrate_feedback

        conn = _make_db()
        _migrate_feedback(conn)
        _migrate_feedback(conn)  # Should not raise

        # Columns should still work
        conn.execute(
            "INSERT INTO recommendation_feedback (user_id, product_title, feedback, price) VALUES (1, 'Test', 'like', '$20')"
        )
        conn.commit()

    def test_old_inserts_still_work_after_migration(self):
        from database import _migrate_feedback

        conn = _make_db()
        _migrate_feedback(conn)

        # Old-style insert with no new columns should work (NULLs)
        conn.execute(
            "INSERT INTO recommendation_feedback (user_id, product_title, feedback) VALUES (1, 'Old Product', 'dislike')"
        )
        conn.commit()

        row = conn.execute("SELECT * FROM recommendation_feedback WHERE id = 1").fetchone()
        assert row["product_title"] == "Old Product"
        assert row["price"] is None
        assert row["seller"] is None


# ── Tests for _build_feedback_patterns ───────────────────────────────────────

class TestBuildFeedbackPatterns:
    """_build_feedback_patterns computes aggregate patterns from enriched feedback."""

    def test_patterns_with_enriched_data(self):
        from agent.system_prompt import _build_feedback_patterns

        rows = [
            {"product_title": "Navy Blazer", "feedback": "like", "price": "$59.99", "seller": "Nordstrom", "color": "navy", "category": "outerwear"},
            {"product_title": "Black Chinos", "feedback": "like", "price": "$45.00", "seller": "ASOS", "color": "black", "category": "bottoms"},
            {"product_title": "Red Graphic Tee", "feedback": "dislike", "price": "$120.00", "seller": "Gucci", "color": "red", "category": "tops"},
            {"product_title": "White Sneakers", "feedback": "like", "price": "$80.00", "seller": "Nordstrom", "color": "white", "category": "shoes"},
        ]
        result = _build_feedback_patterns(rows)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should mention like/dislike counts
        assert "3" in result  # 3 likes
        assert "1" in result  # 1 dislike

    def test_patterns_with_null_metadata(self):
        """Rows with NULL new columns should degrade gracefully."""
        from agent.system_prompt import _build_feedback_patterns

        rows = [
            {"product_title": "Some Shirt", "feedback": "like", "price": None, "seller": None, "color": None, "category": None},
            {"product_title": "Some Pants", "feedback": "dislike", "price": None, "seller": None, "color": None, "category": None},
        ]
        result = _build_feedback_patterns(rows)

        assert isinstance(result, str)
        assert "1" in result  # counts should still show

    def test_patterns_with_empty_rows(self):
        from agent.system_prompt import _build_feedback_patterns

        result = _build_feedback_patterns([])
        assert isinstance(result, str)

    def test_patterns_include_price_range_for_likes(self):
        from agent.system_prompt import _build_feedback_patterns

        rows = [
            {"product_title": "A", "feedback": "like", "price": "$30.00", "seller": "X", "color": "blue", "category": "tops"},
            {"product_title": "B", "feedback": "like", "price": "$70.00", "seller": "Y", "color": "navy", "category": "tops"},
        ]
        result = _build_feedback_patterns(rows)

        # Should mention price range info
        assert "$30" in result or "30" in result
        assert "$70" in result or "70" in result

    def test_patterns_include_common_sellers(self):
        from agent.system_prompt import _build_feedback_patterns

        rows = [
            {"product_title": "A", "feedback": "like", "price": "$40", "seller": "Nordstrom", "color": None, "category": None},
            {"product_title": "B", "feedback": "like", "price": "$50", "seller": "Nordstrom", "color": None, "category": None},
            {"product_title": "C", "feedback": "like", "price": "$60", "seller": "ASOS", "color": None, "category": None},
        ]
        result = _build_feedback_patterns(rows)

        assert "Nordstrom" in result


# ── Tests for FeedbackRequest model ─────────────────────────────────────────

class TestFeedbackRequestModel:
    """FeedbackRequest accepts optional enriched fields."""

    def test_basic_request_still_works(self):
        from models import FeedbackRequest

        req = FeedbackRequest(product_title="Test", feedback="like")
        assert req.product_title == "Test"
        assert req.feedback == "like"

    def test_enriched_request_works(self):
        from models import FeedbackRequest

        req = FeedbackRequest(
            product_title="Navy Blazer",
            feedback="like",
            price="$59.99",
            category="outerwear",
            seller="Nordstrom",
            color="navy",
            search_query="navy blazer mens",
            image_url="http://example.com/img.jpg",
        )
        assert req.price == "$59.99"
        assert req.seller == "Nordstrom"
        assert req.color == "navy"
        assert req.category == "outerwear"
        assert req.search_query == "navy blazer mens"
        assert req.image_url == "http://example.com/img.jpg"

    def test_enriched_fields_default_to_none(self):
        from models import FeedbackRequest

        req = FeedbackRequest(product_title="Test", feedback="like")
        assert req.price is None
        assert req.seller is None
        assert req.color is None
        assert req.category is None
        assert req.search_query is None
        assert req.image_url is None
