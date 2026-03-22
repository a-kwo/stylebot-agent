"""Fetch placeholder images from Pexels for V2 quiz options.

Run: python scripts/fetch_quiz_v2_images.py
     python scripts/fetch_quiz_v2_images.py --force   # re-fetch all
"""

import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("PEXELS_API_KEY")
if not API_KEY:
    print("ERROR: PEXELS_API_KEY not found in .env")
    sys.exit(1)

OUT_DIR = Path(__file__).parent.parent / "static" / "quiz_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PEXELS_SEARCH = "https://api.pexels.com/v1/search"

# Map each image filename to a Pexels search query
# Queries target full-body outfit/fashion photos matching each quiz option
IMAGE_QUERIES = {
    # ── Q1: Energy ────────────────────────────────────────────────────────────
    "v2__q1__quiet": "minimalist neutral outfit simple clean fashion",
    "v2__q1__balanced": "smart casual outfit everyday modern style",
    "v2__q1__expressive": "bold colorful outfit expressive street fashion",

    # ── Q2: Cultural Reference ────────────────────────────────────────────────
    "v2__q2__sport-street": "streetwear outfit sneakers urban fashion",
    "v2__q2__prep": "preppy classic outfit polo blazer chinos",
    "v2__q2__euro-fashion": "high fashion editorial outfit european style",
    "v2__q2__utility": "workwear utility outfit rugged fashion",

    # ── Q3: Refinement (branched by Q2) ───────────────────────────────────────
    "v2__q3__ss-subtle": "clean minimal streetwear white sneakers outfit",
    "v2__q3__ss-core": "streetwear hoodie sneakers casual urban",
    "v2__q3__ss-loud": "bold streetwear statement outfit graphic",
    "v2__q3__prep-quiet": "quiet luxury cashmere neutral elegant outfit",
    "v2__q3__prep-classic": "classic preppy blazer chinos loafers outfit",
    "v2__q3__prep-bold": "bold preppy bright colors pattern outfit",
    "v2__q3__euro-minimal": "scandinavian minimalist monochrome fashion",
    "v2__q3__euro-tailored": "tailored slim fit suit modern european",
    "v2__q3__euro-avantgarde": "avant garde fashion deconstructed outfit",
    "v2__q3__util-clean": "clean modern utility workwear outfit",
    "v2__q3__util-rugged": "rugged heritage workwear denim boots flannel",
    "v2__q3__util-techwear": "techwear technical fashion urban outfit",

    # ── Q4: Social Energy ─────────────────────────────────────────────────────
    "v2__q4__blend-in": "understated dark evening outfit going out",
    "v2__q4__elevated": "elevated smart casual evening outfit",
    "v2__q4__stands-out": "bold standout night out statement outfit",

    # ── Q5: Silhouette ────────────────────────────────────────────────────────
    "v2__q5__structured": "structured tailored fitted outfit fashion",
    "v2__q5__relaxed": "relaxed fit comfortable draped outfit casual",
    "v2__q5__oversized": "oversized baggy loose fit outfit fashion",

    # ── Q6: Silhouette (occasion) ─────────────────────────────────────────────
    "v2__q6__structured": "structured tailored professional work outfit",
    "v2__q6__relaxed": "relaxed comfortable professional outfit",
    "v2__q6__oversized": "oversized loose comfortable casual outfit",

    # ── Q7: Volume Balance ────────────────────────────────────────────────────
    "v2__q7__volume-top": "oversized top slim pants outfit fashion",
    "v2__q7__volume-bottom": "fitted top wide leg pants outfit",
    "v2__q7__volume-consistent": "balanced proportions outfit consistent fit",

    # ── Q8: Color Palette ─────────────────────────────────────────────────────
    "v2__q8__neutral-mono": "monochrome neutral black white grey outfit",
    "v2__q8__warm-earth": "earth tone outfit brown tan beige warm",
    "v2__q8__cool-bold": "cool bold color outfit blue teal fashion",
    "v2__q8__mixed-pattern": "mixed pattern colorful prints outfit fashion",

    # ── Q9: Color Expression ──────────────────────────────────────────────────
    "v2__q9__accent": "neutral outfit pop of color accent accessory",
    "v2__q9__focal": "outfit bold color statement piece focal",
    "v2__q9__full": "full color bold bright outfit fashion",

    # ── Stage 4: Occasion Calibration ─────────────────────────────────────────
    "v2__s4__work-conservative": "conservative formal business office outfit",
    "v2__s4__work-modern": "modern smart business casual outfit",
    "v2__s4__work-creative": "creative expressive office outfit professional",
    "v2__s4__casual-minimal": "minimal casual everyday outfit simple",
    "v2__s4__casual-put-together": "put together casual weekend outfit smart",
    "v2__s4__casual-styled": "fully styled casual fashion forward outfit",
    "v2__s4__out-understated": "understated cool evening night out outfit",
    "v2__s4__out-sharp": "sharp intentional evening outfit night out",
    "v2__s4__out-bold": "bold memorable night out statement outfit",
    "v2__s4__date-effortless": "effortless cool date night outfit",
    "v2__s4__date-polished": "polished refined date night outfit",
    "v2__s4__date-showstopper": "glamorous show-stopping date outfit",
    "v2__s4__event-classic": "classic formal event elegant outfit",
    "v2__s4__event-contemporary": "contemporary modern formal event outfit",
    "v2__s4__event-statement": "bold statement formal event outfit",
    "v2__s4__active-functional": "functional athletic workout gym outfit",
    "v2__s4__active-athleisure": "athleisure sporty casual outfit",
    "v2__s4__active-styled": "styled trendy activewear fashion outfit",
    "v2__s4__travel-practical": "practical comfortable travel airport outfit",
    "v2__s4__travel-curated": "curated casual stylish travel outfit",
    "v2__s4__travel-stylish": "stylish fashionable airport travel outfit",
}


