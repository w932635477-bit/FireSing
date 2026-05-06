#!/usr/bin/env python3
"""
Suno Cover Audio Demo Generator

Uploads a reference audio + new lyrics to Suno API to generate a cover
that preserves the original melody with new lyrics.

Usage:
  source docs/content/.env

  # With a local audio file:
  python suno-cover-demo.py --audio /path/to/上弦月.mp3

  # Dry run (no API calls):
  python suno-cover-demo.py --audio /path/to/上弦月.mp3 --dry-run

  # Custom lyrics file:
  python suno-cover-demo.py --audio /path/to/上弦月.mp3 --lyrics custom.txt
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "cover"
SCRIPTS_DIR = Path(__file__).resolve().parent

SUNO_API_BASE = "https://api.sunoapi.org/api/v1"
FILE_UPLOAD_BASE = "https://sunoapiorg.redpandaai.co"

# Adapted lyrics for 上弦月 melody (from sings01-上弦月改编.md)
DEFAULT_LYRICS = """[Verse]
两万块钱就敢创业
他十四个月干了四个亿
AI帮他全搞定
一个人一台电脑就行

拖车公园里长大的人
借叔叔电脑自学写代码
别人花百万请团队
他用AI一个人全部能替代

[Chorus]
四亿营收净利十六个点
巨头两千四百人干不过
俩人AI效率三倍碾压
这套操作真的太神

[Outro]
日营收超过三百万美金
国内工具全部能替代
私信回复AI获客就行
工具清单我免费发给你"""


def load_env() -> None:
    """Load API keys from docs/content/.env."""
    env_path = PROJECT_ROOT / "docs" / "content" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    line = line.removeprefix("export ").strip()
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip().strip('"'))


def get_api_key() -> str:
    """Get SunoAPI.org API key from environment."""
    key = os.environ.get("SUNOAPI_ORG_KEY", "") or os.environ.get("SUNO_API_KEY", "")
    if not key:
        print("ERROR: SUNOAPI_ORG_KEY or SUNO_API_KEY not set")
        print("  export SUNOAPI_ORG_KEY=your-key")
        print("  Or source docs/content/.env")
        sys.exit(1)
    return key


def audio_to_base64(audio_path: Path) -> str:
    """Read audio file and return base64 encoded string."""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def upload_file_base64(api_key: str, audio_path: Path) -> str:
    """Upload audio file to Suno via Base64. Returns upload URL."""
    print(f"  Encoding {audio_path.name} to base64...")
    b64_data = audio_to_base64(audio_path)
    print(f"  Base64 size: {len(b64_data):,} chars")

    ext = audio_path.suffix.lstrip(".").lower()
    mime_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4"}
    mime_type = mime_map.get(ext, "audio/mpeg")

    payload = {
        "base64Data": f"data:{mime_type};base64,{b64_data}",
        "uploadPath": "audio",
        "fileName": audio_path.name,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FireSing/1.0",
    }

    url = f"{FILE_UPLOAD_BASE}/api/file-base64-upload"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    print("  Uploading to Suno file API...")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: File upload API returned {e.code}")
        print(f"  Response: {body_text[:500]}")
        sys.exit(1)

    upload_url = result.get("data", {}).get("downloadUrl", "")
    if not upload_url:
        print(f"ERROR: No downloadUrl in response: {json.dumps(result, indent=2)[:500]}")
        sys.exit(1)

    return upload_url


def generate_cover(
    api_key: str,
    upload_url: str,
    lyrics: str,
    title: str = "AI黑手上弦月",
    style: str = "Cantonese pop, piano, ballad, emotional",
    model: str = "V4_5",
    audio_weight: float = 0.85,
    vocal_gender: str = "m",
) -> str:
    """Submit cover generation request. Returns task ID."""
    payload = {
        "uploadUrl": upload_url,
        "customMode": True,
        "instrumental": False,
        "model": model,
        "prompt": lyrics,
        "style": style,
        "title": title,
        "audioWeight": audio_weight,
        "vocalGender": vocal_gender,
        "callBackUrl": "https://api.sunoapi.org/callback",
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FireSing/1.0",
    }

    url = f"{SUNO_API_BASE}/generate/upload-cover"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    print("Submitting cover generation...")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"ERROR: API returned {e.code}")
        print(f"  Response: {body_text[:500]}")
        sys.exit(1)

    print(f"  API response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
    task_id = (result.get("data") or {}).get("taskId", "")
    if not task_id:
        print(f"ERROR: No taskId in response: {json.dumps(result, indent=2)[:500]}")
        sys.exit(1)

    return task_id


def poll_task(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    """Poll Suno task API until completion."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "FireSing/1.0",
    }
    url = f"{SUNO_API_BASE}/generate/record-info?taskId={task_id}"

    start_time = time.time()
    consecutive_errors = 0

    while time.time() - start_time < max_wait:
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            consecutive_errors = 0
        except (urllib.error.URLError, OSError) as e:
            consecutive_errors += 1
            if consecutive_errors > 5:
                print(f"ERROR: Too many network errors: {e}")
                sys.exit(1)
            print(f"  Network error, retrying ({consecutive_errors})...")
            time.sleep(2 * consecutive_errors)
            continue

        status = result.get("data", {}).get("status", "")
        if status in ("SUCCESS", "FAILED", "TEXT_SUCCESS"):
            # For TEXT_SUCCESS, check if sunoData has audioUrl
            if status == "TEXT_SUCCESS":
                suno_data = result.get("data", {}).get("sunoData", [])
                response_data = result.get("data", {}).get("response", {}).get("sunoData", [])
                all_audio = suno_data or response_data
                if all_audio and all(item.get("audioUrl") for item in all_audio):
                    return result
                # Still generating audio, keep polling
            else:
                return result

        # Also check sunoData for completion
        suno_data = result.get("data", {}).get("sunoData", [])
        if suno_data and all(
            item.get("audioUrl") for item in suno_data
        ):
            return result

        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s, status={status})")
        time.sleep(5)

    print("ERROR: Generation timed out")
    sys.exit(1)


