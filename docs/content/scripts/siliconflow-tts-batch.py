#!/usr/bin/env python3
"""
SiliconFlow TTS Batch Voiceover Generator (config-driven)
Uses SiliconFlow API with Fish Speech 1.5 — supports Alipay payments.

Usage:
  source docs/content/.env
  python3 siliconflow-tts-batch.py --config config/day5-yangmun.json
  python3 siliconflow-tts-batch.py --config config/day5-yangmun.json --shot S01
  python3 siliconflow-tts-batch.py --config config/day5-yangmun.json --voice charles --dry-run
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

MODEL = "fishaudio/fish-speech-1.5"
BASE_URL = "https://api.siliconflow.com/v1"

VOICES = {
    "alex": "fishaudio/fish-speech-1.5:alex",          # 沉稳男声
    "benjamin": "fishaudio/fish-speech-1.5:benjamin",   # 低沉男声
    "charles": "fishaudio/fish-speech-1.5:charles",     # 磁性男声
    "david": "fishaudio/fish-speech-1.5:david",         # 欢快男声
    "anna": "fishaudio/fish-speech-1.5:anna",            # 沉稳女声
    "bella": "fishaudio/fish-speech-1.5:bella",          # 激情女声
    "claire": "fishaudio/fish-speech-1.5:claire",        # 温柔女声
    "diana": "fishaudio/fish-speech-1.5:diana",          # 欢快女声
}

# Emotion → speed/gain adjustments
EMOTION_SETTINGS = {
    "shock":          {"speed": 0.82, "gain": 2.0},
    "determined":     {"speed": 0.88, "gain": 2.0},
    "power":          {"speed": 0.85, "gain": 3.0},
    "contemplative":  {"speed": 0.78, "gain": 0.0},
    "warm":           {"speed": 0.92, "gain": 0.0},
    # Legacy emotions
    "empathy":   {"speed": 0.90, "gain": 0.0},
    "desire":    {"speed": 0.88, "gain": 0.0},
    "hope":      {"speed": 0.95, "gain": 1.0},
    "contrast":  {"speed": 0.90, "gain": 2.0},
    "joy":       {"speed": 1.0,  "gain": 1.0},
    "trust":     {"speed": 0.92, "gain": 0.0},
}


def get_audio_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def pause_markers_to_punctuation(text: str) -> str:
    """Convert <#0.3#> pause markers to Chinese punctuation for Fish Speech."""
    def replace_marker(match: re.Match) -> str:
        seconds = float(match.group(1))
        if seconds >= 0.5:
            return "——"
        return "…"
    return re.sub(r"<#(\d+\.?\d*)#>", replace_marker, text)


def get_emotion_params(emotion: str) -> dict:
    return EMOTION_SETTINGS.get(emotion, {"speed": 0.90, "gain": 0.0})


def resolve_voice(voice_arg: str) -> str:
    if voice_arg in VOICES:
        return VOICES[voice_arg]
    if "/" in voice_arg:
        return voice_arg
    return f"fishaudio/fish-speech-1.5:{voice_arg}"


def synthesize_segment(client: OpenAI, text: str, voice: str,
                       emotion: str, output_path: Path) -> dict:
    params = get_emotion_params(emotion)
    clean_text = pause_markers_to_punctuation(text)

    with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=voice,
        input=clean_text,
        response_format="mp3",
        speed=params["speed"],
        extra_body={"gain": params["gain"]},
    ) as response:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response.stream_to_file(str(output_path))

    duration_s = get_audio_duration(output_path)
    return {"duration_s": duration_s, "file_size": output_path.stat().st_size}


def generate_srt(segments: list[dict], output_path: Path) -> None:
    entries = []
    cumulative = 0.0
    for i, seg in enumerate(segments):
        duration = seg["actual_duration_s"]
        start = cumulative
        end = cumulative + duration
        text = seg.get("voiceover_text", "")
        entries.append(f"{i + 1}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{text}\n")
        cumulative = end
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))


def concatenate_audio(segment_files: list[Path], output_path: Path) -> None:
    concat_list = output_path.parent / "_concat.txt"
    with open(concat_list, "w") as f:
        for path in segment_files:
            f.write(f"file '{path}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k", str(output_path)],
        capture_output=True, timeout=60,
    )
    concat_list.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="SiliconFlow TTS with Fish Speech (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--voice", type=str, default="alex",
                        help=f"Voice name or shortcut ({', '.join(VOICES.keys())})")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="Delay between requests in seconds (default: 3)")
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
    segments = config.get("segments", [])
    if not segments:
        print("ERROR: No segments in config")
        sys.exit(1)

    voice = resolve_voice(args.voice)
    output_dir = Path(args.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    print(f"SiliconFlow TTS — {video_id}")
    print("=" * 50)
    print(f"Model: {MODEL}")
    print(f"Voice: {voice}")
    print(f"Output: {output_dir}")
    print(f"Segments: {len(segments)}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for seg in segments:
            emotion = seg.get("emotion", seg.get("emotion_arc", ""))
            text = seg.get("voiceover_pause_markers", seg.get("voiceover_text", ""))
            params = get_emotion_params(emotion)
            clean_text = pause_markers_to_punctuation(text)
            print(f"  {seg['id']} [{emotion}]:")
            print(f"    Text: {seg.get('voiceover_text', '')[:60]}...")
            print(f"    Clean: {clean_text[:60]}...")
            print(f"    Speed: {params['speed']}, Gain: {params['gain']}dB")
            print()
        return

    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not api_key:
        print("ERROR: SILICONFLOW_API_KEY not set")
        print("Get it from: https://cloud.siliconflow.com/account/ak")
        print("Set it in: docs/content/.env")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=BASE_URL)

    results = []
    total_duration = 0.0

    for i, seg in enumerate(segments):
        text = seg.get("voiceover_text", "")
        emotion = seg.get("emotion", seg.get("emotion_arc", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        if i > 0 and args.delay > 0:
            print(f"  Waiting {args.delay}s...", flush=True)
            time.sleep(args.delay)

        dest = output_dir / f"{seg['id']}.mp3"
        raw_text = seg.get("voiceover_pause_markers", text)

        print(f"[{seg['id']}] [{emotion}] {text[:50]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize_segment(client, raw_text, voice, emotion, dest)
            total_duration += info["duration_s"]
            params = get_emotion_params(emotion)
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            print(f"    speed={params['speed']} gain={params['gain']}dB")
            results.append({
                "segment": seg["id"], "file": str(dest),
                "duration_s": info["duration_s"], "status": "success",
                "actual_duration_s": info["duration_s"],
                "voiceover_text": text,
                "emotion": emotion,
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles-siliconflow.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-siliconflow.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"siliconflow-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "siliconflow-fish-speech-1.5",
            "voice_id": voice,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total: {total_duration:.1f}s")
    if total_duration > 45:
        print("WARNING: Exceeds 45s limit!")
    elif total_duration < 30:
        print("WARNING: Below 30s minimum!")


if __name__ == "__main__":
    main()
