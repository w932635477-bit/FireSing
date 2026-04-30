#!/usr/bin/env python3
"""
FFmpeg Video Composer for Medvi (unemploy-celebrity) Workflow.
Combines Kling atmosphere videos with Gemini TTS voiceover per segment.

Usage:
  python3 ffmpeg-compose-medvi.py --config config/unemploy-celebrity-02.json
  python3 ffmpeg-compose-medvi.py --config config/unemploy-celebrity-02.json --dry-run
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
REFERENCE_DIR = ASSETS_DIR / "references"
VOICEOVER_DIR = ASSETS_DIR / "voiceover"


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def run_ffmpeg(cmd: list[str], label: str = "") -> bool:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [{label}] ERROR: {r.stderr[-300:]}")
    return r.returncode == 0


def extend_video_to_duration(input_path: Path, output_path: Path, target_duration: float) -> bool:
    clip_duration = get_duration(input_path)
    if clip_duration <= 0:
        return False

    if target_duration <= clip_duration * 1.05:
        return run_ffmpeg([
            "ffmpeg", "-y", "-i", str(input_path),
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ], f"trim {input_path.name}")

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

    ok = run_ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-t", str(target_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(output_path),
    ], f"loop+trim {input_path.name}")

    for p in parts:
        p.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="FFmpeg Medvi Video Composer")
    parser.add_argument("--config", type=str, required=True)
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
    video_dir = DEFAULT_OUTPUT_DIR / video_id
    vo_dir = VOICEOVER_DIR / video_id

    print(f"Medvi Video Composer — {video_id}")
    print("=" * 50)

    segments = config.get("segments", [])
    print(f"Segments: {len(segments)}")

    # Verify materials exist
    clips: list[dict] = []
    for seg in segments:
        seg_id = seg["id"]
        video_path = video_dir / f"{seg_id}.mp4"
        audio_path = vo_dir / f"{seg_id}.mp3"

        if not video_path.exists():
            print(f"  {seg_id}: MISSING video {video_path}")
            continue
        if not audio_path.exists():
            print(f"  {seg_id}: MISSING audio {audio_path}")
            continue

        audio_dur = get_duration(audio_path)
        video_dur = get_duration(video_path)
        clips.append({
            "id": seg_id,
            "video": video_path,
            "audio": audio_path,
            "audio_duration": audio_dur,
            "video_duration": video_dur,
            "seg": seg,
        })
        print(f"  {seg_id}: video={video_dur:.1f}s audio={audio_dur:.1f}s")

    if not clips:
        print("ERROR: No clips with complete materials found")
        sys.exit(1)

    total_audio = sum(c["audio_duration"] for c in clips)
    print(f"\nTotal audio: {total_audio:.1f}s")

    if args.dry_run:
        print("\nDRY RUN — no compositing will happen.")
        return

    temp_dir = video_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Extend each video clip to match its audio duration, then merge
    print("\nStep 1: Preparing segment clips...")
    prepared: list[Path] = []
    for clip in clips:
        seg_id = clip["id"]
        target_dur = clip["audio_duration"]
        extended = temp_dir / f"{seg_id}_extended.mp4"

        ok = extend_video_to_duration(clip["video"], extended, target_dur)
        if not ok:
            print(f"  {seg_id}: FAILED to extend video")
            continue

        # Merge extended video + audio
        merged = temp_dir / f"{seg_id}_merged.mp4"
        ok = run_ffmpeg([
            "ffmpeg", "-y",
            "-i", str(extended), "-i", str(clip["audio"]),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(merged),
        ], f"merge {seg_id}")

        if ok:
            actual = get_duration(merged)
            print(f"  {seg_id}: {target_dur:.1f}s -> {actual:.1f}s OK")
            prepared.append(merged)
        else:
            print(f"  {seg_id}: FAILED to merge")

    if not prepared:
        print("ERROR: No clips prepared")
        sys.exit(1)

    # Step 2: Concatenate all segments
    print("\nStep 2: Concatenating all segments...")
    concat_file = temp_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for p in prepared:
            f.write(f"file '{p.resolve()}'\n")

    final_output = DEFAULT_OUTPUT_DIR / f"{video_id}-medvi.mp4"
    ok = run_ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(final_output),
    ], "FINAL CONCAT")

    if ok:
        final_dur = get_duration(final_output)
        size_mb = final_output.stat().st_size // (1024 * 1024)
        print(f"\nDONE: {final_output}")
        print(f"  Duration: {final_dur:.1f}s")
        print(f"  Size: {size_mb}MB")
        print(f"  Note: Subtitles and transitions in 剪映.")
    else:
        print("\nFAILED: Final concatenation error")
        sys.exit(1)


if __name__ == "__main__":
    main()
