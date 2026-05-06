#!/usr/bin/env python3
"""
DALL-E 3 Batch Image Generator via yunwu.ai OpenAI-compatible API.
Reads image prompts from a video config JSON file.

Usage:
  source docs/content/.env
  python3 dalle-gen-batch.py --config config/unemploy-day3-ai-portrait.json
  python3 dalle-gen-batch.py --config config/unemploy-day3-ai-portrait.json --shot IMG01 --dry-run

Options:
  --config FILE       Video config JSON file (required)
  --shot IMG01        Generate only a specific image
  --output-dir DIR    Output directory (default: docs/content/assets/references/{video_id})
  --fallback-seedream Fall back to Seedream 4.5 via EvoLink if DALL-E fails
  --dry-run           Show plan without generating
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REFERENCE_ROOT = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

YUNWU_BASE_URL = "https://yunwu.ai/v1"
SEEDREAM_API_BASE = "https://api.evolink.ai/v1"
SEEDREAM_MODEL = "doubao-seedream-4.5"


def load_images_from_config(config_path: Path) -> list[dict]:
    """Load image definitions from config JSON."""
    with open(config_path) as f:
        config = json.load(f)

    images = config.get("images", [])
    if not images:
        sys.exit("ERROR: No 'images' array found in config")

    return images


def generate_dalle(client: OpenAI, prompt: str, size: str = "1024x1792") -> str:
    """Generate image via DALL-E 3. Returns image URL."""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1,
    )
    return response.data[0].url


def download_image(url: str, dest: Path) -> None:
    """Download image from URL, bypassing local proxy."""
    req = urllib.request.Request(url)
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())


def generate_seedream(api_key: str, prompt: str, output_path: Path) -> None:
    """Generate image via Seedream 4.5 (EvoLink) as fallback."""
    import json as _json

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": SEEDREAM_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": "1440x2560",
    }
    body = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SEEDREAM_API_BASE}/images/generations",
        data=body,
        headers=headers,
        method="POST",
    )
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        result = _json.loads(resp.read().decode("utf-8"))

    task_id = result.get("task_id") or result.get("id")
    if not task_id:
        raise RuntimeError(f"Seedream unexpected response: {result}")

    # Poll for completion
    poll_url = f"{SEEDREAM_API_BASE}/tasks/{task_id}"
    start = time.time()
    while time.time() - start < 300:
        poll_req = urllib.request.Request(poll_url, headers={"Authorization": f"Bearer {api_key}"})
        with opener.open(poll_req, timeout=60) as poll_resp:
            poll_result = _json.loads(poll_resp.read().decode("utf-8"))
        status = poll_result.get("status", "unknown")
        if status == "completed":
            images = poll_result.get("result_data", [])
            if images and isinstance(images[0], dict):
                img_url = images[0]["url"]
            else:
                img_url = images[0] if images else ""
            if not img_url:
                raise RuntimeError(f"Seedream no image URL in result: {poll_result}")
            download_image(img_url, output_path)
            return
        elif status in ("failed", "error"):
            raise RuntimeError(f"Seedream task failed: {poll_result}")
        print(f"  ... {status} (5s)", end="\r", flush=True)
        time.sleep(5)
    raise TimeoutError(f"Seedream task {task_id} timed out")


def run_batch(
    images: list[dict],
    output_dir: Path,
    yunwu_key: str,
    fallback_seedream: bool = False,
    evolink_key: str | None = None,
) -> list[dict]:
    """Generate all images with DALL-E 3, optional Seedream fallback."""
    output_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=yunwu_key, base_url=YUNWU_BASE_URL)

    results = []
    for img in images:
        img_id = img["id"]
        prompt = img["prompt"]
        output_file = img["output_file"]
        dest = output_dir / output_file

        print(f"\n[{img_id}] {prompt[:80]}...")

        # Skip if exists
        if dest.exists():
            print(f"  EXISTS: {dest} ({dest.stat().st_size // 1024}KB) — skipping")
            results.append({"id": img_id, "file": str(dest), "status": "exists"})
            continue

        # Try DALL-E 3
        success = False
        try:
            print("  DALL-E 3 generating... ", end="", flush=True)
            url = generate_dalle(client, prompt)
            download_image(url, dest)
            print(f"done ({dest.stat().st_size // 1024}KB)")
            results.append({"id": img_id, "file": str(dest), "status": "success", "engine": "dall-e-3"})
            success = True
        except Exception as e:
            print(f"failed: {e}")
            if not fallback_seedream:
                results.append({"id": img_id, "status": "error", "error": str(e)})
                continue

        # Fallback to Seedream
        if not success and fallback_seedream and evolink_key:
            print("  Falling back to Seedream 4.5... ", end="", flush=True)
            try:
                generate_seedream(evolink_key, prompt, dest)
                print(f"done ({dest.stat().st_size // 1024}KB)")
                results.append({"id": img_id, "file": str(dest), "status": "success", "engine": "seedream-4.5"})
            except Exception as e2:
                print(f"failed: {e2}")
                results.append({"id": img_id, "status": "error", "error": str(e2)})

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="DALL-E 3 Batch Image Generator (via yunwu.ai)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--shot", type=str, help="Generate only this image (e.g., IMG01)")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--fallback-seedream", action="store_true", help="Fall back to Seedream if DALL-E fails")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = DEFAULT_CONFIG_DIR / config_path
    if not config_path.exists():
        sys.exit(f"ERROR: Config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    images = load_images_from_config(config_path)

    if args.shot:
        images = [i for i in images if i["id"] == args.shot.upper()]
        if not images:
            sys.exit(f"Image {args.shot} not found. Available: {', '.join(i['id'] for i in config.get('images', []))}")

    output_dir = Path(args.output_dir) if args.output_dir else REFERENCE_ROOT / video_id

    print("DALL-E 3 Batch Image Generator")
    print("=" * 50)
    print(f"Config: {config_path.name}")
    print(f"Video ID: {video_id}")
    print(f"Images: {len(images)} ({', '.join(i['id'] for i in images)})")
    print(f"Output: {output_dir}")
    print(f"API: yunwu.ai (OpenAI-compatible)")
    print(f"Seedream fallback: {'yes' if args.fallback_seedream else 'no'}")
    print(f"Est. cost: ${len(images) * 0.04:.2f}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for img in images:
            existing = (output_dir / img["output_file"]).exists()
            status = "EXISTS" if existing else "NEW"
            print(f"  {img['id']} [{status}]: {img['prompt'][:80]}...")
        return

    yunwu_key = os.environ.get("YUNWU_API_KEY")
    if not yunwu_key:
        sys.exit("ERROR: YUNWU_API_KEY not set. Run: source docs/content/.env")

    evolink_key = os.environ.get("EVOLINK_API_KEY") if args.fallback_seedream else None

    results = run_batch(images, output_dir, yunwu_key, args.fallback_seedream, evolink_key)

    # Save log
    log_path = output_dir / f"dalle-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "dall-e-3-via-yunwu",
            "video_id": video_id,
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    success = sum(1 for r in results if r["status"] in ("success", "exists"))
    failed = sum(1 for r in results if r["status"] == "error")
    cost = sum(0.04 for r in results if r["status"] == "success")
    print(f"\n{'=' * 50}")
    print(f"Done: {success} ok, {failed} failed | Cost: ${cost:.2f}")


if __name__ == "__main__":
    main()
