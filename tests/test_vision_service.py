"""Tests for Google Cloud Vision API image validation service (TDD — written before implementation)."""

from unittest.mock import MagicMock, patch
import pytest

from services.vision_service import (
    VISION_LABEL_TO_STYLE,
    analyze_image,
    extract_style_signals,
    score_image_match,
    search_replacement_image,
)


# ── Label mapping tests ─────────────────────────────────────────


class TestVisionLabelMapping:
    """Verify VISION_LABEL_TO_STYLE maps known labels to style tags."""

    def test_known_labels_map_correctly(self):
        assert "streetwear" in VISION_LABEL_TO_STYLE.get("Street fashion", [])
        assert "classic" in VISION_LABEL_TO_STYLE.get("Formal wear", [])
        assert "athleisure" in VISION_LABEL_TO_STYLE.get("Sportswear", [])

    def test_unknown_labels_return_empty(self):
        assert VISION_LABEL_TO_STYLE.get("xyzzy_not_real", []) == []

    def test_case_sensitive_keys(self):
        # Keys in the mapping are title-case as Vision API returns them
        for key in VISION_LABEL_TO_STYLE:
            assert isinstance(key, str)
            assert len(VISION_LABEL_TO_STYLE[key]) > 0

    def test_mapping_values_are_lists_of_strings(self):
        for key, tags in VISION_LABEL_TO_STYLE.items():
            assert isinstance(tags, list), f"Value for '{key}' is not a list"
            for tag in tags:
                assert isinstance(tag, str), f"Tag '{tag}' in '{key}' is not a string"


# ── extract_style_signals tests ──────────────────────────────────


class TestExtractStyleSignals:
    """Verify extraction from Vision API response structure."""

    def test_extracts_from_label_annotations(self):
        response = {
            "labelAnnotations": [
                {"description": "Street fashion", "score": 0.9},
                {"description": "Jacket", "score": 0.85},
            ],
            "webDetection": {"webEntities": []},
        }
        signals = extract_style_signals(response)
        assert "streetwear" in signals or "urban" in signals

    def test_extracts_from_web_entities(self):
        response = {
            "labelAnnotations": [],
            "webDetection": {
                "webEntities": [
                    {"description": "Formal wear", "score": 0.8},
                ]
            },
        }
        signals = extract_style_signals(response)
        assert "classic" in signals or "professional" in signals

    def test_deduplicates_signals(self):
        response = {
            "labelAnnotations": [
                {"description": "Formal wear", "score": 0.9},
            ],
            "webDetection": {
                "webEntities": [
                    {"description": "Formal wear", "score": 0.8},
                ]
            },
        }
        signals = extract_style_signals(response)
        # Should be a set, no duplicates by definition
        assert isinstance(signals, set)

    def test_filters_low_confidence_labels(self):
        response = {
            "labelAnnotations": [
                {"description": "Street fashion", "score": 0.3},  # below 0.7
            ],
            "webDetection": {"webEntities": []},
        }
        signals = extract_style_signals(response)
        # Low confidence label should be filtered out
        assert len(signals) == 0

    def test_handles_missing_keys_gracefully(self):
        response = {}
        signals = extract_style_signals(response)
        assert signals == set()

    def test_handles_missing_description(self):
        response = {
            "labelAnnotations": [
                {"score": 0.9},  # no description key
            ],
            "webDetection": {"webEntities": []},
        }
        signals = extract_style_signals(response)
        assert isinstance(signals, set)


# ── score_image_match tests ──────────────────────────────────────


class TestScoreImageMatch:
    """Verify scoring logic with mocked analyze_image."""

    @patch("services.vision_service.analyze_image")
    def test_full_match_returns_pass(self, mock_analyze):
        mock_analyze.return_value = {
            "labelAnnotations": [
                {"description": "Street fashion", "score": 0.95},
            ],
            "webDetection": {
                "webEntities": [
                    {"description": "Streetwear", "score": 0.9},
                ]
            },
        }
        result = score_image_match(
            "https://example.com/image.jpg",
            expected_tags=["streetwear", "urban"],
            expected_label="Street-Ready",
        )
        assert result["verdict"] in ("PASS", "PARTIAL")
        assert result["match_score"] > 0

    @patch("services.vision_service.analyze_image")
    def test_no_match_returns_fail(self, mock_analyze):
        mock_analyze.return_value = {
            "labelAnnotations": [
                {"description": "Food", "score": 0.95},
                {"description": "Cuisine", "score": 0.9},
            ],
            "webDetection": {"webEntities": []},
        }
        result = score_image_match(
            "https://example.com/food.jpg",
            expected_tags=["streetwear", "urban"],
            expected_label="Street-Ready",
        )
        assert result["verdict"] == "FAIL"
        assert result["match_score"] == 0

    @patch("services.vision_service.analyze_image")
    def test_partial_match(self, mock_analyze):
        mock_analyze.return_value = {
            "labelAnnotations": [
                {"description": "Street fashion", "score": 0.9},
            ],
            "webDetection": {"webEntities": []},
        }
        result = score_image_match(
            "https://example.com/image.jpg",
            expected_tags=["streetwear", "classic", "polished"],
            expected_label="Mixed Style",
        )
        assert 0 < result["match_score"] < 1
        assert len(result["matched_tags"]) > 0
        assert len(result["missing_tags"]) > 0

    @patch("services.vision_service.analyze_image")
    def test_score_is_fraction_of_matched_to_expected(self, mock_analyze):
        mock_analyze.return_value = {
            "labelAnnotations": [
                {"description": "Street fashion", "score": 0.9},
            ],
            "webDetection": {"webEntities": []},
        }
        result = score_image_match(
            "https://example.com/image.jpg",
            expected_tags=["streetwear", "urban"],
            expected_label="Street-Ready",
        )
        expected_score = len(result["matched_tags"]) / 2
        assert result["match_score"] == expected_score

    @patch("services.vision_service.analyze_image")
    def test_result_contains_required_keys(self, mock_analyze):
        mock_analyze.return_value = {
            "labelAnnotations": [],
            "webDetection": {"webEntities": []},
        }
        result = score_image_match(
            "https://example.com/image.jpg",
            expected_tags=["minimalist"],
            expected_label="Clean",
        )
        required_keys = {"match_score", "matched_tags", "missing_tags", "inferred_tags", "raw_labels", "verdict"}
        assert required_keys.issubset(result.keys())


