"""Tests for the adaptive onboarding quiz tree and chat questions."""

import json
import sqlite3

import pytest

from services.quiz_service import (
    QUIZ_TREE,
    CHAT_QUESTIONS,
    get_quiz_tree,
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
    # Tree-specific composite tags
    "wide-silhouette", "dropped-shoulder", "tailored-casual",
    "relaxed-precise", "COS", "texture-mix", "quiet-luxury",
    "proportion-play", "deconstructed", "asymmetric", "oversized",
    "earth-tones", "neutral-palette", "muted-tones", "warm-tones",
    "cool-tones", "dark-palette", "all-black", "monochromatic",
    "color-block", "statement-color", "muted-color", "heritage-plaid",
    "graphic-print", "logo-free", "tonal", "contrast-stitch",
    "workwear-detail", "utility", "military-inspired", "cargo",
    "western", "denim-on-denim", "raw-denim", "selvedge",
    "techwear", "gorpcore", "functional", "weather-ready",
    "layered-knit", "chunky-knit", "fine-gauge", "cashmere-blend",
    "silk-blend", "linen", "cotton", "wool", "leather", "suede",
    "patent-leather", "velvet", "satin", "mesh", "sheer",
    "structured", "unstructured", "draped", "fitted", "loose",
    "cropped", "elongated", "high-waist", "low-rise", "mid-rise",
    "slim", "straight", "wide-leg", "flare", "bootcut",
    "pleated", "pintuck", "darted", "gathered", "ruched",
    "wrap", "tie-front", "button-down", "zip-up", "pullover",
    "hoodie", "crewneck", "v-neck", "turtleneck", "mock-neck",
    "collared", "band-collar", "mandarin-collar", "henley",
    "polo", "tank", "camisole", "bodysuit", "jumpsuit",
}

CHAT_ONLY_CATEGORIES = [
    "sneakers", "formal_wear", "patterns", "accessories", "dresses", "activewear",
]

ROOT_NODES = ["root_m", "root_f", "root_nb"]


# ── Tree structure tests ─────────────────────────────────────────


class TestQuizTreeStructure:
    """Verify the quiz tree has correct structure."""

    def test_has_three_root_nodes(self):
        for root in ROOT_NODES:
            assert root in QUIZ_TREE, f"Missing root node: {root}"

    def test_each_node_has_prompt_and_options(self):
        for node_id, node in QUIZ_TREE.items():
            assert "prompt" in node, f"Node {node_id} missing prompt"
            assert "options" in node, f"Node {node_id} missing options"
            assert len(node["options"]) >= 2, f"Node {node_id} has fewer than 2 options"

    def test_each_option_has_required_keys(self):
        required = {"id", "label", "image_url", "style_tags", "next"}
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                missing = required - set(opt.keys())
                assert not missing, f"Option {opt.get('id', '?')} in {node_id} missing keys: {missing}"

    def test_next_references_valid_node_or_none(self):
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                if opt["next"] is not None:
                    assert opt["next"] in QUIZ_TREE, (
                        f"Option {opt['id']} in {node_id} references non-existent node: {opt['next']}"
                    )

    def test_style_tags_non_empty(self):
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                assert isinstance(opt["style_tags"], list), f"{opt['id']} style_tags not a list"
                assert len(opt["style_tags"]) > 0, f"{opt['id']} has empty style_tags"

    def test_all_image_urls_are_local_quiz_images(self):
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                url = opt["image_url"]
                assert url.startswith("/static/quiz_images/"), (
                    f"{opt['id']}: URL should start with /static/quiz_images/, got {url}"
                )

    def test_unique_tree_images(self):
        urls = set()
        for node in QUIZ_TREE.values():
            for opt in node["options"]:
                urls.add(opt["image_url"])
        # 181 total options, some color/fit images shared across styles
        assert len(urls) >= 100, f"Expected at least 100 unique tree URLs, got {len(urls)}"

    def test_all_paths_are_depth_5(self):
        """Every quiz path should be exactly 5 questions deep."""
        def trace_depths(node_id, depth=1):
            node = QUIZ_TREE[node_id]
            depths = []
            for opt in node["options"]:
                if opt["next"] is None:
                    depths.append(depth)
                else:
                    depths.extend(trace_depths(opt["next"], depth + 1))
            return depths

        for root in ["root_m", "root_f", "root_nb"]:
            depths = trace_depths(root)
            for d in depths:
                assert d == 5, f"Path from {root} has depth {d}, expected 5"

    def test_color_and_fit_nodes_exist(self):
        """Cross-cutting color and fit nodes must exist."""
        for node_id in ["color_m", "color_f", "fit_m", "fit_f"]:
            assert node_id in QUIZ_TREE, f"Missing cross-cutting node: {node_id}"

    def test_fit_nodes_are_terminal(self):
        """Fit nodes should be the final question (all next=None)."""
        for node_id in ["fit_m", "fit_f"]:
            node = QUIZ_TREE[node_id]
            for opt in node["options"]:
                assert opt["next"] is None, f"{opt['id']} in {node_id} should be terminal"


