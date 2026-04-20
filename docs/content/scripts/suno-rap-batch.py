#!/usr/bin/env python3
"""
Suno AI Rap Audio Batch Generator (Evolink API)

Config-driven: reads lyrics and audio settings from JSON config file.
Generates rap audio via Evolink Suno API, then extracts beat timestamps.

Usage:
  source docs/content/.env

  # Config-driven mode:
  python suno-rap-batch.py --config config/sings01-rvc-intro.json

  # Dry run:
  python suno-rap-batch.py --config config/sings01-rvc-intro.json --dry-run

  # Single segment:
  python suno-rap-batch.py --config config/sings01-rvc-intro.json --shot S01
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "rap"

EVOLINK_API_BASE = "https://api.evolink.ai"


def get_audio_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return float(result.stdout.strip())


def bars_to_suno_lyrics(bars: list[dict]) -> str:
    """Convert config lyrics bars to Suno format with section markers."""
    lines = []
    current_type = None

    section_map = {
        "hook": "[Chorus]",
        "body": "[Verse]",
        "cta": "[Outro]",
    }

    for bar in bars:
        bar_type = bar.get("type", "body")
        if bar_type != current_type:
            section_marker = section_map.get(bar_type, "[Verse]")
            lines.append("")
            lines.append(section_marker)
            current_type = bar_type

        for line in bar.get("lines", []):
            lines.append(line)

    return "\n".join(lines).strip()


def create_generation_request(
    lyrics_text: str,
    style_tags: str,
    title: str = "",
    model: str = "suno-v4.5",
    vocal_gender: str = "m",
    negative_tags: str = "",
    style_weight: float | None = None,
    weirdness_constraint: float | None = None,
) -> dict:
    """Build Evolink Suno API generation request payload."""
    payload: dict = {
        "model": model,
        "custom_mode": True,
        "prompt": lyrics_text,
        "style": style_tags,
        "title": title or "FireSing Rap",
        "vocal_gender": vocal_gender,
    }
    if negative_tags:
        payload["negative_tags"] = negative_tags
    if style_weight is not None:
        payload["style_weight"] = style_weight
    if weirdness_constraint is not None:
        payload["weirdness_constraint"] = weirdness_constraint
    return payload


def start_generation(api_key: str, payload: dict) -> dict:
    """Submit generation request to Evolink Suno API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FireSing/1.0",
    }

    body = json.dumps(payload).encode("utf-8")
    url = f"{EVOLINK_API_BASE}/v1/audios/generations"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_task(
    api_key: str,
    task_id: str,
    max_wait: int = 300,
    poll_interval: int = 5,
) -> dict:
    """Poll Evolink task API until completion."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "FireSing/1.0",
    }
    url = f"{EVOLINK_API_BASE}/v1/tasks/{task_id}"
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)

    start_time = time.time()
    consecutive_errors = 0
    while time.time() - start_time < max_wait:
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with opener.open(req, timeout=30) as resp:
                task = json.loads(resp.read().decode("utf-8"))
            consecutive_errors = 0
        except (urllib.error.URLError, OSError) as e:
            consecutive_errors += 1
            if consecutive_errors > 5:
                print(f"ERROR: Too many network errors polling task: {e}")
                sys.exit(1)
            print(f"  Network error, retrying ({consecutive_errors})...")
            time.sleep(2 * consecutive_errors)
            continue

        status = task.get("status", "")
        if status in ("succeeded", "failed", "completed"):
            return task

        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s, status={status})")
        time.sleep(poll_interval)

    print("ERROR: Generation timed out")
    sys.exit(1)


def download_audio(url: str, output_path: Path, api_key: str = "") -> int:
    """Download audio file from URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "FireSing/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    with opener.open(req, timeout=120) as resp:
        data = resp.read()
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)


