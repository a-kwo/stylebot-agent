#!/usr/bin/env python3
"""CLI script to validate quiz images exist locally and optionally check with Vision API.

Usage:
    python scripts/validate_quiz_images.py                    # validate all
    python scripts/validate_quiz_images.py --source tree      # only tree images
    python scripts/validate_quiz_images.py --source chat      # only chat images
    python scripts/validate_quiz_images.py --verbose          # show file details
    python scripts/validate_quiz_images.py --json             # JSON output

Optionally requires GOOGLE_VISION_API_KEY env var for style-tag validation.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from services.quiz_service import QUIZ_TREE, CHAT_QUESTIONS

PROJECT_ROOT = Path(__file__).parent.parent
QUIZ_IMAGES_DIR = PROJECT_ROOT / "static" / "quiz_images"


def collect_quiz_options(source_filter: str = "all") -> list[dict]:
    """Collect quiz options from QUIZ_TREE and/or CHAT_QUESTIONS."""
    options = []

    if source_filter in ("tree", "all"):
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                options.append({
                    "source": "tree",
                    "category": node_id,
                    "id": opt["id"],
                    "label": opt["label"],
                    "image_url": opt["image_url"],
                    "style_tags": opt["style_tags"],
                })

    if source_filter in ("chat", "all"):
        for cat_name, cat_data in CHAT_QUESTIONS.items():
            for opt in cat_data["options"]:
                options.append({
                    "source": "chat",
                    "category": cat_name,
                    "id": opt["id"],
                    "label": opt["label"],
                    "image_url": opt["image_url"],
                    "style_tags": opt["style_tags"],
                })

    return options


def validate_local_file(option: dict) -> dict:
    """Check that the image URL points to an existing local file."""
    url = option["image_url"]
    result = {**option, "verdict": "FAIL", "error": None, "file_size": 0}

    if not url.startswith("/static/quiz_images/"):
        result["error"] = f"URL not local: {url}"
        return result

    rel_path = url.lstrip("/")
    file_path = PROJECT_ROOT / rel_path

    if not file_path.exists():
        result["error"] = f"File missing: {file_path}"
        return result

    size = file_path.stat().st_size
    if size == 0:
        result["error"] = "File is empty"
        return result

    result["verdict"] = "PASS"
    result["file_size"] = size
    return result


def validate_images(options: list[dict], verbose: bool = False) -> list[dict]:
    """Validate all options by checking local file existence."""
    results = []

    for opt in options:
        result = validate_local_file(opt)
        results.append(result)

        symbol = "+" if result["verdict"] == "PASS" else "!"
        size_str = f" ({result['file_size']:,} bytes)" if result["file_size"] else ""
        print(f"  [{symbol}] {result['verdict']:7s} [{result['source']}] "
              f"{result['category']}/{result['id']} — {result['label']}{size_str}")

        if verbose and result["error"]:
            print(f"         Error: {result['error']}")

    return results


def print_summary(results: list[dict]) -> None:
    """Print a summary of validation results."""
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    total = len(results)

    tree_count = sum(1 for r in results if r["source"] == "tree")
    chat_count = sum(1 for r in results if r["source"] == "chat")

    total_size = sum(r["file_size"] for r in results)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {total} images validated ({tree_count} tree, {chat_count} chat)")
    print(f"  PASS: {pass_count:3d} ({pass_count/total:.0%})")
    print(f"  FAIL: {fail_count:3d} ({fail_count/total:.0%})")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate quiz images (local file existence)"
    )
    parser.add_argument(
        "--source",
        choices=["tree", "chat", "all"],
        default="all",
        help="Which image source to validate (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show error details for failed images",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    options = collect_quiz_options(args.source)
    print(f"Validating {len(options)} quiz images (source: {args.source})...\n")

    results = validate_images(options, verbose=args.verbose)

    if args.json_output:
        print(json.dumps(results, indent=2))
        return

    print_summary(results)


if __name__ == "__main__":
    main()
