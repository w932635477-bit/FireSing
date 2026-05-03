#!/usr/bin/env python3
"""
Rough-cut composer for unemploy-story-01-zhangwei.
Combines UI screenshots + Unsplash atmosphere photos + text cards + Gemini TTS voiceover.

Output is a rough cut for preview. Final editing in JianYing.
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SS_DIR = BASE / "assets" / "screenshots" / "unemploy-story-01-zhangwei"
AT_DIR = BASE / "assets" / "unsplash" / "unemploy-story-01-zhangwei"
TC_DIR = BASE / "assets" / "textcards" / "unemploy-story-01-zhangwei"
VO_DIR = BASE / "assets" / "voiceover" / "unemploy-story-01-zhangwei"
OUT_DIR = BASE / "output" / "unemploy-story-01-zhangwei"

TEMP = OUT_DIR / "temp_clips"
TEMP.mkdir(parents=True, exist_ok=True)

FINAL_OUTPUT = OUT_DIR / "unemploy-story-01-zhangwei-rough-cut.mp4"

# Text card duration
TC_DUR = 4.0


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:4])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:300]}")
        sys.exit(1)


def image_to_video(image: Path, duration: float, output: Path, zoom: bool = False) -> None:
    vf = "scale=1080:1920"
    if zoom:
        frames = int(duration * 24)
        vf = f"scale=1152:2048,crop=1080:1920:36:64,zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920"
    run([
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(image),
        "-c:v", "libx264", "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p",
        "-vf", vf,
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


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def main() -> None:
    # Get actual voiceover durations
    s01_dur = get_duration(VO_DIR / "S01.mp3")
    s02_dur = get_duration(VO_DIR / "S02.mp3")
    s03_dur = get_duration(VO_DIR / "S03.mp3")
    s04_dur = get_duration(VO_DIR / "S04.mp3")
    s05_dur = get_duration(VO_DIR / "S05.mp3")

    print(f"Voiceover: S01={s01_dur:.1f}s S02={s02_dur:.1f}s "
          f"S03={s03_dur:.1f}s S04={s04_dur:.1f}s S05={s05_dur:.1f}s")
    print(f"Total VO: {s01_dur + s02_dur + s03_dur + s04_dur + s05_dur:.1f}s")

    clips: list[Path] = []

    # === S01 Hook: Boss search → Text card "12年经验=废纸" → Resume stats ===
    # Boss search first half, text card 4s, resume stats rest
    s01_visual_dur = s01_dur - TC_DUR  # leave room for text card
    s01_p1_dur = s01_visual_dur * 0.55
    s01_p2_dur = s01_visual_dur - s01_p1_dur

    s01_p1 = TEMP / "s01_p1.mp4"
    image_to_video(SS_DIR / "SS01-boss-search.png", s01_p1_dur, s01_p1)
    s01_p2 = TEMP / "s01_p2.mp4"
    image_to_video(SS_DIR / "SS02-resume-stats.png", s01_p2_dur, s01_p2, zoom=True)

    tc01 = TEMP / "tc01.mp4"
    # Re-encode text card to match resolution/fps
    run([
        "ffmpeg", "-y", "-i", str(TC_DIR / "TC01-waste-paper.mp4"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920",
        str(tc01)
    ], "TC01-resize")

    s01_list = TEMP / "s01_list.txt"
    s01_list.write_text(f"file '{s01_p1}'\nfile '{s01_p2}'\nfile '{tc01}'\n")
    s01_visual = TEMP / "s01_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(s01_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(s01_visual)], "S01-concat")

    s01_merged = TEMP / "s01_merged.mp4"
    concat_video_audio(s01_visual, VO_DIR / "S01.mp3", s01_merged)
    clips.append(s01_merged)

    # === S02 Turn: Warehouse → WeChat positive → Desk lamp ===
    s02_p1_dur = s02_dur * 0.3
    s02_p2_dur = s02_dur * 0.4
    s02_p3_dur = s02_dur - s02_p1_dur - s02_p2_dur

    s02_p1 = TEMP / "s02_p1.mp4"
    image_to_video(AT_DIR / "AT01-warehouse.jpg", s02_p1_dur, s02_p1, zoom=True)
    s02_p2 = TEMP / "s02_p2.mp4"
    image_to_video(SS_DIR / "SS03-wechat-positive.png", s02_p2_dur, s02_p2)
    s02_p3 = TEMP / "s02_p3.mp4"
    image_to_video(AT_DIR / "AT02-desk-lamp.jpg", s02_p3_dur, s02_p3, zoom=True)

    s02_list = TEMP / "s02_list.txt"
    s02_list.write_text(f"file '{s02_p1}'\nfile '{s02_p2}'\nfile '{s02_p3}'\n")
    s02_visual = TEMP / "s02_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(s02_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(s02_visual)], "S02-concat")

    s02_merged = TEMP / "s02_merged.mp4"
    concat_video_audio(s02_visual, VO_DIR / "S02.mp3", s02_merged)
    clips.append(s02_merged)

    # === S03 Montage: Fast cuts (2-3s each) → Rest beat (2s) → Laptop desk ===
    montage_total = s03_dur * 0.35
    rest_beat_dur = 2.0
    rest_dur = s03_dur - montage_total - rest_beat_dur

    # 4 fast cuts, 2-3s each
    cut_dur = min(montage_total / 4, 3.0)

    m1 = TEMP / "m1.mp4"
    image_to_video(SS_DIR / "SS04-dingtalk-leave.png", cut_dur, m1)
    m2 = TEMP / "m2.mp4"
    image_to_video(SS_DIR / "SS02-resume-stats.png", cut_dur, m2)
    m3 = TEMP / "m3.mp4"
    image_to_video(SS_DIR / "SS05-wechat-reject.png", cut_dur, m3)
    m4 = TEMP / "m4.mp4"
    image_to_video(AT_DIR / "AT03-empty-office.jpg", cut_dur, m4, zoom=True)

    # Rest beat: fixed shot, 2s, no zoom
    rb = TEMP / "rest_beat.mp4"
    image_to_video(AT_DIR / "AT03-empty-office.jpg", rest_beat_dur, rb)

    # Remaining: laptop desk with zoom
    m5 = TEMP / "m5.mp4"
    image_to_video(AT_DIR / "AT05-laptop-desk.jpg", rest_dur, m5, zoom=True)

    s03_list = TEMP / "s03_list.txt"
    s03_list.write_text(
        f"file '{m1}'\nfile '{m2}'\nfile '{m3}'\nfile '{m4}'\n"
        f"file '{rb}'\nfile '{m5}'\n"
    )
    s03_visual = TEMP / "s03_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(s03_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(s03_visual)], "S03-concat")

    s03_merged = TEMP / "s03_merged.mp4"
    concat_video_audio(s03_visual, VO_DIR / "S03.mp3", s03_merged)
    clips.append(s03_merged)

    # === S04 Action: Phone light → Text card "经验=没包装过的产品" ===
    s04_visual_dur = s04_dur - TC_DUR
    s04_p1_dur = s04_visual_dur * 0.6
    s04_p2_dur = s04_visual_dur - s04_p1_dur

    s04_p1 = TEMP / "s04_p1.mp4"
    image_to_video(AT_DIR / "AT04-phone-light.jpg", s04_p1_dur, s04_p1, zoom=True)

    tc02 = TEMP / "tc02.mp4"
    run([
        "ffmpeg", "-y", "-i", str(TC_DIR / "TC02-product.mp4"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920",
        str(tc02)
    ], "TC02-resize")

    s04_p2 = TEMP / "s04_p2.mp4"
    image_to_video(AT_DIR / "AT05-laptop-desk.jpg", s04_p2_dur, s04_p2, zoom=True)

    s04_list = TEMP / "s04_list.txt"
    s04_list.write_text(f"file '{s04_p1}'\nfile '{tc02}'\nfile '{s04_p2}'\n")
    s04_visual = TEMP / "s04_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(s04_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(s04_visual)], "S04-concat")

    s04_merged = TEMP / "s04_merged.mp4"
    concat_video_audio(s04_visual, VO_DIR / "S04.mp3", s04_merged)
    clips.append(s04_merged)

    # === S05 CTA: Coffee shop → Text card CTA ===
    s05_visual_dur = s05_dur - TC_DUR
    s05_clip = TEMP / "s05.mp4"
    image_to_video(AT_DIR / "AT06-coffee-shop.jpg", s05_visual_dur, s05_clip, zoom=True)

    tc03 = TEMP / "tc03.mp4"
    run([
        "ffmpeg", "-y", "-i", str(TC_DIR / "TC03-cta.mp4"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920",
        str(tc03)
    ], "TC03-resize")

    s05_list = TEMP / "s05_list.txt"
    s05_list.write_text(f"file '{s05_clip}'\nfile '{tc03}'\n")
    s05_visual = TEMP / "s05_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(s05_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(s05_visual)], "S05-concat")

    s05_merged = TEMP / "s05_merged.mp4"
    concat_video_audio(s05_visual, VO_DIR / "S05.mp3", s05_merged)
    clips.append(s05_merged)

    # === Final concat ===
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
    dur = get_duration(FINAL_OUTPUT)
    size = FINAL_OUTPUT.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {FINAL_OUTPUT}")
    print(f"  Duration: {dur:.1f}s")
    print(f"  Size: {size}MB")
    if dur > 90:
        print("  WARNING: Exceeds 90s target — trim in JianYing")
    elif dur < 60:
        print("  WARNING: Below 60s minimum!")


if __name__ == "__main__":
    main()
