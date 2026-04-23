#!/usr/bin/env python3
"""
Gemini 3.1 Flash TTS Batch Voiceover Generator (config-driven)
Uses Google Gemini with advanced prompting (Director's Notes + audio tags).

Usage:
  source docs/content/.env
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json --shot S01 --dry-run
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json --voice Charon
"""

import argparse
import json
import os
import struct
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
import re

from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

VOICES = [
    "Charon", "Orus", "Iapetus", "Sadaltager", "Sulafat",
    "Puck", "Fenrir", "Kore", "Aoede", "Ledas",
    "Enceladus", "Zephyr", "Vindemiatrix", "Leda", "Sadachbia",
]

# Unified narrator profile — same person throughout the whole video
NARRATOR_PROFILE = (
    "You are a Chinese male narrator telling a compelling story in a Douyin short video. "
    "Speak Mandarin naturally and warmly, as if sharing an amazing discovery with a friend. "
    "You have a confident, grounded voice with natural emotional range."
)

NARRATOR_SCENE = "Narrating a short video about an underdog founder's incredible business success."

# Emotion arc → Director's Notes only (same narrator, different emotional delivery)
EMOTION_PROMPTS = {
    "empathy": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Open with genuine amazement at the numbers. Use [amazed] at the key figure. Sound like you just discovered something incredible and can't wait to share it. Natural, conversational energy.",
    },
    "desire": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Shift to a more reflective, storytelling tone. Paint the humble beginnings vividly. Use [softly] to create intimacy. Slow down slightly. This is backstory, let it breathe.",
    },
    "hope": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Build momentum. List the AI capabilities with quiet excitement. Use [warmly] when describing the tools. This is the 'aha' moment where the listener sees the path forward.",
    },
    "shock": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Deliver the financial data with controlled impact. Use [confidently] for the numbers. Not shouting — let the data speak. A slight pause before each key figure adds weight.",
    },
    "contrast": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "This is the punchline. Use [serious] for the industry giants, then shift to subtle [impressed] satisfaction for the underdog's numbers. The contrast should feel earned, not forced.",
    },
    "joy": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Light, upbeat energy. Use [cheerfully] naturally. The daily revenue figure should land with a sense of 'can you believe this?' Don't oversell — let the number do the work.",
    },
    "trust": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Warm, direct invitation. Use [warmly] and speak with quiet certainty. This is a friend making a genuine recommendation, not a sales pitch. End with natural conviction.",
    },
    # Yang Mun character emotions (Day4)
    "determined": {
        "profile": NARRATOR_PROFILE,
        "scene": "Narrating a business efficiency video exposing wasted human labor.",
        "director": "Speak with quiet anger and conviction. Use [confidently] to call out inefficiency. Not shouting, but firm. Each sentence should land like a fact, not an opinion. Slow down before the key insight.",
    },
    "power": {
        "profile": NARRATOR_PROFILE,
        "scene": "Delivering business rules that separate winners from losers.",
        "director": "Authority mode. Use [seriously] for the rule, then [impressed] for the result. Let numbers hit hard. Short pauses between statements. Sound like someone who has seen this truth firsthand.",
    },
    "contemplative": {
        "profile": NARRATOR_PROFILE,
        "scene": "Reflecting on what speed really means for survival.",
        "director": "Slow down. Use [thoughtfully] throughout. This is reflection, not attack. Each example should feel like turning a page. End with quiet certainty, not aggression.",
    },
    "warm": {
        "profile": NARRATOR_PROFILE,
        "scene": "Turning business lessons into a personal call to action.",
        "director": "Drop the authority. Use [warmly] and speak like a friend who genuinely cares. The shift from business data to 'you' should feel natural. End with gentle invitation, not pressure.",
    },
}

