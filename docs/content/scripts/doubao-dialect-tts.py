#!/usr/bin/env python3
"""
Doubao Seed TTS 2.0 方言说唱生成器
用 Seed TTS 2.0 SSE 端点 + context_texts 控制东北话风格。
（火山引擎标准 TTS 需要 appid 权限，Seed TTS 2.0 不需要，且支持 context_texts 情绪/方言控制）

Usage:
  source docs/content/.env
  python3 doubao-dialect-tts.py --config config/sings-dialect-rap-ep01.json
  python3 doubao-dialect-tts.py --config config/sings-dialect-rap-ep01.json --shot S01
  python3 doubao-dialect-tts.py --config config/sings-dialect-rap-ep01.json --dry-run
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

TTS_ENDPOINT = "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse"
TTS_RESOURCE_ID = "seed-tts-2.0"

DEFAULT_VOICE = "zh_female_vv_uranus_bigtts"

DIALECT_CONTEXT = {
    "dongbei": "用东北话说，语气夸张搞笑，东北口音浓重，半说半唱的感觉，像东北二人转演员",
    "yueyu": "用粤语说，语气夸张搞笑，粤语口音",
    "shanghai": "用上海话说，语气夸张搞笑，上海话口音",
    "xian": "用西安话说，语气夸张搞笑，西安话口音",
    "chengdu": "用成都话说，语气夸张搞笑，成都话口音",
}


def get_audio_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def pause_markers_to_punctuation(text: str) -> str:
    """Convert <#0.3#> pause markers to punctuation."""
    def replace_marker(match):
        seconds = float(match.group(1))
        if seconds >= 0.5:
            return "——"
        return "…"
    return re.sub(r"<#(\d+\.?\d*)#>", replace_marker, text)


EMOTION_MAP = {
    "shock": {"speech_rate": 10, "loudness_rate": 10, "pitch": 1},
    "joy": {"speech_rate": 10, "loudness_rate": 5, "pitch": 2},
    "contrast": {"speech_rate": 0, "loudness_rate": 10, "pitch": 0},
    "contemplative": {"speech_rate": -15, "loudness_rate": -5, "pitch": 0},
    "power": {"speech_rate": -10, "loudness_rate": 15, "pitch": -1},
    "warm": {"speech_rate": -5, "loudness_rate": 0, "pitch": 1},
}

DEFAULT_PARAMS = {"speech_rate": -5, "loudness_rate": 0, "pitch": 0}


