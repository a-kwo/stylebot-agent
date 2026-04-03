"""Tests verifying quiz answers are properly reflected in agent recommendations.

Two layers tested:
1. System prompt inclusion — quiz data appears verbatim in the prompt sent to Claude.
2. Search query alignment — mocked agent turn uses quiz-derived terms in tool calls.
"""

import json
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from agent.system_prompt import build_system_prompt
from services.profile_service import get_profile, update_profile


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_db(style_quiz=None, style_vector=None, style_adjectives=None,
             gender="male", budget_min=0, budget_max=300):
    """In-memory SQLite DB with one user whose profile reflects quiz answers."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE profiles (
            user_id           INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives  TEXT DEFAULT '{}',
            preferred_colors  TEXT DEFAULT '{}',
            avoided_colors    TEXT DEFAULT '{}',
            preferred_brands  TEXT DEFAULT '{}',
            avoided_brands    TEXT DEFAULT '{}',
            size_tops         TEXT,
            size_bottoms      TEXT,
            size_shoes        TEXT,
            budget_min        INTEGER DEFAULT 0,
            budget_max        INTEGER DEFAULT 500,
            occasions         TEXT DEFAULT '{}',
            fit_preferences   TEXT DEFAULT '{}',
            notes             TEXT DEFAULT '',
            gender            TEXT,
            age               INTEGER,
            climate           TEXT,
            onboarded         INTEGER DEFAULT 0,
            style_quiz        TEXT DEFAULT '[]',
            style_vector      TEXT DEFAULT '{}',
            refined_style_vector TEXT DEFAULT '{}',
            updated_at        TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            category TEXT,
            color TEXT,
            brand TEXT
        );
        CREATE TABLE recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_title TEXT,
            feedback TEXT,
            price TEXT,
            category TEXT,
            seller TEXT,
            color TEXT,
            search_query TEXT,
            image_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", "fakehash"),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        """INSERT INTO profiles
           (user_id, gender, style_quiz, style_vector, style_adjectives, budget_min, budget_max)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            gender,
            json.dumps(style_quiz or []),
            json.dumps(style_vector or {}),
            json.dumps(style_adjectives or {}),
            budget_min,
            budget_max,
        ),
    )
    conn.commit()
    return conn, user_id


MINIMALIST_QUIZ = [
    {"node": "root_m", "choice": "clean_basic_m", "style_tags": ["minimalist", "clean", "logo-free"]},
    {"node": "sub_clean_m", "choice": "neutral_m", "style_tags": ["neutral-palette", "muted-tones"]},
    {"node": "var_neutral_m", "choice": "linen_m", "style_tags": ["linen", "cotton"]},
    {"node": "color_m", "choice": "cool_m", "style_tags": ["cool-tones", "charcoal", "navy"]},
    {"node": "fit_m", "choice": "relaxed_m", "style_tags": ["relaxed", "unstructured"]},
]

STREETWEAR_QUIZ = [
    {"node": "root_m", "choice": "sport_street_m", "style_tags": ["streetwear", "urban", "bold"]},
    {"node": "sub_street_m", "choice": "graphic_m", "style_tags": ["graphic-print", "oversized"]},
    {"node": "var_graphic_m", "choice": "hoodie_m", "style_tags": ["hoodie", "crewneck"]},
    {"node": "color_m", "choice": "dark_m", "style_tags": ["dark-palette", "all-black"]},
    {"node": "fit_m", "choice": "oversized_m", "style_tags": ["oversized", "dropped-shoulder"]},
]

MINIMALIST_VECTOR = {
    "energy": 0.2,
    "primary_cultural_ref": "clean_basic",
    "cultural_ref": {"clean_basic": 0.8, "prep": 0.2, "sport_street": 0.0, "utility": 0.0},
    "silhouette": {"structured": 0.1, "relaxed": 0.7, "oversized": 0.2},
    "color": {"temperature": -0.5, "range": 0.3, "expression": 0.2},
}

STREETWEAR_VECTOR = {
    "energy": 0.85,
    "primary_cultural_ref": "sport_street",
    "cultural_ref": {"sport_street": 0.9, "prep": 0.0, "clean_basic": 0.1, "utility": 0.0, "vintage_street": 0.0},
    "silhouette": {"structured": 0.0, "relaxed": 0.2, "oversized": 0.8},
    "color": {"temperature": -0.6, "range": 0.8, "expression": 0.9},
}

VINTAGE_STREET_VECTOR = {
    "energy": 0.55,
    "primary_cultural_ref": "vintage_street",
    "cultural_ref": {"sport_street": 0.0, "prep": 0.0, "clean_basic": 0.0, "utility": 0.0, "vintage_street": 0.9},
    "silhouette": {"structured": 0.0, "relaxed": 0.5, "oversized": 0.5},
    "color": {"temperature": 0.1, "range": 0.6, "expression": 0.5},
}