AUDIO_TAGS = {
    "empathy": ["[amazed]", "[curious]"],
    "desire": ["[softly]", "[thoughtfully]"],
    "hope": ["[warmly]", "[gently]"],
    "shock": ["[gasps]", "[excitedly]"],
    "contrast": ["[serious]", "[impressed]"],
    "joy": ["[cheerfully]", "[laughing]"],
    "trust": ["[warmly]", "[confidently]"],
    "determined": ["[confidently]", "[seriously]"],
    "power": ["[seriously]", "[impressed]"],
    "contemplative": ["[thoughtfully]", "[softly]"],
    "warm": ["[warmly]", "[gently]"],
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


def save_pcm_as_wav(pcm_data: bytes, output_path: Path, sample_rate: int = 24000,
                    sample_width: int = 2, channels: int = 1) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)


def build_prompt(seg: dict, emotion: str) -> str:
    """Build advanced prompt with Profile + Scene + Director's Notes."""
    text = strip_pause_markers(seg.get("voiceover_pause_markers", seg.get("voiceover_text", "")))
    tags = AUDIO_TAGS.get(emotion, [])
    tagged_text = f"{tags[0]} {text}" if tags else text

    ep = EMOTION_PROMPTS.get(emotion, {})
    profile = ep.get("profile", "You are a Chinese male narrator. Speak Mandarin naturally.")
    scene = ep.get("scene", "Narrating a short video segment.")
    director = ep.get("director", "Speak naturally and clearly.")

    return f"""Audio Profile: {profile}

Scene: {scene}

Director's Notes: {director}

Transcript: {tagged_text}"""


