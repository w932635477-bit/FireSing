#!/usr/bin/env python3
"""
FFmpeg Video Composer (config-driven)
Reads video config JSON, matches voiceover + video segments, composites with de-AI post-processing.

Usage:
  python3 ffmpeg-compose-day1.py --config config/day1-medvi-story.json
  python3 ffmpeg-compose-day1.py --config config/day1-medvi-story.json --dry-run
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output"
ASSETS_DIR = PROJECT_ROOT / "docs" / "content" / "assets"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def generate_text_card(seg: dict, output_path: Path, duration: float) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cfg = seg.get("text_card_config", {})
    lines = cfg.get("lines", [])
    if not lines:
        text = seg.get("subtitle_text", "")
        lines = [text]

    font_size = cfg.get("font_size", 52)
    font_color = cfg.get("font_color", "#c9a96e")
    bg_color = cfg.get("bg_color", "#000000")

    # Generate text card image with PIL
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (720, 1280), bg_color)
    draw = ImageDraw.Draw(img)

    # Try CJK fonts on macOS
    font_paths = [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    font = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    line_spacing = font_size * 1.8
    total_height = len(lines) * line_spacing
    start_y = (1280 - total_height) / 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (720 - tw) / 2
        y = start_y + i * line_spacing
        draw.text((x, y), line, fill=font_color, font=font)

    card_img = output_path.parent / f"{seg['id']}_card.png"
    img.save(str(card_img))

    # Convert image to video with gentle zoom
    frames = int(duration * 24)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(card_img),
        "-vf", f"zoompan=z='min(zoom+0.001,1.08)':d={frames}:s=720x1280:fps=24,fade=t=in:st=0:d=0.5",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        "-t", str(duration),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    card_img.unlink(missing_ok=True)
    if result.returncode != 0:
        print(f"  text_card error: {result.stderr[-300:]}")
        return False
    return True


def load_segments(config_path: Path) -> list[dict]:
    """Load segments from config with resolved file paths."""
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    video_dir = DEFAULT_OUTPUT_DIR / video_id
    voiceover_dir = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / video_id

    post = config.get("post_production", {})
    compositing = config.get("compositing", {})

    segments = []
    for seg in config["segments"]:
        seg_id = seg["id"]

        # Find voiceover audio
        audio_path = voiceover_dir / f"{seg_id}.mp3"
        if not audio_path.exists():
            audio_path = voiceover_dir / f"{seg_id}.mp3"

        # Find video clip
        video_path = None
        for ext in [".mp4"]:
            for p in video_dir.glob(f"{seg_id}*{ext}"):
                video_path = p
                break
            if video_path:
                break

        segments.append({
            "id": seg_id,
            "audio_path": audio_path,
            "video_path": video_path,
            "subtitle_text": seg.get("subtitle_text", ""),
            "voiceover_text": seg.get("voiceover_text", ""),
            "duration_sec": seg.get("duration_sec", 5),
            "emotion_arc": seg.get("emotion_arc", ""),
            "shot_type": seg.get("shot_type", "medium"),
            "text_card_config": seg.get("text_card_config", {}),
            "overlay_image": seg.get("overlay_image", ""),
        })

    return segments, video_id, post, compositing


def prepare_segment(seg: dict, temp_dir: Path, output_path: Path) -> None:
    """Prepare a video segment matching audio duration."""
    if not seg["audio_path"].exists():
        print(f"  {seg['id']}: SKIP — no audio ({seg['audio_path']})")
        return False

    target_duration = get_duration(seg["audio_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Route 1: text_card → generate via FFmpeg drawtext
    shot_type = seg.get("shot_type", "medium")
    if shot_type == "text_card":
        print(f"  {seg['id']}: generating text_card ({target_duration:.1f}s)")
        return generate_text_card(seg, output_path, target_duration)

    # Route 2: normal video from Runway, optionally with photo overlay
    if not seg["video_path"] or not seg["video_path"].exists():
        print(f"  {seg['id']}: SKIP — no video ({seg['video_path']})")
        return False

    video_duration = get_duration(seg["video_path"])

    if target_duration <= video_duration * 1.05:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(seg["video_path"]),
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    elif target_duration <= video_duration * 2.0:
        speed_factor = target_duration / video_duration
        cmd = [
            "ffmpeg", "-y",
            "-i", str(seg["video_path"]),
            "-filter:v", f"setpts={speed_factor}*PTS",
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    else:
        # Loop video to fill duration
        clip_duration = video_duration
        loops_needed = int(target_duration / clip_duration) + 1
        parts = []
        for i in range(loops_needed):
            part_path = temp_dir / f"{seg['id']}_loop_{i}.mp4"
            if i % 2 == 0:
                loop_cmd = ["ffmpeg", "-y", "-i", str(seg["video_path"]),
                            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                            "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path)]
            else:
                loop_cmd = ["ffmpeg", "-y", "-i", str(seg["video_path"]),
                            "-vf", "reverse",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                            "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path)]
            subprocess.run(loop_cmd, check=True, capture_output=True)
            parts.append(part_path)

        concat_file = temp_dir / f"{seg['id']}_loops.txt"
        with open(concat_file, "w") as f:
            for p in parts:
                f.write(f"file '{p.resolve()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        for p in parts:
            p.unlink(missing_ok=True)

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FFmpeg Video Composer (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without compositing")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = DEFAULT_CONFIG_DIR / config_path
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    segments, video_id, post, compositing = load_segments(config_path)
    output_dir = DEFAULT_OUTPUT_DIR
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"FFmpeg Video Composer — {video_id}")
    print("=" * 50)
    print(f"Segments: {len(segments)}")
    print()

    # Check readiness
    ready_segs = []
    for seg in segments:
        audio_ok = seg["audio_path"].exists()
        is_text_card = seg.get("shot_type") == "text_card"
        video_ok = seg["video_path"] is not None and seg["video_path"].exists()
        if is_text_card:
            video_ok = True
        status = "text_card" if is_text_card else ("OK" if video_ok else "MISSING")
        print(f"  {seg['id']} [{seg['emotion_arc']}] ({seg.get('shot_type', '')}): audio={'OK' if audio_ok else 'MISSING'}, video={status}")
        if audio_ok and video_ok:
            ready_segs.append(seg)
    print()

    if not ready_segs:
        print("ERROR: No segments have both audio and video ready")
        print("Run Fish Audio TTS and Runway Gen-4 first")
        sys.exit(1)

    if len(ready_segs) < len(segments):
        print(f"WARNING: Only {len(ready_segs)}/{len(segments)} segments ready")

    if args.dry_run:
        print("DRY RUN — no compositing will happen.")
        total = sum(get_duration(s["audio_path"]) for s in ready_segs)
        print(f"Estimated total duration: {total:.1f}s")
        return

    # Step 1: Prepare segments
    print("Step 1: Preparing video segments...")
    prepared = []
    total_duration = 0.0

    for seg in ready_segs:
        output_path = temp_dir / f"{seg['id']}_trimmed.mp4"
        duration = get_duration(seg["audio_path"])
        total_duration += duration
        print(f"  {seg['id']}: audio={duration:.1f}s", end="")
        ok = prepare_segment(seg, temp_dir, output_path)
        if ok:
            actual = get_duration(output_path)
            print(f" -> video={actual:.1f}s")
            prepared.append(output_path)
        else:
            total_duration -= duration

    print(f"\nTotal audio: {total_duration:.1f}s")

    # Step 2: Concat video
    print("\nStep 2: Concatenating video segments...")
    concat_file = temp_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for vp in prepared:
            f.write(f"file '{vp.resolve()}'\n")

    concat_video = temp_dir / "concat_raw.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(concat_video),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Video: {get_duration(concat_video):.1f}s")

    # Step 3: Concat audio
    print("\nStep 3: Concatenating audio segments...")
    concat_audio_file = temp_dir / "audio_concat.txt"
    with open(concat_audio_file, "w") as f:
        for seg in ready_segs:
            f.write(f"file '{seg['audio_path'].resolve()}'\n")

    concat_audio = temp_dir / "narration.mp3"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_audio_file),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(concat_audio),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Narration: {get_duration(concat_audio):.1f}s")

    # Step 4: Merge video + audio (no filters, no overlays)
    print("\nStep 4: Merging video + audio...")

    final_output = output_dir / f"{video_id}-concat.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_video),
        "-i", str(concat_audio),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-500:]}")
        sys.exit(1)

    final_dur = get_duration(final_output)
    print(f"\n  Output: {final_output}")
    print(f"  Duration: {final_dur:.1f}s")
    print(f"  Resolution: 720x1280 (9:16)")
    print(f"  Note: No filters applied. All visual processing done in CapCut.")


if __name__ == "__main__":
    main()