def fetch_image(query: str, filename: str, force: bool = False) -> bool:
    """Search Pexels and download the top portrait-oriented result."""
    filepath = OUT_DIR / f"{filename}.png"
    if not force and filepath.exists() and filepath.stat().st_size > 1024:
        print(f"  SKIP {filename} (already exists, {filepath.stat().st_size // 1024}KB)")
        return True

    try:
        resp = requests.get(
            PEXELS_SEARCH,
            params={
                "query": query,
                "per_page": 5,
                "orientation": "portrait",
                "size": "medium",
            },
            headers={"Authorization": API_KEY},
            timeout=30,
        )
    except requests.exceptions.Timeout:
        print(f"  TIMEOUT {filename} (Pexels search)")
        return False

    if resp.status_code == 429:
        print(f"  RATE LIMITED — waiting 60s...")
        time.sleep(60)
        return fetch_image(query, filename, force)

    if resp.status_code != 200:
        print(f"  ERROR {filename}: HTTP {resp.status_code}")
        return False

    data = resp.json()
    photos = data.get("photos", [])
    if not photos:
        print(f"  NO RESULTS for {filename}: '{query}'")
        return False

    # Try multiple results in case some fail to download
    for photo in photos[:5]:
        # Use the "large" size — good quality without being huge
        image_url = photo.get("src", {}).get("large")
        if not image_url:
            continue

        try:
            img_resp = requests.get(image_url, timeout=30)
            if img_resp.status_code != 200:
                continue
            if len(img_resp.content) < 1024:
                continue

            filepath.write_bytes(img_resp.content)
            photographer = photo.get("photographer", "unknown")
            print(f"  OK {filename} ({len(img_resp.content) // 1024}KB) — by {photographer}")
            return True
        except Exception:
            continue

    print(f"  ALL DOWNLOADS FAILED {filename}")
    return False


def main():
    force = "--force" in sys.argv

    print(f"Fetching {len(IMAGE_QUERIES)} quiz images from Pexels...")
    if force:
        print("  (--force: re-fetching all images)")
    print(f"Output: {OUT_DIR}\n")

    success = 0
    failed = []

    for filename, query in IMAGE_QUERIES.items():
        ok = fetch_image(query, filename, force=force)
        if ok:
            success += 1
        else:
            failed.append(filename)

        # Pexels rate limit: 200 req/hr — pace requests
        time.sleep(1)

    print(f"\nDone: {success}/{len(IMAGE_QUERIES)} images fetched")
    if failed:
        print(f"Failed ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
