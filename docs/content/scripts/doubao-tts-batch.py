#!/usr/bin/env python3
"""
Doubao TTS 2.0 Batch Voiceover Generator (config-driven)
Uses 火山引擎 豆包 TTS 2.0 API with SSE streaming.

Usage:
  source docs/content/.env
  python3 doubao-tts-batch.py --config config/day5-yangmun.json
  python3 doubao-tts-batch.py --config config/day5-yangmun.json --shot S01
  python3 doubao-tts-batch.py --config config/day5-yangmun.json --voice tvb_female --dry-run
"""

import argparse
import base64
import json
import os
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

VOICES = {
    "default_female": "zh_female_vv_uranus_bigtts",
    "tvb_female": "zh_female_tvbnv_uranus_bigtts",
    "sisi": "zh_female_shuangkuaisisi_moon_bigtts",
    "taozi": "zh_female_tianmeitaozi_mars_bigtts",
}

# Voice clone reference audio (base speaker + ref_audio overrides timbre)
REF_AUDIO_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / "_ref_audio"
DEFAULT_REF_AUDIO = REF_AUDIO_DIR / "day4-gemini.mp3"

# Emotion → speech_rate + context_texts (natural language emotion control)
EMOTION_SETTINGS = {
    "shock": {
        "speech_rate": 10,
        "loudness_rate": 10,
        "pitch": 1,
        "context_texts": ["用震惊、不可思议的语气说话，语速稍慢，带有惊讶的停顿"],
    },
    "determined": {
        "speech_rate": -5,
        "loudness_rate": 5,
        "pitch": 0,
        "context_texts": ["用坚定、有力、自信的语气说话，像在分享一个深刻的道理"],
    },
    "power": {
        "speech_rate": -10,
        "loudness_rate": 15,
        "pitch": -1,
        "context_texts": ["用充满力量、压迫感的语气说话，每个字都有分量"],
    },
    "contemplative": {
        "speech_rate": -15,
        "loudness_rate": -5,
        "pitch": 0,
        "context_texts": ["用深思、沉静、像在自言自语的语气说话，缓慢而温柔"],
    },
    "warm": {
        "speech_rate": -5,
        "loudness_rate": 0,
        "pitch": 1,
        "context_texts": ["用温暖、亲切、像跟朋友聊天的语气说话，带着微笑的感觉"],
    },
    # Legacy emotions
    "empathy": {
        "speech_rate": -10,
        "loudness_rate": 0,
        "pitch": 0,
        "context_texts": ["用共情、理解的语气说话"],
    },
    "desire": {
        "speech_rate": -5,
        "loudness_rate": 5,
        "pitch": 0,
        "context_texts": ["用充满渴望的语气说话"],
    },
    "hope": {
        "speech_rate": 5,
        "loudness_rate": 5,
        "pitch": 1,
        "context_texts": ["用充满希望、积极向上的语气说话"],
    },
    "contrast": {
        "speech_rate": 0,
        "loudness_rate": 10,
        "pitch": 0,
        "context_texts": ["用对比强烈的语气，前半段平静后半段有力"],
    },
    "joy": {
        "speech_rate": 10,
        "loudness_rate": 5,
        "pitch": 2,
        "context_texts": ["用开心、愉快的语气说话"],
    },
    "trust": {
        "speech_rate": -5,
        "loudness_rate": 0,
        "pitch": 0,
        "context_texts": ["用可靠、值得信赖的语气说话"],
    },
}

