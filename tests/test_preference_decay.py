"""Tests for preference decay and confidence scoring (Item 7)."""

import json
import sqlite3
import pytest
from datetime import datetime, timedelta


def _make_db():
    """Create in-memory DB with profiles table."""
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
        onboarded INTEGER DEFAULT 0,
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    return conn


# ── Tests for _apply_decay ──────────────────────────────────────────────────

class TestApplyDecay:
    """_apply_decay reduces weights over time and prunes low values."""

    def test_zero_days_no_change(self):
        from services.profile_service import _apply_decay

        weights = {"navy": 3.0, "black": 2.0}
        result = _apply_decay(weights, 0)
        assert result == {"navy": 3.0, "black": 2.0}

    def test_one_half_life_halves_weights(self):
        from services.profile_service import _apply_decay, DECAY_HALF_LIFE_DAYS

        weights = {"navy": 4.0, "black": 2.0}
        result = _apply_decay(weights, DECAY_HALF_LIFE_DAYS)
        assert abs(result["navy"] - 2.0) < 0.1
        assert abs(result["black"] - 1.0) < 0.1

    def test_prunes_below_threshold(self):
        from services.profile_service import _apply_decay, DECAY_HALF_LIFE_DAYS, MIN_WEIGHT

        weights = {"navy": 0.2}  # 0.2 * 0.5 = 0.1, at threshold
        result = _apply_decay(weights, DECAY_HALF_LIFE_DAYS)
        assert result.get("navy", 0) >= MIN_WEIGHT or "navy" not in result

        weights2 = {"faint": 0.15}  # 0.15 * 0.5 = 0.075, below threshold
        result2 = _apply_decay(weights2, DECAY_HALF_LIFE_DAYS)
        assert "faint" not in result2

    def test_empty_dict(self):
        from services.profile_service import _apply_decay

        assert _apply_decay({}, 90) == {}

    def test_negative_days_no_change(self):
        from services.profile_service import _apply_decay

        weights = {"navy": 3.0}
        result = _apply_decay(weights, -5)
        assert result == {"navy": 3.0}


# ── Tests for _migrate_weighted ──────────────────────────────────────────────

class TestMigrateWeighted:
    """_migrate_weighted converts arrays to weighted dicts."""

    def test_converts_array_to_dict(self):
        from services.profile_service import _migrate_weighted

        result = _migrate_weighted('["navy", "black"]')
        assert result == {"navy": 1, "black": 1}

    def test_preserves_existing_dict(self):
        from services.profile_service import _migrate_weighted

        result = _migrate_weighted('{"navy": 3, "black": 1}')
        assert result == {"navy": 3, "black": 1}


# ── Tests for WEIGHTED_FIELDS migration ──────────────────────────────────────

class TestWeightedFieldsMigration:
    """All former array fields are now in WEIGHTED_FIELDS."""

    def test_array_fields_is_empty(self):
        from services.profile_service import ARRAY_FIELDS

        assert ARRAY_FIELDS == []

    def test_weighted_fields_contains_all_preference_fields(self):
        from services.profile_service import WEIGHTED_FIELDS

        expected = [
            "style_adjectives", "preferred_colors", "avoided_colors",
            "preferred_brands", "avoided_brands", "occasions", "fit_preferences",
        ]
        for field in expected:
            assert field in WEIGHTED_FIELDS, f"{field} should be in WEIGHTED_FIELDS"


# ── Tests for get_profile with decay ─────────────────────────────────────────

class TestGetProfileWithDecay:
    """get_profile applies time decay to weighted fields."""

    def test_fresh_profile_no_decay(self):
        from services.profile_service import get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps({"navy": 3.0}),),
        )
        db.commit()

        profile = get_profile(1, db)
        assert abs(profile["preferred_colors"]["navy"] - 3.0) < 0.1

    def test_old_profile_decayed(self):
        from services.profile_service import get_profile, DECAY_HALF_LIFE_DAYS

        db = _make_db()
        old_date = (datetime.now() - timedelta(days=DECAY_HALF_LIFE_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, ?)",
            (json.dumps({"navy": 4.0}), old_date),
        )
        db.commit()

        profile = get_profile(1, db)
        assert profile["preferred_colors"]["navy"] < 4.0, "Old preferences should decay"
        assert abs(profile["preferred_colors"]["navy"] - 2.0) < 0.2

    def test_old_array_format_auto_migrates(self):
        from services.profile_service import get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps(["navy", "black"]),),
        )
        db.commit()

        profile = get_profile(1, db)
        assert isinstance(profile["preferred_colors"], dict)
        assert "navy" in profile["preferred_colors"]


# ── Tests for update_profile with decrements ─────────────────────────────────

class TestUpdateProfileDecrement:
    """update_profile supports decrement_<field> keys."""

    def test_decrement_reduces_weight(self):
        from services.profile_service import update_profile, get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps({"navy": 3.0, "black": 2.0}),),
        )
        db.commit()

        update_profile(1, {"decrement_preferred_colors": ["navy"]}, db)
        profile = get_profile(1, db)
        assert profile["preferred_colors"]["navy"] < 3.0

    def test_decrement_prunes_at_zero(self):
        from services.profile_service import update_profile, get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps({"red": 1.0}),),
        )
        db.commit()

        update_profile(1, {"decrement_preferred_colors": ["red"]}, db)
        profile = get_profile(1, db)
        assert "red" not in profile["preferred_colors"]

    def test_decrement_nonexistent_key_no_crash(self):
        from services.profile_service import update_profile, get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps({"navy": 2.0}),),
        )
        db.commit()

        # Should not crash
        update_profile(1, {"decrement_preferred_colors": ["pink"]}, db)
        profile = get_profile(1, db)
        assert "navy" in profile["preferred_colors"]

    def test_increment_weighted_field(self):
        from services.profile_service import update_profile, get_profile

        db = _make_db()
        db.execute(
            "INSERT INTO profiles (user_id, preferred_colors, updated_at) VALUES (1, ?, datetime('now'))",
            (json.dumps({"navy": 1.0}),),
        )
        db.commit()

        update_profile(1, {"preferred_colors": ["navy"]}, db)
        profile = get_profile(1, db)
        assert profile["preferred_colors"]["navy"] > 1.0


# ── Tests for system prompt rendering ────────────────────────────────────────

class TestSystemPromptWeightedRendering:
    """System prompt uses _fmt_weighted for all preference fields."""

    def test_preferred_colors_rendered_weighted(self):
        from agent.system_prompt import build_system_prompt

        profile = {
            "preferred_colors": {"navy": 5, "black": 1},
            "avoided_colors": {},
            "preferred_brands": {},
            "avoided_brands": {},
            "occasions": {},
            "fit_preferences": {},
            "style_adjectives": {"minimalist": 3},
            "gender": "male",
            "age": 25,
            "climate": "temperate",
        }

        prompt = build_system_prompt(profile, "")

        # Should show weighted format, not comma-separated list
        assert "strong" in prompt or "moderate" in prompt or "mild" in prompt
        assert "navy" in prompt
