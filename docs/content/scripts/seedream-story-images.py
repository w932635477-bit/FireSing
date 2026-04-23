#!/usr/bin/env python3
"""
Generate story scene images from a video config's story_images arrays.
Reads the story_images from each segment and generates them via Seedream API.

Usage:
  source docs/content/.env
  python3 seedream-story-images.py --config config/day6-yangmun.json
  python3 seedream-story-images.py --config config/day6-yangmun.json --dry-run
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REFERENCE_ROOT = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

API_BASE = "https://api.evolink.ai/v1"
MODEL = "doubao-seedream-4.5"


def load_story_images(config_path: Path) -> list[dict]:
    """Extract all story_images from segments."""
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    shots = []

    for seg in config.get("segments", []):
        for story in seg.get("story_images", []):
            story_id = story.get("id", f"{seg['id']}-story")
            shots.append({
                "id": story_id,
                "segment": seg["id"],
                "prompt": story["reference_prompt"],
                "description": story.get("description", ""),
                "output_file": f"{story_id}.png",
            })

    return shots


def api_request(url: str, headers: dict, data: dict | None = None) -> dict:
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method="GET" if data is None else "POST")
    if body:
        req.add_header("Content-Type", "application/json")
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_task(api_key: str, task_id: str, timeout: int = 300) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{API_BASE}/tasks/{task_id}"
    start = time.time()

    while time.time() - start < timeout:
        result = api_request(url, headers)
        status = result.get("status", "unknown")
        if status == "completed":
            return result
        elif status in ("failed", "error"):
            raise RuntimeError(f"Task {task_id} failed: {result}")
        print(f"  ... {status} (waiting 5s)", end="\r", flush=True)
        time.sleep(5)

    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")


def download_image(url: str, dest: Path) -> None:
    req = urllib.request.Request(url)
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Generate story scene images from config")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = DEFAULT_CONFIG_DIR / config_path
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    negative_prompt = config.get("reference_images", {}).get("negative_prompt")
    shots = load_story_images(config_path)
    if not shots:
        print("No story_images found in config")
        sys.exit(0)

    print("Seedream Story Image Generator")
    print("=" * 50)
    print(f"Config: {config_path.name}")
    print(f"Story images: {len(shots)}")
    for shot in shots:
        print(f"  {shot['id']} ({shot['segment']}): {shot['description']}")
    print(f"Model: {MODEL}")
    print(f"Size: 1440x2560 (9:16 2K)")
    print(f"Video ID: {config['video_id']}")
    print(f"Est. cost: ${len(shots) * 0.030:.2f}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for shot in shots:
            print(f"  {shot['id']}: {shot['prompt'][:80]}...")
        return

    api_key = os.environ.get("EVOLINK_API_KEY")
    if not api_key:
        print("ERROR: EVOLINK_API_KEY not set")
        print("  source docs/content/.env")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else REFERENCE_ROOT / config["video_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    results = []
    for shot in shots:
        print(f"\n[{shot['id']}] {shot['description']}")
        print(f"  Prompt: {shot['prompt'][:80]}...")

        payload = {
            "model": MODEL,
            "prompt": shot["prompt"],
            "n": 1,
            "size": "1440x2560",
            "prompt_priority": "standard",
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            print("  Submitting... ", end="", flush=True)
            resp = api_request(f"{API_BASE}/images/generations", headers, payload)
            task_id = resp.get("task_id") or resp.get("id")
            if not task_id:
                print(f"\n  X Unexpected response: {resp}")
                results.append({"shot": shot["id"], "status": "error", "error": str(resp)})
                continue
            print(f"task_id={task_id}")

            task_result = poll_task(api_key, task_id)
            images = []
            for item in task_result.get("result_data", []):
                if isinstance(item, dict) and "url" in item:
                    images.append(item["url"])
                elif isinstance(item, str):
                    images.append(item)
            if not images:
                images = task_result.get("results", [])

            if images:
                dest = output_dir / shot["output_file"]
                print(f"  Downloading {shot['output_file']}... ", end="", flush=True)
                download_image(images[0], dest)
                print(f"saved ({dest.stat().st_size // 1024}KB)")
                results.append({"shot": shot["id"], "file": str(dest), "status": "success"})
            else:
                print("  X No images returned")
                results.append({"shot": shot["id"], "status": "error", "error": "no images"})

        except Exception as e:
            print(f"\n  X Error: {e}")
            results.append({"shot": shot["id"], "status": "error", "error": str(e)})

    log_path = output_dir / f"seedream-story-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "model": MODEL, "results": results}, f, indent=2)

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed | Cost: ${success * 0.030:.2f}")


if __name__ == "__main__":
    main()
