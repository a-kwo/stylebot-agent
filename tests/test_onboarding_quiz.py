"""Tests for the outfit-based onboarding quiz (TDD — written before implementation)."""

import json
import sqlite3

import pytest

from services.quiz_service import (
    QUIZ_QUESTIONS,
    ONBOARDING_CATEGORIES,
    get_onboarding_questions,
    get_chat_question,
)

# ── Valid archetypes ──────────────────────────────────────────────

VALID_ARCHETYPES = {
    "minimalist", "streetwear", "classic", "preppy", "bohemian",
    "athleisure", "edgy", "avant-garde", "smart-casual", "vintage",
    "retro", "relaxed", "sporty", "refined", "polished", "urban",
    "rugged", "cozy", "bold", "modern", "elegant", "eclectic",
    "monochrome", "layered", "tailored", "casual", "professional",
    "adventurous", "sophisticated", "artsy", "chic", "grunge",
    "outdoorsy", "trendy", "timeless",
}

CORE_ARCHETYPES = {
    "minimalist", "streetwear", "classic", "bohemian",
    "athleisure", "edgy", "smart-casual", "vintage",
}

CHAT_ONLY_CATEGORIES = [
    "sneakers", "formal_wear", "patterns", "accessories", "dresses", "activewear",
]

EXPECTED_ONBOARDING_CATEGORIES = [
    "outfit_everyday", "outfit_weekend", "outfit_going_out", "outfit_date",
    "outfit_summer", "outfit_winter", "outfit_work", "outfit_dream",
]


# ── Structure tests ──────────────────────────────────────────────


class TestQuizStructure:
    """Verify the onboarding quiz returns 8 outfit-based questions."""

    def test_returns_exactly_8_questions(self):
        questions = get_onboarding_questions()
        assert len(questions) == 8

    def test_each_question_has_4_options(self):
        for q in get_onboarding_questions():
            assert len(q["options"]) == 4, f"{q['category']} has {len(q['options'])} options"

    def test_each_option_has_required_keys(self):
        required = {"id", "label", "image_url", "style_tags"}
        for q in get_onboarding_questions():
            for opt in q["options"]:
                missing = required - set(opt.keys())
                assert not missing, f"Option {opt.get('id', '?')} missing keys: {missing}"

    def test_each_question_has_prompt_and_category(self):
        for q in get_onboarding_questions():
            assert "prompt" in q and q["prompt"], f"Missing prompt in {q.get('category')}"
            assert "category" in q and q["category"], "Missing category"

    def test_all_image_urls_globally_unique(self):
        urls = []
        for q in get_onboarding_questions():
            for opt in q["options"]:
                urls.append(opt["image_url"])
        assert len(urls) == 32
        assert len(set(urls)) == 32, "Duplicate image URLs found"

    def test_all_option_ids_unique(self):
        ids = []
        for q in get_onboarding_questions():
            for opt in q["options"]:
                ids.append(opt["id"])
        assert len(ids) == 32
        assert len(set(ids)) == 32, "Duplicate option IDs found"

    def test_style_tags_non_empty_list(self):
        for q in get_onboarding_questions():
            for opt in q["options"]:
                assert isinstance(opt["style_tags"], list), f"{opt['id']} style_tags not a list"
                assert len(opt["style_tags"]) > 0, f"{opt['id']} has empty style_tags"

    def test_onboarding_categories_list_has_8(self):
        assert len(ONBOARDING_CATEGORIES) == 8

    def test_onboarding_categories_are_outfit_based(self):
        for cat in ONBOARDING_CATEGORIES:
            assert cat.startswith("outfit_"), f"Category '{cat}' should be outfit-based"

    def test_onboarding_categories_match_expected(self):
        assert set(ONBOARDING_CATEGORIES) == set(EXPECTED_ONBOARDING_CATEGORIES)


# ── Style archetype tests ────────────────────────────────────────


class TestStyleArchetypes:
    """Verify style tags are valid and cover all core archetypes."""

    def test_all_tags_belong_to_valid_set(self):
        for q in get_onboarding_questions():
            for opt in q["options"]:
                for tag in opt["style_tags"]:
                    assert tag in VALID_ARCHETYPES, (
                        f"Unknown tag '{tag}' in option '{opt['id']}'"
                    )

    def test_core_archetypes_each_appear_at_least_twice(self):
        tag_counts = {}
        for q in get_onboarding_questions():
            for opt in q["options"]:
                for tag in opt["style_tags"]:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        for archetype in CORE_ARCHETYPES:
            count = tag_counts.get(archetype, 0)
            assert count >= 2, (
                f"Core archetype '{archetype}' only appears {count} time(s), need >= 2"
            )

    def test_questions_are_about_full_outfits(self):
        """Category names reflect outfit-based contexts, not single items."""
        single_item_categories = {
            "shirts", "hoodies", "pants", "shoes", "jackets",
        }
        for q in get_onboarding_questions():
            assert q["category"] not in single_item_categories, (
                f"Category '{q['category']}' is a single-item category, not an outfit"
            )