def extract_beats(audio_path: Path, output_path: Path) -> dict:
    """Extract beat timestamps using librosa."""
    try:
        import librosa
        import numpy as np
    except ImportError:
        print("  WARNING: librosa not installed. Skipping beat extraction.")
        print("  Install: pip install librosa")
        return {}

    y, sr = librosa.load(str(audio_path), sr=44100)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    tempo = float(np.atleast_1d(np.asarray(tempo)).flat[0])
    beat_frames = np.atleast_1d(np.asarray(beat_frames))
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    beats_per_bar = 4
    bar_lines = beat_times[::beats_per_bar]

    result = {
        "bpm": round(tempo, 1),
        "beat_count": len(beat_times),
        "beats": [round(t, 3) for t in beat_times],
        "bar_lines": [round(t, 3) for t in bar_lines],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def generate_rap(
    config: dict,
    output_dir: Path,
    dry_run: bool = False,
    shot_filter: str | None = None,
) -> None:
    """Generate rap audio from config."""
    video_id = config.get("video_id", "unknown")
    lyrics_cfg = config.get("lyrics", {})
    audio_cfg = config.get("audio", {}).get("generation", {})

    bars = lyrics_cfg.get("bars", [])
    if not bars:
        print("ERROR: No lyrics.bars found in config")
        sys.exit(1)

    audio_parent = config.get("audio", {})
    bpm = lyrics_cfg.get("bpm", 130)
    style_tags = lyrics_cfg.get(
        "suno_tags",
        audio_parent.get(
            "style_prompt",
            "chinese hip hop, rap, energetic, educational, 130 bpm",
        ),
    )
    negative_tags = audio_parent.get("negative_tags", "")
    style_weight = audio_parent.get("style_weight")
    weirdness_constraint = audio_parent.get("weirdness_constraint")
    model = audio_cfg.get("model", "suno-v4.5")
    vocal_gender = audio_cfg.get("vocal_gender", "m")

    suno_api_key = os.environ.get("SUNO_API_KEY", "")

    if not dry_run and not suno_api_key:
        print("ERROR: SUNO_API_KEY not set")
        print("  export SUNO_API_KEY=your-key")
        print("  Or source docs/content/.env")
        sys.exit(1)

    seg_dir = output_dir / video_id
    seg_dir.mkdir(parents=True, exist_ok=True)

    suno_lyrics = bars_to_suno_lyrics(bars)

    print(f"Suno AI Rap Generator (Evolink) — {video_id}")
    print("=" * 50)
    print(f"BPM: {bpm}")
    print(f"Bars: {len(bars)}")
    print(f"Model: {model}")
    print(f"Style: {style_tags}")
    if negative_tags:
        print(f"Negative: {negative_tags}")
    if style_weight is not None:
        print(f"Style weight: {style_weight}")
    if weirdness_constraint is not None:
        print(f"Weirdness: {weirdness_constraint}")
    print(f"Output: {seg_dir}")
    print()
    print("Suno lyrics format:")
    print("-" * 40)
    print(suno_lyrics)
    print("-" * 40)
    print()

    if dry_run:
        print("DRY RUN — no generation will happen.")
        print(f"Would generate: 1 rap track ({len(bars)} bars, model={model})")
        print(f"Would extract: beats.json")
        return

    payload = create_generation_request(
        lyrics_text=suno_lyrics,
        style_tags=style_tags,
        title=f"FireSing {video_id}",
        model=model,
        vocal_gender=vocal_gender,
        negative_tags=negative_tags,
        style_weight=style_weight,
        weirdness_constraint=weirdness_constraint,
    )

    print("Submitting to Evolink Suno API...")
    try:
        result = start_generation(suno_api_key, payload)
    except urllib.error.HTTPError as e:
        print(f"ERROR: Evolink API returned {e.code}")
        body = e.read().decode("utf-8", errors="replace")
        print(f"  Response: {body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Cannot reach Evolink API: {e.reason}")
        sys.exit(1)

    task_id = result.get("task_id") or result.get("id", "")
    if not task_id:
        print("ERROR: No task_id returned from Evolink")
        print(f"  Response: {json.dumps(result, indent=2)[:500]}")
        sys.exit(1)

    print(f"Task ID: {task_id}")
    print("Waiting for generation...")

    task_result = poll_task(suno_api_key, task_id)

    status = task_result.get("status", "")
    if status in ("failed", "error"):
        print(f"ERROR: Task failed — {task_result.get('error', 'unknown')}")
        sys.exit(1)

    # Extract audio URLs from task result
    # Evolink returns results in result_data (primary), data, or output
    task_data = (
        task_result.get("result_data")
        or task_result.get("data")
        or task_result.get("output")
        or []
    )

    # Handle single result or list
    audio_items = task_data if isinstance(task_data, list) else [task_data]

    for i, item in enumerate(audio_items):
        audio_url = item.get("audio_url", "")
        if not audio_url:
            print(f"  Item {i + 1}: No audio URL found")
            continue

        output_name = f"{video_id}_rap_v{i + 1}.mp3"
        output_path = seg_dir / output_name
        print(f"  Downloading → {output_name}...")

        try:
            file_size = download_audio(audio_url, output_path, api_key=suno_api_key)
            duration = get_audio_duration(output_path)
            print(f"  Done: {file_size:,} bytes, {duration:.1f}s")

            beats_name = f"{video_id}_beats_v{i + 1}.json"
            beats_path = seg_dir / beats_name
            print(f"  Extracting beats → {beats_name}...")
            beat_data = extract_beats(output_path, beats_path)
            if beat_data:
                print(
                    f"  Beats: {beat_data['beat_count']} beats, "
                    f"{len(beat_data['bar_lines'])} bars, "
                    f"BPM={beat_data['bpm']}"
                )
        except Exception as e:
            print(f"  ERROR downloading item {i + 1}: {e}")

    print()
    print("Generation complete.")

    log_entry = {
        "video_id": video_id,
        "timestamp": datetime.now().isoformat(),
        "api": "evolink",
        "model": model,
        "bpm": bpm,
        "bars": len(bars),
        "style": style_tags,
        "negative_tags": negative_tags,
        "style_weight": style_weight,
        "weirdness_constraint": weirdness_constraint,
        "task_id": task_id,
        "output_dir": str(seg_dir),
    }
    log_path = seg_dir / f"suno-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    print(f"Log: {log_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suno AI Rap Audio Batch Generator (Evolink)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to video config JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without generating",
    )
    parser.add_argument(
        "--shot",
        type=str,
        help="Generate only a specific shot (e.g. S01)",
    )

    args = parser.parse_args()

    if not args.config:
        print("ERROR: --config is required")
        print("Usage: python suno-rap-batch.py --config config/sings01.json")
        sys.exit(1)

    config_path = args.config
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if config.get("workflow") != "sings":
        print(f"WARNING: Config workflow is '{config.get('workflow')}', expected 'sings'")

    env_path = PROJECT_ROOT / "docs" / "content" / ".env"
    if env_path.exists():
        print(f"Loading env from {env_path}")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    line = line.removeprefix("export ")
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"'))

    output_dir = DEFAULT_OUTPUT_DIR
    generate_rap(
        config=config,
        output_dir=output_dir,
        dry_run=args.dry_run,
        shot_filter=args.shot,
    )


if __name__ == "__main__":
    main()