# ── Layer 1: System Prompt Inclusion ─────────────────────────────────────────

class TestSystemPromptIncludesQuizAnswers:
    """Quiz answers must appear in the system prompt sent to Claude."""

    def test_quiz_section_present_in_prompt(self):
        conn, user_id = _make_db(style_quiz=MINIMALIST_QUIZ)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "Style Quiz Answers" in prompt

    def test_minimalist_style_tags_in_prompt(self):
        conn, user_id = _make_db(style_quiz=MINIMALIST_QUIZ)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # Tags from quiz choices should appear somewhere in the quiz section
        assert "minimalist" in prompt.lower() or "clean_basic" in prompt.lower() or "logo-free" in prompt.lower()

    def test_streetwear_style_tags_in_prompt(self):
        conn, user_id = _make_db(style_quiz=STREETWEAR_QUIZ)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "streetwear" in prompt.lower() or "sport_street" in prompt.lower() or "graphic-print" in prompt.lower()

    def test_empty_quiz_shows_none_yet(self):
        conn, user_id = _make_db(style_quiz=[])
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "None yet" in prompt

    def test_multiple_quiz_nodes_all_appear(self):
        """All 5 quiz answers should be represented in the prompt."""
        conn, user_id = _make_db(style_quiz=MINIMALIST_QUIZ)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # Each answer's node id should appear
        for answer in MINIMALIST_QUIZ:
            assert answer["node"] in prompt, f"Node {answer['node']} missing from prompt"

    def test_different_quiz_answers_produce_different_prompts(self):
        conn1, uid1 = _make_db(style_quiz=MINIMALIST_QUIZ)
        conn2, uid2 = _make_db(style_quiz=STREETWEAR_QUIZ)
        prompt1 = build_system_prompt(get_profile(uid1, conn1), "", uid1, conn1)
        prompt2 = build_system_prompt(get_profile(uid2, conn2), "", uid2, conn2)
        assert prompt1 != prompt2