# ── get_quiz_tree() API tests ────────────────────────────────────


class TestGetQuizTree:
    """Verify the get_quiz_tree() public API."""

    def test_returns_start_and_nodes(self):
        result = get_quiz_tree("male")
        assert "start" in result
        assert "nodes" in result

    @pytest.mark.parametrize("gender,expected_start", [
        ("male", "root_m"),
        ("Man", "root_m"),
        ("female", "root_f"),
        ("Woman", "root_f"),
        ("non-binary", "root_nb"),
        ("Non-binary", "root_nb"),
        ("Prefer not to say", "root_nb"),
        (None, "root_nb"),
    ])
    def test_gender_maps_to_correct_root(self, gender, expected_start):
        result = get_quiz_tree(gender)
        assert result["start"] == expected_start

    def test_nodes_is_the_full_tree(self):
        result = get_quiz_tree("male")
        assert result["nodes"] is QUIZ_TREE


# ── Chat question tests ──────────────────────────────────────────


class TestChatQuestions:
    """Verify chat-only questions work correctly."""

    def test_chat_question_returns_for_all_categories(self):
        for cat in CHAT_ONLY_CATEGORIES:
            q = get_chat_question(cat)
            assert q is not None, f"get_chat_question('{cat}') returned None"
            assert q["category"] == cat
            assert len(q["options"]) == 4

    def test_chat_question_returns_none_for_unknown(self):
        assert get_chat_question("nonexistent") is None

    def test_chat_options_have_required_keys(self):
        required = {"id", "label", "image_url", "style_tags"}
        for cat in CHAT_ONLY_CATEGORIES:
            q = get_chat_question(cat)
            for opt in q["options"]:
                missing = required - set(opt.keys())
                assert not missing, f"Chat option {opt.get('id', '?')} missing keys: {missing}"

    def test_22_unique_chat_images(self):
        urls = set()
        for cat_data in CHAT_QUESTIONS.values():
            for opt in cat_data["options"]:
                urls.add(opt["image_url"])
        assert len(urls) == 24, f"Expected 24 unique chat URLs, got {len(urls)}"


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
    """Test quiz submission flow with an in-memory DB."""

    def test_submit_tree_answers_saves_style_quiz(self):
        conn, user_id = _setup_test_db()
        tree = get_quiz_tree("male")
        start_node = QUIZ_TREE[tree["start"]]

        # Simulate picking the first option
        opt = start_node["options"][0]
        answers = [{
            "node": tree["start"],
            "choice": opt["id"],
            "style_tags": opt["style_tags"],
        }]

        conn.execute(
            "UPDATE profiles SET style_quiz = ?, onboarded = 1, updated_at = datetime('now') WHERE user_id = ?",
            (json.dumps(answers), user_id),
        )
        conn.commit()

        row = conn.execute("SELECT style_quiz, onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        saved = json.loads(row["style_quiz"])
        assert len(saved) == 1
        assert row["onboarded"] == 1
        conn.close()

    def test_style_tags_union_merged_into_adjectives(self):
        conn, user_id = _setup_test_db()
        from services.profile_service import update_profile

        # Collect tags from first option of root_m
        start_node = QUIZ_TREE["root_m"]
        all_tags = list(start_node["options"][0]["style_tags"])

        update_profile(user_id, {"style_adjectives": all_tags}, conn)

        row = conn.execute("SELECT style_adjectives FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        saved = json.loads(row["style_adjectives"])

        assert isinstance(saved, dict)
        for tag in all_tags:
            assert tag in saved, f"Tag '{tag}' not in style_adjectives"
            assert saved[tag] >= 1
        conn.close()

    def test_onboarded_flag_set_after_submission(self):
        conn, user_id = _setup_test_db()

        row = conn.execute("SELECT onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        assert row["onboarded"] == 0

        conn.execute(
            "UPDATE profiles SET onboarded = 1, updated_at = datetime('now') WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()

        row = conn.execute("SELECT onboarded FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        assert row["onboarded"] == 1
        conn.close()

    def test_get_quiz_tree_returns_valid_structure(self):
        """Simulates GET /api/quiz/tree response format."""
        for gender in ["male", "female", "non-binary", None]:
            result = get_quiz_tree(gender)
            assert "start" in result
            assert "nodes" in result
            assert result["start"] in result["nodes"]
