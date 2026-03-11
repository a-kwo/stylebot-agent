"""Test that every quiz image exists as a local file in static/quiz_images/."""

import os
from pathlib import Path

import pytest

from services.quiz_service import QUIZ_TREE, CHAT_QUESTIONS

PROJECT_ROOT = Path(__file__).parent.parent
QUIZ_IMAGES_DIR = PROJECT_ROOT / "static" / "quiz_images"


def _all_quiz_image_entries():
    """Yield (source, category, option_id, label, image_url) for every quiz image."""
    for node_id, node in QUIZ_TREE.items():
        for opt in node["options"]:
            yield "tree", node_id, opt["id"], opt["label"], opt["image_url"]

    for cat, question in CHAT_QUESTIONS.items():
        for opt in question["options"]:
            yield "chat", cat, opt["id"], opt["label"], opt["image_url"]


ALL_IMAGES = list(_all_quiz_image_entries())


@pytest.mark.parametrize(
    "source,category,option_id,label,image_url",
    ALL_IMAGES,
    ids=[f"{src}/{cat}/{oid}" for src, cat, oid, _, _ in ALL_IMAGES],
)
def test_image_file_exists(source, category, option_id, label, image_url):
    """Each quiz image URL must point to a local file that exists."""
    assert image_url.startswith("/static/quiz_images/"), (
        f"[{source}/{category}/{option_id}] '{label}' URL should start with "
        f"/static/quiz_images/, got: {image_url}"
    )
    # Extract relative path from URL
    rel_path = image_url.lstrip("/")
    file_path = PROJECT_ROOT / rel_path
    assert file_path.exists(), (
        f"[{source}/{category}/{option_id}] '{label}' image file missing: {file_path}"
    )
    assert file_path.stat().st_size > 0, (
        f"[{source}/{category}/{option_id}] '{label}' image file is empty: {file_path}"
    )


def test_unique_image_counts():
    """Correct number of unique images across both structures."""
    tree_urls = set()
    for node in QUIZ_TREE.values():
        for opt in node["options"]:
            url = opt["image_url"]
            assert url.startswith("/static/quiz_images/"), (
                f"{opt['id']}: URL should start with /static/quiz_images/"
            )
            tree_urls.add(url)

    chat_urls = set()
    for cat_data in CHAT_QUESTIONS.values():
        for opt in cat_data["options"]:
            url = opt["image_url"]
            assert url.startswith("/static/quiz_images/"), (
                f"{opt['id']}: URL should start with /static/quiz_images/"
            )
            chat_urls.add(url)

    assert len(tree_urls) >= 100, f"Expected at least 100 unique tree URLs, got {len(tree_urls)}"
    assert len(chat_urls) == 24, f"Expected 24 unique chat URLs, got {len(chat_urls)}"

    # No overlap between tree and chat
    overlap = tree_urls & chat_urls
    assert len(overlap) == 0, f"Tree and chat share {len(overlap)} URLs"
