#!/usr/bin/env python3
"""
B+ Repeat Blast video composer.
Assembles interview stock footage + text cards + voiceover + BGM.

Usage:
  python3 compose-repeat-blast.py --config config/unemploy-repeat-01-waitnotice.json
  python3 compose-repeat-blast.py --config config/unemploy-repeat-01-waitnotice.json --dry-run
"""

import argparse
import json
import subprocess
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE / "config"
STOCK_DIR = BASE / "assets" / "stock"
TC_DIR = BASE / "assets" / "textcards"
VO_DIR = BASE / "assets" / "voiceover"
BGM_DIR = BASE / "assets" / "bgm"
OUTPUT_DIR = BASE / "output"


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:5])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:500]}")
        sys.exit(1)


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def extract_stock_clip(
    source: Path, seek: float, length: float, output: Path,
) -> None:
    run([
        "ffmpeg", "-y", "-ss", f"{seek:.3f}", "-i", str(source),
        "-t", f"{length:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-an", str(output),
    ], f"extract {output.name}")


def overlay_badge(video: Path, badge: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(badge),
        "-filter_complex",
        "[1:v]scale=300:80[badge];"
        "[0:v][badge]overlay=(W-w)/2:H*88/100:enable='between(t,0,999)'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-an", str(output),
    ], f"badge {output.name}")


def overlay_center_text(video: Path, text: str, output: Path) -> None:
    escaped = text.replace("'", "'\\''").replace(":", "\\:")
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf",
        f"drawtext=text='{escaped}':fontsize=72:fontcolor=white:"
        f"borderw=2:bordercolor=0xFF2D2D@0.8:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"fontfile=/System/Library/Fonts/PingFang.ttc",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-an", str(output),
    ], f"text {output.name}")


def merge_vo(video: Path, vo: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(vo),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        str(output),
    ], f"vo {output.name}")


def build_shot(
    shot: dict, config: dict, temp_dir: Path, video_id: str,
) -> Path:
    shot_num = shot["shot"]
    out = temp_dir / f"shot_{shot_num:02d}.mp4"
    shot_type = shot["type"]

    if shot_type == "text_card":
        tc_ref = shot["ref"]
        tc_dir = TC_DIR / video_id
        tc_file = tc_dir / f"{tc_ref}.mp4"
        if tc_file.exists():
            run([
                "ffmpeg", "-y", "-i", str(tc_file),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920", "-t", f"{shot['duration']:.3f}",
                str(out),
            ], f"tc {tc_ref}")
        else:
            tc_png = tc_dir / f"{tc_ref}.png"
            if tc_png.exists():
                run([
                    "ffmpeg", "-y", "-loop", "1", "-i", str(tc_png),
                    "-c:v", "libx264", "-t", f"{shot['duration']:.3f}",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    "-vf", "scale=1080:1920", str(out),
                ], f"tc-png {tc_ref}")
            else:
                run([
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=black:s=1080x1920:d={shot['duration']:.3f}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                    str(out),
                ], f"black {shot_num}")

    elif shot_type == "video_clip":
        clip_key = shot["clip"]
        clip_cfg = config["stock_clips"][clip_key]
        source = STOCK_DIR / clip_cfg["file"]
        seek = shot["seek"]
        length = shot["len"]
        raw = temp_dir / f"shot_{shot_num:02d}_raw.mp4"
        extract_stock_clip(source, seek, length, raw)

        current = raw

        if "overlay" in shot:
            badge_num = {"第1次": 1, "第7次": 7, "第23次": 23, "第47次": 47}.get(
                shot["overlay"], 1
            )
            badge_file = TC_DIR / video_id / f"badge-{badge_num}.png"
            if badge_file.exists():
                badged = temp_dir / f"shot_{shot_num:02d}_badge.mp4"
                overlay_badge(current, badge_file, badged)
                current = badged

        if "text_center" in shot:
            texted = temp_dir / f"shot_{shot_num:02d}_text.mp4"
            overlay_center_text(current, shot["text_center"], texted)
            current = texted

        if "vo" in shot:
            vo_ref = shot["vo"]
            vo_file = VO_DIR / video_id / f"{vo_ref}.mp3"
            if vo_file.exists():
                voiced = temp_dir / f"shot_{shot_num:02d}_vo.mp4"
                merge_vo(current, vo_file, voiced)
                current = voiced

        if current != out:
            shutil.move(str(current), str(out))

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="B+ Repeat Blast composer")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = CONFIG_DIR / config_path.name
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "temp_shots"
    temp_dir.mkdir(parents=True, exist_ok=True)

    storyboard = config["storyboard"]

    if args.dry_run:
        print(f"Dry run: {video_id} ({len(storyboard)} shots)")
        for s in storyboard:
            extras = []
            if "vo" in s:
                extras.append(f"vo={s['vo']}")
            if "overlay" in s:
                extras.append(f"overlay={s['overlay']}")
            if "text_center" in s:
                extras.append(f"text={s['text_center']}")
            print(f"  Shot {s['shot']:2d} ({s['time']:10s}): {s['type']} {' '.join(extras)}")
        return

    print(f"Composing: {video_id} ({len(storyboard)} shots)")

    shot_files: list[Path] = []
    for shot in storyboard:
        print(f"\n--- Shot {shot['shot']} ({shot['time']}) ---")
        sf = build_shot(shot, config, temp_dir, video_id)
        shot_files.append(sf)

    concat_list = temp_dir / "shot_list.txt"
    concat_list.write_text("".join(f"file '{sf}'\n" for sf in shot_files))
    no_bgm = out_dir / f"{video_id}-no-bgm.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(no_bgm),
    ], "CONCAT all shots")

    final = out_dir / f"{video_id}-rough-cut.mp4"
    heartbeat = BGM_DIR / "heartbeat-60bpm.mp3"
    if heartbeat.exists():
        video_dur = get_duration(no_bgm)
        fade_out_start = max(0, video_dur - 3)
        run([
            "ffmpeg", "-y",
            "-i", str(no_bgm),
            "-stream_loop", "-1", "-i", str(heartbeat),
            "-filter_complex",
            f"[1:a]volume=0.08,afade=t=in:st=0:d=2,"
            f"afade=t=out:st={fade_out_start:.3f}:d=3[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final),
        ], "FINAL+bgm")
    else:
        shutil.copy2(str(no_bgm), str(final))

    dur = get_duration(final)
    size = final.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {final}")
    print(f"  Duration: {dur:.1f}s (target: 50s)")
    print(f"  Size: {size}MB")


if __name__ == "__main__":
    main()