# ── analyze_image tests (mocked httpx) ───────────────────────────


class TestAnalyzeImage:
    """Verify Cloud Vision API call shape and error handling."""

    @patch("services.vision_service.httpx.post")
    def test_correct_payload_shape(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "responses": [{
                    "labelAnnotations": [{"description": "Shirt", "score": 0.9}],
                    "webDetection": {"webEntities": []},
                }]
            }),
            raise_for_status=MagicMock(),
        )
        with patch.dict("os.environ", {"GOOGLE_VISION_API_KEY": "test-key"}):
            result = analyze_image("https://example.com/img.jpg")

        call_args = mock_post.call_args
        payload = call_args[1].get("json") or call_args[0][1] if len(call_args[0]) > 1 else call_args[1]["json"]
        assert "requests" in payload
        req = payload["requests"][0]
        assert "image" in req
        assert "source" in req["image"]
        assert req["image"]["source"]["imageUri"] == "https://example.com/img.jpg"
        assert "features" in req

    @patch("services.vision_service.httpx.post")
    def test_handles_api_error(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=403,
            raise_for_status=MagicMock(side_effect=Exception("Forbidden")),
        )
        with patch.dict("os.environ", {"GOOGLE_VISION_API_KEY": "test-key"}):
            with pytest.raises(Exception):
                analyze_image("https://example.com/img.jpg")

    @patch("services.vision_service.httpx.post")
    def test_raises_on_missing_api_key(self, mock_post):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_VISION_API_KEY"):
                analyze_image("https://example.com/img.jpg")


# ── search_replacement_image tests ───────────────────────────────


class TestSearchReplacementImage:
    """Verify Unsplash search and candidate scoring."""

    @patch("services.vision_service.score_image_match")
    @patch("services.vision_service.httpx.get")
    def test_calls_unsplash_search(self, mock_get, mock_score):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "results": [
                    {"urls": {"regular": "https://images.unsplash.com/new1?w=400&h=400&fit=crop"}},
                    {"urls": {"regular": "https://images.unsplash.com/new2?w=400&h=400&fit=crop"}},
                ]
            }),
            raise_for_status=MagicMock(),
        )
        mock_score.side_effect = [
            {"match_score": 0.8, "verdict": "PASS", "matched_tags": ["streetwear"], "missing_tags": [], "inferred_tags": set(), "raw_labels": []},
            {"match_score": 0.5, "verdict": "PARTIAL", "matched_tags": ["streetwear"], "missing_tags": ["urban"], "inferred_tags": set(), "raw_labels": []},
        ]

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key", "GOOGLE_VISION_API_KEY": "test-key"}):
            result = search_replacement_image(
                style_tags=["streetwear", "urban"],
                label="Street-Ready",
                category="outfit_everyday",
            )

        assert result is not None
        assert "unsplash.com" in result

    @patch("services.vision_service.httpx.get")
    def test_handles_no_results(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"results": []}),
            raise_for_status=MagicMock(),
        )

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key", "GOOGLE_VISION_API_KEY": "test-key"}):
            result = search_replacement_image(
                style_tags=["streetwear", "urban"],
                label="Street-Ready",
                category="outfit_everyday",
            )

        assert result is None

    @patch("services.vision_service.score_image_match")
    @patch("services.vision_service.httpx.get")
    def test_picks_best_scoring_candidate(self, mock_get, mock_score):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={
                "results": [
                    {"urls": {"regular": "https://images.unsplash.com/low"}},
                    {"urls": {"regular": "https://images.unsplash.com/high"}},
                    {"urls": {"regular": "https://images.unsplash.com/mid"}},
                ]
            }),
            raise_for_status=MagicMock(),
        )
        mock_score.side_effect = [
            {"match_score": 0.3, "verdict": "FAIL", "matched_tags": [], "missing_tags": ["a"], "inferred_tags": set(), "raw_labels": []},
            {"match_score": 0.9, "verdict": "PASS", "matched_tags": ["a"], "missing_tags": [], "inferred_tags": set(), "raw_labels": []},
            {"match_score": 0.5, "verdict": "PARTIAL", "matched_tags": ["a"], "missing_tags": [], "inferred_tags": set(), "raw_labels": []},
        ]

        with patch.dict("os.environ", {"UNSPLASH_ACCESS_KEY": "test-key", "GOOGLE_VISION_API_KEY": "test-key"}):
            result = search_replacement_image(
                style_tags=["a"],
                label="Test",
                category="test",
            )

        assert result == "https://images.unsplash.com/high"

    def test_raises_on_missing_unsplash_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="UNSPLASH_ACCESS_KEY"):
                search_replacement_image(
                    style_tags=["streetwear"],
                    label="Test",
                    category="test",
                )
