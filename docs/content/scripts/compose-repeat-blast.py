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

# Per-segment volume targets (dB) per Codex review
SEGMENT_VOLUME = {
    "LINE01": -4, "LINE02": -4,          # HOOK
    "LINE03": -5, "LINE04": -5, "LINE05": -5,  # PATTERN
    "LINE06": -17, "LINE07": -13, "LINE08": -9,  # ESCALATION (linear ramp)
    "LINE09": -5, "LINE10": -3, "LINE11": -1,
    "LINE12": -20, "LINE13": -20, "LINE14": -20,  # BREAK (sudden silence)
    "LINE15": -5,                            # CTA
}

# Target durations per shot (to reach ~50s total)
SHOT_TARGET_DUR = {
    3: 3.5, 4: 4.6, 5: 4.0, 6: 3.0, 7: 4.0,   # HOOK+PATTERN
    9: 2.2, 10: 2.0, 11: 2.0, 12: 2.0,           # ESCALATION
    13: 3.0, 14: 2.0,                             # RAPID
    16: 2.0, 17: 2.0, 18: 1.5,                    # BREAK
    20: 2.0,                                       # CTA
}


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


def overlay_center_text(video: Path, text: str, output: Path, temp_dir: Path) -> None:
    """Generate text PNG via Playwright and overlay on video."""
    text_png = temp_dir / f"text_{hash(text)}.png"
    if not text_png.exists():
        html = (
            '<!DOCTYPE html><html><head><style>'
            '* { margin: 0; padding: 0; } '
            f'body {{ width: 1080px; height: 1920px; display: flex; '
            f'align-items: center; justify-content: center; '
            f'font-family: "Hiragino Sans GB", "STHeiti", sans-serif; }} '
            f'.text {{ font-size: 72px; font-weight: 700; color: #fff; '
            f'text-shadow: 2px 0 #FF2D2D, -2px 0 #FF2D2D, 0 2px #FF2D2D, 0 -2px #FF2D2D; '
            f'letter-spacing: 4px; }}'
            '</style></head><body>'
            f'<div class="text">{text}</div>'
            '</body></html>'
        )
        html_path = temp_dir / f"text_{hash(text)}.html"
        html_path.write_text(html)
        subprocess.run([
            "python3", "-c",
            "from playwright.sync_api import sync_playwright; "
            "from pathlib import Path; "
            "p = sync_playwright().start(); "
            "b = p.chromium.launch(); "
            f"pg = b.new_page(viewport={{'width': 1080, 'height': 1920}}); "
            f"pg.goto('file://{html_path.resolve()}'); "
            "pg.wait_for_timeout(300); "
            f"pg.screenshot(path='{text_png}'); "
            "b.close(); p.stop()",
        ], capture_output=True, timeout=30)
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(text_png),
        "-filter_complex", "[0:v][1:v]overlay=(W-w)/2:(H-h)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-an", str(output),
    ], f"text {output.name}")


def prepare_vo(vo_ref: str, vo_file: Path, target_dur: float, temp_dir: Path) -> Path:
    """Normalize volume + compress duration of a VO file. Returns processed path."""
    vol_db = SEGMENT_VOLUME.get(vo_ref, -5)
    out = temp_dir / f"vo_{vo_ref}_processed.mp3"

    vo_dur = get_duration(vo_file)
    filters = [f"volume={vol_db}dB"]

    # Apply atempo if VO is significantly longer than target
    if target_dur > 0 and vo_dur > target_dur * 1.1:
        ratio = vo_dur / target_dur
        # atempo supports 0.5-2.0 per filter; chain for >2x
        if ratio <= 2.0:
            filters.append(f"atempo={ratio:.3f}")
        elif ratio <= 4.0:
            r1 = 2.0
            r2 = ratio / r1
            filters.append(f"atempo={r1:.3f},atempo={r2:.3f}")
        else:
            r1 = 2.0
            r2 = 2.0
            r3 = ratio / (r1 * r2)
            filters.append(f"atempo={r1:.3f},atempo={r2:.3f},atempo={r3:.3f}")

    filter_str = ",".join(filters)
    run([
        "ffmpeg", "-y", "-i", str(vo_file),
        "-af", filter_str,
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out),
    ], f"vo-process {vo_ref}")

    return out