class TestSystemPromptIncludesStyleVector:
    """Style vector (computed from quiz) must surface in the prompt."""

    def test_minimalist_vector_energy_in_prompt(self):
        conn, user_id = _make_db(style_vector=MINIMALIST_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # Energy 0.2 → "quiet"
        assert "quiet" in prompt or "0.20" in prompt

    def test_minimalist_cultural_ref_in_prompt(self):
        conn, user_id = _make_db(style_vector=MINIMALIST_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "Clean Basic" in prompt or "clean_basic" in prompt

    def test_streetwear_cultural_ref_in_prompt(self):
        conn, user_id = _make_db(style_vector=STREETWEAR_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "Sport/Street" in prompt or "sport_street" in prompt

    def test_vector_section_absent_without_primary_ref(self):
        """An empty vector should show 'Not completed yet'."""
        conn, user_id = _make_db(style_vector={})
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "Not completed yet" in prompt

    def test_search_guidance_present_for_minimalist(self):
        conn, user_id = _make_db(style_vector=MINIMALIST_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # Search Guidance section should appear with brands from style_translator
        assert "Search Guidance" in prompt
        # clean_basic brands: Uniqlo, COS, Everlane, Muji
        assert any(brand in prompt for brand in ["Uniqlo", "COS", "Everlane", "Muji"])

    def test_search_guidance_brands_differ_between_styles(self):
        conn1, uid1 = _make_db(style_vector=MINIMALIST_VECTOR)
        conn2, uid2 = _make_db(style_vector=STREETWEAR_VECTOR)
        prompt1 = build_system_prompt(get_profile(uid1, conn1), "", uid1, conn1)
        prompt2 = build_system_prompt(get_profile(uid2, conn2), "", uid2, conn2)
        # Minimalist → Uniqlo/COS; Streetwear → Nike/Jordan/Stussy
        assert "Uniqlo" in prompt1 or "COS" in prompt1
        assert "Nike" in prompt2 or "Jordan" in prompt2 or "Stussy" in prompt2

    def test_fit_guidance_relaxed_for_minimalist(self):
        conn, user_id = _make_db(style_vector=MINIMALIST_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # silhouette: relaxed dominant → relaxed fit guidance
        assert "relaxed" in prompt.lower()

    def test_fit_guidance_oversized_for_streetwear(self):
        conn, user_id = _make_db(style_vector=STREETWEAR_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "oversized" in prompt.lower()

    def test_color_guidance_cool_for_minimalist(self):
        conn, user_id = _make_db(style_vector=MINIMALIST_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        # temperature: -0.5 → cool palette
        assert "cool" in prompt.lower() or "navy" in prompt.lower() or "charcoal" in prompt.lower()


# ── Layer 2: Agent Turn Uses Quiz-Derived Terms ───────────────────────────────

def _make_mock_final_response(text="Here are some options."):
    """Build a mock Anthropic response that ends the turn with text."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def _make_mock_tool_then_end(tool_name, tool_input, tool_result_json, final_text="Done."):
    """Build two mock responses: first a tool_use, then end_turn."""
    # First response: tool use
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = tool_name
    tool_block.input = tool_input
    tool_block.id = "tool_call_1"

    first_response = MagicMock()
    first_response.stop_reason = "tool_use"
    first_response.content = [tool_block]

    # Second response: end turn
    second_response = _make_mock_final_response(final_text)
    return first_response, second_response


def _make_db_with_conversations():
    """DB with conversations and conversation_summaries tables for agent loop."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE profiles (
            user_id           INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives  TEXT DEFAULT '{}',
            preferred_colors  TEXT DEFAULT '{}',
            avoided_colors    TEXT DEFAULT '{}',
            preferred_brands  TEXT DEFAULT '{}',
            avoided_brands    TEXT DEFAULT '{}',
            size_tops         TEXT,
            size_bottoms      TEXT,
            size_shoes        TEXT,
            budget_min        INTEGER DEFAULT 0,
            budget_max        INTEGER DEFAULT 300,
            occasions         TEXT DEFAULT '{}',
            fit_preferences   TEXT DEFAULT '{}',
            notes             TEXT DEFAULT '',
            gender            TEXT DEFAULT 'male',
            age               INTEGER,
            climate           TEXT,
            onboarded         INTEGER DEFAULT 1,
            style_quiz        TEXT DEFAULT '[]',
            style_vector      TEXT DEFAULT '{}',
            refined_style_vector TEXT DEFAULT '{}',
            updated_at        TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, name TEXT, category TEXT, color TEXT, brand TEXT
        );
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, role TEXT, content TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE conversation_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, summary TEXT, messages_up_to INTEGER
        );
        CREATE TABLE recommendation_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, product_title TEXT, feedback TEXT,
            price TEXT, category TEXT, seller TEXT, color TEXT,
            search_query TEXT, image_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, name TEXT, items TEXT
        );
    """)
    conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", "fakehash"),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    return conn, user_id


class TestAgentTurnUsesQuizData:
    """The system prompt passed to Claude during a turn must encode quiz data."""

    def test_system_prompt_in_agent_call_contains_quiz_tags(self):
        """After onboarding, run_agent_turn must pass a system prompt with quiz tags."""
        from agent.loop import run_agent_turn

        conn, user_id = _make_db_with_conversations()
        conn.execute(
            "UPDATE profiles SET style_quiz = ?, style_vector = ?, onboarded = 1 WHERE user_id = ?",
            (json.dumps(MINIMALIST_QUIZ), json.dumps(MINIMALIST_VECTOR), user_id),
        )
        conn.commit()

        captured_system = {}

        def capture_create(**kwargs):
            captured_system["prompt"] = kwargs.get("system", "")
            return _make_mock_final_response("Here are some minimal suggestions.")

        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.side_effect = capture_create
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(user_id, "Show me some outfit ideas", conn)

        prompt = captured_system.get("prompt", "")
        assert "minimalist" in prompt.lower() or "clean_basic" in prompt.lower(), (
            "System prompt should contain minimalist/clean_basic from quiz"
        )

    def test_system_prompt_contains_vector_brands_for_minimalist(self):
        """Minimalist vector → Uniqlo/COS brands must appear in system prompt."""
        from agent.loop import run_agent_turn

        conn, user_id = _make_db_with_conversations()
        conn.execute(
            "UPDATE profiles SET style_quiz = ?, style_vector = ?, onboarded = 1 WHERE user_id = ?",
            (json.dumps(MINIMALIST_QUIZ), json.dumps(MINIMALIST_VECTOR), user_id),
        )
        conn.commit()

        captured_system = {}

        def capture_create(**kwargs):
            captured_system["prompt"] = kwargs.get("system", "")
            return _make_mock_final_response("Here are some minimal suggestions.")

        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.side_effect = capture_create
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(user_id, "What should I buy?", conn)

        prompt = captured_system.get("prompt", "")
        assert any(brand in prompt for brand in ["Uniqlo", "COS", "Everlane", "Muji"]), (
            "Minimalist vector should inject clean_basic brands into system prompt"
        )

    def test_system_prompt_contains_vector_brands_for_streetwear(self):
        """Streetwear vector → Nike/Jordan/Stussy brands must appear in system prompt."""
        from agent.loop import run_agent_turn

        conn, user_id = _make_db_with_conversations()
        conn.execute(
            "UPDATE profiles SET style_quiz = ?, style_vector = ?, onboarded = 1 WHERE user_id = ?",
            (json.dumps(STREETWEAR_QUIZ), json.dumps(STREETWEAR_VECTOR), user_id),
        )
        conn.commit()

        captured_system = {}

        def capture_create(**kwargs):
            captured_system["prompt"] = kwargs.get("system", "")
            return _make_mock_final_response("Here are some streetwear picks.")

        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.side_effect = capture_create
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(user_id, "What should I buy?", conn)

        prompt = captured_system.get("prompt", "")
        assert any(brand in prompt for brand in ["Nike", "Jordan", "Stussy", "New Balance"]), (
            "Streetwear vector should inject sport_street brands into system prompt"
        )

    def test_no_onboarding_shows_empty_quiz_section(self):
        """A user who skipped the quiz should get 'None yet' in their system prompt."""
        from agent.loop import run_agent_turn

        conn, user_id = _make_db_with_conversations()
        # Leave style_quiz as default empty
        captured_system = {}

        def capture_create(**kwargs):
            captured_system["prompt"] = kwargs.get("system", "")
            return _make_mock_final_response("Let me ask you some questions first.")

        with patch("agent.loop.client") as mock_client:
            mock_client.messages.create.side_effect = capture_create
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(user_id, "Give me outfit ideas", conn)

        prompt = captured_system.get("prompt", "")
        assert "None yet" in prompt

    def test_minimalist_and_streetwear_produce_different_system_prompts(self):
        """Two users with different quiz results must receive different system prompts."""
        from agent.loop import run_agent_turn

        conn1, uid1 = _make_db_with_conversations()
        conn1.execute(
            "UPDATE profiles SET style_quiz = ?, style_vector = ?, onboarded = 1 WHERE user_id = ?",
            (json.dumps(MINIMALIST_QUIZ), json.dumps(MINIMALIST_VECTOR), uid1),
        )
        conn1.commit()

        conn2, uid2 = _make_db_with_conversations()
        conn2.execute(
            "UPDATE profiles SET style_quiz = ?, style_vector = ?, onboarded = 1 WHERE user_id = ?",
            (json.dumps(STREETWEAR_QUIZ), json.dumps(STREETWEAR_VECTOR), uid2),
        )
        conn2.commit()

        prompts = {}

        def capture1(**kwargs):
            prompts["minimalist"] = kwargs.get("system", "")
            return _make_mock_final_response()

        def capture2(**kwargs):
            prompts["streetwear"] = kwargs.get("system", "")
            return _make_mock_final_response()

        with patch("agent.loop.client") as mock1:
            mock1.messages.create.side_effect = capture1
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(uid1, "What should I buy?", conn1)

        with patch("agent.loop.client") as mock2:
            mock2.messages.create.side_effect = capture2
            with patch("agent.loop._reflect_on_turn"):
                with patch("agent.loop.maybe_refine_vector"):
                    run_agent_turn(uid2, "What should I buy?", conn2)

        assert prompts["minimalist"] != prompts["streetwear"], (
            "Different quiz answers must produce different system prompts"
        )


# ── Vintage/Streetwear dimension tests ───────────────────────────────────────

class TestVintageStreetVector:
    """vintage_street must surface as a distinct label and brand set in system prompts."""

    def test_vintage_street_cultural_ref_in_prompt(self):
        conn, user_id = _make_db(style_vector=VINTAGE_STREET_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert "Vintage" in prompt, (
            "System prompt should display 'Vintage/Streetwear' for vintage_street primary_cultural_ref"
        )

    def test_vintage_street_brands_in_prompt(self):
        conn, user_id = _make_db(style_vector=VINTAGE_STREET_VECTOR)
        profile = get_profile(user_id, conn)
        prompt = build_system_prompt(profile, "", user_id, conn)
        assert any(brand in prompt for brand in ["Champion", "Levi", "Carhartt", "Supreme", "Dickies"]), (
            "Vintage/Streetwear vector should inject vintage brands into system prompt"
        )

    def test_vintage_street_brands_differ_from_sport_street(self):
        conn1, uid1 = _make_db(style_vector=STREETWEAR_VECTOR)
        conn2, uid2 = _make_db(style_vector=VINTAGE_STREET_VECTOR)
        prompt1 = build_system_prompt(get_profile(uid1, conn1), "", uid1, conn1)
        prompt2 = build_system_prompt(get_profile(uid2, conn2), "", uid2, conn2)
        assert prompt1 != prompt2, (
            "sport_street and vintage_street vectors must produce different system prompts"
        )
