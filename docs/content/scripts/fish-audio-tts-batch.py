#!/usr/bin/env python3
"""
Fish Audio S2 Pro TTS Batch Voiceover Generator

Config-driven: reads segments and voice settings from JSON config file.

Usage:
  export FISH_AUDIO_API_KEY="your-api-key"

  # Config-driven mode (recommended):
  python fish-audio-tts-batch.py --config config/day1.json

  # Quick test with a single segment:
  python fish-audio-tts-batch.py --test "测试配音质量" --reference-id MODEL_ID

  # Dry run:
  python fish-audio-tts-batch.py --config config/day1.json --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"

API_URL = "https://api.fish.audio/v1/tts"


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


def strip_pause_markers(text: str) -> str:
    """Remove MiniMax-style pause markers <#0.3#> from text."""
    return re.sub(r"<#\d+\.?\d*#>", "", text)


def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def synthesize(
    api_key: str,
    text: str,
    reference_id: str,
    output_path: Path,
    temperature: float = 0.7,
    top_p: float = 0.7,
    speed: float = 1.0,
    sample_rate: int = 44100,
) -> dict:
    """Synthesize speech via Fish Audio TTS API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": "s2-pro",
    }

    payload = {
        "text": text,
        "reference_id": reference_id,
        "temperature": temperature,
        "top_p": top_p,
        "prosody": {"speed": speed},
        "format": "mp3",
        "sample_rate": sample_rate,
        "normalize": True,
        "condition_on_previous_chunks": False,
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=body, headers=headers, method="POST")

    with urllib.request.urlopen(req, timeout=120) as resp:
        audio_data = resp.read()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_data)

    duration_s = get_audio_duration(output_path)

    return {
        "file_size": len(audio_data),
        "duration_s": duration_s,
    }


def generate_srt(segments: list[dict], output_path: Path) -> None:
    """Generate SRT subtitle file from segment timings."""
    entries = []
    cumulative = 0.0

    for i, seg in enumerate(segments):
        duration = seg["actual_duration_s"]
        start = cumulative
        end = cumulative + duration

        text = seg.get("voiceover_text", "")
        if not text:
            text = strip_pause_markers(seg.get("voiceover_pause_markers", ""))

        entries.append(
            f"{i + 1}\n"
            f"{format_srt_time(start)} --> {format_srt_time(end)}\n"
            f"{text}\n"
        )
        cumulative = end

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))


def concatenate_audio(segment_files: list[Path], output_path: Path) -> None:
    """Concatenate segment audio files into full narration via FFmpeg."""
    concat_list = output_path.parent / "_concat.txt"
    with open(concat_list, "w") as f:
        for path in segment_files:
            f.write(f"file '{path}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(output_path),
        ],
        capture_output=True,
        timeout=60,
    )
    concat_list.unlink(missing_ok=True)


def run_config_mode(
    config_path: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> None:
    """Run in config-driven mode."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    voice_cfg = config.get("voiceover", {})
    reference_id = voice_cfg.get("reference_id", "")

    if not reference_id:
        print("ERROR: voiceover.reference_id not set in config")
        print("  Create a voice model at https://fish.audio and add the ID")
        sys.exit(1)

    segments = config.get("segments", [])
    if not segments:
        print("ERROR: No segments found in config")
        sys.exit(1)

    video_id = config.get("video_id", "unknown")
    seg_dir = output_dir / video_id
    seg_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fish Audio S2 Pro TTS — {video_id}")
    print("=" * 50)
    print(f"Segments: {len(segments)}")
    print(f"Voice model: {reference_id}")
    print(f"Speed: {voice_cfg.get('speed', 1.0)}")
    print(f"Output: {seg_dir}")
    print()

    if dry_run:
        print("DRY RUN — no generation will happen.")
        for seg in segments:
            text = seg.get("voiceover_text", "(no voiceover_text)")
            print(f"  {seg['id']}: {text[:60]}...")
        return

    api_key = os.environ.get("FISH_AUDIO_API_KEY")
    if not api_key:
        print("ERROR: FISH_AUDIO_API_KEY not set")
        print("  export FISH_AUDIO_API_KEY='your-api-key'")
        sys.exit(1)

    results = []
    total_duration = 0.0

    for seg in segments:
        text = seg.get("voiceover_text", "")
        if not text:
            text = strip_pause_markers(seg.get("voiceover_pause_markers", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        dest = seg_dir / f"{seg['id']}.mp3"
        print(f"[{seg['id']}] {text[:50]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize(
                api_key=api_key,
                text=text,
                reference_id=reference_id,
                output_path=dest,
                temperature=voice_cfg.get("temperature", 0.7),
                top_p=voice_cfg.get("top_p", 0.7),
                speed=voice_cfg.get("speed", 1.0),
                sample_rate=voice_cfg.get("sample_rate", 44100),
            )
            duration_s = info["duration_s"]
            total_duration += duration_s
            print(f"done ({duration_s:.1f}s, {info['file_size'] // 1024}KB)")

            results.append({
                "segment": seg["id"],
                "file": str(dest),
                "duration_s": duration_s,
                "chars": len(text),
                "status": "success",
                "actual_duration_s": duration_s,
            })

            time.sleep(1)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {body[:200]}")
            results.append({
                "segment": seg["id"],
                "status": "error",
                "error": f"HTTP {e.code}: {body[:200]}",
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({
                "segment": seg["id"],
                "status": "error",
                "error": str(e),
            })

    successful = [r for r in results if r["status"] == "success"]

    # Generate SRT
    if successful:
        duration_map = {r["segment"]: r["actual_duration_s"] for r in successful}
        srt_segments = []
        for seg in segments:
            if seg["id"] in duration_map:
                s = dict(seg)
                s["actual_duration_s"] = duration_map[seg["id"]]
                srt_segments.append(s)

        srt_path = seg_dir / f"{video_id}-subtitles.srt"
        generate_srt(srt_segments, srt_path)
        print(f"\nSRT saved: {srt_path}")

    # Concatenate full narration
    if successful:
        full_path = seg_dir / f"{video_id}-full-narration.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    # Save log
    log_path = seg_dir / f"fish-audio-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "fish_audio_s2_pro",
            "model": "s2-pro",
            "reference_id": reference_id,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "segments": len(segments),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total audio: {total_duration:.1f}s")
    if total_duration > 45:
        print("WARNING: Total duration exceeds 45s limit!")
    elif total_duration < 30:
        print("WARNING: Total duration below 30s minimum!")


def run_test_mode(
    text: str,
    reference_id: str,
    output_dir: Path,
) -> None:
    """Quick test mode for voice quality."""
    api_key = os.environ.get("FISH_AUDIO_API_KEY")
    if not api_key:
        print("ERROR: FISH_AUDIO_API_KEY not set")
        sys.exit(1)

    if not reference_id:
        print("ERROR: --reference-id required for test mode")
        print("  Create a voice model at https://fish.audio")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "test-voice.mp3"

    print(f"Test: \"{text}\"")
    print(f"Voice: {reference_id}")
    print("Synthesizing... ", end="", flush=True)

    try:
        info = synthesize(api_key, text, reference_id, dest)
        print(f"done ({info['duration_s']:.1f}s)")
        print(f"Saved: {dest}")
        print(f"\nListen: open \"{dest}\"")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body[:300]}")
        sys.exit(1)
    except Exception as e:
        print(f"failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Fish Audio S2 Pro TTS Batch Voiceover Generator",
    )
    parser.add_argument("--config", type=str, help="Path to video config JSON")
    parser.add_argument("--test", type=str, help="Quick test with custom text")
    parser.add_argument(
        "--reference-id", type=str,
        help="Fish Audio voice model ID (for --test mode)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"ERROR: Config not found: {config_path}")
            sys.exit(1)
        run_config_mode(config_path, output_dir, args.dry_run)
    elif args.test:
        run_test_mode(args.test, args.reference_id, output_dir)
    else:
        parser.print_help()
        print("\nExamples:")
        print(f"  python {Path(__file__).name} --config config/day1.json")
        print(f"  python {Path(__file__).name} --test '测试配音质量' --reference-id YOUR_MODEL_ID")


if __name__ == "__main__":
    main()