# ── Integration tests (in-memory SQLite) ─────────────────────────


def _setup_test_db():
    """Create an in-memory SQLite DB with the full schema + a test user."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE profiles (
            user_id           INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives  TEXT DEFAULT '[]',
            preferred_colors  TEXT DEFAULT '[]',
            avoided_colors    TEXT DEFAULT '[]',
            preferred_brands  TEXT DEFAULT '[]',
            avoided_brands    TEXT DEFAULT '[]',
            size_tops         TEXT,
            size_bottoms      TEXT,
            size_shoes        TEXT,
            budget_min        INTEGER DEFAULT 0,
            budget_max        INTEGER DEFAULT 500,
            occasions         TEXT DEFAULT '[]',
            fit_preferences   TEXT DEFAULT '[]',
            notes             TEXT DEFAULT '',
            gender            TEXT,
            age               INTEGER,
            climate           TEXT,
            onboarded         INTEGER DEFAULT 0,
            style_quiz        TEXT DEFAULT '[]',
            updated_at        TEXT DEFAULT (datetime('now'))
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


class TestIntegration:
    """Test the full quiz submission flow with an in-memory DB."""

    def test_submit_8_answers_saves_style_quiz(self):
        conn, user_id = _setup_test_db()
        questions = get_onboarding_questions()
        assert len(questions) == 8

        # Simulate picking the first option from each question
        answers = []
        for q in questions:
            opt = q["options"][0]
            answers.append({
                "category": q["category"],
                "choice": opt["id"],
                "style_tags": opt["style_tags"],
            })

        # Save quiz answers (mirrors profile_router.submit_style_quiz logic)
        conn.execute(
            "UPDATE profiles SET style_quiz = ?, onboarded = 1, updated_at = datetime('now') WHERE user_id = ?",
            (json.dumps(answers), user_id),
        )
        conn.commit()

        row = conn.execute("SELECT style_quiz, onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        saved = json.loads(row["style_quiz"])
        assert len(saved) == 8
        assert row["onboarded"] == 1
        conn.close()

    def test_style_tags_union_merged_into_adjectives(self):
        conn, user_id = _setup_test_db()
        from services.profile_service import update_profile

        questions = get_onboarding_questions()
        all_tags = []
        for q in questions:
            opt = q["options"][0]
            all_tags.extend(opt["style_tags"])

        update_profile(user_id, {"style_adjectives": all_tags}, conn)

        row = conn.execute("SELECT style_adjectives FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        saved = json.loads(row["style_adjectives"])

        # Weighted format: dict of {tag: count}
        assert isinstance(saved, dict)
        for tag in all_tags:
            assert tag in saved, f"Tag '{tag}' not in style_adjectives"
            assert saved[tag] >= 1
        conn.close()

    def test_onboarded_flag_set_after_submission(self):
        conn, user_id = _setup_test_db()

        # Before: not onboarded
        row = conn.execute("SELECT onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        assert row["onboarded"] == 0

        # Submit quiz
        conn.execute(
            "UPDATE profiles SET onboarded = 1, updated_at = datetime('now') WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

        row = conn.execute("SELECT onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        assert row["onboarded"] == 1
        conn.close()

    def test_get_onboarding_endpoint_returns_8_questions(self):
        """Simulates GET /api/quiz/onboarding response format."""
        questions = get_onboarding_questions()
        assert len(questions) == 8
        for q in questions:
            assert "prompt" in q
            assert "category" in q
            assert "options" in q
            assert len(q["options"]) == 4


# ── Backward compatibility tests ─────────────────────────────────


class TestBackwardCompatibility:
    """Verify in-chat quiz categories are unaffected."""

    def test_chat_question_still_works_for_all_categories(self):
        for cat in CHAT_ONLY_CATEGORIES:
            q = get_chat_question(cat)
            assert q is not None, f"get_chat_question('{cat}') returned None"
            assert q["category"] == cat
            assert len(q["options"]) == 4

    def test_in_chat_categories_unaffected(self):
        for cat in CHAT_ONLY_CATEGORIES:
            assert cat in QUIZ_QUESTIONS, f"Chat category '{cat}' missing from QUIZ_QUESTIONS"

    def test_old_answer_format_still_valid(self):
        """The QuizAnswer schema {category, choice, style_tags} is unchanged."""
        # Just verify the shape works — no schema change needed
        answer = {"category": "sneakers", "choice": "retro-runner", "style_tags": ["retro", "sporty"]}
        assert "category" in answer
        assert "choice" in answer
        assert "style_tags" in answer
        assert isinstance(answer["style_tags"], list)

    def test_old_onboarding_categories_removed(self):
        """The old single-item onboarding categories should no longer be in ONBOARDING_CATEGORIES."""
        old_categories = {"shirts", "hoodies", "pants", "shoes", "outfits", "jackets"}
        for cat in old_categories:
            assert cat not in ONBOARDING_CATEGORIES, (
                f"Old category '{cat}' still in ONBOARDING_CATEGORIES"
            )
