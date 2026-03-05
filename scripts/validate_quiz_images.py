#!/usr/bin/env python3
"""CLI script to validate quiz images against their style tags using Google Vision API.

Usage:
    python scripts/validate_quiz_images.py                    # validate all
    python scripts/validate_quiz_images.py --category outfit_everyday
    python scripts/validate_quiz_images.py --verbose          # show raw labels
    python scripts/validate_quiz_images.py --json             # JSON output
    python scripts/validate_quiz_images.py --apply            # replace FAIL images
    python scripts/validate_quiz_images.py --threshold 0.3    # lower bar

Requires GOOGLE_VISION_API_KEY env var (and UNSPLASH_ACCESS_KEY for --apply).
"""

import argparse
import json
import os
import re
import sys

# Add project root to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from services.quiz_service import QUIZ_QUESTIONS
from services.vision_service import (
    analyze_images_batch,
    extract_style_signals,
    search_replacement_image,
)


def collect_quiz_options(category_filter: str | None = None) -> list[dict]:
    """Collect all quiz options, optionally filtered by category."""
    options = []
    for cat_name, cat_data in QUIZ_QUESTIONS.items():
        if category_filter and cat_name != category_filter:
            continue
        for opt in cat_data["options"]:
            options.append({
                "category": cat_name,
                "id": opt["id"],
                "label": opt["label"],
                "image_url": opt["image_url"],
                "style_tags": opt["style_tags"],
            })
    return options


def score_option(option: dict, vision_response: dict, threshold: float) -> dict:
    """Score a single option against its Vision API response."""
    inferred = extract_style_signals(vision_response)
    raw_labels = [
        a.get("description", "")
        for a in vision_response.get("labelAnnotations", [])
    ]

    matched = [t for t in option["style_tags"] if t in inferred]
    missing = [t for t in option["style_tags"] if t not in inferred]
    score = len(matched) / len(option["style_tags"]) if option["style_tags"] else 0

    if score >= threshold:
        verdict = "PASS"
    elif score > 0:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return {
        **option,
        "match_score": score,
        "matched_tags": matched,
        "missing_tags": missing,
        "inferred_tags": sorted(inferred),
        "raw_labels": raw_labels,
        "verdict": verdict,
    }


def validate_images(
    options: list[dict],
    threshold: float = 0.5,
    verbose: bool = False,
) -> list[dict]:
    """Validate all options using batched Vision API calls."""
    results = []

    # Batch in groups of 16
    for i in range(0, len(options), 16):
        batch = options[i : i + 16]
        urls = [o["image_url"] for o in batch]

        print(f"  Analyzing batch {i // 16 + 1} ({len(urls)} images)...")
        responses = analyze_images_batch(urls)

        for opt, resp in zip(batch, responses):
            result = score_option(opt, resp, threshold)
            results.append(result)

            symbol = {"PASS": "+", "PARTIAL": "~", "FAIL": "!"}[result["verdict"]]
            print(f"  [{symbol}] {result['verdict']:7s} {result['match_score']:.0%}  "
                  f"{result['category']}/{result['id']} — {result['label']}")

            if verbose:
                print(f"         Expected: {result['style_tags']}")
                print(f"         Inferred: {result['inferred_tags']}")
                print(f"         Matched:  {result['matched_tags']}")
                print(f"         Missing:  {result['missing_tags']}")
                print(f"         Labels:   {result['raw_labels'][:8]}")
                print()

    return results


def apply_replacements(results: list[dict], threshold: float) -> list[dict]:
    """For FAIL results, search Unsplash for replacements and validate them."""
    failures = [r for r in results if r["verdict"] == "FAIL"]
    if not failures:
        print("\nNo FAIL images to replace.")
        return []

    print(f"\nSearching replacements for {len(failures)} failed images...")
    replacements = []

    for r in failures:
        print(f"  Searching for: {r['category']}/{r['id']} ({r['label']})...")
        new_url = search_replacement_image(
            style_tags=r["style_tags"],
            label=r["label"],
            category=r["category"],
        )
        if new_url:
            replacements.append({
                "category": r["category"],
                "id": r["id"],
                "old_url": r["image_url"],
                "new_url": new_url,
            })
            print(f"    Found replacement")
        else:
            print(f"    No suitable replacement found")

    return replacements


def write_replacements(replacements: list[dict]) -> int:
    """Update quiz_service.py with replacement image URLs."""
    if not replacements:
        return 0

    quiz_file = os.path.join(os.path.dirname(__file__), "..", "services", "quiz_service.py")
    quiz_file = os.path.normpath(quiz_file)

    with open(quiz_file, "r") as f:
        content = f.read()

    count = 0
    for rep in replacements:
        old = rep["old_url"]
        # Normalize the new URL to have the standard crop params
        new_url = rep["new_url"].split("?")[0] + "?w=400&h=400&fit=crop"
        if old in content:
            content = content.replace(old, new_url)
            count += 1
            print(f"  Replaced: {rep['category']}/{rep['id']}")

    with open(quiz_file, "w") as f:
        f.write(content)

    return count


def print_summary(results: list[dict]) -> None:
    """Print a summary of validation results."""
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    partial_count = sum(1 for r in results if r["verdict"] == "PARTIAL")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    total = len(results)

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {total} images validated")
    print(f"  PASS:    {pass_count:3d} ({pass_count/total:.0%})")
    print(f"  PARTIAL: {partial_count:3d} ({partial_count/total:.0%})")
    print(f"  FAIL:    {fail_count:3d} ({fail_count/total:.0%})")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate quiz images using Google Vision API"
    )
    parser.add_argument(
        "--category",
        help="Only validate a specific category (e.g. outfit_everyday)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show raw labels and detailed match info",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Auto-replace FAIL images with Unsplash alternatives",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Match score threshold for PASS (default: 0.5)",
    )

    args = parser.parse_args()

    if not os.environ.get("GOOGLE_VISION_API_KEY"):
        print("Error: GOOGLE_VISION_API_KEY environment variable is required.")
        sys.exit(1)

    if args.apply and not os.environ.get("UNSPLASH_ACCESS_KEY"):
        print("Error: UNSPLASH_ACCESS_KEY environment variable is required for --apply.")
        sys.exit(1)

    options = collect_quiz_options(args.category)
    print(f"Validating {len(options)} quiz images (threshold: {args.threshold:.0%})...\n")

    results = validate_images(options, threshold=args.threshold, verbose=args.verbose)

    if args.json_output:
        # Convert sets to lists for JSON serialization
        for r in results:
            if isinstance(r.get("inferred_tags"), set):
                r["inferred_tags"] = sorted(r["inferred_tags"])
        print(json.dumps(results, indent=2))
        return

    print_summary(results)

    if args.apply:
        replacements = apply_replacements(results, args.threshold)
        if replacements:
            count = write_replacements(replacements)
            print(f"\nUpdated {count} image URLs in quiz_service.py")
        else:
            print("\nNo replacements to apply.")


if __name__ == "__main__":
    main()
