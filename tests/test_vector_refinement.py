"""Tests for feedback-driven style vector refinement (Item 8)."""

import json
import sqlite3
import pytest


def _make_db():
    """Create in-memory DB with profiles + recommendation_feedback tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
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
        notes TEXT DEFAULT '',
        style_quiz TEXT DEFAULT '[]',
        style_vector TEXT DEFAULT '{}',
        feedback_vector TEXT DEFAULT '{}',
        refined_style_vector TEXT DEFAULT '{}',
        feedback_vector_count INTEGER DEFAULT 0,
        onboarded INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE recommendation_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_title TEXT NOT NULL,
        feedback TEXT NOT NULL,
        price TEXT,
        category TEXT,
        seller TEXT,
        color TEXT,
        search_query TEXT,
        image_url TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    return conn


def _quiz_vector(**overrides):
    """Build a base quiz-style vector."""
    base = {
        "energy": 0.5,
        "cultural_ref": {"sport_street": 0.0, "prep": 0.0, "clean_basic": 0.0, "utility": 0.0},
        "silhouette": {"structured": 0.3, "relaxed": 0.4, "oversized": 0.3},
        "color": {"temperature": 0.0, "range": 0.5, "expression": 0.5},
        "primary_cultural_ref": "none",
        "occasions": [],
    }
    base.update(overrides)
    return base


# ── Tests for cultural signal extraction ─────────────────────────────────────

class TestExtractCulturalSignal:

    def test_nike_maps_to_sport_street(self):
        from services.vector_refinement import _extract_cultural_signal

        product = {"seller": "Nike", "product_title": "Nike Air Max"}
        signal = _extract_cultural_signal(product)
        assert signal.get("sport_street", 0) > 0

    def test_brooks_brothers_maps_to_prep(self):
        from services.vector_refinement import _extract_cultural_signal

        product = {"seller": "Brooks Brothers", "product_title": "Oxford Shirt"}
        signal = _extract_cultural_signal(product)
        assert signal.get("prep", 0) > 0

    def test_unknown_brand_neutral(self):
        from services.vector_refinement import _extract_cultural_signal

        product = {"seller": "RandomStore", "product_title": "Basic Item"}
        signal = _extract_cultural_signal(product)
        total = sum(signal.values())
        assert total == 0


# ── Tests for color signal extraction ────────────────────────────────────────

class TestExtractColorSignal:

    def test_warm_color_positive_temp(self):
        from services.vector_refinement import _extract_color_signal

        product = {"color": "brown"}
        signal = _extract_color_signal(product)
        assert signal.get("temperature", 0) > 0

    def test_cool_color_negative_temp(self):
        from services.vector_refinement import _extract_color_signal

        product = {"color": "navy"}
        signal = _extract_color_signal(product)
        assert signal.get("temperature", 0) < 0

    def test_no_color_neutral(self):
        from services.vector_refinement import _extract_color_signal

        product = {"color": None}
        signal = _extract_color_signal(product)
        assert signal.get("temperature", 0) == 0


# ── Tests for silhouette signal extraction ───────────────────────────────────

class TestExtractSilhouetteSignal:

    def test_oversized_in_title(self):
        from services.vector_refinement import _extract_silhouette_signal

        product = {"product_title": "Oversized Cotton Hoodie"}
        signal = _extract_silhouette_signal(product)
        assert signal.get("oversized", 0) > 0

    def test_slim_fit_in_title(self):
        from services.vector_refinement import _extract_silhouette_signal

        product = {"product_title": "Slim Fit Oxford Shirt"}
        signal = _extract_silhouette_signal(product)
        assert signal.get("structured", 0) > 0


# ── Tests for compute_feedback_vector ────────────────────────────────────────

class TestComputeFeedbackVector:

    def test_empty_returns_neutral(self):
        from services.vector_refinement import compute_feedback_vector

        result = compute_feedback_vector([])
        assert result["energy"] == 0.5
        assert all(v == 0.0 for v in result["cultural_ref"].values())

    def test_likes_produce_positive_signal(self):
        from services.vector_refinement import compute_feedback_vector

        rows = [
            {"feedback": "like", "seller": "Nike", "color": "blue", "product_title": "Nike Hoodie", "price": "80"},
            {"feedback": "like", "seller": "Nike", "color": "navy", "product_title": "Nike Joggers", "price": "60"},
        ]
        result = compute_feedback_vector(rows)
        assert result["cultural_ref"]["sport_street"] > 0

    def test_dislikes_produce_negative_signal(self):
        from services.vector_refinement import compute_feedback_vector

        rows = [
            {"feedback": "dislike", "seller": "Brooks Brothers", "color": "white", "product_title": "Prep Blazer", "price": "200"},
        ]
        result = compute_feedback_vector(rows)
        # Dislike of prep should push prep negative (clamped to 0)
        assert result["cultural_ref"]["prep"] <= 0


# ── Tests for blend_vectors ──────────────────────────────────────────────────

class TestBlendVectors:

    def test_70_30_blend_energy(self):
        from services.vector_refinement import blend_vectors

        quiz = _quiz_vector(energy=0.2)
        feedback = _quiz_vector(energy=0.8)
        result = blend_vectors(quiz, feedback, 0.7, 0.3)

        expected = 0.7 * 0.2 + 0.3 * 0.8  # 0.38
        assert abs(result["energy"] - expected) < 0.01

    def test_nested_dicts_blend(self):
        from services.vector_refinement import blend_vectors

        quiz = _quiz_vector()
        quiz["cultural_ref"]["prep"] = 0.8
        feedback = _quiz_vector()
        feedback["cultural_ref"]["sport_street"] = 0.6

        result = blend_vectors(quiz, feedback, 0.7, 0.3)
        assert result["cultural_ref"]["prep"] == pytest.approx(0.7 * 0.8, abs=0.01)
        assert result["cultural_ref"]["sport_street"] == pytest.approx(0.3 * 0.6, abs=0.01)

    def test_recomputes_primary_cultural_ref(self):
        from services.vector_refinement import blend_vectors

        quiz = _quiz_vector(primary_cultural_ref="prep")
        quiz["cultural_ref"]["prep"] = 0.2
        feedback = _quiz_vector()
        feedback["cultural_ref"]["sport_street"] = 0.9

        result = blend_vectors(quiz, feedback, 0.5, 0.5)
        # sport_street should dominate after blend
        assert result["primary_cultural_ref"] == "sport_street"


# ── Tests for maybe_refine_vector ────────────────────────────────────────────

class TestMaybeRefineVector:

    def test_skips_when_below_threshold(self):
        from services.vector_refinement import maybe_refine_vector

        db = _make_db()
        quiz_vec = _quiz_vector(primary_cultural_ref="prep")
        quiz_vec["cultural_ref"]["prep"] = 0.8
        db.execute(
            "INSERT INTO profiles (user_id, style_vector, feedback_vector_count) VALUES (1, ?, 0)",
            (json.dumps(quiz_vec),),
        )
        # Only 3 feedback rows (below threshold of 5)
        for i in range(3):
            db.execute(
                "INSERT INTO recommendation_feedback (user_id, product_title, feedback, seller, color) VALUES (1, ?, 'like', 'Nike', 'blue')",
                (f"Product {i}",),
            )
        db.commit()

        result = maybe_refine_vector(1, db)
        assert result is None

    def test_triggers_at_threshold(self):
        from services.vector_refinement import maybe_refine_vector

        db = _make_db()
        quiz_vec = _quiz_vector(primary_cultural_ref="prep")
        quiz_vec["cultural_ref"]["prep"] = 0.8
        db.execute(
            "INSERT INTO profiles (user_id, style_vector, feedback_vector_count) VALUES (1, ?, 0)",
            (json.dumps(quiz_vec),),
        )
        for i in range(5):
            db.execute(
                "INSERT INTO recommendation_feedback (user_id, product_title, feedback, seller, color) VALUES (1, ?, 'like', 'Nike', 'blue')",
                (f"Product {i}",),
            )
        db.commit()

        result = maybe_refine_vector(1, db)
        assert result is not None
        assert "cultural_ref" in result

    def test_stores_refined_vector(self):
        from services.vector_refinement import maybe_refine_vector

        db = _make_db()
        quiz_vec = _quiz_vector(primary_cultural_ref="prep")
        quiz_vec["cultural_ref"]["prep"] = 0.8
        db.execute(
            "INSERT INTO profiles (user_id, style_vector, feedback_vector_count) VALUES (1, ?, 0)",
            (json.dumps(quiz_vec),),
        )
        for i in range(5):
            db.execute(
                "INSERT INTO recommendation_feedback (user_id, product_title, feedback, seller, color) VALUES (1, ?, 'like', 'Nike', 'navy')",
                (f"Product {i}",),
            )
        db.commit()

        maybe_refine_vector(1, db)

        row = db.execute("SELECT refined_style_vector, feedback_vector_count FROM profiles WHERE user_id = 1").fetchone()
        refined = json.loads(row["refined_style_vector"])
        assert refined  # non-empty
        assert row["feedback_vector_count"] == 5

    def test_no_quiz_vector_skips(self):
        from services.vector_refinement import maybe_refine_vector

        db = _make_db()
        db.execute("INSERT INTO profiles (user_id, style_vector) VALUES (1, '{}')")
        for i in range(10):
            db.execute(
                "INSERT INTO recommendation_feedback (user_id, product_title, feedback, seller, color) VALUES (1, ?, 'like', 'Nike', 'blue')",
                (f"Product {i}",),
            )
        db.commit()

        result = maybe_refine_vector(1, db)
        assert result is None


# ── Tests for system prompt integration ──────────────────────────────────────

class TestSystemPromptRefinedVector:

    def test_uses_refined_vector_when_available(self):
        from agent.system_prompt import build_system_prompt

        refined = _quiz_vector(primary_cultural_ref="sport_street", energy=0.8)
        refined["cultural_ref"]["sport_street"] = 0.9

        profile = {
            "style_adjectives": {"bold": 2},
            "preferred_colors": {"navy": 1},
            "avoided_colors": {},
            "preferred_brands": {},
            "avoided_brands": {},
            "occasions": {},
            "fit_preferences": {},
            "gender": "male",
            "age": 25,
            "climate": "temperate",
            "style_vector": json.dumps(_quiz_vector(primary_cultural_ref="prep")),
            "refined_style_vector": json.dumps(refined),
        }

        prompt = build_system_prompt(profile, "")
        # Should show sport_street from refined vector, not prep from quiz vector
        assert "Sport/Street" in prompt or "sport_street" in prompt
