#!/usr/bin/env python3
"""
FFmpeg compose script for sings-dialect-rap.
Mixes BGM (Primetime-Sexcrime) + 东北话 voiceover + visuals into final video.

Usage:
  source docs/content/.env
  python3 ffmpeg-compose-dialect-rap.py --config config/sings-dialect-rap-ep01.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "output"
BGM_FILE = PROJECT_ROOT / "docs" / "content" / "assets" / "bgm" / "精彩01_副本.mp3"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def main():
    parser = argparse.ArgumentParser(description="Compose dialect-rap video")
    parser.add_argument("--config", type=str, required=True)
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

    bgm_config = config.get("bgm", {})
    bgm_file = PROJECT_ROOT / bgm_config.get("file", str(BGM_FILE))
    if not bgm_file.exists():
        print(f"ERROR: BGM not found: {bgm_file}")
        sys.exit(1)

    voice_config = config.get("voice", {})
    voice_dir = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / video_id
    voice_file = voice_dir / f"{video_id}-voice.mp3"

    if not voice_file.exists():
        print(f"ERROR: Voice file not found: {voice_file}")
        print(f"Run: python3 doubao-dialect-tts.py --config {args.config}")
        sys.exit(1)

    voice_dur = get_duration(voice_file)
    bgm_dur = get_duration(bgm_file)

    # Use enough BGM to cover the voice + 3s fade
    needed_dur = voice_dur + 3.0
    bgm_start = bgm_config.get("start_sec", 0)
    bgm_end = min(bgm_config.get("end_sec", bgm_dur), bgm_start + needed_dur)

    bgm_volume = bgm_config.get("volume", 0.35)
    voice_volume = voice_config.get("volume", 1.0) if voice_config else 1.0
    fade_out = bgm_config.get("fade_out_s", 3)

    print(f"Composing: {video_id}")
    print(f"  BGM: {bgm_file.name} ({bgm_start}s-{bgm_end}s, volume={bgm_volume})")
    print(f"  Voice: {voice_file.name} ({voice_dur:.1f}s, volume={voice_volume})")
    print(f"  Target duration: ~{voice_dur:.0f}s")
    print()

    # Step 1: Mix audio (BGM + voice)
    mixed_audio = output_dir / f"{video_id}-mixed.mp3"
    audio_cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_file),           # input 0: voice
        "-i", str(bgm_file),             # input 1: BGM
        "-filter_complex",
        (
            f"[1:a]atrim=start={bgm_start}:end={bgm_end},asetpts=PTS-STARTPTS,"
            f"volume={bgm_volume},afade=t=out:st={needed_dur - fade_out}:d={fade_out}[bgm];"
            f"[0:a]volume={voice_volume}[voice];"
            f"[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=3[aout]"
        ),
        "-map", "[aout]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(mixed_audio),
    ]

    print("Step 1: Mixing audio...")
    result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:500]}")
        sys.exit(1)
    print(f"  Mixed audio: {mixed_audio} ({get_duration(mixed_audio):.1f}s)")

    # Step 2: Create visual (solid color placeholder for 剪映 post-production)
    final_dur = get_duration(mixed_audio)
    visual = output_dir / f"{video_id}-visual.mp4"

    # Use a black background with text overlay as placeholder
    # User will replace with Kling videos or stage footage in 剪映
    visual_cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={final_dur}:r=24",
        "-vf", (
            f"drawtext=text='{config.get('episode_title', video_id)}':"
            f"fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,0,3)',"
            f"drawtext=text='剪映替换画面':fontsize=32:fontcolor=gray:"
            f"x=(w-text_w)/2:y=(h-text_h)/2+80:enable='between(t,3,{final_dur})'"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        str(visual),
    ]

    print("Step 2: Creating visual placeholder...")
    result = subprocess.run(visual_cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"WARNING: Visual creation failed: {result.stderr[:300]}")
        print("  You can manually create visuals in 剪映")
        visual = None

    # Step 3: Combine visual + mixed audio
    if visual and visual.exists():
        final_video = output_dir / f"{video_id}-final.mp4"
        combine_cmd = [
            "ffmpeg", "-y",
            "-i", str(visual),
            "-i", str(mixed_audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_video),
        ]

        print("Step 3: Combining video + audio...")
        result = subprocess.run(combine_cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"WARNING: Combine failed: {result.stderr[:300]}")
        else:
            print(f"  Final video: {final_video} ({get_duration(final_video):.1f}s)")
    else:
        final_video = None

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Output files:")
    print(f"  Mixed audio: {mixed_audio}")
    if final_video and final_video.exists():
        print(f"  Final video: {final_video}")
    print(f"\nNext steps:")
    print(f"  1. 打开剪映，导入 {final_video or mixed_audio}")
    print(f"  2. 用Kling生成的视频替换黑色占位画面")
    print(f"  3. 添加花字字幕（参考SRT: {voice_dir / f'{video_id}-subtitles.srt'}）")
    print(f"  4. 添加音效（笑声、鼓点加重等）")
    print(f"  5. 导出发布到抖音")


if __name__ == "__main__":
    main()
