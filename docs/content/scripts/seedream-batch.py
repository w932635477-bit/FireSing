#!/usr/bin/env python3
"""
Seedream 4.5 Batch Reference Image Generator
Reads segment prompts from a video config JSON file.

Usage:
  source docs/content/.env
  python seedream-batch.py --config config/day1-medvi-story.json
  python seedream-batch.py --config config/day1-medvi-story.json --shot S01 --dry-run

Options:
  --config FILE     Video config JSON file (required)
  --candidates N    Override candidates per shot (1-15, default: from config)
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

API_BASE = "https://api.evolink.ai/v1"
MODEL = "doubao-seedream-4.5"


def load_shots_from_config(config_path: Path) -> list[dict]:
    """Load segments from config JSON and convert to shot format."""
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    shots = []

    for seg in config["segments"]:
        prompt = seg.get("reference_prompt", "")
        if not prompt or prompt == "text_card":
            continue

        emotion_arc = seg.get("emotion_arc", seg.get("emotion", ""))
        name = f"{emotion_arc}-{seg['id']}" if emotion_arc else seg["id"]
        output_file = f"{seg['id']}-{emotion_arc.lower().replace('/', '-')}.png"

        shots.append({
            "id": seg["id"],
            "name": name,
            "prompt": prompt,
            "output_file": output_file,
            "cost_per_image": 0.030,
            "emotion_arc": emotion_arc,
            "voiceover_text": seg.get("voiceover_text", ""),
        })

    return shots


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


def run_batch(
    api_key: str,
    shots: list[dict],
    output_dir: Path,
    candidates: int = 2,
    negative_prompt: str | None = None,
):
    """Generate reference images for all shots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    results = []
    total = len(shots) * candidates
    completed = 0

    for shot in shots:
        print(f"\n[{shot['id']}] {shot['name']}")
        print(f"  Emotion arc: {shot.get('emotion_arc', 'N/A')}")
        print(f"  Prompt: {shot['prompt'][:80]}...")
        print(f"  Voiceover: {shot.get('voiceover_text', '')[:50]}...")
        print(f"  Size: 1440x2560 (9:16 2K) | Candidates: {candidates}")
        if negative_prompt:
            print(f"  Negative prompt: {negative_prompt[:60]}...")

        payload = {
            "model": MODEL,
            "prompt": shot["prompt"],
            "n": candidates,
            "size": "1440x2560",
            "prompt_priority": "standard",
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            print("  Submitting task... ", end="", flush=True)
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

            for idx, img_url in enumerate(images):
                suffix = f"_v{idx + 1}" if len(images) > 1 else ""
                stem = shot["output_file"].rsplit(".", 1)[0]
                ext = shot["output_file"].rsplit(".", 1)[1]
                filename = f"{stem}{suffix}.{ext}"
                dest = output_dir / filename

                print(f"  Downloading {filename}... ", end="", flush=True)
                download_image(img_url, dest)
                print(f"saved ({dest.stat().st_size // 1024}KB)")

                results.append({
                    "shot": shot["id"],
                    "file": str(dest),
                    "task_id": task_id,
                    "status": "success",
                })
                completed += 1

        except Exception as e:
            print(f"\n  X Error: {e}")
            results.append({"shot": shot["id"], "status": "error", "error": str(e)})

        print(f"  Progress: {completed}/{total}")

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
    parser.add_argument("--config", type=str, help="Video config JSON file (relative to config/ or absolute)")
    parser.add_argument("--candidates", type=int, help="Override candidates per shot (1-15)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this shot (e.g., S01)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    # Resolve config path
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = DEFAULT_CONFIG_DIR / config_path
        if not config_path.exists():
            print(f"ERROR: Config file not found: {config_path}")
            sys.exit(1)
    else:
        print("ERROR: --config is required")
        print("  python seedream-batch.py --config config/day1-medvi-story.json")
        sys.exit(1)

    # Load shots from config
    shots = load_shots_from_config(config_path)
    if not shots:
        print("ERROR: No segments with reference_prompt found in config")
        sys.exit(1)

    # Get candidates from config or CLI override
    with open(config_path) as f:
        config = json.load(f)
    candidates = args.candidates or config.get("reference_images", {}).get("candidates_per_segment", 2)
    negative_prompt = config.get("reference_images", {}).get("negative_prompt")

    if candidates < 1 or candidates > 15:
        print("ERROR: candidates must be 1-15")
        sys.exit(1)

    # Filter shots
    if args.shot:
        shots = [s for s in shots if s["id"] == args.shot.upper()]
        if not shots:
            print(f"Shot {args.shot} not found. Available: {', '.join(s['id'] for s in load_shots_from_config(config_path))}")
            sys.exit(1)

    total_images = len(shots) * candidates
    print("Seedream 4.5 Batch Reference Image Generator")
    print("=" * 50)
    print(f"Config: {config_path.name}")
    print(f"Shots: {len(shots)} ({', '.join(s['id'] for s in shots)})")
    print(f"Candidates per shot: {candidates}")
    print(f"Total images: {total_images}")
    print(f"Model: {MODEL}")
    print(f"Size: 1440x2560 (9:16 2K)")
    print(f"Output: {args.output_dir}")
    print(f"Est. cost: ${total_images * 0.030:.2f}")
    print()
    print("Emotion arc:")
    for shot in shots:
        print(f"  {shot['id']}: {shot.get('emotion_arc', '?')}")
    print()

    if args.dry_run:
        print("DRY RUN - no generation will happen.")
        print("\nShot plan:")
        for shot in shots:
            existing = (Path(args.output_dir) / shot["output_file"]).exists()
            status = "exists (will overwrite)" if existing else "new"
            print(f"  {shot['id']} [{shot.get('emotion_arc', '?')}]: {status}")
            print(f"    {shot['prompt'][:100]}...")
        return

    api_key = os.environ.get("EVOLINK_API_KEY")
    if not api_key:
        print("ERROR: EVOLINK_API_KEY not set")
        print("  source docs/content/.env")
        sys.exit(1)

    run_batch(
        api_key=api_key,
        shots=shots,
        output_dir=Path(args.output_dir),
        candidates=candidates,
        negative_prompt=negative_prompt,
    )


if __name__ == "__main__":
    main()