def synthesize_segment(
    api_key: str,
    text: str,
    voice: str,
    dialect: str,
    emotion: str,
    output_path: Path,
) -> dict:
    clean_text = pause_markers_to_punctuation(text)
    params = EMOTION_MAP.get(emotion, DEFAULT_PARAMS)

    dialect_instruction = DIALECT_CONTEXT.get(dialect, DIALECT_CONTEXT["dongbei"])

    additions = {
        "post_process": {"pitch": params["pitch"]},
        "disable_markdown_filter": True,
        "enable_latex_tn": False,
        "context_texts": [dialect_instruction],
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": TTS_RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
    }

    body = {
        "user": {"uid": f"dialect-rap-{uuid.uuid4().hex[:8]}"},
        "req_params": {
            "text": clean_text,
            "speaker": voice,
            "sample_rate": 24000,
            "audio_params": {
                "format": "mp3",
                "speech_rate": params["speech_rate"],
                "loudness_rate": params["loudness_rate"],
                "bit_rate": 128000,
            },
            "additions": json.dumps(additions),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_chunks = []
    timeout_config = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    with httpx.Client(timeout=timeout_config) as client:
        with client.stream("POST", TTS_ENDPOINT, headers=headers, json=body) as resp:
            if resp.status_code != 200:
                error_body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"API error {resp.status_code}: {error_body[:500]}")

            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = json.loads(line[5:].strip())
                code = payload.get("code", 0)
                if code not in (0, 20000000):
                    msg = payload.get("message", "unknown error")
                    raise RuntimeError(f"TTS error code {code}: {msg}")
                audio_data = payload.get("data")
                if audio_data and isinstance(audio_data, str):
                    audio_chunks.append(base64.b64decode(audio_data))

    if not audio_chunks:
        raise RuntimeError("No audio data received")

    output_path.write_bytes(b"".join(audio_chunks))
    duration_s = get_audio_duration(output_path)
    return {"duration_s": duration_s, "file_size": output_path.stat().st_size}


def get_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser(description="Doubao Seed TTS 2.0 方言说唱生成器")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--dialect", type=str, default=None,
                        help="Override dialect (dongbei/yueyu/shanghai/xian/chengdu)")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE,
                        help="Override voice speaker ID")
    parser.add_argument("--shot", type=str, help="Only generate this segment")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--delay", type=float, default=1.5)
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

    voice_config = config.get("voice", {})
    dialect = args.dialect or voice_config.get("language", "zh_dongbei").replace("zh_", "")
    voice = args.voice

    output_dir = Path(args.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Doubao Seed TTS 2.0 方言说唱 — {video_id}")
    print("=" * 50)
    print(f"Dialect: {dialect}")
    print(f"Voice: {voice}")
    print(f"Instruction: {DIALECT_CONTEXT.get(dialect, DIALECT_CONTEXT['dongbei'])}")
    print(f"Output: {output_dir}")
    print(f"Segments: {len(segments)}")
    print()

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    if args.dry_run:
        print("DRY RUN")
        total_chars = 0
        for seg in segments:
            text = seg.get("voiceover_text", "")
            chars = len(text)
            total_chars += chars
            estimated_dur = chars / 5.0
            print(f"  {seg['id']} [{seg.get('emotion', 'N/A')}]:")
            print(f"    Text ({chars}字, ~{estimated_dur:.1f}s): {text}")
        print(f"\nTotal: {total_chars}字, estimated ~{total_chars/5:.0f}s")
        return

    api_key = os.environ.get("MODEL_SPEECH_API_KEY")
    if not api_key:
        print("ERROR: MODEL_SPEECH_API_KEY not set")
        print("source docs/content/.env first")
        sys.exit(1)

    results = []
    total_duration = 0.0
    segment_files = []

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

        print(f"[{seg['id']}] [{emotion}] {text[:40]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize_segment(
                api_key=api_key,
                text=text,
                voice=voice,
                dialect=dialect,
                emotion=emotion,
                output_path=dest,
            )
            total_duration += info["duration_s"]
            segment_files.append(dest)
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")

            results.append({
                "segment": seg["id"],
                "file": str(dest),
                "duration_s": round(info["duration_s"], 2),
                "status": "success",
                "text": text,
                "emotion": emotion,
                "actual_duration_s": info["duration_s"],
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles.srt"
        entries = []
        cumulative = 0.0
        for i, r in enumerate(successful):
            dur = r["duration_s"]
            start = cumulative
            end = cumulative + dur
            entries.append(
                f"{i + 1}\n{get_srt_time(start)} --> {get_srt_time(end)}\n{r['text']}\n"
            )
            cumulative = end
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(entries))
        print(f"\nSRT: {srt_path}")

        full_path = output_dir / f"{video_id}-voice.mp3"
        concat_list = output_dir / "_concat.txt"
        with open(concat_list, "w") as f:
            for p in segment_files:
                f.write(f"file '{p}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k",
             str(full_path)],
            capture_output=True, timeout=60,
        )
        concat_list.unlink(missing_ok=True)
        print(f"Full voice: {full_path}")

    log_path = output_dir / f"dialect-tts-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "doubao-seed-tts-2.0",
            "voice_id": voice,
            "dialect": dialect,
            "dialect_instruction": DIALECT_CONTEXT.get(dialect, ""),
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total voice: {total_duration:.1f}s")
    if total_duration > 70:
        print("WARNING: Exceeds 70s target!")
    elif total_duration < 45:
        print("WARNING: Below 45s minimum!")


if __name__ == "__main__":
    main()
