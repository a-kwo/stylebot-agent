"""Tests for post-search product re-ranking (Item 9)."""

import pytest


def _product(title="Test Product", price="50.0", seller="TestStore", image_url="http://img/t.jpg", item_url="http://test.com/p"):
    return {
        "title": title,
        "price": price,
        "currency": "USD",
        "image_url": image_url,
        "item_url": item_url,
        "seller": seller,
    }


def _profile(**overrides):
    base = {
        "preferred_brands": [],
        "avoided_brands": [],
        "preferred_colors": [],
        "avoided_colors": [],
        "budget_min": 0,
        "budget_max": 500,
    }
    base.update(overrides)
    return base


class TestRankProducts:
    """rank_products re-orders products by personalization score."""

    def test_returns_same_count(self):
        from services.product_ranker import rank_products

        products = [_product(), _product(), _product()]
        result = rank_products(products, _profile(), [])
        assert len(result) == 3

    def test_adds_rank_score(self):
        from services.product_ranker import rank_products

        products = [_product()]
        result = rank_products(products, _profile(), [])
        assert "_rank_score" in result[0]
        assert isinstance(result[0]["_rank_score"], float)

    def test_preferred_brand_ranked_higher(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Generic Shirt", seller="NoName"),
            _product(title="Nike Air Max", seller="Nike"),
        ]
        profile = _profile(preferred_brands=["Nike"])
        result = rank_products(products, profile, [])

        assert result[0]["seller"] == "Nike", "Preferred brand should rank first"

    def test_avoided_brand_ranked_lower(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Shein Dress", seller="Shein"),
            _product(title="Basic Shirt", seller="COS"),
        ]
        profile = _profile(avoided_brands=["Shein"])
        result = rank_products(products, profile, [])

        assert result[0]["seller"] == "COS", "Avoided brand should rank last"

    def test_price_within_budget_ranked_higher(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Expensive Jacket", price="450.0"),
            _product(title="Budget Jacket", price="120.0"),
        ]
        profile = _profile(budget_min=50, budget_max=200)
        result = rank_products(products, profile, [])

        assert result[0]["title"] == "Budget Jacket", "Product within budget should rank higher"

    def test_preferred_color_boost(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Red Graphic Tee"),
            _product(title="Navy Oxford Shirt"),
        ]
        profile = _profile(preferred_colors=["navy"])
        result = rank_products(products, profile, [])

        assert result[0]["title"] == "Navy Oxford Shirt"

    def test_avoided_color_penalty(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Red Hoodie"),
            _product(title="Black Hoodie"),
        ]
        profile = _profile(avoided_colors=["red"])
        result = rank_products(products, profile, [])

        assert result[0]["title"] == "Black Hoodie"

    def test_wardrobe_duplicate_penalized(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Navy Chinos", seller="COS"),
            _product(title="Leather Boots", seller="RedWing"),
        ]
        wardrobe = [{"name": "Navy Chinos", "category": "bottoms", "color": "navy", "brand": "COS"}]
        result = rank_products(products, _profile(), wardrobe)

        assert result[0]["title"] == "Leather Boots", "Duplicate wardrobe item should rank lower"

    def test_missing_category_boosted(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Another Blue Shirt"),
            _product(title="Black Leather Jacket"),
        ]
        # User has tops but no outerwear
        wardrobe = [
            {"name": "White Tee", "category": "tops", "color": "white", "brand": "Uniqlo"},
            {"name": "Blue Shirt", "category": "tops", "color": "blue", "brand": "COS"},
        ]
        result = rank_products(products, _profile(), wardrobe)

        assert result[0]["title"] == "Black Leather Jacket", "Item in missing category should rank higher"

    def test_seller_diversity_penalizes_repeats(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Nike Shirt 1", seller="Nike"),
            _product(title="Nike Shirt 2", seller="Nike"),
            _product(title="Nike Shirt 3", seller="Nike"),
            _product(title="COS Shirt", seller="COS"),
        ]
        result = rank_products(products, _profile(), [])

        # COS should not be last — it gets diversity bonus
        cos_idx = next(i for i, p in enumerate(result) if p["seller"] == "COS")
        assert cos_idx < 3, "Unique seller should rank above 3rd repeat"

    def test_empty_products_returns_empty(self):
        from services.product_ranker import rank_products

        result = rank_products([], _profile(), [])
        assert result == []

    def test_empty_profile_no_crash(self):
        from services.product_ranker import rank_products

        products = [_product()]
        result = rank_products(products, {}, [])
        assert len(result) == 1

    def test_stable_sort_for_equal_scores(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="A Shirt", seller="Store1"),
            _product(title="B Shirt", seller="Store2"),
            _product(title="C Shirt", seller="Store3"),
        ]
        result = rank_products(products, _profile(), [])

        # With identical inputs, original order should be preserved
        titles = [p["title"] for p in result]
        assert titles == ["A Shirt", "B Shirt", "C Shirt"]

    def test_custom_weights_override(self):
        from services.product_ranker import rank_products

        products = [
            _product(title="Nike Sneakers", seller="Nike"),
            _product(title="Cheap Basics", price="10.0"),
        ]
        profile = _profile(preferred_brands=["Nike"], budget_min=5, budget_max=15)

        # With brand_match weight 0, price_fit at 1.0 — price should dominate
        result = rank_products(
            products, profile, [],
            weights={"brand_match": 0, "price_fit": 1.0, "color_alignment": 0, "wardrobe_novelty": 0, "seller_diversity": 0},
        )
        assert result[0]["title"] == "Cheap Basics", "Custom weights should override default ranking"
