"""Tests for negative signal filtering of search results."""

import json
import pytest
from unittest.mock import patch


# ── Helper: build product dicts ──────────────────────────────────────────────

def _product(title="Test Product", seller="TestStore", price="$50.00"):
    return {
        "title": title,
        "price": price,
        "currency": "USD",
        "image_url": "http://img.test/thumb.jpg",
        "item_url": "http://test.com/product",
        "seller": seller,
    }


# ── Tests for filter_results ─────────────────────────────────────────────────

class TestFilterResults:
    """filter_results removes products matching avoided brands/colors."""

    def test_filters_avoided_brand_from_title(self):
        from services.shopping import filter_results

        items = [_product(title="Shein Summer Dress"), _product(title="COS Linen Shirt")]
        result = filter_results(items, avoided_brands=["Shein"], avoided_colors=[])

        assert len(result) == 1
        assert result[0]["title"] == "COS Linen Shirt"

    def test_filters_avoided_brand_from_seller(self):
        from services.shopping import filter_results

        items = [_product(title="Summer Dress", seller="Shein"), _product(title="Linen Shirt", seller="COS")]
        result = filter_results(items, avoided_brands=["Shein"], avoided_colors=[])

        assert len(result) == 1
        assert result[0]["seller"] == "COS"

    def test_brand_matching_is_case_insensitive(self):
        from services.shopping import filter_results

        items = [_product(title="SHEIN Summer Dress")]
        result = filter_results(items, avoided_brands=["shein"], avoided_colors=[])

        assert len(result) == 0

    def test_filters_avoided_color_from_title(self):
        from services.shopping import filter_results

        items = [_product(title="Red Graphic Tee"), _product(title="Navy Blazer")]
        result = filter_results(items, avoided_colors=["red"], avoided_brands=[])

        assert len(result) == 1
        assert result[0]["title"] == "Navy Blazer"

    def test_color_word_boundary_blue_not_bluetooth(self):
        from services.shopping import filter_results

        items = [_product(title="Bluetooth Speaker Case")]
        result = filter_results(items, avoided_colors=["blue"], avoided_brands=[])

        assert len(result) == 1, "Should NOT filter 'Bluetooth' when avoiding 'blue'"

    def test_color_word_boundary_green_not_greenhouse(self):
        from services.shopping import filter_results

        items = [_product(title="Greenhouse Supplies Kit")]
        result = filter_results(items, avoided_colors=["green"], avoided_brands=[])

        assert len(result) == 1, "Should NOT filter 'Greenhouse' when avoiding 'green'"

    def test_color_matches_with_punctuation(self):
        from services.shopping import filter_results

        items = [_product(title="Navy Blue, Striped Shirt")]
        result = filter_results(items, avoided_colors=["blue"], avoided_brands=[])

        assert len(result) == 0, "Should filter 'Blue' followed by comma"

    def test_color_case_insensitive(self):
        from services.shopping import filter_results

        items = [_product(title="BLUE Oxford Shirt")]
        result = filter_results(items, avoided_colors=["blue"], avoided_brands=[])

        assert len(result) == 0

    def test_empty_avoided_lists_returns_all(self):
        from services.shopping import filter_results

        items = [_product(), _product(), _product()]
        result = filter_results(items, avoided_brands=[], avoided_colors=[])

        assert len(result) == 3

    def test_empty_items_returns_empty(self):
        from services.shopping import filter_results

        result = filter_results([], avoided_brands=["Shein"], avoided_colors=["red"])
        assert result == []

    def test_multiple_avoided_brands_all_filtered(self):
        from services.shopping import filter_results

        items = [
            _product(title="Shein Dress"),
            _product(title="Temu Jacket"),
            _product(title="COS Shirt"),
        ]
        result = filter_results(items, avoided_brands=["Shein", "Temu"], avoided_colors=[])

        assert len(result) == 1
        assert result[0]["title"] == "COS Shirt"

    def test_non_matching_items_preserved(self):
        from services.shopping import filter_results

        items = [_product(title="COS Linen Shirt", seller="COS")]
        result = filter_results(items, avoided_brands=["Shein"], avoided_colors=["red"])

        assert len(result) == 1
        assert result[0]["title"] == "COS Linen Shirt"

    def test_partial_brand_match(self):
        """H&M in avoided should match 'H&M Premium Selection'."""
        from services.shopping import filter_results

        items = [_product(title="H&M Premium Selection Blazer")]
        result = filter_results(items, avoided_brands=["H&M"], avoided_colors=[])

        assert len(result) == 0

    def test_brand_and_color_both_checked(self):
        """Item matching either avoided brand OR color should be filtered."""
        from services.shopping import filter_results

        items = [
            _product(title="Red Nike Hoodie"),     # color match
            _product(title="Shein Blue Dress"),     # brand match
            _product(title="COS Black Jacket"),     # no match
        ]
        result = filter_results(items, avoided_brands=["Shein"], avoided_colors=["red"])

        assert len(result) == 1
        assert result[0]["title"] == "COS Black Jacket"
