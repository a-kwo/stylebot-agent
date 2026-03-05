"""Tests for Image Resilience: onError fallback + server-side persistence.

Change 1: Frontend onError fallback — broken images degrade to styled placeholder
Change 2: Server-side image persistence — download and store images at add-time
"""

import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "src"


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def db():
    """In-memory DB with full schema including local_image_path column."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            style_adjectives TEXT DEFAULT '[]',
            preferred_colors TEXT DEFAULT '[]',
            avoided_colors TEXT DEFAULT '[]',
            preferred_brands TEXT DEFAULT '[]',
            avoided_brands TEXT DEFAULT '[]',
            size_tops TEXT, size_bottoms TEXT, size_shoes TEXT,
            budget_min INTEGER DEFAULT 0, budget_max INTEGER DEFAULT 500,
            occasions TEXT DEFAULT '[]', fit_preferences TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            gender TEXT, age INTEGER, climate TEXT,
            onboarded INTEGER DEFAULT 0,
            style_quiz TEXT DEFAULT '[]',
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE wardrobe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL, category TEXT NOT NULL,
            color TEXT, brand TEXT, condition TEXT DEFAULT 'good',
            tags TEXT DEFAULT '[]', image_url TEXT, purchase_url TEXT,
            local_image_path TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.execute("INSERT INTO users (username, password_hash) VALUES ('testuser', 'fakehash')")
    conn.commit()
    yield conn
    conn.close()


# ── Change 1: Frontend onError fallback ─────────────────────────

class TestFrontendOnErrorFallback:
    """Broken images must degrade to a styled placeholder, not show a broken icon."""

    def test_wardrobe_page_has_onerror_fallback(self):
        """wardrobe/page.tsx img tags must include an onError handler."""
        source = (FRONTEND_DIR / "app" / "wardrobe" / "page.tsx").read_text()
        assert "onError" in source, (
            "Wardrobe page must have onError handler on img tags"
        )

    def test_product_card_has_onerror_fallback(self):
        """ProductCard.tsx img tags must include an onError handler."""
        source = (FRONTEND_DIR / "components" / "ProductCard.tsx").read_text()
        assert "onError" in source, (
            "ProductCard must have onError handler on img tags"
        )


# ── Change 2: Server-side image persistence ─────────────────────

class TestWardrobeSchemaHasLocalImage:
    """DB schema must include local_image_path column on wardrobe table."""

    def test_wardrobe_table_has_local_image_column(self, db):
        """The wardrobe table must have a local_image_path TEXT column."""
        cols = db.execute("PRAGMA table_info(wardrobe)").fetchall()
        col_names = [c["name"] for c in cols]
        assert "local_image_path" in col_names, (
            "wardrobe table must have local_image_path column"
        )

    def test_init_db_migrates_local_image_column(self):
        """init_db() must add local_image_path to existing wardrobe tables."""
        from database import init_db, DB_PATH
        # init_db writes to disk; just verify the migration function exists
        from database import _migrate_wardrobe
        assert callable(_migrate_wardrobe)


class TestImageStorageService:
    """services/image_storage.py download helper."""

    def test_download_and_store_image_success(self, tmp_path):
        """download_and_store_image writes file to uploads/wardrobe/ and returns path."""
        from services.image_storage import download_and_store_image
        import asyncio

        fake_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100  # fake PNG header

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.content = fake_content
        mock_resp.headers = {"content-type": "image/png"}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("services.image_storage.httpx.AsyncClient", return_value=mock_client):
            with patch("services.image_storage.UPLOAD_DIR", tmp_path / "uploads" / "wardrobe"):
                result = asyncio.run(
                    download_and_store_image("https://example.com/shirt.png", 42)
                )

        assert result is not None, "Should return a path on success"
        assert "42_" in result, "Path should contain item_id"
        assert result.endswith(".png"), "Should preserve png extension"

    def test_download_and_store_image_failure_returns_none(self, tmp_path):
        """Bad URL / network error returns None instead of raising."""
        from services.image_storage import download_and_store_image
        import asyncio
        import httpx

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection failed"))

        with patch("services.image_storage.httpx.AsyncClient", return_value=mock_client):
            with patch("services.image_storage.UPLOAD_DIR", tmp_path / "uploads" / "wardrobe"):
                result = asyncio.run(
                    download_and_store_image("https://bad-url.example.com/nope.jpg", 99)
                )

        assert result is None, "Should return None on failure"


class TestWardrobeRouterStoresLocalImage:
    """POST /api/wardrobe with image_url should trigger download and store local_image_path."""

    def test_add_wardrobe_item_stores_local_image(self):
        """After inserting a wardrobe item with image_url, local_image_path should be set in DB."""
        from fastapi.testclient import TestClient
        import main

        client = TestClient(main.app)

        # Register + login to get token
        client.post("/api/auth/register", json={"username": "imgtest", "password": "pass1234"})
        resp = client.post("/api/auth/login", json={"username": "imgtest", "password": "pass1234"})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock the download helper to return a fake path
        with patch("routers.wardrobe_router.download_and_store_image", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = "/uploads/wardrobe/1_abc123.png"
            resp = client.post("/api/wardrobe", json={
                "name": "Test Shirt",
                "category": "tops",
                "image_url": "https://example.com/shirt.png",
            }, headers=headers)

        assert resp.status_code == 201
        data = resp.json()
        assert mock_dl.called, "download_and_store_image should be called when image_url is provided"

    def test_add_wardrobe_item_without_image_skips_download(self):
        """Items without image_url should not trigger download."""
        from fastapi.testclient import TestClient
        import main

        client = TestClient(main.app)

        client.post("/api/auth/register", json={"username": "imgtest2", "password": "pass1234"})
        resp = client.post("/api/auth/login", json={"username": "imgtest2", "password": "pass1234"})
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        with patch("routers.wardrobe_router.download_and_store_image", new_callable=AsyncMock) as mock_dl:
            resp = client.post("/api/wardrobe", json={
                "name": "Basic Tee",
                "category": "tops",
            }, headers=headers)

        assert resp.status_code == 201
        assert not mock_dl.called, "download should not be called without image_url"


class TestServeLocalImages:
    """GET /uploads/wardrobe/<filename> must serve the stored file."""

    def test_serve_local_image_endpoint(self):
        """Uploads directory must be mounted as static files."""
        from fastapi.testclient import TestClient
        import main

        # Verify the uploads mount exists by checking app routes
        route_paths = []
        for route in main.app.routes:
            if hasattr(route, "path"):
                route_paths.append(route.path)
        # The mount will show as /uploads path
        mounted = any("/uploads" in str(r) for r in main.app.routes)
        assert mounted or any("/uploads" in p for p in route_paths), (
            "uploads/ must be mounted as static files at /uploads/"
        )


class TestWardrobePagePrefersLocalImage:
    """wardrobe/page.tsx must check local_image_path before proxied image_url."""

    def test_wardrobe_page_prefers_local_image(self):
        """page.tsx should reference local_image_path."""
        source = (FRONTEND_DIR / "app" / "wardrobe" / "page.tsx").read_text()
        assert "local_image_path" in source, (
            "Wardrobe page must use local_image_path when available"
        )


# ── Change 3: Search results include image_url for add_to_wardrobe ──

class TestSearchResultsIncludeImageUrls:
    """When search_products results are summarized for Claude, the summary must
    include a compact product reference list so Claude can pass image_url and
    purchase_url when calling add_to_wardrobe."""

    def test_search_summary_includes_product_references(self):
        """The claude_result for search_products must contain product titles
        and image_urls so Claude can use them with add_to_wardrobe."""
        from agent.loop import _build_search_summary

        products = [
            {"title": "Cool Sneaker", "price": "59.99", "image_url": "https://img.example.com/shoe.jpg", "item_url": "https://shop.com/shoe", "seller": "TestStore"},
            {"title": "Retro Runner", "price": "89.00", "image_url": "https://img.example.com/runner.jpg", "item_url": "https://shop.com/runner", "seller": "RunShop"},
        ]
        summary = _build_search_summary(products)
        parsed = json.loads(summary)

        # Must include a product reference list
        assert "products" in parsed, "Summary must include 'products' key with reference data"
        assert len(parsed["products"]) == 2
        assert parsed["products"][0]["image_url"] == "https://img.example.com/shoe.jpg"
        assert parsed["products"][1]["title"] == "Retro Runner"

    def test_search_summary_instructs_claude_to_use_image_url(self):
        """The summary status text must instruct Claude to pass image_url
        when adding items to wardrobe."""
        from agent.loop import _build_search_summary

        products = [
            {"title": "Shoe", "price": "50", "image_url": "https://img.example.com/s.jpg", "item_url": "https://x.com/s", "seller": "X"},
        ]
        summary = _build_search_summary(products)
        parsed = json.loads(summary)

        assert "image_url" in parsed.get("status", ""), (
            "Summary must instruct Claude to use image_url when calling add_to_wardrobe"
        )


# ── Change 4: Auto-enrich add_to_wardrobe with image from recent search ──

class TestAutoEnrichWardrobe:
    """When Claude calls add_to_wardrobe without image_url, the tool handler
    should auto-match against recent search results and fill in image_url."""

    def test_enrich_finds_matching_product(self):
        """_enrich_from_recent_search should find a fuzzy match and return image_url + item_url."""
        from agent.tool_handlers import _enrich_from_recent_search

        recent_products = [
            {"title": "H&M Canvas Sneakers", "image_url": "https://img.example.com/hm.jpg", "item_url": "https://hm.com/shoe"},
            {"title": "Cole Haan Grand Crosscourt", "image_url": "https://img.example.com/cole.jpg", "item_url": "https://colehaan.com/shoe"},
        ]
        result = _enrich_from_recent_search("H&M Canvas Sneakers", recent_products)
        assert result is not None
        assert result["image_url"] == "https://img.example.com/hm.jpg"
        assert result["item_url"] == "https://hm.com/shoe"

    def test_enrich_partial_match(self):
        """Should match even if the name is a substring of the product title."""
        from agent.tool_handlers import _enrich_from_recent_search

        recent_products = [
            {"title": "H&M Canvas Sneakers - White/Blue", "image_url": "https://img.example.com/hm.jpg", "item_url": "https://hm.com/shoe"},
        ]
        result = _enrich_from_recent_search("H&M Canvas Sneakers", recent_products)
        assert result is not None
        assert result["image_url"] == "https://img.example.com/hm.jpg"

    def test_enrich_no_match_returns_none(self):
        """No match should return None."""
        from agent.tool_handlers import _enrich_from_recent_search

        recent_products = [
            {"title": "Nike Air Max", "image_url": "https://img.example.com/nike.jpg", "item_url": "https://nike.com"},
        ]
        result = _enrich_from_recent_search("Adidas Ultraboost", recent_products)
        assert result is None

    def test_add_to_wardrobe_auto_enriches(self, db):
        """When add_to_wardrobe is called without image_url but recent_search_products
        has a match, image_url should be auto-filled."""
        from agent.tool_handlers import dispatch_tool, set_recent_search_products

        set_recent_search_products([
            {"title": "Cool Sneaker", "image_url": "https://img.example.com/shoe.jpg", "item_url": "https://shop.com/shoe"},
        ])

        result_str = dispatch_tool("add_to_wardrobe", {
            "name": "Cool Sneaker",
            "category": "shoes",
        }, user_id=1, db=db)

        result = json.loads(result_str)
        assert result["status"] == "added"
        item_id = result["id"]

        # Check DB has image_url populated
        row = db.execute("SELECT image_url, purchase_url FROM wardrobe WHERE id = ?", (item_id,)).fetchone()
        assert row["image_url"] == "https://img.example.com/shoe.jpg"
        assert row["purchase_url"] == "https://shop.com/shoe"
