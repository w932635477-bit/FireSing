#!/usr/bin/env python3
"""
Suno → Demucs → BGM Mix Pipeline for 方言说唱
完整的半说半唱生成管线：
  Step 1: Suno 生成半说半唱曲目（含人声+beat）
  Step 2: Demucs 分离出纯人声
  Step 3: 人声叠在固定 BGM (Primetime-Sexcrime) 上

Usage:
  source docs/content/.env
  python3 suno-dialect-rap.py --config config/sings-dialect-rap-ep01.json
  python3 suno-dialect-rap.py --config config/sings-dialect-rap-ep01.json --step mix-only
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "output"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

EVOLINK_API_BASE = "https://api.evolink.ai"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def download_file(url: str, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "FireSing/1.0"})
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    with opener.open(req, timeout=120) as resp:
        data = resp.read()
    with open(output_path, "wb") as f:
        f.write(data)
    return len(data)


# ── Step 1: Suno Generation ──

def start_suno_generation(api_key: str, payload: dict) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "FireSing/1.0",
    }
    body = json.dumps(payload).encode("utf-8")
    url = f"{EVOLINK_API_BASE}/v1/audios/generations"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def poll_suno_task(api_key: str, task_id: str, max_wait: int = 300) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "FireSing/1.0",
    }
    url = f"{EVOLINK_API_BASE}/v1/tasks/{task_id}"
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with opener.open(req, timeout=30) as resp:
                task = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"  Network error: {e}, retrying...")
            time.sleep(5)
            continue

        status = task.get("status", "")
        if status in ("succeeded", "failed", "completed"):
            return task

        elapsed = int(time.time() - start_time)
        print(f"  Waiting... ({elapsed}s, status={status})")
        time.sleep(5)

    raise RuntimeError("Suno generation timed out")


def run_suno_step(config: dict, output_dir: Path) -> Path:
    """Generate full track via Suno API."""
    api_key = os.environ.get("SUNO_API_KEY")
    if not api_key:
        raise RuntimeError("SUNO_API_KEY not set")

    suno_config = config.get("suno", {})
    lyrics_config = config.get("lyrics", {})
    lyrics = lyrics_config.get("suno_format", "")

    payload = {
        "model": suno_config.get("model", "suno-v4.5"),
        "custom_mode": True,
        "prompt": lyrics,
        "style": suno_config.get("style_tags", ""),
        "title": suno_config.get("title", f"dialect-rap-{config['video_id']}"),
        "vocal_gender": suno_config.get("vocal_gender", "f"),
    }

    neg = suno_config.get("negative_tags", "")
    if neg:
        payload["negative_tags"] = neg

    print(f"Step 1: Suno generation...")
    print(f"  Style: {payload['style'][:80]}...")
    print(f"  Lyrics: {len(lyrics)} chars")

    resp = start_suno_generation(api_key, payload)
    task_id = (resp.get("data", {}).get("task_id")
               or resp.get("task_id")
               or resp.get("id"))
    if not task_id:
        # Maybe direct result
        audio_url = resp.get("data", {}).get("audio_url")
        if audio_url:
            suno_path = output_dir / f"{config['video_id']}-suno-full.mp3"
            download_file(audio_url, suno_path)
            print(f"  Direct download: {suno_path}")
            return suno_path
        raise RuntimeError(f"Unexpected response: {json.dumps(resp, ensure_ascii=False)[:300]}")

    print(f"  Task ID: {task_id}")
    task = poll_suno_task(api_key, task_id)

    if task.get("status") == "failed":
        raise RuntimeError(f"Suno failed: {task}")

    # Extract audio URL from task result
    audio_url = None
    for key in ("result_data", "data", "result", "outputs"):
        data = task.get(key)
        if data is None:
            continue
        if isinstance(data, list) and data:
            for item in data:
                if isinstance(item, dict):
                    audio_url = (item.get("audio_url")
                                 or item.get("url")
                                 or item.get("stream_url"))
                    if audio_url:
                        break
        elif isinstance(data, dict):
            audio_url = (data.get("audio_url")
                         or data.get("url")
                         or data.get("stream_url"))
        if audio_url:
            break

    if not audio_url:
        raise RuntimeError(f"No audio URL in response: {json.dumps(task, ensure_ascii=False)[:300]}")

    suno_path = output_dir / f"{config['video_id']}-suno-full.mp3"
    size = download_file(audio_url, suno_path)
    dur = get_duration(suno_path)
    print(f"  Downloaded: {suno_path} ({dur:.1f}s, {size // 1024}KB)")

    return suno_path


# ── Step 2: Demucs Vocal Extraction ──

def run_demucs_step(suno_path: Path, output_dir: Path, video_id: str) -> Path:
    """Extract vocals from Suno track using Demucs."""
    print(f"\nStep 2: Demucs vocal extraction...")
    print(f"  Input: {suno_path}")

    demucs_output = output_dir / "demucs"
    if demucs_output.exists():
        shutil.rmtree(demucs_output)

    cmd = [
        sys.executable, "-m", "demucs",
        "--two-stems=vocals",
        "-o", str(demucs_output),
        str(suno_path),
    ]

    print(f"  Running demucs...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"Demucs failed: {result.stderr[:300]}")

    # Find extracted vocals
    vocals_path = None
    for p in demucs_output.rglob("vocals.*"):
        vocals_path = p
        break

    if not vocals_path or not vocals_path.exists():
        raise RuntimeError("Demucs output not found")

    # Copy to output dir
    vocals_dest = output_dir / f"{video_id}-vocals-only.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(vocals_path),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(vocals_dest),
    ], capture_output=True, timeout=60)

    dur = get_duration(vocals_dest)
    print(f"  Vocals extracted: {vocals_dest} ({dur:.1f}s)")

    # Clean up demucs temp
    shutil.rmtree(demucs_output, ignore_errors=True)

    return vocals_dest


# ── Step 3: BGM + Vocals Mix ──

def run_mix_step(vocals_path: Path, config: dict, output_dir: Path) -> Path:
    """Mix extracted vocals over fixed BGM."""
    print(f"\nStep 3: BGM + Vocals mix...")

    bgm_config = config.get("bgm", {})
    bgm_file = PROJECT_ROOT / bgm_config.get("file", "")
    if not bgm_file.exists():
        raise RuntimeError(f"BGM not found: {bgm_file}")

    bgm_volume = bgm_config.get("volume", 0.35)
    fade_out = bgm_config.get("fade_out_s", 3)

    vocals_dur = get_duration(vocals_path)
    needed_dur = vocals_dur + fade_out

    mixed_path = output_dir / f"{config['video_id']}-final.mp3"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(vocals_path),     # input 0: vocals
        "-i", str(bgm_file),        # input 1: BGM
        "-filter_complex",
        (
            f"[1:a]atrim=start=0:end={needed_dur},asetpts=PTS-STARTPTS,"
            f"volume={bgm_volume},"
            f"afade=t=out:st={needed_dur - fade_out}:d={fade_out}[bgm];"
            f"[0:a]volume=1.0[vocals];"
            f"[vocals][bgm]amix=inputs=2:duration=longest:dropout_transition=3[aout]"
        ),
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(mixed_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"Mix failed: {result.stderr[:300]}")

    dur = get_duration(mixed_path)
    print(f"  Final mix: {mixed_path} ({dur:.1f}s)")
    print(f"  BGM volume: {bgm_volume}, Vocals volume: 1.0")

    return mixed_path


# ── Main Pipeline ──

def main():
    parser = argparse.ArgumentParser(description="Suno → Demucs → BGM 方言说唱管线")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--step", type=str, default="all",
                        choices=["all", "suno-only", "demucs-only", "mix-only"],
                        help="Which step to run")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
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
    output_dir = Path(args.output_dir) / video_id
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'=' * 60}")
    print(f"方言说唱管线 — {video_id}")
    print(f"{'=' * 60}")

    suno_path = output_dir / f"{video_id}-suno-full.mp3"
    vocals_path = output_dir / f"{video_id}-vocals-only.mp3"
    final_path = output_dir / f"{video_id}-final.mp3"

    if args.step == "all":
        suno_path = run_suno_step(config, output_dir)
        vocals_path = run_demucs_step(suno_path, output_dir, video_id)
        final_path = run_mix_step(vocals_path, config, output_dir)

    elif args.step == "suno-only":
        suno_path = run_suno_step(config, output_dir)

    elif args.step == "demucs-only":
        if not suno_path.exists():
            print(f"ERROR: Suno output not found: {suno_path}")
            print("Run --step suno-only first")
            sys.exit(1)
        vocals_path = run_demucs_step(suno_path, output_dir, video_id)

    elif args.step == "mix-only":
        if not vocals_path.exists():
            print(f"ERROR: Vocals not found: {vocals_path}")
            print("Run --step demucs-only first")
            sys.exit(1)
        final_path = run_mix_step(vocals_path, config, output_dir)

    # Save pipeline log
    log_path = output_dir / f"pipeline-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "step": args.step,
            "files": {
                "suno": str(suno_path) if suno_path.exists() else None,
                "vocals": str(vocals_path) if vocals_path.exists() else None,
                "final": str(final_path) if final_path.exists() else None,
            },
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Done!")
    if final_path.exists():
        print(f"  Final: {final_path} ({get_duration(final_path):.1f}s)")
    print(f"\nNext: 打开剪映 → 导入final.mp3 → 加画面+花字字幕")


if __name__ == "__main__":
    main()
