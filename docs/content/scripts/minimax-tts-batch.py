#!/usr/bin/env python3
"""
MiniMax Speech-02 TTS Batch Voiceover Generator
Generates voiceover audio for Day 1 storyboard via MiniMax T2A API.

Usage:
  export MINIMAX_API_KEY="your-api-key"
  python minimax-tts-batch.py [--voice VOICE] [--output-dir DIR]
  python minimax-tts-batch.py --shot S01 --dry-run

Options:
  --voice VOICE   Voice ID (default: male-qn-jingying)
  --output-dir DIR  Output directory (default: docs/content/assets/voiceover)
  --shot S01      Generate only a specific shot
  --full          Generate full narration as single file
  --dry-run       Show plan without generating
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
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"

API_BASE = "https://api.minimaxi.com/v1/t2a_v2"

# Available voices for Chinese narration
VOICES = {
    "male-elite": "male-qn-jingying",
    "male-young": "male-qn-qingse",
    "male-dominant": "male-qn-badao",
    "male-student": "male-qn-daxuesheng",
    "female-young": "female-shaonv",
    "female-mature": "female-yujie",
    "female-sweet": "female-tianmei",
    "presenter-male": "presenter_male",
    "presenter-female": "presenter_female",
    "audiobook-male": "audiobook_male_1",
}

# Day 1 v2 narration segments (6 segments, ~35s target)
# <#0.3#> = 0.3s pause before key numbers
SEGMENTS = [
    {
        "id": "S01",
        "name": "钩子-数字震撼",
        "text": "一个人<#0.2#>两万美元启动资金<#0.3#>14个月做到4亿美元营收。",
        "output_file": "S01-hook-numbers.mp3",
    },
    {
        "id": "S02",
        "name": "人物背景",
        "text": "创始人Matthew Gallagher<#0.2#>在拖车公园长大<#0.2#>用叔叔的电脑自学编程。",
        "output_file": "S02-character-bg.mp3",
    },
    {
        "id": "S03",
        "name": "关键数据+对比",
        "text": (
            "2025年<#0.2#>营收4.01亿美元<#0.2#>净利率16.2%。"
            "<#0.4#>行业巨头2400人<#0.2#>净利率才5.5%。"
        ),
        "output_file": "S03-key-data.mp3",
    },
    {
        "id": "S04",
        "name": "利润率+方法",
        "text": "他用两个人<#0.2#>跑了同行3倍的利润率。<#0.3#>代码AI写<#0.2#>广告AI生成。",
        "output_file": "S04-method.mp3",
    },
    {
        "id": "S05",
        "name": "规模+替代",
        "text": (
            "客服是AI机器人<#0.2#>日营收超300万美元。"
            "<#0.4#>这整套工具链<#0.2#>国内都有免费替代。"
        ),
        "output_file": "S05-scale-alt.mp3",
    },
    {
        "id": "S06",
        "name": "CTA",
        "text": "私信AI获客<#0.2#>我发你完整工具清单。",
        "output_file": "S06-cta.mp3",
    },
]

# Full narration for single-file generation
FULL_NARRATION = " ".join(s["text"] for s in SEGMENTS)


def api_request(url: str, headers: dict, data: dict | None = None) -> dict:
    """Make HTTP request to MiniMax API."""
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def synthesize(
    api_key: str,
    text: str,
    voice_id: str,
    output_path: Path,
    speed: float = 1.05,
    model: str = "speech-02-hd",
) -> dict:
    """Synthesize speech via MiniMax T2A API."""
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": 1,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
        "language_boost": "Chinese",
        "output_format": "hex",
    }

    result = api_request(API_BASE, headers, payload)

    status_code = result.get("base_resp", {}).get("status_code")
    if status_code != 0:
        raise RuntimeError(f"API error ({status_code}): {result.get('base_resp', {}).get('status_msg')}")

    hex_audio = result["data"]["audio"]
    audio_bytes = bytes.fromhex(hex_audio)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    extra = result.get("extra_info", {})
    duration_ms = extra.get("audio_length", 0)
    char_count = extra.get("usage_characters", 0)

    return {
        "duration_ms": duration_ms,
        "file_size": len(audio_bytes),
        "chars": char_count,
    }


def run_batch(
    api_key: str,
    segments: list[dict],
    output_dir: Path,
    voice_id: str,
    speed: float = 1.05,
) -> None:
    """Generate voiceover for all segments."""
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_duration = 0
    total_chars = 0

    for seg in segments:
        print(f"\n[{seg['id']}] {seg['name']}")
        print(f"  Text: {seg['text'][:60]}...")
        dest = output_dir / seg["output_file"]

        try:
            print("  Synthesizing... ", end="", flush=True)
            info = synthesize(api_key, seg["text"], voice_id, dest, speed)
            duration_s = info["duration_ms"] / 1000
            total_duration += duration_s
            total_chars += info["chars"]
            print(f"done ({duration_s:.1f}s, {info['file_size'] // 1024}KB)")

            results.append({
                "segment": seg["id"],
                "file": str(dest),
                "duration_ms": info["duration_ms"],
                "chars": info["chars"],
                "status": "success",
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    # Save log
    log_path = output_dir / f"minimax-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "speech-02-hd",
            "voice_id": voice_id,
            "speed": speed,
            "segments": len(segments),
            "total_duration_ms": total_duration * 1000,
            "total_chars": total_chars,
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nLog saved: {log_path}")

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] != "success")
    cost = total_chars * 3.5 / 10000  # 3.5 yuan per 10k chars
    print(f"\n{'='*50}")
    print(f"Done: {success} succeeded, {failed} failed")
    print(f"Total audio: {total_duration:.1f}s | Chars: {total_chars} | Cost: ¥{cost:.2f}")
    if failed > 0:
        print("Failed segments:")
        for r in results:
            if r["status"] != "success":
                print(f"  - {r['segment']}: {r.get('error', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="MiniMax Speech-02 TTS Batch Voiceover Generator")
    parser.add_argument("--voice", type=str, default="presenter_male",
                        help=f"Voice ID (options: {', '.join(VOICES.keys())}, or raw ID)")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed (0.5-2.0, default: 1.0)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--full", action="store_true", help="Generate full narration as single file")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without generating")
    args = parser.parse_args()

    # Resolve voice ID
    voice_id = VOICES.get(args.voice, args.voice)

    # Filter segments
    segments = SEGMENTS
    if args.shot:
        segments = [s for s in SEGMENTS if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Segment {args.shot} not found. Available: {', '.join(s['id'] for s in SEGMENTS)}")
            sys.exit(1)

    print("MiniMax Speech-02 TTS Batch Voiceover Generator")
    print("=" * 50)
    print(f"Segments: {len(segments)} ({', '.join(s['id'] for s in segments)})")
    print(f"Voice: {voice_id}")
    print(f"Speed: {args.speed}")
    print(f"Model: speech-02-hd")
    print(f"Output: {args.output_dir}")

    if args.full:
        full_chars = len(FULL_NARRATION.replace("<#", "").replace("#>", ""))
        print(f"Full narration chars: ~{full_chars}")
        print(f"Est. cost: ¥{full_chars * 3.5 / 10000:.2f}")
    else:
        total_chars = sum(len(s["text"]) for s in segments)
        print(f"Total chars: ~{total_chars}")
        print(f"Est. cost: ¥{total_chars * 3.5 / 10000:.2f}")
    print()

    if args.dry_run:
        print("DRY RUN - no generation will happen.")
        if args.full:
            print(f"\nFull narration:\n{FULL_NARRATION[:200]}...")
        else:
            print("\nSegment plan:")
            for seg in segments:
                existing = (Path(args.output_dir) / seg["output_file"]).exists()
                status = "exists (will overwrite)" if existing else "new"
                print(f"  {seg['id']} {seg['name']}: {status}")
                print(f"    {seg['text'][:80]}...")
        return

    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        print("ERROR: MINIMAX_API_KEY not set")
        print("  export MINIMAX_API_KEY='your-api-key'")
        print("  Register at: https://platform.minimaxi.com")
        sys.exit(1)

    if args.full:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        dest = output_dir / "day1-full-narration.mp3"
        print(f"Generating full narration...")
        info = synthesize(api_key, FULL_NARRATION, voice_id, dest, args.speed)
        print(f"Saved: {dest} ({info['duration_ms'] / 1000:.1f}s, {info['file_size'] // 1024}KB)")
    else:
        run_batch(api_key, segments, Path(args.output_dir), voice_id, args.speed)


if __name__ == "__main__":
    main()