def add_silent_audio(video: Path, output: Path, duration: float) -> None:
    """Add a silent audio track to a video-only file."""
    run([
        "ffmpeg", "-y",
        "-i", str(video),
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-t", f"{duration:.3f}", "-shortest",
        str(output),
    ], f"silent-audio {output.name}")


def merge_vo(video: Path, vo: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(vo),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        str(output),
    ], f"vo {output.name}")


def ensure_audio(path: Path, duration: float, temp_dir: Path) -> Path:
    """Ensure the video file has an audio stream. Add silent if missing."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    if "audio" in r.stdout:
        return path
    out = temp_dir / f"{path.stem}_withaudio.mp4"
    add_silent_audio(path, out, duration)
    return out


def build_shot(
    shot: dict, config: dict, temp_dir: Path, video_id: str,
) -> Path:
    shot_num = shot["shot"]
    out = temp_dir / f"shot_{shot_num:02d}.mp4"
    shot_type = shot["type"]
    target_dur = SHOT_TARGET_DUR.get(shot_num, shot.get("duration", 2.0))

    if shot_type == "text_card":
        tc_ref = shot["ref"]
        tc_dir = TC_DIR / video_id
        tc_file = tc_dir / f"{tc_ref}.mp4"
        dur = shot["duration"]
        if tc_file.exists():
            run([
                "ffmpeg", "-y", "-i", str(tc_file),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920", "-t", f"{dur:.3f}",
                "-an", str(out),
            ], f"tc {tc_ref}")
        else:
            tc_png = tc_dir / f"{tc_ref}.png"
            if tc_png.exists():
                run([
                    "ffmpeg", "-y", "-loop", "1", "-i", str(tc_png),
                    "-c:v", "libx264", "-t", f"{dur:.3f}",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    "-an", str(out),
                ], f"tc-png {tc_ref}")
            else:
                run([
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=black:s=1080x1920:d={dur:.3f}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                    "-an", str(out),
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
            overlay_center_text(current, shot["text_center"], texted, temp_dir)
            current = texted

        # Merge VO with volume normalization + duration compression
        if "vo" in shot:
            vo_ref = shot["vo"]
            vo_file = VO_DIR / video_id / f"{vo_ref}.mp3"
            if vo_file.exists():
                processed_vo = prepare_vo(vo_ref, vo_file, target_dur, temp_dir)
                voiced = temp_dir / f"shot_{shot_num:02d}_vo.mp4"
                merge_vo(current, processed_vo, voiced)
                current = voiced

        if current != out:
            shutil.move(str(current), str(out))

    # Ensure every final shot has audio (add silent track if missing)
    dur = shot.get("duration", 2.0)
    final = ensure_audio(out, dur, temp_dir)
    if final != out:
        shutil.move(str(final), str(out))

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
                vol = SEGMENT_VOLUME.get(s["vo"], -5)
                extras.append(f"vo={s['vo']} ({vol}dB)")
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

    # Verify all shots have both streams before concat
    print("\n--- Pre-concat stream check ---")
    for sf in shot_files:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
             "-of", "csv=p=0", str(sf)],
            capture_output=True, text=True,
        )
        streams = r.stdout.strip().replace("\n", ",")
        dur = get_duration(sf)
        print(f"  {sf.name}: [{streams}] {dur:.2f}s")
        if "audio" not in streams:
            print(f"  WARNING: {sf.name} missing audio!")

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
    heartbeat = BGM_DIR / "heartbeat-60bpm.m4a"
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

    # Final stream check
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name",
         "-of", "csv=p=0", str(final)],
        capture_output=True, text=True,
    )
    print(f"\nDONE: {final}")
    print(f"  Duration: {dur:.1f}s (target: 50s)")
    print(f"  Size: {size}MB")
    print(f"  Streams: {r.stdout.strip().replace(chr(10), ', ')}")


if __name__ == "__main__":
    main()
