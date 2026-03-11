#!/usr/bin/env python3
"""Update quiz_service.py image URLs from Unsplash to local AI-generated images.

Reads the manifest.json produced by generate_quiz_images.py and rewrites all
image_url values in quiz_service.py to point to /static/quiz_images/{key}.jpg.

Usage:
    python scripts/update_quiz_urls.py            # apply changes
    python scripts/update_quiz_urls.py --dry-run   # preview only
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.quiz_service import QUIZ_TREE, CHAT_QUESTIONS

MANIFEST_PATH = Path(__file__).parent.parent / "static" / "quiz_images" / "manifest.json"
QUIZ_SERVICE_PATH = Path(__file__).parent.parent / "services" / "quiz_service.py"


def option_id_key(source: str, node_or_cat: str, option_id: str) -> str:
    return f"{source}__{node_or_cat}__{option_id}"


def build_url_map(manifest: dict[str, str]) -> dict[str, str]:
    """Build old_url -> new_url mapping by matching manifest keys to current quiz data."""
    url_map: dict[str, str] = {}

    for node_id, node in QUIZ_TREE.items():
        for opt in node["options"]:
            key = option_id_key("tree", node_id, opt["id"])
            if key in manifest:
                new_url = f"/static/quiz_images/{manifest[key]}"
                url_map[opt["image_url"]] = (new_url, key)

    for cat, q in CHAT_QUESTIONS.items():
        for opt in q["options"]:
            key = option_id_key("chat", cat, opt["id"])
            if key in manifest:
                new_url = f"/static/quiz_images/{manifest[key]}"
                url_map[opt["image_url"]] = (new_url, key)

    return url_map


def main():
    parser = argparse.ArgumentParser(description="Update quiz image URLs to local files")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes only")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        print("Run generate_quiz_images.py first.")
        sys.exit(1)

    manifest = json.loads(MANIFEST_PATH.read_text())
    print(f"Loaded manifest with {len(manifest)} entries")

    url_map = build_url_map(manifest)
    print(f"Found {len(url_map)} URL replacements to make")

    content = QUIZ_SERVICE_PATH.read_text(encoding="utf-8")
    original = content
    count = 0

    # Sort by length descending to avoid partial replacements
    for old_url, (new_url, key) in sorted(url_map.items(), key=lambda x: -len(x[0])):
        if old_url in content:
            if args.dry_run:
                print(f"  Would replace: {old_url[:60]}... -> {new_url}")
            content = content.replace(old_url, new_url)
            count += 1

    if count == 0:
        print("No URLs to replace (already updated or manifest mismatch).")
        return

    if args.dry_run:
        print(f"\n[DRY-RUN] Would replace {count} URLs in quiz_service.py")
        return

    QUIZ_SERVICE_PATH.write_text(content, encoding="utf-8")
    print(f"\nUpdated {count} URLs in {QUIZ_SERVICE_PATH}")


if __name__ == "__main__":
    main()
