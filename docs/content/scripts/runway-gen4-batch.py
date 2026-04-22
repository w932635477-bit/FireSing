#!/usr/bin/env python3
"""
Runway Gen-4 Batch Video Generator
Config-driven: reads segments from video config JSON file.

Usage:
  export RUNWAYML_API_SECRET="your-api-key"
  python runway-gen4-batch.py --config config/day1-medvi-story.json
  python runway-gen4-batch.py --config config/day1-medvi-story.json --turbo --shot S01 --dry-run

Options:
  --config FILE     Video config JSON file (required)
  --turbo           Use Gen-4 Turbo (default)
  --no-turbo        Use Gen-4 (higher quality, for final)
  --output-dir DIR  Output directory
  --shot S01        Generate only a specific shot
  --candidates N    Candidates per shot (default: from config)
  --dry-run         Show plan without generating
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from runwayml import RunwayML

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REFERENCE_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"


def load_shots_from_config(config_path: Path) -> list[dict]:
    """Load segments from config JSON and convert to Runway shot format."""
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    video_cfg = config.get("video_generation", {})
    shots = []

    for seg in config["segments"]:
        motion_prompt = seg.get("motion_prompt", "")
        if not motion_prompt or motion_prompt == "text_card":
            continue

        emotion_arc = seg.get("emotion_arc", seg.get("emotion", ""))
        name = f"{emotion_arc}-{seg['id']}" if emotion_arc else seg["id"]

        # Use explicit reference_file from config, or auto-detect
        ref_file = seg.get("reference_file", "")
        if not ref_file:
            ref_candidates = sorted(REFERENCE_DIR.glob(f"{seg['id']}-*.png"))
            ref_file = ref_candidates[0].name if ref_candidates else f"{seg['id']}.png"

        runway_duration = min(video_cfg.get("duration_sec", 5), 10)
        shots.append({
            "id": seg["id"],
            "name": name,
            "duration": runway_duration,
            "segment_duration": seg.get("duration_sec", 5),
            "ratio": video_cfg.get("resolution", "720x1280").replace("x", ":"),
            "prompt": motion_prompt,
            "reference_file": ref_file,
            "emotion_arc": emotion_arc,
        })

    return shots


def image_to_data_uri(image_path: Path) -> str:
    """Convert local image file to base64 data URI."""
    suffix = image_path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/png")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def find_reference_image(shot_id: str, reference_file: str) -> Path | None:
    """Find reference image — try exact filename first, then glob fallback."""
    exact = REFERENCE_DIR / reference_file
    if exact.exists():
        return exact
    if REFERENCE_DIR.exists():
        for f in sorted(REFERENCE_DIR.iterdir()):
            if f.name.startswith(shot_id) and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                return f
    return None


def run_batch(
    client: RunwayML,
    shots: list[dict],
    video_id: str,
    output_dir: Path,
    turbo: bool = True,
    candidates_per_shot: int = 1,
    seed: int | None = None,
):
    """Generate all shots via Runway API."""
    model = "gen4_turbo" if turbo else "gen4"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(shots) * candidates_per_shot
    completed = 0

    for shot in shots:
        ref_path = find_reference_image(shot["id"], shot["reference_file"])
        if not ref_path:
            print(f"[SKIP] {shot['id']}: no reference image found")
            continue

        print(f"\n[{shot['id']}] {shot['name']}")
        print(f"  Reference: {ref_path.name}")
        print(f"  Prompt: {shot['prompt']}")
        print(f"  Model: {model} | Duration: {shot['duration']}s")

        data_uri = image_to_data_uri(ref_path)

        for candidate_idx in range(candidates_per_shot):
            suffix = f"_v{candidate_idx + 1}" if candidates_per_shot > 1 else ""
            output_name = f"{shot['id']}{suffix}.mp4"

            try:
                print(f"  Generating{suffix}... ", end="", flush=True)
                kwargs: dict = {
                    "model": model,
                    "prompt_image": data_uri,
                    "prompt_text": shot["prompt"],
                    "ratio": shot["ratio"],
                    "duration": shot["duration"],
                }
                if seed is not None:
                    kwargs["seed"] = seed
                task = client.image_to_video.create(**kwargs)
                task_id = task.id
                print(f"task_id={task_id}")

                while True:
                    task_result = client.tasks.retrieve(task_id)
                    status = task_result.status
                    if status == "SUCCEEDED":
                        print(f"  SUCCEEDED")
                        break
                    elif status == "FAILED":
                        print(f"  FAILED: {getattr(task_result, 'error', 'unknown')}")
                        break
                    else:
                        print(f"  ... {status} (10s)", end="\r", flush=True)
                        time.sleep(10)

                if status == "SUCCEEDED" and task_result.output:
                    video_url = task_result.output[0] if isinstance(task_result.output, list) else task_result.output
                    output_path = output_dir / output_name
                    import urllib.request
                    urllib.request.urlretrieve(video_url, str(output_path))
                    print(f"  Saved: {output_path.name}")
                    results.append({"shot": shot["id"], "file": str(output_path), "task_id": task_id, "status": "success"})
                else:
                    results.append({"shot": shot["id"], "task_id": task_id, "status": "failed"})

                completed += 1
                print(f"  Progress: {completed}/{total}")

            except Exception as e:
                print(f"  Error: {e}")
                results.append({"shot": shot["id"], "status": "error", "error": str(e)})

    log_path = output_dir / f"runway-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "video_id": video_id,
            "shots": len(shots),
            "candidates_per_shot": candidates_per_shot,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nLog saved: {log_path}")

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed out of {total}")


def main():
    parser = argparse.ArgumentParser(description="Runway Gen-4 Batch Video Generator (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--turbo", action="store_true", default=True, help="Use Gen-4 Turbo (default)")
    parser.add_argument("--no-turbo", dest="turbo", action="store_false", help="Use Gen-4 (higher quality)")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--shot", type=str, help="Generate only this shot (e.g., S01)")
    parser.add_argument("--candidates", type=int, default=None, help="Candidates per shot")
    parser.add_argument("--seed", type=int, default=None, help="Fixed seed for consistency")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    # Resolve config path
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = DEFAULT_CONFIG_DIR / config_path
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    video_cfg = config.get("video_generation", {})

    shots = load_shots_from_config(config_path)
    if not shots:
        print("ERROR: No segments with motion_prompt found in config")
        sys.exit(1)

    candidates = args.candidates or video_cfg.get("candidates_per_segment", 1)
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_OUTPUT_DIR / video_id

    if args.shot:
        shots = [s for s in shots if s["id"] == args.shot.upper()]
        if not shots:
            all_shots = load_shots_from_config(config_path)
            print(f"Shot {args.shot} not found. Available: {', '.join(s['id'] for s in all_shots)}")
            sys.exit(1)

    print("Runway Gen-4 Batch Video Generator")
    print("=" * 50)
    print(f"Config: {config_path.name}")
    print(f"Video ID: {video_id}")
    print(f"Shots: {len(shots)} ({', '.join(s['id'] for s in shots)})")
    print(f"Candidates per shot: {candidates}")
    print(f"Model: {'Gen-4 Turbo' if args.turbo else 'Gen-4'}")
    print(f"Resolution: {video_cfg.get('resolution', '720x1280')}")
    print(f"Output: {output_dir}")
    print()

    if args.dry_run:
        print("DRY RUN - no generation will happen.\n")
        for shot in shots:
            ref = find_reference_image(shot["id"], shot["reference_file"])
            status = "found" if ref else "MISSING"
            print(f"  {shot['id']} [{shot.get('emotion_arc', '?')}]: {status}")
            if ref:
                print(f"    Ref: {ref.name}")
            print(f"    Motion: {shot['prompt']}")
        return

    api_key = os.environ.get("RUNWAYML_API_SECRET")
    if not api_key:
        print("ERROR: RUNWAYML_API_SECRET not set")
        print("  export RUNWAYML_API_SECRET='your-api-key'")
        sys.exit(1)

    seed = args.seed or (video_cfg.get("fixed_seed") and video_cfg.get("runway_seed"))
    client = RunwayML()
    run_batch(
        client=client,
        shots=shots,
        video_id=video_id,
        output_dir=output_dir,
        turbo=args.turbo,
        candidates_per_shot=candidates,
        seed=seed,
    )


if __name__ == "__main__":
    main()
