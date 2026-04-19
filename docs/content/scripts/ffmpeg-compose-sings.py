#!/usr/bin/env python3
"""
FFmpeg Video Composer for Sings Workflow
Takes full song audio + Runway video clips, distributes clips evenly, composites final video.

Usage:
  python3 ffmpeg-compose-sings.py --config config/sings01-ai-hack-40yi.json
  python3 ffmpeg-compose-sings.py --config config/sings01-ai-hack-40yi.json --dry-run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output"
ASSETS_DIR = PROJECT_ROOT / "docs" / "content" / "assets"
REFERENCE_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "references"


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

    font_size = cfg.get("font_size", 48)
    font_color = cfg.get("color", cfg.get("font_color", "#ffd700"))
    bg_color = cfg.get("bg_color", "#0a0a1a")

    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (720, 1280), bg_color)
    draw = ImageDraw.Draw(img)

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
    return result.returncode == 0


def find_video_clip(seg_id: str, video_dir: Path) -> Path | None:
    for pattern in [f"{seg_id}.mp4", f"{seg_id}_v1.mp4"]:
        p = video_dir / pattern
        if p.exists():
            return p
    for p in sorted(video_dir.glob(f"{seg_id}*.mp4")):
        return p
    return None


def find_reference_image(seg: dict) -> Path | None:
    ref_file = seg.get("reference_file", "")
    if ref_file:
        p = REFERENCE_DIR / ref_file
        if p.exists():
            return p
    return None


def image_to_video(image_path: Path, output_path: Path, duration: float, motion: str = "zoom_in") -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(duration * 24)

    motion_filters = {
        "zoom_in": f"zoompan=z='min(zoom+0.0008,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=24",
        "zoom_out": f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.0008,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=24",
        "pan_left": f"zoompan=z='1.08':x='if(eq(on,1),0,max(x-1.5,0))':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=24",
        "pan_right": f"zoompan=z='1.08':x='if(eq(on,1),iw-iw/zoom,max(x+1.5,iw-iw/zoom))':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=24",
        "gentle_sway": f"zoompan=z='1.06+0.02*sin(on/80)':x='iw/2-(iw/zoom/2)+5*sin(on/60)':y='ih/2-(ih/zoom/2)':d={frames}:s=720x1280:fps=24",
    }
    vf = motion_filters.get(motion, motion_filters["zoom_in"])
    fade_duration = min(0.5, duration * 0.1)
    vf += f",fade=t=in:st=0:d={fade_duration},fade=t=out:st={duration - fade_duration}:d={fade_duration}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        "-t", str(duration),
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    FFmpeg error: {result.stderr[-300:]}")
    return result.returncode == 0


MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "gentle_sway"]


def extend_clip(input_path: Path, output_path: Path, target_duration: float) -> bool:
    clip_duration = get_duration(input_path)
    if clip_duration <= 0:
        return False

    if target_duration <= clip_duration * 1.05:
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    loops_needed = int(target_duration / clip_duration) + 1
    temp_dir = output_path.parent / "loop_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    parts: list[Path] = []

    for i in range(loops_needed):
        part_path = temp_dir / f"{input_path.stem}_loop_{i}.mp4"
        if i % 2 == 0:
            loop_cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path),
            ]
        else:
            loop_cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", "reverse",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path),
            ]
        subprocess.run(loop_cmd, capture_output=True, text=True)
        parts.append(part_path)

    concat_file = temp_dir / f"{input_path.stem}_loops.txt"
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    for p in parts:
        p.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="FFmpeg Sings Video Composer")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audio", type=str, default=None, help="Override audio file path")
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
    video_dir = DEFAULT_OUTPUT_DIR / video_id

    compositing = config.get("compositing", {})
    ai_label = config.get("ai_labeling", {})

    # Find the audio file
    audio_path = None
    if args.audio:
        audio_path = Path(args.audio)
    else:
        cover_dir = ASSETS_DIR / "cover"
        candidates = sorted(cover_dir.glob("sings01_duet_v*.mp3"), reverse=True)
        if candidates:
            audio_path = candidates[0]
    if not audio_path or not audio_path.exists():
        print("ERROR: No audio file found")
        print("  Use --audio /path/to/song.mp3")
        sys.exit(1)

    song_duration = get_duration(audio_path)
    print(f"Sings Video Composer — {video_id}")
    print("=" * 50)
    print(f"Audio: {audio_path.name} ({song_duration:.1f}s)")
    print()

    # Collect video clips (Runway video > Ken Burns from image)
    segments = config.get("segments", [])
    clips: list[dict] = []

    for seg in segments:
        seg_id = seg["id"]
        clip_path = find_video_clip(seg_id, video_dir)
        is_text_card = seg.get("shot_type") == "text_card"
        ref_image = find_reference_image(seg)

        if is_text_card:
            clips.append({"id": seg_id, "type": "text_card", "seg": seg})
        elif clip_path:
            clips.append({"id": seg_id, "type": "video", "path": clip_path, "seg": seg})
        elif ref_image:
            motion_idx = len(clips) % len(MOTIONS)
            clips.append({
                "id": seg_id,
                "type": "image",
                "image_path": ref_image,
                "motion": MOTIONS[motion_idx],
                "seg": seg,
            })
        else:
            print(f"  {seg_id}: SKIP — no video or image found")

    if not clips:
        print("ERROR: No clips found")
        print(f"  Expected videos in: {video_dir}")
        print(f"  Expected images in: {REFERENCE_DIR}")
        sys.exit(1)

    print(f"Clips: {len(clips)}")
    for c in clips:
        if c["type"] == "video":
            dur = get_duration(c["path"])
            print(f"  {c['id']}: [Runway] {c['path'].name} ({dur:.1f}s)")
        elif c["type"] == "image":
            print(f"  {c['id']}: [KenBurns:{c['motion']}] {c['image_path'].name}")
        else:
            print(f"  {c['id']}: text_card")
    print()

    # Calculate per-clip duration
    per_clip_duration = song_duration / len(clips)
    print(f"Per-clip target: {per_clip_duration:.1f}s")
    total_planned = per_clip_duration * len(clips)
    print(f"Total planned: {total_planned:.1f}s (song: {song_duration:.1f}s)")
    print()

    if args.dry_run:
        print("DRY RUN — no compositing will happen.")
        return

    # Step 1: Prepare each clip to target duration
    print("Step 1: Preparing clips...")
    temp_dir = video_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    prepared: list[Path] = []
    for i, clip in enumerate(clips):
        output_path = temp_dir / f"{clip['id']}_extended.mp4"

        if clip["type"] == "text_card":
            ok = generate_text_card(clip["seg"], output_path, per_clip_duration)
        elif clip["type"] == "image":
            ok = image_to_video(clip["image_path"], output_path, per_clip_duration, clip["motion"])
        else:
            ok = extend_clip(clip["path"], output_path, per_clip_duration)

        if ok:
            actual = get_duration(output_path)
            print(f"  {clip['id']}: {per_clip_duration:.1f}s -> {actual:.1f}s")
            prepared.append(output_path)
        else:
            print(f"  {clip['id']}: FAILED")

    print()

    # Step 2: Concatenate all clips
    print("Step 2: Concatenating video clips...")
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
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Concat error: {result.stderr[-500:]}")
        sys.exit(1)
    print(f"  Video: {get_duration(concat_video):.1f}s")

    # Step 3: Merge video + audio
    print("\nStep 3: Merging video + audio...")
    final_output = DEFAULT_OUTPUT_DIR / f"{video_id}-sings.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_video),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Merge error: {result.stderr[-500:]}")
        sys.exit(1)

    final_dur = get_duration(final_output)
    print(f"\n  Output: {final_output}")
    print(f"  Duration: {final_dur:.1f}s")
    print(f"  Resolution: 720x1280 (9:16)")
    print(f"  Note: No filters applied. Subtitles and transitions in CapCut.")


if __name__ == "__main__":
    main()
