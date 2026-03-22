"""Tests for behavioral reflection upgrade (Item 5)."""

import json
import sqlite3
import pytest
from unittest.mock import patch, MagicMock


# ── Tests for REFLECTION_PROMPT content ──────────────────────────────────────

class TestReflectionPrompt:
    """REFLECTION_PROMPT includes behavioral signal extraction."""

    def test_prompt_contains_behavioral_signals(self):
        from agent.loop import REFLECTION_PROMPT

        assert "behavioral_signals" in REFLECTION_PROMPT

    def test_prompt_contains_price_reaction(self):
        from agent.loop import REFLECTION_PROMPT

        assert "price_reaction" in REFLECTION_PROMPT

    def test_prompt_contains_category_interest(self):
        from agent.loop import REFLECTION_PROMPT

        assert "category_interest" in REFLECTION_PROMPT

    def test_prompt_contains_engagement_level(self):
        from agent.loop import REFLECTION_PROMPT

        assert "engagement_level" in REFLECTION_PROMPT


# ── Tests for _reflect_on_turn behavioral processing ────────────────────────

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
        notes TEXT,
        style_quiz TEXT DEFAULT '[]',
        style_vector TEXT DEFAULT '{}'
    )""")
    conn.execute("INSERT INTO profiles (user_id) VALUES (1)")
    conn.commit()
    return conn


class TestReflectOnTurnBehavioral:
    """_reflect_on_turn processes behavioral_signals from Claude response."""

    def test_behavioral_signals_written_as_notes(self):
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [],
                "preferred_colors": [],
                "avoided_colors": [],
                "preferred_brands": [],
                "avoided_brands": [],
                "occasions": [],
                "fit_preferences": [],
                "notes": "",
            },
            "has_updates": True,
            "behavioral_signals": {
                "price_reaction": "budget_conscious",
                "category_interest": ["outerwear", "boots"],
                "engagement_level": "high",
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test message", "test response", db)

                # Should have been called — at least once for behavioral signals
                assert mock_update.called
                # Find the behavioral call
                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "[behavioral]" in str(c)
                ]
                assert len(behavioral_calls) > 0, "Should write behavioral notes"

    def test_budget_conscious_note_content(self):
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
            "behavioral_signals": {
                "price_reaction": "budget_conscious",
                "category_interest": [],
                "engagement_level": None,
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test", "test", db)

                # Find behavioral call with budget_conscious
                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "budget_conscious" in str(c)
                ]
                assert len(behavioral_calls) > 0

    def test_category_interest_written(self):
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
            "behavioral_signals": {
                "price_reaction": None,
                "category_interest": ["sneakers", "jackets"],
                "engagement_level": None,
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test", "test", db)

                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "sneakers" in str(c) or "jackets" in str(c)
                ]
                assert len(behavioral_calls) > 0

    def test_medium_engagement_skipped(self):
        """engagement_level 'medium' should not produce a note."""
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
            "behavioral_signals": {
                "price_reaction": None,
                "category_interest": [],
                "engagement_level": "medium",
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test", "test", db)

                # No behavioral notes should be written for medium engagement only
                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "[behavioral]" in str(c)
                ]
                assert len(behavioral_calls) == 0

    def test_old_format_no_behavioral_signals_no_crash(self):
        """Response without behavioral_signals key should not crash."""
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                # Should not raise
                _reflect_on_turn(1, "test", "test", db)

    def test_null_signals_no_notes(self):
        """All-null behavioral signals should produce no notes."""
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
            "behavioral_signals": {
                "price_reaction": None,
                "category_interest": [],
                "engagement_level": None,
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test", "test", db)

                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "[behavioral]" in str(c)
                ]
                assert len(behavioral_calls) == 0

    def test_exception_in_parsing_silent(self):
        """Exception during reflection should be silently caught."""
        from agent.loop import _reflect_on_turn

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.side_effect = Exception("API error")
            # Should not raise
            _reflect_on_turn(1, "test", "test", db)

    def test_high_engagement_written(self):
        from agent.loop import _reflect_on_turn

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps({
            "profile_updates": {
                "style_adjectives": [], "preferred_colors": [], "avoided_colors": [],
                "preferred_brands": [], "avoided_brands": [],
                "occasions": [], "fit_preferences": [], "notes": "",
            },
            "has_updates": False,
            "behavioral_signals": {
                "price_reaction": None,
                "category_interest": [],
                "engagement_level": "high",
            },
        })

        db = _make_db()
        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.return_value = mock_response
            with patch("agent.loop.update_profile") as mock_update:
                _reflect_on_turn(1, "test", "test", db)

                behavioral_calls = [
                    c for c in mock_update.call_args_list
                    if "[behavioral]" in str(c) and "high" in str(c).lower()
                ]
                assert len(behavioral_calls) > 0
