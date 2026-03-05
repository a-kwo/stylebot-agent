"""Test that every quiz image URL returns a valid image (HTTP 200 + image content-type)."""

import urllib.request
import pytest

from services.quiz_service import QUIZ_QUESTIONS, ONBOARDING_CATEGORIES


def _check_image_url(url: str, timeout: int = 15) -> tuple[int, str, int]:
    """GET-request the URL; return (status_code, content_type, bytes_read)."""
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "Mozilla/5.0 (StyleBot-Test)")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        return exc.code, "", 0
    content_type = resp.headers.get("Content-Type", "")
    # Read a small chunk to confirm it's real image data
    data = resp.read(16)
    resp.close()
    return resp.getcode(), content_type, len(data)


def _all_quiz_image_entries():
    """Yield (category, option_id, label, image_url) for every quiz option."""
    for cat, question in QUIZ_QUESTIONS.items():
        for opt in question["options"]:
            yield cat, opt["id"], opt["label"], opt["image_url"]


# ── Parametrized test: one test case per image ───────────────────


ALL_IMAGES = list(_all_quiz_image_entries())


@pytest.mark.parametrize(
    "category,option_id,label,image_url",
    ALL_IMAGES,
    ids=[f"{cat}/{oid}" for cat, oid, _, _ in ALL_IMAGES],
)
def test_image_loads_successfully(category, option_id, label, image_url):
    """Each quiz image URL must return HTTP 200 with an image content-type."""
    status, content_type, data_len = _check_image_url(image_url)
    assert status == 200, f"[{category}/{option_id}] '{label}' returned HTTP {status}"
    assert "image" in content_type.lower(), (
        f"[{category}/{option_id}] '{label}' returned content-type '{content_type}', expected image/*"
    )
    assert data_len > 0, f"[{category}/{option_id}] '{label}' returned empty body"


# ── Onboarding-specific: all 8 categories × 4 options = 32 images ─


def test_onboarding_has_32_valid_image_urls():
    """Quick smoke test: exactly 32 onboarding images, all are https URLs."""
    urls = []
    for cat in ONBOARDING_CATEGORIES:
        q = QUIZ_QUESTIONS[cat]
        for opt in q["options"]:
            url = opt["image_url"]
            assert url.startswith("https://"), f"{opt['id']}: URL doesn't start with https://"
            assert "unsplash.com" in url, f"{opt['id']}: URL not from Unsplash"
            urls.append(url)
    assert len(urls) == 32
    assert len(set(urls)) == 32, "Duplicate image URLs in onboarding"