def synthesize(client: genai.Client, text_prompt: str, voice: str,
               output_path: Path) -> dict:
    response = client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=text_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )

    audio_part = response.candidates[0].content.parts[0]
    pcm_data = audio_part.inline_data.data

    wav_path = output_path.with_suffix(".wav")
    save_pcm_as_wav(pcm_data, wav_path)

    mp3_path = output_path.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-ar", "44100",
         "-ac", "1", "-b:a", "192k", str(mp3_path)],
        capture_output=True, timeout=30,
    )
    wav_path.unlink(missing_ok=True)

    duration_s = get_audio_duration(mp3_path)
    return {"duration_s": duration_s, "file_size": mp3_path.stat().st_size}


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
    parser = argparse.ArgumentParser(description="Gemini TTS (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--voice", type=str, default="Charon",
                        help=f"Voice name ({', '.join(VOICES[:5])} recommended)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--delay", type=float, default=25.0,
                        help="Delay between requests in seconds (free tier: 25s)")
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

    voice = args.voice
    output_dir = Path(args.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    print(f"Gemini TTS — {video_id}")
    print("=" * 50)
    print(f"Model: gemini-3.1-flash-tts-preview")
    print(f"Voice: {voice}")
    print(f"Output: {output_dir}")
    print()

    if args.dry_run:
        print("DRY RUN")
        for seg in segments:
            emotion = seg.get("emotion", "")
            prompt = build_prompt(seg, emotion)
            print(f"  {seg['id']} [{emotion}]:")
            print(f"    Text: {seg.get('voiceover_text', '')[:60]}...")
            ep = EMOTION_PROMPTS.get(emotion, {})
            print(f"    Profile: {ep.get('profile', '')[:60]}...")
            print(f"    Director: {ep.get('director', '')[:60]}...")
            print()
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        print("Get it from: https://aistudio.google.com/apikey")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    def _is_quota_error(error: Exception) -> bool:
        msg = str(error).lower()
        return any(kw in msg for kw in ["429", "quota", "resource_exhausted", "403", "permission"])

    def _synthesize_doubao(seg: dict, dest: Path) -> dict:
        """Fallback: synthesize via Doubao TTS. Returns {duration_s, file_size}."""
        import base64
        import importlib.util
        # Import from sibling script
        spec = importlib.util.spec_from_file_location(
            "doubao_tts_batch",
            str(Path(__file__).resolve().parent / "doubao-tts-batch.py"),
        )
        dtb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dtb)
        doubao_key = os.environ.get("MODEL_SPEECH_API_KEY")
        if not doubao_key:
            raise RuntimeError("MODEL_SPEECH_API_KEY not set for Doubao fallback")
        voice_id = dtb.resolve_voice("default_female")
        emotion = seg.get("emotion", seg.get("emotion_arc", "shock"))
        raw_text = seg.get("voiceover_pause_markers", seg.get("voiceover_text", ""))
        ref_audio_b64 = None
        voiceover_cfg = config.get("voiceover", {})
        if voiceover_cfg.get("ref_audio") == "claire":
            ref_path = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / "_ref_audio" / "day4-gemini.mp3"
            if ref_path.exists():
                with open(ref_path, "rb") as f:
                    ref_audio_b64 = base64.b64encode(f.read()).decode()
        return dtb.synthesize_segment(doubao_key, raw_text, voice_id, emotion, dest, ref_audio_b64=ref_audio_b64)

    use_doubao = False
    results = []
    total_duration = 0.0

    for i, seg in enumerate(segments):
        text = seg.get("voiceover_text", "")
        emotion = seg.get("emotion", seg.get("emotion_arc", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        if i > 0 and not use_doubao:
            print(f"  Waiting {args.delay}s (rate limit)...", flush=True)
            time.sleep(args.delay)

        dest = output_dir / f"{seg['id']}.mp3"
        prompt = build_prompt(seg, emotion)

        print(f"[{seg['id']}] [{seg.get('emotion_arc', '')}] {text[:50]}...")

        if use_doubao:
            # Already fallen back to Doubao
            print("  Synthesizing (Doubao)... ", end="", flush=True)
            try:
                info = _synthesize_doubao(seg, dest)
                total_duration += info["duration_s"]
                print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                results.append({
                    "segment": seg["id"], "file": str(dest),
                    "duration_s": info["duration_s"], "status": "success",
                    "actual_duration_s": info["duration_s"],
                    "voiceover_text": text, "engine": "doubao_fallback",
                })
            except Exception as e:
                print(f"failed: {e}")
                results.append({"segment": seg["id"], "status": "error", "error": str(e)})
            continue

        print("  Synthesizing... ", end="", flush=True)

        try:
            info = synthesize(client, prompt, voice, dest)
            total_duration += info["duration_s"]
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            ep = EMOTION_PROMPTS.get(emotion, {})
            print(f"    director: {ep.get('director', '')[:50]}...")
            results.append({
                "segment": seg["id"], "file": str(dest),
                "duration_s": info["duration_s"], "status": "success",
                "actual_duration_s": info["duration_s"],
                "voiceover_text": text,
                "director_notes": ep.get("director", ""),
            })
        except Exception as e:
            if _is_quota_error(e):
                use_doubao = True
                print(f"\n  Gemini TTS quota exceeded, falling back to Doubao TTS")
                print(f"  Retrying {seg['id']} with Doubao... ", end="", flush=True)
                try:
                    info = _synthesize_doubao(seg, dest)
                    total_duration += info["duration_s"]
                    print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                    results.append({
                        "segment": seg["id"], "file": str(dest),
                        "duration_s": info["duration_s"], "status": "success",
                        "actual_duration_s": info["duration_s"],
                        "voiceover_text": text, "engine": "doubao_fallback",
                    })
                except Exception as e2:
                    print(f"Doubao fallback also failed: {e2}")
                    results.append({"segment": seg["id"], "status": "error", "error": str(e2)})
            else:
                print(f"failed: {e}")
                results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles-gemini.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-gemini.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"gemini-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "gemini-3.1-flash-tts-preview",
            "voice_id": voice,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total: {total_duration:.1f}s")
    if total_duration > 60:
        print("WARNING: Exceeds 60s limit!")
    elif total_duration < 30:
        print("WARNING: Below 30s minimum!")


if __name__ == "__main__":
    main()
