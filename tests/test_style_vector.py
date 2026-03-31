"""Tests for style vector computation — ensures both dot and underscore key formats work."""

import pytest
from services.quiz_v2 import compute_style_vector


class TestComputeStyleVector:
    """Tests for compute_style_vector handling of vector_scores key formats."""

    def test_dot_notation_keys(self):
        """Dot-separated keys (as defined in quiz) should map into nested dicts."""
        answers = [
            {"question_id": "q2_cultural", "option_id": "clean_basic", "vector_scores": {"cultural_ref.clean_basic": 0.9, "cultural_ref.prep": 0.1}},
            {"question_id": "q5_silhouette", "option_id": "relaxed", "vector_scores": {"silhouette.relaxed": 0.8, "silhouette.structured": 0.2}},
            {"question_id": "q8_color", "option_id": "warm_earth", "vector_scores": {"color.temperature": 0.8, "color.range": 0.4}},
        ]
        vector = compute_style_vector(answers, ["casual", "work"])

        assert vector["cultural_ref"]["clean_basic"] == 0.9
        assert vector["cultural_ref"]["prep"] == 0.1
        assert vector["silhouette"]["relaxed"] == 0.8
        assert vector["silhouette"]["structured"] == 0.2
        assert vector["color"]["temperature"] == 0.8
        assert vector["color"]["range"] == 0.4
        assert vector["primary_cultural_ref"] == "clean_basic"

    def test_underscore_notation_keys(self):
        """Underscore-separated keys (as sent by frontend) should also map into nested dicts."""
        answers = [
            {"question_id": "q2_cultural", "option_id": "clean_basic", "vector_scores": {"cultural_ref_clean_basic": 0.9, "cultural_ref_prep": 0.1}},
            {"question_id": "q5_silhouette", "option_id": "relaxed", "vector_scores": {"silhouette_relaxed": 0.8, "silhouette_structured": 0.2}},
            {"question_id": "q8_color", "option_id": "warm_earth", "vector_scores": {"color_temperature": 0.8, "color_range": 0.4}},
        ]
        vector = compute_style_vector(answers, ["casual", "work"])

        assert vector["cultural_ref"]["clean_basic"] == 0.9
        assert vector["cultural_ref"]["prep"] == 0.1
        assert vector["silhouette"]["relaxed"] == 0.8
        assert vector["silhouette"]["structured"] == 0.2
        assert vector["color"]["temperature"] == 0.8
        assert vector["color"]["range"] == 0.4
        assert vector["primary_cultural_ref"] == "clean_basic"

    def test_underscore_keys_not_stored_as_top_level(self):
        """Underscore keys should NOT end up as flat top-level keys on the vector."""
        answers = [
            {"question_id": "q2_cultural", "option_id": "clean_basic", "vector_scores": {"cultural_ref_clean_basic": 0.9}},
            {"question_id": "q5_silhouette", "option_id": "relaxed", "vector_scores": {"silhouette_relaxed": 0.8}},
            {"question_id": "q8_color", "option_id": "warm_earth", "vector_scores": {"color_temperature": 0.8}},
        ]
        vector = compute_style_vector(answers, [])

        assert "cultural_ref_clean_basic" not in vector
        assert "silhouette_relaxed" not in vector
        assert "color_temperature" not in vector

    def test_energy_stays_top_level(self):
        """Energy is a simple top-level key, not nested — should work with both formats."""
        answers = [
            {"question_id": "q1_energy", "option_id": "balanced", "vector_scores": {"energy": 0.5}},
            {"question_id": "q4_social_energy", "option_id": "smart_casual", "vector_scores": {"energy": 0.7}},
        ]
        vector = compute_style_vector(answers, [])

        assert vector["energy"] == 0.6  # average of 0.5 and 0.7

    def test_mixed_dot_and_underscore_keys(self):
        """Both formats in the same submission should work correctly."""
        answers = [
            {"question_id": "q2_cultural", "option_id": "clean_basic", "vector_scores": {"cultural_ref.clean_basic": 1.0}},
            {"question_id": "q3_refine", "option_id": "cb_minimal", "vector_scores": {"cultural_ref_clean_basic": 0.5}},
        ]
        vector = compute_style_vector(answers, [])

        # Should average: (1.0 + 0.5) / 2 = 0.75
        assert vector["cultural_ref"]["clean_basic"] == 0.75

    def test_occasions_passed_through(self):
        """Selected occasions should be stored as-is."""
        vector = compute_style_vector([], ["casual", "work", "date_night"])
        assert vector["occasions"] == ["casual", "work", "date_night"]

    def test_empty_answers(self):
        """Empty answers should return default vector."""
        vector = compute_style_vector([], [])

        assert vector["energy"] == 0.5
        assert vector["cultural_ref"]["clean_basic"] == 0.0
        assert vector["silhouette"]["relaxed"] == 0.0
        assert vector["color"]["range"] == 0.5
        assert vector["primary_cultural_ref"] == "none"
