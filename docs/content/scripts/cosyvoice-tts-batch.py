#!/usr/bin/env python3
"""
CosyVoice TTS Batch Voiceover Generator (config-driven)
Uses Alibaba Cloud DashScope CosyVoice-v3-flash with Instruct emotion control.

Usage:
  source docs/content/.env
  python3 cosyvoice-tts-batch.py --config config/day1-medvi-story.json
  python3 cosyvoice-tts-batch.py --config config/day1-medvi-story.json --shot S01 --dry-run
  python3 cosyvoice-tts-batch.py --config config/day1-medvi-story.json --voice longfei_v3
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import dashscope
from dashscope.audio.tts_v2 import AudioFormat, SpeechSynthesizer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

VOICES = {
    "longanyang": "longanyang",
    "longfei": "longfei_v3",
    "longsanshu": "longsanshu_v3",
    "longshuo": "longshuo_v3",
    "longtian": "longtian_v3",
    "longxiu": "longxiu_v3",
    "longanyun": "longanyun_v3",
}

EMOTION_MAP = {
    "empathy": "你正在进行新闻播报，你说话的情感是surprised。",
    "desire": "你现在说话的角色是一个旁白，你说话的情感是neutral。",
    "hope": "你现在说话的角色是一个旁白，你说话的情感是neutral。",
    "shock": "你正在进行新闻播报，你说话的情感是surprised。",
    "contrast": "你正在进行新闻播报，你说话的情感是surprised。",
    "joy": "你说话的情感是happy。",
    "trust": "你正在进行广告促销，你说话的情感是happy。",
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


def strip_pause_markers(text: str) -> str:
    return re.sub(r"<#\d+\.?\d*#>", "", text)


def synthesize(
    text: str, voice: str, output_path: Path,
    emotion: str = "", speed: float = 1.0,
) -> dict:
    dashscope.base_websocket_api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

    kwargs = {
        "model": "cosyvoice-v3-flash",
        "voice": voice,
        "format": AudioFormat.MP3_44100HZ_MONO_256KBPS,
        "speech_rate": speed,
        "volume": 50,
    }

    instruction = EMOTION_MAP.get(emotion, "")
    if instruction and voice == "longanyang":
        kwargs["instruction"] = instruction

    synthesizer = SpeechSynthesizer(**kwargs)
    audio = synthesizer.call(text)

    if not audio:
        resp = synthesizer.get_response()
        raise RuntimeError(f"Synthesis returned no audio. Response: {resp}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio)

    duration_s = get_audio_duration(output_path)
    return {
        "duration_s": duration_s,
        "file_size": len(audio),
        "instruction": instruction,
    }


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
    parser = argparse.ArgumentParser(description="CosyVoice TTS (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--voice", type=str, default="longanyang",
                        help=f"Voice key or raw ID ({', '.join(VOICES.keys())})")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.5-2.0)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--no-emotion", action="store_true", help="Disable Instruct emotion control")
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

    voice_id = VOICES.get(args.voice, args.voice)
    output_dir = Path(args.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    print(f"CosyVoice TTS — {video_id}")
    print("=" * 50)
    print(f"Model: cosyvoice-v3-flash")
    print(f"Voice: {voice_id}")
    print(f"Speed: {args.speed}")
    print(f"Emotion control: {'off' if args.no_emotion else 'on'}")
    print(f"Output: {output_dir}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for seg in segments:
            text = seg.get("voiceover_text", "")
            emotion = seg.get("emotion", "")
            instruction = EMOTION_MAP.get(emotion, "(none)")
            print(f"  {seg['id']} [{emotion}]: {text[:50]}...")
            print(f"    instruction: {instruction}")
        return

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("ERROR: DASHSCOPE_API_KEY not set")
        print("Get it from: https://help.aliyun.com/zh/model-studio/get-api-key")
        sys.exit(1)
    dashscope.api_key = api_key

    results = []
    total_duration = 0.0

    for seg in segments:
        text = strip_pause_markers(seg.get("voiceover_pause_markers", seg.get("voiceover_text", "")))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        emotion = "" if args.no_emotion else seg.get("emotion", "")
        dest = output_dir / f"{seg['id']}.mp3"
        print(f"[{seg['id']}] [{seg.get('emotion_arc', '')}] {seg.get('voiceover_text', '')[:50]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize(text, voice_id, dest, emotion=emotion, speed=args.speed)
            total_duration += info["duration_s"]
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            if info.get("instruction"):
                print(f"    instruction: {info['instruction']}")
            results.append({
                "segment": seg["id"], "file": str(dest),
                "duration_s": info["duration_s"], "status": "success",
                "actual_duration_s": info["duration_s"],
                "voiceover_text": seg.get("voiceover_text", ""),
                "instruction": info.get("instruction", ""),
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles-cosyvoice.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-cosyvoice.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"cosyvoice-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "cosyvoice-v3-flash",
            "voice_id": voice_id,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total: {total_duration:.1f}s")
    if total_duration > 45:
        print("WARNING: Exceeds 45s limit!")
    elif total_duration < 30:
        print("WARNING: Below 30s minimum!")


if __name__ == "__main__":
    main()
