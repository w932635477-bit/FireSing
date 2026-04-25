#!/usr/bin/env python3
"""
Kling 3.0 Batch Video Generator (via Evolink API).
Config-driven: reads segments from video config JSON file.

Usage:
  source docs/content/.env
  python3 kling-gen-batch.py --config config/day6-yangmun.json
  python3 kling-gen-batch.py --config config/day6-yangmun.json --shot S01 --dry-run
  python3 kling-gen-batch.py --config config/day6-yangmun.json --include-stories
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REFERENCE_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

API_BASE = "https://api.evolink.ai/v1"
MODEL_IMAGE_TO_VIDEO = "kling-v3-image-to-video"


def image_to_data_uri(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/png")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def find_reference_image(shot_id: str, reference_file: str) -> Path | None:
    if not reference_file:
        return None
    exact = REFERENCE_DIR / reference_file
    if exact.exists() and exact.is_file():
        return exact
    basename = reference_file.split("/")[-1]
    exact2 = REFERENCE_DIR / basename
    if exact2.exists() and exact2.is_file():
        return exact2
    return None


def load_shots(config_path: Path, include_stories: bool = False) -> list[dict]:
    with open(config_path) as f:
        config = json.load(f)

    video_cfg = config.get("video_generation", {})
    shots = []

    for seg in config.get("segments", []):
        motion_prompt = seg.get("motion_prompt", "")
        if motion_prompt and motion_prompt != "text_card":
            emotion_arc = seg.get("emotion_arc", seg.get("emotion", ""))
            name = f"{emotion_arc}-{seg['id']}" if emotion_arc else seg["id"]
            ref_file = seg.get("reference_file", "")

            shots.append({
                "id": seg["id"],
                "name": name,
                "prompt": motion_prompt,
                "reference_file": ref_file,
                "emotion_arc": emotion_arc,
                "duration": min(video_cfg.get("duration_sec", 5), 10),
                "type": "character",
            })

        if include_stories:
            for story in seg.get("story_images", []):
                story_id = story.get("id", f"{seg['id']}-story")
                story_prompt = story.get("motion_prompt", f"slow subtle camera movement, {story.get('description', '')}")
                shots.append({
                    "id": story_id,
                    "name": story.get("description", story_id),
                    "prompt": story_prompt,
                    "reference_file": story.get("reference_file", f"{story_id}.png"),
                    "emotion_arc": "",
                    "duration": min(video_cfg.get("duration_sec", 5), 10),
                    "type": "story",
                })

    return shots


def api_request(url: str, headers: dict, data: dict | None = None) -> dict:
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method="GET" if data is None else "POST")
    if body:
        req.add_header("Content-Type", "application/json")
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_task(api_key: str, task_id: str, timeout: int = 600) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{API_BASE}/tasks/{task_id}"
    start = time.time()

    while time.time() - start < timeout:
        result = api_request(url, headers)
        status = result.get("status", "unknown")
        progress = result.get("progress", 0)
        if status == "completed":
            return result
        elif status in ("failed", "error"):
            raise RuntimeError(f"Task {task_id} failed: {result}")
        elapsed = int(time.time() - start)
        print(f"  ... {status} {progress}% ({elapsed}s elapsed)", end="\r", flush=True)
        time.sleep(10)

    raise TimeoutError(f"Task {task_id} timed out after {timeout}s")


def download_file(url: str, dest: Path) -> None:
    req = urllib.request.Request(url)
    no_proxy = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy)
    with opener.open(req, timeout=120) as resp:
        with open(dest, "wb") as f:
            f.write(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Kling 3.0 Batch Video Generator (Evolink)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--shot", type=str, help="Generate only this shot (e.g., S01)")
    parser.add_argument("--include-stories", action="store_true", help="Also generate story scene videos")
    parser.add_argument("--quality", type=str, default="720p", choices=["720p", "1080p"])
    parser.add_argument("--duration", type=int, default=5, help="Video duration in seconds (3-15)")
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

    video_id = config["video_id"]
    shots = load_shots(config_path, include_stories=args.include_stories)
    if not shots:
        print("ERROR: No segments with motion_prompt found in config")
        sys.exit(1)

    if args.shot:
        shots = [s for s in shots if s["id"] == args.shot.upper() or s["id"].startswith(args.shot.upper())]
        if not shots:
            print(f"Shot {args.shot} not found.")
            sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR / video_id

    # Estimate cost
    duration = args.duration
    price_per_sec = 0.079 if args.quality == "720p" else 0.106
    total_cost = len(shots) * duration * price_per_sec

    print("Kling 3.0 Batch Video Generator (Evolink)")
    print("=" * 50)
    print(f"Config: {config_path.name}")
    print(f"Video ID: {video_id}")
    print(f"Shots: {len(shots)} ({', '.join(s['id'] for s in shots)})")
    print(f"Model: {MODEL_IMAGE_TO_VIDEO}")
    print(f"Quality: {args.quality} | Duration: {duration}s | Aspect: 9:16")
    print(f"Est. cost: ${total_cost:.2f} ({len(shots) * duration}s x ${price_per_sec}/s)")
    print(f"Output: {output_dir}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for shot in shots:
            ref = find_reference_image(shot["id"], shot["reference_file"])
            status = "found" if ref else "MISSING"
            print(f"  {shot['id']} [{shot.get('type', '?')}]: {status}")
            if ref:
                print(f"    Ref: {ref.name}")
            print(f"    Motion: {shot['prompt']}")
        return

    api_key = os.environ.get("EVOLINK_API_KEY")
    if not api_key:
        print("ERROR: EVOLINK_API_KEY not set")
        print("  source docs/content/.env")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    results = []
    for shot in shots:
        ref_path = find_reference_image(shot["id"], shot["reference_file"])
        if not ref_path:
            print(f"\n[SKIP] {shot['id']}: no reference_file in config (exact path required, no fallback)")
            continue

        print(f"\n[{shot['id']}] {shot['name']}")
        print(f"  Reference: {ref_path.name}")
        print(f"  Prompt: {shot['prompt'][:80]}...")

        data_uri = image_to_data_uri(ref_path)

        payload = {
            "model": MODEL_IMAGE_TO_VIDEO,
            "prompt": shot["prompt"],
            "image_start": data_uri,
            "duration": duration,
            "aspect_ratio": "9:16",
            "quality": args.quality,
            "sound": "off",
        }

        try:
            print("  Submitting... ", end="", flush=True)
            resp = api_request(f"{API_BASE}/videos/generations", headers, payload)
            task_id = resp.get("id") or resp.get("task_id")
            if not task_id:
                print(f"\n  X Unexpected response: {resp}")
                results.append({"shot": shot["id"], "status": "error", "error": str(resp)})
                continue
            print(f"task_id={task_id}")

            task_result = poll_task(api_key, task_id)
            print(f"  Completed")

            video_url = None
            result_data = task_result.get("result_data", {})
            if isinstance(result_data, dict):
                task_result_inner = result_data.get("task_result", {})
                videos = task_result_inner.get("videos", [])
                if videos and isinstance(videos, list):
                    video_url = videos[0].get("url")
            if not video_url and isinstance(result_data, list):
                for item in result_data:
                    if isinstance(item, dict) and "url" in item:
                        video_url = item["url"]
                        break
            if not video_url:
                video_url = task_result.get("video_url") or task_result.get("output", {}).get("video_url")

            if video_url:
                dest = output_dir / f"{shot['id']}.mp4"
                print(f"  Downloading {shot['id']}.mp4... ", end="", flush=True)
                download_file(video_url, dest)
                size_mb = dest.stat().st_size / (1024 * 1024)
                print(f"saved ({size_mb:.1f}MB)")
                results.append({"shot": shot["id"], "file": str(dest), "task_id": task_id, "status": "success"})
            else:
                print(f"  X No video URL in response: {task_result}")
                results.append({"shot": shot["id"], "task_id": task_id, "status": "error", "error": "no video url"})

        except Exception as e:
            print(f"\n  X Error: {e}")
            results.append({"shot": shot["id"], "status": "error", "error": str(e)})

    log_path = output_dir / f"kling-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": MODEL_IMAGE_TO_VIDEO,
            "video_id": video_id,
            "quality": args.quality,
            "duration": duration,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nLog saved: {log_path}")

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed | Cost: ~${success * duration * price_per_sec:.2f}")


if __name__ == "__main__":
    main()
