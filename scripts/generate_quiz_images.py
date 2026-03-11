#!/usr/bin/env python3
"""Generate AI quiz images via Kie AI (Nano Banana 2 / Gemini image generation).

Usage:
    python scripts/generate_quiz_images.py --source all
    python scripts/generate_quiz_images.py --source tree --dry-run
    python scripts/generate_quiz_images.py --source chat --force --concurrency 5
    python scripts/generate_quiz_images.py --resolution 2K

Requires KIE_API_KEY env var. API base: https://api.kie.ai
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import httpx

from services.quiz_service import QUIZ_TREE, CHAT_QUESTIONS

OUTPUT_DIR = Path(__file__).parent.parent / "static" / "quiz_images"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

# ── Prompt building ──────────────────────────────────────────────

# Style archetype prompt fragments
STYLE_PROMPTS = {
    # Streetwear
    "streetwear": "streetwear outfit with oversized silhouettes, graphic elements, and urban edge",
    "skate": "skateboarding-inspired outfit with loose-fit pants, graphic tee, and skate shoes",
    "techwear": "techwear outfit with technical fabrics, utility pockets, and futuristic silhouette",
    "hiphop": "hip-hop inspired outfit with bold layering, statement jewelry, and fresh kicks",
    "hypebeast": "hypebeast outfit with designer logos, limited-edition sneakers, and trendy accessories",
    "tomboy": "tomboy streetwear with oversized hoodie, baggy jeans, and chunky sneakers",
    "luxe": "luxury streetwear with premium materials, subtle branding, and refined urban edge",
    "y2k": "Y2K inspired outfit with low-rise bottoms, butterfly clips, and nostalgic early-2000s aesthetic",

    # Old Money / Classic
    "old-money": "old money style with tailored blazer, quality fabrics, and understated luxury",
    "british": "British heritage style with tweed, oxford shoes, and classic tailoring",
    "italian": "Italian style with slim-cut suit, leather loafers, and Mediterranean elegance",
    "preppy": "preppy outfit with polo shirt, chinos, and boat shoes or loafers",
    "quiet-luxury": "quiet luxury outfit with cashmere, neutral tones, and no visible logos",
    "parisian": "Parisian chic outfit with breton stripes, tailored trousers, and ballet flats",

    # Vintage
    "vintage": "vintage-inspired outfit with retro patterns and throwback silhouettes",
    "70s": "1970s inspired outfit with flared pants, earthy tones, and bohemian accessories",
    "80s-90s": "80s/90s inspired outfit with bold colors, high-waist jeans, and retro sneakers",
    "90s": "90s inspired outfit with relaxed denim, band tee, and combat boots",
    "workwear": "vintage workwear with raw denim, heritage boots, and rugged accessories",

    # Athleisure
    "athleisure": "athleisure outfit blending athletic wear with casual style",
    "performance": "performance athleisure with technical fabrics, sleek sneakers, and fitted silhouette",
    "fashion-athletic": "fashion-forward athleisure with designer sportswear and trendy workout pieces",
    "outdoor": "outdoor athleisure with gorpcore elements, trail shoes, and functional layers",

    # Smart Casual
    "smart-casual": "smart casual outfit balancing polished and relaxed elements",
    "euro": "European smart casual with slim trousers, knit polo, and minimal sneakers",
    "japanese": "Japanese minimalist outfit with clean lines, neutral palette, and architectural silhouette",
    "modern": "modern smart casual with clean lines, monochrome palette, and architectural shapes",

    # General / cross-gender
    "bohemian": "bohemian outfit with flowing fabrics, earthy prints, and layered accessories",
    "minimalist": "minimalist outfit with clean silhouette, neutral colors, and zero excess",
    "edgy": "edgy outfit with leather jacket, dark palette, and statement boots",
    "classic": "classic tailored outfit with structured blazer, quality fabrics, and elegant accessories",
    "old-money-root": "old money outfit with tailored blazer, quality fabrics, and understated elegance",
    "smart": "smart minimal outfit with clean lines, quality fabrics, and understated sophistication",
}

# Gender-aware subject descriptions
GENDER_SUBJECTS = {
    "m": "a young man",
    "f": "a young woman",
    "nb": "a young person",
}

# Chat category contexts
CHAT_CONTEXTS = {
    "sneakers": "Close-up product shot of {label} sneakers on a clean background. {detail}",
    "formal_wear": "Professional fashion photography of {subject} wearing {label} formal attire. {detail}",
    "patterns": "Fashion flat-lay or outfit shot featuring {label} pattern clothing. {detail}",
    "accessories": "Stylish product photography of {label} fashion accessories. {detail}",
    "dresses": "Fashion photography of a young woman wearing a {label} dress. {detail}",
    "activewear": "Athletic fashion photography of {subject} wearing {label} activewear. {detail}",
}

# Per-option detail overrides for chat questions
CHAT_DETAILS = {
    "retro-runner": "Vintage-inspired running shoe with suede and mesh, muted colorway",
    "high-tops": "Classic high-top basketball sneaker, bold colorway",
    "slip-on": "Minimalist slip-on sneaker, clean canvas or leather",
    "designer-sneaker": "Luxury designer sneaker with premium materials and subtle branding",
    "classic-suit": "Well-fitted two-piece suit in navy or charcoal",
    "black-tie": "Formal tuxedo or evening gown, elegant and refined",
    "modern-formal": "Contemporary formal wear with slim silhouette and modern details",
    "cocktail": "Cocktail attire with stylish semi-formal pieces",
    "floral": "Fresh floral print pattern on quality fabric",
    "geometric": "Bold geometric pattern with clean lines",
    "stripes": "Classic stripe pattern, versatile and timeless",
    "abstract": "Artistic abstract print with unique design",
    "minimal-watch": "Clean, minimalist watch with leather or metal band",
    "statement-bag": "Bold designer bag with distinctive shape or hardware",
    "layered-jewelry": "Delicate layered necklaces and bracelets, gold or silver",
    "classic-sunglasses": "Timeless sunglasses shape like aviator or wayfarer",
    "cocktail-dress": "Elegant cocktail dress with flattering silhouette",
    "maxi-dress": "Flowing maxi dress with beautiful drape and print",
    "shirt-dress": "Structured shirt dress with belt, smart-casual vibe",
    "wrap-dress": "Classic wrap dress with flattering V-neckline",
    "performance-set": "Technical performance set with moisture-wicking fabric",
    "yoga-flow": "Yoga-inspired activewear with stretchy, breathable fabric",
    "street-sport": "Street-sport hybrid with bold logos and urban styling",
    "outdoor-active": "Outdoor activewear with trail-ready features and earthy tones",
}


def _detect_gender(node_id: str) -> str:
    """Detect gender context from node_id prefix."""
    if node_id.startswith("m_") or node_id == "root_m":
        return "m"
    elif node_id.startswith("f_") or node_id == "root_f":
        return "f"
    # Cross-cutting nodes: color_m, fit_m, color_f, fit_f
    if node_id.endswith("_m"):
        return "m"
    if node_id.endswith("_f"):
        return "f"
    return "nb"


def _detect_style_key(node_id: str, option_id: str, style_tags: list[str]) -> str:
    """Best-effort mapping from option context to a STYLE_PROMPTS key."""
    # Explicit overrides for root-level options
    explicit = {
        "root_m_oldmoney": "old-money", "root_f_oldmoney": "old-money", "root_nb_oldmoney": "old-money",
        "root_m_street": "streetwear", "root_f_street": "streetwear", "root_nb_street": "streetwear",
        "root_m_vintage": "vintage", "root_f_vintage": "vintage", "root_nb_vintage": "vintage",
        "root_m_ath": "athleisure", "root_f_ath": "athleisure", "root_nb_ath": "athleisure",
        "root_m_smart": "smart", "root_f_smart": "minimalist", "root_nb_smart": "smart",
    }
    if option_id in explicit:
        return explicit[option_id]

    # Check option_id and node_id fragments against known keys
    candidates = [option_id] + node_id.split("_") + style_tags
    for candidate in candidates:
        key = candidate.lower().replace(" ", "-")
        if key in STYLE_PROMPTS:
            return key
    # Fallback: try partial matches (prefer longer key matches)
    for key in sorted(STYLE_PROMPTS.keys(), key=len, reverse=True):
        for c in candidates:
            c_norm = c.lower().replace("_", "-")
            if key in c_norm or c_norm in key:
                return key
    return "smart-casual"


# Color palette prompt descriptions
COLOR_PROMPTS = {
    "earth": "a complete outfit entirely in earth tones and warm neutrals: brown, tan, olive, cream, camel. Head-to-toe look",
    "dark": "a complete outfit in dark, moody tones: all black, charcoal, deep navy, burgundy. Head-to-toe look",
    "bold": "a complete outfit with bold, vivid colors: red, cobalt blue, emerald green, statement color pops. Head-to-toe look",
    "muted": "a complete outfit in soft, muted tones: sage green, dusty blue, lavender, blush, soft pastels. Head-to-toe look",
}

# Fit/silhouette prompt descriptions
FIT_PROMPTS = {
    "slim": "a slim, tailored outfit with fitted silhouette, structured shoulders, and defined waist",
    "relaxed": "a relaxed, oversized outfit with dropped shoulders, wide-leg pants, and loose volume",
    "classic": "a classic, balanced outfit with traditional proportions and versatile everyday fit",
    "layered": "a layered, experimental outfit with mixed proportions, deconstructed details, and textural depth",
}


def build_tree_prompt(node_id: str, option: dict) -> str:
    """Build a generation prompt for a tree quiz option."""
    gender = _detect_gender(node_id)
    subject = GENDER_SUBJECTS[gender]

    # Cross-cutting color nodes — focus on color palette
    if node_id.startswith("color_"):
        color_key = option["id"].split("_")[-1]  # e.g. "color_m_earth" -> "earth"
        color_desc = COLOR_PROMPTS.get(color_key, f"{option['label']} color palette")
        return (
            f"Professional fashion photography of {subject} wearing {color_desc}. "
            f"Full body shot, clean studio background, emphasis on the color palette. "
            f"Editorial quality, photorealistic, 35mm lens."
        )

    # Cross-cutting fit nodes — focus on silhouette
    if node_id.startswith("fit_"):
        fit_key = option["id"].split("_")[-1]  # e.g. "fit_m_slim" -> "slim"
        fit_desc = FIT_PROMPTS.get(fit_key, f"{option['label']} silhouette")
        return (
            f"Professional fashion photography of {subject} wearing {fit_desc}. "
            f"Full body shot showing the complete silhouette, clean background. "
            f"Editorial quality, photorealistic, 35mm lens."
        )

    # Regular style nodes
    style_key = _detect_style_key(node_id, option["id"], option["style_tags"])
    style_desc = STYLE_PROMPTS.get(style_key, f"{option['label']} style outfit")

    tags_str = ", ".join(option["style_tags"][:5])
    return (
        f"Professional fashion photography of {subject} wearing a {style_desc}. "
        f"Style keywords: {tags_str}. "
        f"Editorial quality, full body shot, clean composition, natural lighting. "
        f"Photorealistic, 35mm lens, fashion magazine aesthetic."
    )


def build_chat_prompt(category: str, option: dict) -> str:
    """Build a generation prompt for a chat quiz option."""
    template = CHAT_CONTEXTS.get(category, "Fashion photography of {label}. {detail}")
    detail = CHAT_DETAILS.get(option["id"], option["label"])
    subject = "a young person"  # Chat questions are gender-neutral
    return template.format(label=option["label"], detail=detail, subject=subject) + (
        " Editorial quality, clean composition, photorealistic, 35mm lens."
    )


def option_id_key(source: str, node_or_cat: str, option_id: str) -> str:
    """Create a unique key for an option (used as filename stem)."""
    return f"{source}__{node_or_cat}__{option_id}"


def collect_all_options(source_filter: str = "all") -> list[dict]:
    """Collect all quiz options with their prompts."""
    options = []

    if source_filter in ("tree", "all"):
        for node_id, node in QUIZ_TREE.items():
            for opt in node["options"]:
                key = option_id_key("tree", node_id, opt["id"])
                prompt = build_tree_prompt(node_id, opt)
                options.append({
                    "key": key,
                    "source": "tree",
                    "node_id": node_id,
                    "option_id": opt["id"],
                    "label": opt["label"],
                    "prompt": prompt,
                    "aspect_ratio": "4:5",  # Portrait for tree
                })

    if source_filter in ("chat", "all"):
        for cat, q in CHAT_QUESTIONS.items():
            for opt in q["options"]:
                key = option_id_key("chat", cat, opt["id"])
                prompt = build_chat_prompt(cat, opt)
                options.append({
                    "key": key,
                    "source": "chat",
                    "node_id": cat,
                    "option_id": opt["id"],
                    "label": opt["label"],
                    "prompt": prompt,
                    "aspect_ratio": "1:1",  # Square for chat
                })

    return options


# ── Kie AI API client ────────────────────────────────────────────

API_BASE = "https://api.kie.ai"
CREATE_TASK_URL = f"{API_BASE}/api/v1/jobs/createTask"
TASK_STATUS_URL = f"{API_BASE}/api/v1/jobs/recordInfo"

# Nano Banana 2 model ID (Gemini 3.1 Flash Image via Kie AI)
MODEL_ID = "nano-banana-2"


async def submit_task(
    client: httpx.AsyncClient,
    api_key: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
    output_format: str = "png",
) -> str:
    """Submit an image generation task and return the task ID."""
    resp = await client.post(
        CREATE_TASK_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format,
            },
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"API error: {data.get('msg', data)}")
    return data["data"]["taskId"]


async def poll_task(
    client: httpx.AsyncClient,
    api_key: str,
    task_id: str,
    max_wait: int = 120,
) -> dict:
    """Poll for task completion with exponential backoff."""
    wait = 2.0
    elapsed = 0.0
    while elapsed < max_wait:
        await asyncio.sleep(wait)
        elapsed += wait

        resp = await client.get(
            TASK_STATUS_URL,
            params={"taskId": task_id},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 200:
            raise RuntimeError(f"Status API error: {data.get('msg', data)}")

        state = data["data"].get("state", "")
        if state == "success":
            return data["data"]
        elif state == "fail":
            fail_msg = data["data"].get("failMsg", "unknown")
            raise RuntimeError(f"Task {task_id} failed: {fail_msg}")

        wait = min(wait * 1.5, 10.0)

    raise TimeoutError(f"Task {task_id} did not complete within {max_wait}s")


async def download_image(
    client: httpx.AsyncClient,
    image_url: str,
    dest: Path,
) -> None:
    """Download the generated image to a local file."""
    resp = await client.get(image_url, timeout=30.0, follow_redirects=True)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


async def generate_single(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    api_key: str,
    option: dict,
    resolution: str,
    output_dir: Path,
    dry_run: bool,
) -> tuple[str, str | None]:
    """Generate a single image. Returns (key, filename|None)."""
    key = option["key"]
    filename = f"{key}.png"
    dest = output_dir / filename

    if dry_run:
        print(f"  [DRY-RUN] {key}")
        print(f"    Prompt: {option['prompt'][:100]}...")
        return key, filename

    async with semaphore:
        try:
            print(f"  Submitting: {key}...")
            task_id = await submit_task(
                client, api_key,
                option["prompt"], option["aspect_ratio"], resolution,
            )
            print(f"    Task {task_id} — polling...")
            result = await poll_task(client, api_key, task_id)

            # Parse resultJson to get the image URL
            result_json = json.loads(result.get("resultJson", "{}"))
            result_urls = result_json.get("resultUrls", [])
            if not result_urls:
                raise RuntimeError(f"No resultUrls in response for task {task_id}")
            image_url = result_urls[0]

            await download_image(client, image_url, dest)
            print(f"    Saved: {filename}")
            return key, filename
        except Exception as e:
            print(f"    FAILED: {key} — {e}")
            return key, None


async def generate_all(
    options: list[dict],
    api_key: str,
    resolution: str,
    concurrency: int,
    force: bool,
    dry_run: bool,
) -> dict[str, str]:
    """Generate images for all options. Returns manifest dict."""
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest for idempotency
    manifest: dict[str, str] = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())

    # Filter out already-generated unless --force
    to_generate = []
    for opt in options:
        key = opt["key"]
        if not force and key in manifest and (output_dir / manifest[key]).exists():
            print(f"  [SKIP] {key} (already exists)")
            continue
        to_generate.append(opt)

    if not to_generate:
        print("All images already generated. Use --force to regenerate.")
        return manifest

    print(f"\nGenerating {len(to_generate)} images (concurrency={concurrency})...\n")

    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient() as client:
        tasks = [
            generate_single(
                semaphore, client, api_key,
                opt, resolution, output_dir, dry_run,
            )
            for opt in to_generate
        ]
        results = await asyncio.gather(*tasks)

    for key, filename in results:
        if filename:
            manifest[key] = filename

    # Write manifest
    if not dry_run:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
        print(f"\nManifest written: {MANIFEST_PATH} ({len(manifest)} entries)")

    succeeded = sum(1 for _, f in results if f)
    failed = sum(1 for _, f in results if not f)
    print(f"\nDone: {succeeded} succeeded, {failed} failed")

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI quiz images via Kie AI (Nano Banana 2)"
    )
    parser.add_argument(
        "--source", choices=["tree", "chat", "all"], default="all",
        help="Which quiz options to generate images for (default: all)",
    )
    parser.add_argument(
        "--resolution", choices=["1K", "2K"], default="1K",
        help="Image resolution (default: 1K)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=3,
        help="Max concurrent API requests (default: 3)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerate all images even if they already exist",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print prompts without calling the API",
    )

    args = parser.parse_args()

    api_key = os.environ.get("KIE_API_KEY")

    if not args.dry_run and not api_key:
        print("Error: KIE_API_KEY environment variable is required.")
        print("Get your API key at https://kie.ai/api-key")
        sys.exit(1)

    options = collect_all_options(args.source)
    print(f"Collected {len(options)} quiz options (source: {args.source})")

    asyncio.run(generate_all(
        options,
        api_key=api_key or "dry-run-key",
        resolution=args.resolution,
        concurrency=args.concurrency,
        force=args.force,
        dry_run=args.dry_run,
    ))


if __name__ == "__main__":
    main()
