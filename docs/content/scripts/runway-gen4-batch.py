#!/usr/bin/env python3
"""
Runway Gen-4 Batch Video Generator
Reads Day 1 storyboard and generates all shots via Runway API.

Usage:
  export RUNWAYML_API_SECRET="your-api-key"
  python runway-gen4-batch.py [--turbo] [--output-dir DIR]

Options:
  --turbo           Use Gen-4 Turbo (faster, cheaper, for iteration)
  --output-dir DIR  Output directory (default: docs/content/output/day1)
  --shot S01        Generate only a specific shot (e.g., --shot S01)
  --dry-run         Show plan without generating
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

from runwayml import RunwayML

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # scripts/content/docs -> FireSing
REFERENCE_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output" / "day1"

# Day 1 shot definitions (from storyboard + runway-params-template)
SHOTS = [
    {
        "id": "S01",
        "name": "数字浮现",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow zoom in on golden numbers, subtle glow pulsing, cinematic motion",
        "reference_file": "S01-digital-emergence.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S02",
        "name": "空办公室",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow pan right across empty office, single lamp flickering slightly, cinematic",
        "reference_file": "S02-empty-office.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S03",
        "name": "拖车公园",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow push in, warm golden hour light shifting, subtle wind movement",
        "reference_file": "S03-trailer-park.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S04",
        "name": "编程场景",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "subtle screen glow changing, focused stillness, cinematic mood",
        "reference_file": "S04-coding-scene.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S05",
        "name": "数据展示",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow zoom in, data numbers appearing sequentially, golden glow",
        "reference_file": "S05-data-display.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S06",
        "name": "公司对比",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow pan right revealing office scale, cinematic contrast",
        "reference_file": "S06-company-comparison.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S07",
        "name": "利润率对比",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "slow zoom in on comparison bars, subtle animation, minimal movement",
        "reference_file": "S07-profit-comparison.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    # S08 uses real screenshots, not Runway
    {
        "id": "S09",
        "name": "日营收",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "dramatic zoom out revealing revenue number, rising energy",
        "reference_file": "S09-daily-revenue.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
    {
        "id": "S10",
        "name": "转化卡片",
        "duration": 5,
        "ratio": "720:1280",
        "prompt": "gentle fade in, clean text appearing, warm cinematic",
        "reference_file": "S10-cta-card.png",
        "credits_turbo": 25,
        "credits_gen4": 60,
    },
]


def image_to_data_uri(image_path: Path) -> str:
    """Convert local image file to base64 data URI."""
    suffix = image_path.suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_map.get(suffix, "image/png")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def find_reference_image(shot_id: str, reference_file: str) -> Path | None:
    """Find reference image, trying multiple naming conventions."""
    candidates = [
        REFERENCE_DIR / reference_file,
        REFERENCE_DIR / f"{shot_id}.png",
        REFERENCE_DIR / f"{shot_id}.jpg",
        REFERENCE_DIR / f"{shot_id}.jpeg",
        REFERENCE_DIR / f"{shot_id}.webp",
    ]
    # Also try any file starting with the shot ID
    if REFERENCE_DIR.exists():
        for f in REFERENCE_DIR.iterdir():
            if f.name.startswith(shot_id) and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                candidates.insert(0, f)
                break

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def estimate_cost(shots: list[dict], turbo: bool) -> str:
    """Estimate total credits cost."""
    total = sum(s["credits_turbo" if turbo else "credits_gen4"] for s in shots)
    model = "Gen-4 Turbo" if turbo else "Gen-4.5"
    return f"{model}: ~{total} credits ({len(shots)} shots x 5s)"


def run_batch(
    client: RunwayML,
    shots: list[dict],
    output_dir: Path,
    turbo: bool = True,
    candidates_per_shot: int = 1,
    seed: int | None = None,
):
    """Generate all shots via Runway API."""
    model = "gen4_turbo" if turbo else "gen4.5"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(shots) * candidates_per_shot
    completed = 0

    for shot in shots:
        ref_path = find_reference_image(shot["id"], shot["reference_file"])
        if not ref_path:
            print(f"[SKIP] {shot['id']} {shot['name']}: no reference image found in {REFERENCE_DIR}")
            print(f"       Expected: {REFERENCE_DIR / shot['reference_file']}")
            continue

        print(f"\n[{shot['id']}] {shot['name']}")
        print(f"  Reference: {ref_path.name}")
        print(f"  Prompt: {shot['prompt']}")
        print(f"  Model: {model} | Duration: {shot['duration']}s | Ratio: {shot['ratio']}")

        # Upload reference image
        print("  Uploading reference image...")
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

                # Poll for completion
                while True:
                    task_result = client.tasks.retrieve(task_id)
                    status = task_result.status
                    if status == "SUCCEEDED":
                        print(f"  ✓ SUCCEEDED")
                        break
                    elif status == "FAILED":
                        print(f"  ✗ FAILED: {getattr(task_result, 'error', 'unknown')}")
                        break
                    else:
                        print(f"  ... {status} (waiting 10s)", end="\r", flush=True)
                        time.sleep(10)

                if status == "SUCCEEDED" and task_result.output:
                    # Download video
                    video_url = task_result.output[0] if isinstance(task_result.output, list) else task_result.output
                    output_path = output_dir / output_name
                    print(f"  Downloading to {output_path}...")
                    import urllib.request
                    urllib.request.urlretrieve(video_url, str(output_path))
                    print(f"  ✓ Saved: {output_path.name}")
                    results.append({
                        "shot": shot["id"],
                        "file": str(output_path),
                        "task_id": task_id,
                        "status": "success",
                    })
                else:
                    results.append({
                        "shot": shot["id"],
                        "task_id": task_id,
                        "status": "failed",
                    })

                completed += 1
                print(f"  Progress: {completed}/{total}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                results.append({
                    "shot": shot["id"],
                    "status": "error",
                    "error": str(e),
                })

    # Save results log
    log_path = output_dir / f"generation-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "shots": len(shots),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nLog saved: {log_path}")

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed out of {total}")
    if failed > 0:
        print("Failed shots:")
        for r in results:
            if r["status"] != "success":
                print(f"  - {r['shot']}: {r.get('error', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="Runway Gen-4 Batch Video Generator")
    parser.add_argument("--turbo", action="store_true", default=True, help="Use Gen-4 Turbo (default)")
    parser.add_argument("--no-turbo", dest="turbo", action="store_false", help="Use Gen-4 (higher quality)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this shot (e.g., S01)")
    parser.add_argument("--candidates", type=int, default=1, help="Generate N candidates per shot (Turbo iteration)")
    parser.add_argument("--seed", type=int, default=None, help="Fixed seed for style consistency across shots")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    # Filter shots
    shots = SHOTS
    if args.shot:
        shots = [s for s in SHOTS if s["id"] == args.shot.upper()]
        if not shots:
            print(f"Shot {args.shot} not found. Available: {', '.join(s['id'] for s in SHOTS)}")
            sys.exit(1)

    print("Runway Gen-4 Batch Video Generator")
    print("=" * 50)
    print(f"Shots: {len(shots)} ({', '.join(s['id'] for s in shots)})")
    print(f"Candidates per shot: {args.candidates}")
    print(f"Model: {'Gen-4 Turbo' if args.turbo else 'Gen-4.5'}")
    print(f"Output: {args.output_dir}")
    print(f"Cost estimate: {estimate_cost(shots * args.candidates, args.turbo)}")
    print(f"Reference dir: {REFERENCE_DIR}")
    print()

    # Check reference images
    missing = []
    for shot in shots:
        if not find_reference_image(shot["id"], shot["reference_file"]):
            missing.append(shot["id"])
    if missing:
        print(f"WARNING: Missing reference images for: {', '.join(missing)}")
        print(f"  Place images in: {REFERENCE_DIR}/")
        print(f"  Expected files: {', '.join(s['reference_file'] for s in shots if s['id'] in missing)}")
        print()

    if args.dry_run:
        print("DRY RUN - no generation will happen.")
        print("\nShot plan:")
        for shot in shots:
            ref = find_reference_image(shot["id"], shot["reference_file"])
            status = "✓ found" if ref else "✗ missing"
            print(f"  {shot['id']} {shot['name']}: {shot['duration']}s | {status}")
            print(f"    Prompt: {shot['prompt']}")
        return

    # Check API key
    api_key = os.environ.get("RUNWAYML_API_SECRET")
    if not api_key:
        print("ERROR: RUNWAYML_API_SECRET not set")
        print("  export RUNWAYML_API_SECRET='your-api-key'")
        print("  Get your key at: https://dev.runwayml.com")
        sys.exit(1)

    # Create client and run
    client = RunwayML()
    run_batch(
        client=client,
        shots=shots,
        output_dir=Path(args.output_dir),
        turbo=args.turbo,
        candidates_per_shot=args.candidates,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
