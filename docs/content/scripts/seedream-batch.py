#!/usr/bin/env python3
"""
Seedream 4.5 Batch Reference Image Generator
Generates reference images for Day 1 storyboard via EvoLink API.

Usage:
  export EVOLINK_API_KEY="your-api-key"
  python seedream-batch.py [--candidates N] [--output-dir DIR]
  python seedream-batch.py --shot S01 --dry-run

Options:
  --candidates N    Generate N candidates per shot (1-15, default: 2)
  --output-dir DIR  Output directory (default: docs/content/assets/references)
  --shot S01        Generate only a specific shot
  --dry-run         Show plan without generating
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"

API_BASE = "https://api.evolink.ai/v1"
MODEL = "doubao-seedream-4.5"

# Day 1 v2: 5 shots (S06 is text card, no image needed)
# Story-driven approach: specific people in specific scenes, emotional connection to voiceover
# Anti-AI: real camera specs, film stock, no hands, no text, natural imperfections
SHOTS = [
    {
        "id": "S01",
        "name": "钩子-孤独决心",
        "prompt": (
            "close-up of a young man's face in near total darkness, "
            "the only light is warm amber screen glow from below illuminating his eyes and jaw, "
            "expression of quiet fierce determination, "
            "the rest of the frame is pure deep black void, "
            "stark minimal composition, warm amber and black palette, "
            "cinematic mood lighting, natural film grain texture, "
            "face positioned in lower center, vertical composition 9:16"
        ),
        "output_file": "S01-hook-isolation.png",
        "cost_per_image": 0.030,
    },
    {
        "id": "S02",
        "name": "卑微起点",
        "prompt": (
            "warm golden afternoon light flooding a small sparse room, "
            "a person sitting on the floor hunched over a laptop, "
            "seen from behind so the face is not visible, "
            "surroundings simple and bare barely visible in the warm shadows, "
            "the entire scene radiates quiet hope from humble beginnings, "
            "warm golden and deep amber tones, natural light, soft shadows, "
            "subject small in lower frame emphasizing the modest space, "
            "vertical composition 9:16"
        ),
        "output_file": "S02-humble-beginnings.png",
        "cost_per_image": 0.030,
    },
    {
        "id": "S03",
        "name": "数据震撼",
        "prompt": (
            "abstract golden light trails rising upward from deep black void, "
            "warm amber data visualization lines and bars trending dramatically upward, "
            "volumetric golden light creating sense of massive scale and achievement, "
            "no people no text no numbers, pure atmospheric data mood, "
            "warm gold and deep navy black palette, cinematic volumetric lighting, "
            "natural grain texture, glow centered in lower two-thirds, "
            "vertical composition 9:16"
        ),
        "output_file": "S03-data-awe.png",
        "cost_per_image": 0.030,
    },
    {
        "id": "S04",
        "name": "两人草根",
        "prompt": (
            "two faces close together lit only by warm screen glow in total darkness, "
            "leaning in studying something with intense focus, "
            "partnership against the world energy, "
            "deep shadows swallowing everything except their expressions, "
            "tight intimate framing, warm amber light on faces against pure black, "
            "natural film grain, cinematic mood, "
            "faces in lower two-thirds, vertical composition 9:16"
        ),
        "output_file": "S04-two-vs-world.png",
        "cost_per_image": 0.030,
    },
    {
        "id": "S05",
        "name": "一人帝国",
        "prompt": (
            "wide shot of a single figure at a desk in a vast empty dark office, "
            "rows of vacant desks stretching into deep shadow behind, "
            "the negative space tells the story of one person doing the work of many, "
            "cool ambient light from monitors mixing with warm desk lamp glow, "
            "cinematic atmosphere, moody and quiet, "
            "natural film grain, figure small in lower third with vast emptiness above, "
            "vertical composition 9:16"
        ),
        "output_file": "S05-one-person-empire.png",
        "cost_per_image": 0.030,
    },
]


def api_request(url: str, headers: dict, data: dict | None = None) -> dict:
    """Make HTTP request to EvoLink API. Bypasses local proxy if present."""
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method="GET" if data is None else "POST")
    if body:
        req.add_header("Content-Type", "application/json")
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_task(api_key: str, task_id: str, timeout: int = 300) -> dict:
    """Poll async task until completion or timeout."""
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
    """Download image from URL to local file. Bypasses local proxy."""
    req = urllib.request.Request(url)
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=60) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())


def run_batch(api_key: str, shots: list[dict], output_dir: Path, candidates: int = 2):
    """Generate reference images for all shots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    results = []
    total = len(shots) * candidates
    completed = 0

    for shot in shots:
        print(f"\n[{shot['id']}] {shot['name']}")
        print(f"  Prompt: {shot['prompt'][:80]}...")
        print(f"  Size: 1440x2560 (9:16 2K) | Candidates: {candidates}")

        payload = {
            "model": MODEL,
            "prompt": shot["prompt"],
            "n": candidates,
            "size": "1440x2560",
            "prompt_priority": "standard",
        }

        try:
            print("  Submitting task... ", end="", flush=True)
            resp = api_request(f"{API_BASE}/images/generations", headers, payload)
            task_id = resp.get("task_id") or resp.get("id")
            if not task_id:
                print(f"\n  ✗ Unexpected response: {resp}")
                results.append({"shot": shot["id"], "status": "error", "error": str(resp)})
                continue
            print(f"task_id={task_id}")

            task_result = poll_task(api_key, task_id)
            # EvoLink returns images in result_data[].url or results[]
            images = []
            for item in task_result.get("result_data", []):
                if isinstance(item, dict) and "url" in item:
                    images.append(item["url"])
                elif isinstance(item, str):
                    images.append(item)
            if not images:
                images = task_result.get("results", [])

            for idx, img_url in enumerate(images):
                suffix = f"_v{idx + 1}" if len(images) > 1 else ""
                stem = shot["output_file"].rsplit(".", 1)[0]
                ext = shot["output_file"].rsplit(".", 1)[1]
                filename = f"{stem}{suffix}.{ext}"
                dest = output_dir / filename

                print(f"  Downloading {filename}... ", end="", flush=True)
                download_image(img_url, dest)
                print(f"✓ saved ({dest.stat().st_size // 1024}KB)")

                results.append({
                    "shot": shot["id"],
                    "file": str(dest),
                    "task_id": task_id,
                    "status": "success",
                })
                completed += 1

            # If only 1 candidate, also save as the canonical name for Runway compatibility
            if candidates == 1 and images:
                canonical = output_dir / shot["output_file"]
                if not canonical.exists():
                    download_image(images[0], canonical)

        except Exception as e:
            print(f"\n  ✗ Error: {e}")
            results.append({"shot": shot["id"], "status": "error", "error": str(e)})

        print(f"  Progress: {completed}/{total}")

    # Save log
    log_path = output_dir / f"seedream-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "shots": len(shots),
            "candidates_per_shot": candidates,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nLog saved: {log_path}")

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    cost = success * 0.030
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed | Cost: ${cost:.2f}")
    if failed > 0:
        print("Failed shots:")
        for r in results:
            if r["status"] != "success":
                print(f"  - {r['shot']}: {r.get('error', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="Seedream 4.5 Batch Reference Image Generator")
    parser.add_argument("--candidates", type=int, default=2, help="Candidates per shot (1-15, default: 2)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this shot (e.g., S01)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    # Validate
    if args.candidates < 1 or args.candidates > 15:
        print("ERROR: --candidates must be 1-15")
        sys.exit(1)

    # Filter shots
    shots = SHOTS
    if args.shot:
        shots = [s for s in SHOTS if s["id"] == args.shot.upper()]
        if not shots:
            print(f"Shot {args.shot} not found. Available: {', '.join(s['id'] for s in SHOTS)}")
            sys.exit(1)

    total_images = len(shots) * args.candidates
    print("Seedream 4.5 Batch Reference Image Generator")
    print("=" * 50)
    print(f"Shots: {len(shots)} ({', '.join(s['id'] for s in shots)})")
    print(f"Candidates per shot: {args.candidates}")
    print(f"Total images: {total_images}")
    print(f"Model: {MODEL}")
    print(f"Size: 1440x2560 (9:16 2K)")
    print(f"Output: {args.output_dir}")
    print(f"Est. cost: ${total_images * 0.030:.2f}")
    print()

    if args.dry_run:
        print("DRY RUN - no generation will happen.")
        print("\nShot plan:")
        for shot in shots:
            existing = (Path(args.output_dir) / shot["output_file"]).exists()
            status = "✓ exists (will overwrite)" if existing else "○ new"
            print(f"  {shot['id']} {shot['name']}: {status}")
            print(f"    {shot['prompt'][:100]}...")
        return

    api_key = os.environ.get("EVOLINK_API_KEY")
    if not api_key:
        print("ERROR: EVOLINK_API_KEY not set")
        print("  export EVOLINK_API_KEY='your-api-key'")
        print("  Get your key at: https://evolink.ai")
        sys.exit(1)

    run_batch(
        api_key=api_key,
        shots=shots,
        output_dir=Path(args.output_dir),
        candidates=args.candidates,
    )


if __name__ == "__main__":
    main()
