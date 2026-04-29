#!/usr/bin/env python3
"""
Rough-cut composer for unemploy-01-fired47.
Creates a preview video by combining UI screenshots + atmosphere videos + voiceover.

This is a rough cut for preview. Final editing is done in JianYing.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "output" / "unemploy-01-fired47"
REF_DIR = BASE / "assets" / "references" / "unemploy-01-fired47"
VO_DIR = BASE / "assets" / "voiceover" / "unemploy-01-fired47"

TEMP = OUT_DIR / "temp_clips"
TEMP.mkdir(exist_ok=True)

FINAL_OUTPUT = OUT_DIR / "unemploy-01-fired47-rough-cut.mp4"


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:4])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:300]}")
        sys.exit(1)


def image_to_video(image: Path, duration: float, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(image),
        "-c:v", "libx264", "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=1080:1920",
        "-r", "24",
        str(output)
    ], f"img→vid {output.name}")


def concat_video_audio(video: Path, audio: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y",
        "-i", str(video), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output)
    ], f"merge {output.name}")


def main() -> None:
    # Segment durations from voiceover
    seg_durations = {
        "S01": 7.56, "S02": 11.16, "S03": 27.04,
        "S04": 20.96, "S05": 11.60, "S06": 3.24,
    }

    # Visual mapping per segment
    # S01: Boss search screenshot (SS01) - full duration
    # S02: atmosphere video S02-01
    # S03: mix of SS03 screenshot + atmosphere S03-01 + SS04 screenshot
    #      split: first 10s atmosphere, then 10s screenshot, rest atmosphere
    # S04: atmosphere S04-01
    # S05: atmosphere S04-01 (reuse, extend)
    # S06: SS06 screenshot

    clips: list[Path] = []

    # S01: Boss search screenshot
    s01_clip = TEMP / "s01.mp4"
    image_to_video(OUT_DIR / "SS01-boss-search.png", seg_durations["S01"], s01_clip)
    s01_merged = TEMP / "s01_merged.mp4"
    concat_video_audio(s01_clip, VO_DIR / "S01.mp3", s01_merged)
    clips.append(s01_merged)

    # S02: atmosphere video + voiceover
    s02_merged = TEMP / "s02_merged.mp4"
    concat_video_audio(OUT_DIR / "S02-01.mp4", VO_DIR / "S02.mp3", s02_merged)
    clips.append(s02_merged)

    # S03: mixed visuals (screenshot + atmosphere + screenshot)
    # Split S03 into 3 sub-clips to show different visuals
    s03_dur = seg_durations["S03"]
    s03_part1_dur = 8.0   # atmosphere video
    s03_part2_dur = 9.0   # resume stats screenshot
    s03_part3_dur = s03_dur - s03_part1_dur - s03_part2_dur  # remaining: wechat reject + atmosphere

    # Part 1: atmosphere video (looped to fill duration)
    s03_p1 = TEMP / "s03_p1.mp4"
    run([
        "ffmpeg", "-y", "-stream_loop", "-1",
        "-i", str(OUT_DIR / "S03-01.mp4"),
        "-c:v", "libx264", "-t", f"{s03_part1_dur:.3f}",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(s03_p1)
    ], "S03-p1")

    # Part 2: resume stats screenshot
    s03_p2 = TEMP / "s03_p2.mp4"
    image_to_video(OUT_DIR / "SS03-resume-stats.png", s03_part2_dur, s03_p2)

    # Part 3: wechat reject screenshot
    s03_p3 = TEMP / "s03_p3.mp4"
    image_to_video(OUT_DIR / "SS04-wechat-reject.png", s03_part3_dur, s03_p3)

    # Concat S03 visual parts
    s03_visual_list = TEMP / "s03_visuals.txt"
    s03_visual_list.write_text(
        f"file '{s03_p1}'\nfile '{s03_p2}'\nfile '{s03_p3}'\n"
    )
    s03_visual = TEMP / "s03_visual.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(s03_visual_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        str(s03_visual)
    ], "S03-concat")

    s03_merged = TEMP / "s03_merged.mp4"
    concat_video_audio(s03_visual, VO_DIR / "S03.mp3", s03_merged)
    clips.append(s03_merged)

    # S04: atmosphere video
    s04_merged = TEMP / "s04_merged.mp4"
    concat_video_audio(OUT_DIR / "S04-01.mp4", VO_DIR / "S04.mp3", s04_merged)
    clips.append(s04_merged)

    # S05: atmosphere video (looped, reuse S04-01)
    s05_clip = TEMP / "s05.mp4"
    run([
        "ffmpeg", "-y", "-stream_loop", "-1",
        "-i", str(OUT_DIR / "S04-01.mp4"),
        "-c:v", "libx264", "-t", f"{seg_durations['S05']:.3f}",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(s05_clip)
    ], "S05-loop")
    s05_merged = TEMP / "s05_merged.mp4"
    concat_video_audio(s05_clip, VO_DIR / "S05.mp3", s05_merged)
    clips.append(s05_merged)

    # S06: douyin comment screenshot
    s06_clip = TEMP / "s06.mp4"
    image_to_video(OUT_DIR / "SS06-douyin-comment.png", seg_durations["S06"], s06_clip)
    s06_merged = TEMP / "s06_merged.mp4"
    concat_video_audio(s06_clip, VO_DIR / "S06.mp3", s06_merged)
    clips.append(s06_merged)

    # Final concat
    concat_list = TEMP / "final_list.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clips))
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(FINAL_OUTPUT)
    ], "FINAL")

    # Report
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(FINAL_OUTPUT)],
        capture_output=True, text=True
    ).stdout.strip()
    size = FINAL_OUTPUT.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {FINAL_OUTPUT}")
    print(f"  Duration: {float(dur):.1f}s")
    print(f"  Size: {size}MB")


if __name__ == "__main__":
    main()