def download_audio(url: str, output_path: Path) -> int:
    """Download audio file from URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "FireSing/1.0"}
    req = urllib.request.Request(url, headers=headers, method="GET")
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    with opener.open(req, timeout=120) as resp:
        data = resp.read()
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suno Cover Audio Demo Generator (上弦月改编)"
    )
    parser.add_argument(
        "--audio",
        type=Path,
        required=True,
        help="Path to reference audio file (e.g. 上弦月.mp3)",
    )
    parser.add_argument(
        "--lyrics",
        type=Path,
        help="Path to lyrics text file (default: built-in adapted lyrics)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="AI黑手上弦月",
        help="Song title for Suno",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="Cantonese pop, piano, ballad, emotional",
        help="Style tags",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="V4_5",
        choices=["V4", "V4_5", "V4_5PLUS", "V4_5ALL", "V5"],
        help="Suno model version",
    )
    parser.add_argument(
        "--audio-weight",
        type=float,
        default=0.85,
        help="How much input audio influences output (0.0-1.0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: docs/content/assets/cover)",
    )
    parser.add_argument(
        "--vocal-gender",
        type=str,
        default="m",
        choices=["m", "f"],
        help="Vocal gender (m or f)",
    )
    parser.add_argument(
        "--video-id",
        type=str,
        default="sings01",
        help="Video ID for output naming",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without generating",
    )

    args = parser.parse_args()

    if not args.audio.exists():
        print(f"ERROR: Audio file not found: {args.audio}")
        sys.exit(1)

    # Load lyrics
    lyrics = DEFAULT_LYRICS
    if args.lyrics:
        if not args.lyrics.exists():
            print(f"ERROR: Lyrics file not found: {args.lyrics}")
            sys.exit(1)
        with open(args.lyrics, "r", encoding="utf-8") as f:
            lyrics = f.read().strip()

    # Load env and get API key
    load_env()

    print(f"Suno Cover Demo — {args.video_id}")
    print("=" * 50)
    print(f"Audio: {args.audio}")
    print(f"Model: {args.model}")
    print(f"Style: {args.style}")
    print(f"Audio weight: {args.audio_weight}")
    print(f"Title: {args.title}")
    print()
    print("Lyrics:")
    print("-" * 40)
    print(lyrics)
    print("-" * 40)
    print()

    if args.dry_run:
        print("DRY RUN — no generation will happen.")
        print(f"Would upload: {args.audio.name}")
        print(f"Would generate: cover with {len(lyrics)} chars of lyrics")
        print(f"Output dir: {DEFAULT_OUTPUT_DIR}")
        return

    api_key = get_api_key()

    # Step 1: Upload audio to Suno
    print("Step 1: Uploading reference audio...")
    upload_url = upload_file_base64(api_key, args.audio)
    print(f"  Upload URL: {upload_url[:80]}...")
    print()

    # Step 2: Generate cover
    print("Step 2: Generating cover...")
    task_id = generate_cover(
        api_key=api_key,
        upload_url=upload_url,
        lyrics=lyrics,
        title=args.title,
        style=args.style,
        model=args.model,
        audio_weight=args.audio_weight,
        vocal_gender=args.vocal_gender,
    )
    print(f"  Task ID: {task_id}")
    print()

    # Step 3: Poll for results
    print("Step 3: Waiting for generation...")
    result = poll_task(api_key, task_id)

    status = result.get("data", {}).get("status", "")
    if status == "FAILED":
        error_msg = result.get("data", {}).get("error_message", "unknown")
        print(f"ERROR: Generation failed — {error_msg}")
        sys.exit(1)

    # Step 4: Download results
    suno_data = (
        result.get("data", {}).get("sunoData", [])
        or result.get("data", {}).get("response", {}).get("sunoData", [])
    )
    if not suno_data:
        print("ERROR: No audio data in response")
        print(f"  Full response: {json.dumps(result, indent=2)[:1000]}")
        sys.exit(1)

    output_dir = args.output_dir or DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    video_id = args.video_id

    for i, item in enumerate(suno_data):
        audio_url = item.get("audioUrl", "")
        if not audio_url:
            print(f"  Version {i + 1}: No audio URL")
            continue

        output_name = f"{video_id}_cover_v{i + 1}.mp3"
        output_path = output_dir / output_name
        print(f"  Downloading v{i + 1} → {output_name}...")

        try:
            file_size = download_audio(audio_url, output_path)
            duration = item.get("duration", "?")
            print(f"  Done: {file_size:,} bytes, duration={duration}s")
        except Exception as e:
            print(f"  ERROR downloading v{i + 1}: {e}")

    # Save log
    log_entry = {
        "video_id": args.video_id,
        "timestamp": datetime.now().isoformat(),
        "method": "suno-cover",
        "model": args.model,
        "style": args.style,
        "audio_weight": args.audio_weight,
        "task_id": task_id,
        "reference_audio": str(args.audio),
        "output_dir": str(output_dir),
    }
    log_path = output_dir / f"cover-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    print()
    print("Cover generation complete.")
    print(f"Output: {output_dir}")
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
