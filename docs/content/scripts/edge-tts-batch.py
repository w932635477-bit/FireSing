#!/usr/bin/env python3
"""
Edge TTS Batch Voiceover Generator (config-driven)
Uses Microsoft Edge TTS — completely free, no API key needed.

Usage:
  python3 edge-tts-batch.py --config config/day2-medvi-tools.json
  python3 edge-tts-batch.py --config config/day2-medvi-tools.json --shot S01
  python3 edge-tts-batch.py --config config/day2-medvi-tools.json --voice zh-CN-YunxiNeural
  python3 edge-tts-batch.py --config config/day2-medvi-tools.json --dry-run
"""

import argparse
import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import edge_tts

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

VOICES = {
    "yunxi": "zh-CN-YunxiNeural",       # 年轻男声，温暖叙事，推荐
    "yunjian": "zh-CN-YunjianNeural",    # 沉稳男声，新闻播报
    "yunyang": "zh-CN-YunyangNeural",    # 新闻主播风格
    "yunxia": "zh-CN-YunxiaNeural",      # 少年音
}

# Emotion arc → rate/pitch adjustments for Edge TTS
EMOTION_SETTINGS = {
    "shock":    {"rate": "-5%",  "pitch": "+2Hz",  "volume": "+10%"},  # 沉重有力
    "震撼":     {"rate": "-5%",  "pitch": "+2Hz",  "volume": "+10%"},
    "tension":  {"rate": "+5%",  "pitch": "-2Hz",  "volume": "+5%"},   # 紧凑压迫
    "紧张":     {"rate": "+5%",  "pitch": "-2Hz",  "volume": "+5%"},
    "reversal": {"rate": "-10%", "pitch": "+0Hz",  "volume": "+5%"},   # 减速强调
    "反转":     {"rate": "-10%", "pitch": "+0Hz",  "volume": "+5%"},
    "curiosity":{"rate": "+0%",  "pitch": "+3Hz",  "volume": "+0%"},   # 微妙好奇
    "好奇":     {"rate": "+0%",  "pitch": "+3Hz",  "volume": "+0%"},
    "fear":     {"rate": "+3%",  "pitch": "-3Hz",  "volume": "-5%"},   # 低沉威胁
    "恐惧":     {"rate": "+3%",  "pitch": "-3Hz",  "volume": "-5%"},
    "engagement":{"rate": "+5%", "pitch": "+2Hz",  "volume": "+5%"},   # 真诚互动
    "参与":     {"rate": "+5%",  "pitch": "+2Hz",  "volume": "+5%"},
    # Legacy emotions (转化优先)
    "empathy":  {"rate": "-5%",  "pitch": "+0Hz",  "volume": "+0%"},
    "共情":     {"rate": "-5%",  "pitch": "+0Hz",  "volume": "+0%"},
    "desire":   {"rate": "+0%",  "pitch": "+2Hz",  "volume": "+5%"},
    "向往":     {"rate": "+0%",  "pitch": "+2Hz",  "volume": "+5%"},
    "hope":     {"rate": "+5%",  "pitch": "+3Hz",  "volume": "+5%"},
    "希望":     {"rate": "+5%",  "pitch": "+3Hz",  "volume": "+5%"},
    "contrast": {"rate": "+5%",  "pitch": "+0Hz",  "volume": "+10%"},
    "对比":     {"rate": "+5%",  "pitch": "+0Hz",  "volume": "+10%"},
    "trust":    {"rate": "+5%",  "pitch": "+2Hz",  "volume": "+5%"},
    "信任":     {"rate": "+5%",  "pitch": "+2Hz",  "volume": "+5%"},
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


def pause_markers_to_ssml_breaks(text: str) -> str:
    """Convert <#0.3#> pause markers to SSML <break> tags."""
    def replace_marker(match: re.Match) -> str:
        seconds = float(match.group(1))
        ms = int(seconds * 1000)
        return f'<break time="{ms}ms"/>'
    return re.sub(r"<#(\d+\.?\d*)#>", replace_marker, text)


def get_emotion_params(emotion: str) -> dict[str, str]:
    """Get rate/pitch/volume params for an emotion."""
    return EMOTION_SETTINGS.get(emotion, {"rate": "+0%", "pitch": "+0Hz", "volume": "+0%"})


def strip_pause_markers(text: str) -> str:
    """Remove pause markers, keeping the text clean for Edge TTS."""
    return re.sub(r"<#\d+\.?\d*#>", "，", text)


async def synthesize_segment(voice: str, text: str, emotion: str,
                             output_path: Path) -> dict:
    """Synthesize a single segment using Edge TTS."""
    clean_text = strip_pause_markers(text)
    params = get_emotion_params(emotion)

    communicate = edge_tts.Communicate(
        text=clean_text,
        voice=voice,
        rate=params["rate"],
        pitch=params["pitch"],
        volume=params["volume"],
    )
    await communicate.save(str(output_path))

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


def resolve_voice(voice_arg: str) -> str:
    if voice_arg in VOICES:
        return VOICES[voice_arg]
    return voice_arg


async def run_async(args: argparse.Namespace) -> None:
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

    print(f"Edge TTS — {video_id}")
    print("=" * 50)
    print(f"Voice: {voice}")
    print(f"Output: {output_dir}")
    print(f"Segments: {len(segments)}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for seg in segments:
            emotion = seg.get("emotion", seg.get("emotion_arc", ""))
            text = seg.get("voiceover_pause_markers", seg.get("voiceover_text", ""))
            settings = get_emotion_params(emotion)
            clean_text = strip_pause_markers(text)
            print(f"  {seg['id']} [{emotion}]:")
            print(f"    Text: {seg.get('voiceover_text', '')[:60]}...")
            print(f"    Clean: {clean_text[:60]}...")
            print(f"    Rate: {settings['rate']}, "
                  f"Pitch: {settings['pitch']}, "
                  f"Volume: {settings['volume']}")
            print()
        return

    results = []
    total_duration = 0.0

    for seg in segments:
        text = seg.get("voiceover_text", "")
        emotion = seg.get("emotion", seg.get("emotion_arc", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        dest = output_dir / f"{seg['id']}.mp3"
        raw_text = seg.get("voiceover_pause_markers", text)

        print(f"[{seg['id']}] [{emotion}] {text[:50]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = await synthesize_segment(voice, raw_text, emotion, dest)
            total_duration += info["duration_s"]
            params = get_emotion_params(emotion)
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            print(f"    rate={params['rate']} "
                  f"pitch={params['pitch']} "
                  f"vol={params['volume']}")
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
        srt_path = output_dir / f"{video_id}-subtitles-edge.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-edge.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"edge-tts-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "edge-tts",
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


def main():
    parser = argparse.ArgumentParser(description="Edge TTS (config-driven, free)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--voice", type=str, default="yunxi",
                        help=f"Voice name or shortcut ({', '.join(VOICES.keys())})")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    asyncio.run(run_async(args))


if __name__ == "__main__":
    main()