DEFAULT_EMOTION = {
    "speech_rate": -5,
    "loudness_rate": 0,
    "pitch": 0,
    "context_texts": [],
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
    """Convert <#0.3#> pause markers to Chinese punctuation."""
    def replace_marker(match):
        seconds = float(match.group(1))
        if seconds >= 0.5:
            return "——"
        return "…"
    import re
    return re.sub(r"<#(\d+\.?\d*)#>", replace_marker, text)


def get_emotion_params(emotion: str) -> dict:
    return EMOTION_SETTINGS.get(emotion, DEFAULT_EMOTION)


def resolve_voice(voice_arg: str) -> str:
    if voice_arg in VOICES:
        return VOICES[voice_arg]
    return voice_arg


def build_headers(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": TTS_RESOURCE_ID,
        "X-Api-Request-Id": str(uuid.uuid4()),
    }


def build_body(
    text: str, speaker: str, emotion_params: dict,
    ref_audio_b64: Optional[str] = None,
) -> dict:
    additions_dict = {
        "post_process": {"pitch": emotion_params["pitch"]},
        "disable_markdown_filter": True,
        "enable_latex_tn": False,
    }
    context = emotion_params.get("context_texts", [])
    if context:
        additions_dict["context_texts"] = context
    if ref_audio_b64:
        additions_dict["ref_audio"] = ref_audio_b64

    return {
        "user": {"uid": "doubao-tts-batch"},
        "req_params": {
            "text": text,
            "speaker": speaker,
            "sample_rate": 24000,
            "audio_params": {
                "format": "mp3",
                "speech_rate": emotion_params["speech_rate"],
                "loudness_rate": emotion_params["loudness_rate"],
                "bit_rate": 128000,
            },
            "additions": json.dumps(additions_dict),
        },
    }


def synthesize_segment(
    api_key: str, text: str, voice: str, emotion: str, output_path: Path,
    ref_audio_b64: Optional[str] = None,
) -> dict:
    params = get_emotion_params(emotion)
    clean_text = pause_markers_to_punctuation(text)
    headers = build_headers(api_key)
    body = build_body(clean_text, voice, params, ref_audio_b64=ref_audio_b64)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio_chunks: list[bytes] = []
    timeout_config = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    with httpx.Client(timeout=timeout_config) as client:
        with client.stream("POST", TTS_ENDPOINT, headers=headers, json=body) as resp:
            if resp.status_code != 200:
                error_body = resp.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"API error {resp.status_code}: {error_body[:500]}"
                )

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
        raise RuntimeError("No audio data received from API")

    output_path.write_bytes(b"".join(audio_chunks))

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
        entries.append(
            f"{i + 1}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{text}\n"
        )
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
         "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k",
         str(output_path)],
        capture_output=True, timeout=60,
    )
    concat_list.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Doubao TTS 2.0 Batch Voiceover Generator"
    )
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument(
        "--voice", type=str, default="default_female",
        help=f"Voice name or ID ({', '.join(VOICES.keys())})"
    )
    parser.add_argument(
        "--ref-audio", type=str, default=None,
        help="Reference audio for voice cloning (path or 'claire' for default)",
    )
    parser.add_argument(
        "--emotion", type=str, default=None,
        help="Force all segments to use this emotion (e.g., shock, determined)",
    )
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument(
        "--delay", type=float, default=2.0,
        help="Delay between requests in seconds (default: 2)"
    )
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

    ref_audio_b64: Optional[str] = None
    if args.ref_audio:
        ref_path = Path(args.ref_audio)
        if ref_path.name == "claire" or not ref_path.suffix:
            ref_path = DEFAULT_REF_AUDIO
        if not ref_path.is_absolute():
            ref_path = PROJECT_ROOT / ref_path
        if not ref_path.exists():
            print(f"ERROR: Ref audio not found: {ref_path}")
            sys.exit(1)
        with open(ref_path, "rb") as f:
            ref_audio_b64 = base64.b64encode(f.read()).decode()
        print(f"Ref audio: {ref_path.name} ({ref_path.stat().st_size // 1024}KB)")

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    if args.emotion:
        for seg in segments:
            seg["emotion_arc"] = args.emotion
        print(f"Uniform emotion: {args.emotion}")

    print(f"Doubao TTS 2.0 — {video_id}")
    print("=" * 50)
    print(f"Model: {TTS_RESOURCE_ID}")
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
            print(f"    Speed: {params['speech_rate']}, Loudness: {params['loudness_rate']}, Pitch: {params['pitch']}")
            if params.get("context_texts"):
                print(f"    Emotion: {params['context_texts'][0]}")
            print()
        return

    api_key = os.environ.get("MODEL_SPEECH_API_KEY")
    if not api_key:
        print("ERROR: MODEL_SPEECH_API_KEY not set")
        print("Register at: https://console.volcengine.com/speech/new/setting/apikeys")
        print("Then add to docs/content/.env:")
        print('  export MODEL_SPEECH_API_KEY="your-api-key-here"')
        sys.exit(1)

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
        params = get_emotion_params(emotion)

        print(f"[{seg['id']}] [{emotion}] {text[:50]}...")
        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize_segment(api_key, raw_text, voice, emotion, dest, ref_audio_b64=ref_audio_b64)
            total_duration += info["duration_s"]
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            print(f"    speed={params['speech_rate']} loudness={params['loudness_rate']} pitch={params['pitch']}")
            results.append({
                "segment": seg["id"],
                "file": str(dest),
                "duration_s": info["duration_s"],
                "status": "success",
                "actual_duration_s": info["duration_s"],
                "voiceover_text": text,
                "emotion": emotion,
            })
        except Exception as e:
            print(f"failed: {e}")
            results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles-doubao.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-doubao.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"doubao-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "doubao-tts-2.0",
            "voice_id": voice,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total: {total_duration:.1f}s")
    if total_duration > 90:
        print("WARNING: Exceeds 90s!")
    elif total_duration < 30:
        print("WARNING: Below 30s minimum!")


if __name__ == "__main__":
    main()
