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
NARRATOR_PROFILE_MALE = (
    "You are a Chinese male narrator telling a compelling story in a Douyin short video. "
    "Speak Mandarin naturally and warmly, as if sharing an amazing discovery with a friend. "
    "You have a confident, grounded voice with natural emotional range."
)

NARRATOR_PROFILE_FEMALE = (
    "You are a Chinese female narrator telling a compelling story in a Douyin short video. "
    "Speak Mandarin naturally and warmly, as if sharing an amazing discovery with a friend. "
    "You have a confident, clear voice with natural emotional range."
)

# Unemployment series narrator — first person, male, 38yo laid-off worker
NARRATOR_PROFILE_UNEMPLOY = (
    "你是一个38岁的中国男性，在外企工作了15年后被裁员。"
    "你在讲述自己的真实经历，不是旁白，是第一人称自述。"
    "语气自然，像跟老朋友聊天，不要播音腔。声音沉稳但带着真实情感。"
)

NARRATOR_PROFILE = NARRATOR_PROFILE_UNEMPLOY

NARRATOR_SCENE = "第一人称讲述被裁47天后靠翻通讯录赚到第一个5000块的经历。"

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
    # Day7 emotion arcs
    "tension": {
        "profile": NARRATOR_PROFILE,
        "scene": "Delivering an uncomfortable truth about busywork and wasted effort.",
        "director": "Build tension steadily. Use [seriously] to state the iron law. List examples with quiet intensity, each one sharper than the last. Not angry, but firm. End with the punchline landing like a verdict.",
    },
    "reversal": {
        "profile": NARRATOR_PROFILE,
        "scene": "Revealing a counterintuitive insight that changes the listener's perspective.",
        "director": "Start with the conventional wisdom, then flip it. Use [thoughtfully] for the setup, [impressed] for the reveal. The data point should feel like a plot twist. Slow down before the key figure.",
    },
    "fear": {
        "profile": NARRATOR_PROFILE,
        "scene": "Describing a vicious cycle that traps people in mediocrity.",
        "director": "Speak with controlled urgency. Use [seriously] for the cycle, then [softly] for the escape. Each repetition of the trap should feel heavier. End with quiet hope, not despair.",
    },
    # Unemployment series emotions (first-person male)
    "好奇": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "开场告诉朋友一个意外的结果。",
        "director": "像跟朋友说'你猜怎么着'一样开场。语气轻松带悬念，不要太沉重。说完数字后稍微停顿，让听众消化。结尾'翻通讯录'三个字稍微加重，制造好奇。",
    },
    "代入": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "平淡回忆被裁那天的事。",
        "director": "像回忆一件已经过去的事，不激动也不委屈。数字'38岁'、'15年'轻轻带过。'全没了'之后要有一个明显的停顿。HR那句话用稍微不同的语气模仿，然后'你太贵了'要轻，不要咬牙切齿，要轻得像刀子。",
    },
    "共鸣": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "讲述求职失败和经济压力。",
        "director": "压力递增。每个'回复0'比上一个更沉重，像一块块石头往上加。房贷、幼儿园、降压药三连要快，要窒息。最后一句'醒来就要面对一天'要慢下来，声音要空，像说完就没力气了。",
    },
    "希望": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "转折点，老客户的一句话改变了一切。",
        "director": "语气从沉重自然变暖。老客户那句话'我找的是你，不是你们公司'要带着温暖和意外，像第一次听到时那种感动。翻通讯录那段微微上扬，'原来这些东西一直都在'要有发现宝藏的感觉。",
    },
    "力量": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "从过来人的角度给同样处境的人力量。",
        "director": "安静笃定，不是说教，是确认。像一个已经走出来的人回头告诉你'你身上的东西比你以为的多'。不煽情，不反问，用陈述句传递力量。语速适中，每个短句之间有呼吸空间。",
    },
    "参与": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "放下故事，直接问听众。",
        "director": "从讲故事切换到直接对话。语气放松，像朋友问一句'你投了多少了？'。不要严肃，不要煽情，就一个自然的邀请。最后'评论区说说'要轻松，像随口一说。",
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
    "tension": ["[seriously]", "[confidently]"],
    "reversal": ["[thoughtfully]", "[impressed]"],
    "fear": ["[seriously]", "[softly]"],
    "好奇": ["[curious]", "[gently]"],
    "代入": ["[softly]", "[thoughtfully]"],
    "共鸣": ["[seriously]", "[softly]"],
    "希望": ["[warmly]", "[gently]"],
    "力量": ["[confidently]", "[warmly]"],
    "参与": ["[cheerfully]", "[warmly]"],
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
    parser.add_argument("--female", action="store_true", help="Use female narrator profile")
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

    if args.female:
        print(f"  Note: Using female narrator profile (Aoede voice)")
        global NARRATOR_PROFILE
        NARRATOR_PROFILE = NARRATOR_PROFILE_FEMALE
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
    print(f"Channel priority: Google → 云雾AI → Doubao")
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

    google_key = os.environ.get("GEMINI_API_KEY")
    yunwu_key = os.environ.get("YUNWU_API_KEY")
    yunwu_base = os.environ.get("YUNWU_BASE_URL", "https://yunwu.ai")

    if not google_key and not yunwu_key:
        print("ERROR: No API key set (GEMINI_API_KEY or YUNWU_API_KEY)")
        print("Get Google key: https://aistudio.google.com/apikey")
        sys.exit(1)

    google_client = genai.Client(api_key=google_key) if google_key else None
    yunwu_client = (
        genai.Client(api_key=yunwu_key, http_options={"base_url": yunwu_base})
        if yunwu_key else None
    )
    client = google_client or yunwu_client
    active_channel = "google"
    print(f"Channel: Google (direct) → 云雾AI (fallback) → Doubao (last resort)")
    if yunwu_client:
        print(f"  云雾AI ready: {yunwu_base}")
    else:
        print("  云雾AI: not configured (no YUNWU_API_KEY)")

    def _is_quota_error(error: Exception) -> bool:
        msg = str(error).lower()
        return any(kw in msg for kw in ["429", "quota", "resource_exhausted", "403", "permission", "503", "unavailable", "high demand"])

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
    use_yunwu = False
    results = []
    total_duration = 0.0

    for i, seg in enumerate(segments):
        text = seg.get("voiceover_text", "")
        emotion = seg.get("emotion", seg.get("emotion_arc", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        if i > 0 and not use_doubao and not use_yunwu:
            print(f"  Waiting {args.delay}s (rate limit)...", flush=True)
            time.sleep(args.delay)

        dest = output_dir / f"{seg['id']}.mp3"
        prompt = build_prompt(seg, emotion)

        print(f"[{seg['id']}] [{seg.get('emotion_arc', '')}] {text[:50]}...")

        if use_doubao:
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

        if use_yunwu:
            print("  Synthesizing (云雾AI)... ", end="", flush=True)
            try:
                info = synthesize(yunwu_client, prompt, voice, dest)
                total_duration += info["duration_s"]
                print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                results.append({
                    "segment": seg["id"], "file": str(dest),
                    "duration_s": info["duration_s"], "status": "success",
                    "actual_duration_s": info["duration_s"],
                    "voiceover_text": text, "engine": "yunwu_gemini",
                })
            except Exception as e:
                if _is_quota_error(e) or "503" in str(e):
                    print(f"云雾AI failed: {e}")
                    print(f"  Falling back to Doubao TTS")
                    use_doubao = True
                    try:
                        info = _synthesize_doubao(seg, dest)
                        total_duration += info["duration_s"]
                        print(f"  Doubao done ({info['duration_s']:.1f}s)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "doubao_fallback",
                        })
                    except Exception as e2:
                        print(f"  Doubao also failed: {e2}")
                        results.append({"segment": seg["id"], "status": "error", "error": str(e2)})
                else:
                    print(f"failed: {e}")
                    results.append({"segment": seg["id"], "status": "error", "error": str(e)})
            continue

        print(f"  Synthesizing (Google direct)... ", end="", flush=True)

        try:
            info = synthesize(google_client, prompt, voice, dest)
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
                print(f"\n  Google quota exceeded!")
                if yunwu_client:
                    use_yunwu = True
                    print(f"  Retrying {seg['id']} with 云雾AI... ", end="", flush=True)
                    try:
                        info = synthesize(yunwu_client, prompt, voice, dest)
                        total_duration += info["duration_s"]
                        print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "yunwu_gemini",
                        })
                    except Exception as e2:
                        print(f"云雾AI failed: {e2}")
                        print(f"  Falling back to Doubao TTS")
                        use_doubao = True
                        try:
                            info = _synthesize_doubao(seg, dest)
                            total_duration += info["duration_s"]
                            print(f"  Doubao done ({info['duration_s']:.1f}s)")
                            results.append({
                                "segment": seg["id"], "file": str(dest),
                                "duration_s": info["duration_s"], "status": "success",
                                "actual_duration_s": info["duration_s"],
                                "voiceover_text": text, "engine": "doubao_fallback",
                            })
                        except Exception as e3:
                            print(f"  Doubao also failed: {e3}")
                            results.append({"segment": seg["id"], "status": "error", "error": str(e3)})
                else:
                    print(f"  No 云雾AI configured, falling back to Doubao TTS")
                    use_doubao = True
                    try:
                        info = _synthesize_doubao(seg, dest)
                        total_duration += info["duration_s"]
                        print(f"  Doubao done ({info['duration_s']:.1f}s)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "doubao_fallback",
                        })
                    except Exception as e2:
                        print(f"  Doubao also failed: {e2}")
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
