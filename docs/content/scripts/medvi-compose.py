#!/usr/bin/env python3
"""
Generic rough-cut composer for Medvi v3 videos.
Reads a v3 config JSON and produces a rough-cut MP4.

Usage:
  python3 medvi-compose.py --config config/unemploy-story-01-zhangwei-v3.json
  python3 medvi-compose.py --config config/xxx.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"

ASSET_DIRS = {
    "screenshot": BASE / "assets" / "screenshots",
    "atmosphere": BASE / "assets" / "unsplash",
    "text_card": BASE / "assets" / "textcards",
    "voiceover": BASE / "assets" / "voiceover",
    "bgm": BASE / "assets" / "bgm",
    "opening": BASE / "output" / "unemploy-story-opening",
}


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:4])}...")
    import subprocess
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:300]}")
        sys.exit(1)


def get_duration(path: Path) -> float:
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def image_to_video(image: Path, duration: float, output: Path, zoom: bool = False) -> None:
    vf = "scale=1080:1920"
    if zoom:
        frames = int(duration * 24)
        vf = (
            f"scale=1152:2048,crop=1080:1920:36:64,"
            f"zoompan=z='min(zoom+0.0008,1.08)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920"
        )
    run([
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(image),
        "-c:v", "libx264", "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p", "-vf", vf, "-r", "24",
        str(output)
    ], f"img→vid {output.name}")


def concat_video_audio(video: Path, audio: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y",
        "-i", str(video), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output)
    ], f"merge {output.name}")


def find_asset(ref: str, asset_type: str, video_id: str) -> Path:
    """Find asset file by ref ID and type."""
    dir_path = ASSET_DIRS[asset_type] / video_id
    # Try exact filename patterns
    for ext in [".png", ".jpg", ".jpeg", ".mp4", ".mp3"]:
        p = dir_path / f"{ref}{ext}"
        if p.exists():
            return p
    # Try prefix match (e.g., TC01-waste-paper.mp4)
    for f in dir_path.iterdir():
        if f.name.startswith(ref + "-") or f.name.startswith(ref + "."):
            return f
    print(f"  ERROR: {asset_type} asset not found: {ref} in {dir_path}")
    sys.exit(1)


def build_segment_clips(
    segment_id: str,
    clips_config: list[dict],
    vo_duration: float,
    video_id: str,
    temp_dir: Path,
) -> Path:
    """Build all clips for one segment, concat them, merge voiceover."""
    # Separate text cards (fixed duration) from flexible clips
    text_card_clips = [c for c in clips_config if c["type"] == "text_card"]
    flexible_clips = [c for c in clips_config if c["type"] != "text_card"]

    fixed_time = sum(c.get("duration", 4.0) for c in text_card_clips)
    remaining = max(0.1, vo_duration - fixed_time)

    clip_files: list[Path] = []
    clip_idx = 0

    # Process flexible clips (screenshot / atmosphere)
    for clip_cfg in flexible_clips:
        pct = clip_cfg.get("pct", 1.0 / max(len(flexible_clips), 1))
        dur = remaining * pct
        zoom = clip_cfg.get("zoom", False)
        asset_type = clip_cfg["type"]  # "screenshot" or "atmosphere"
        ref = clip_cfg["ref"]
        asset_path = find_asset(ref, asset_type, video_id)
        out = temp_dir / f"{segment_id}_clip{clip_idx}.mp4"
        image_to_video(asset_path, dur, out, zoom=zoom)
        clip_files.append(out)
        clip_idx += 1

    # Process text cards
    for tc_cfg in text_card_clips:
        ref = tc_cfg["ref"]
        tc_src = find_asset(ref, "text_card", video_id)
        out = temp_dir / f"{segment_id}_tc{clip_idx}.mp4"
        run([
            "ffmpeg", "-y", "-i", str(tc_src),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            "-vf", "scale=1080:1920",
            str(out)
        ], f"TC-resize {ref}")
        clip_files.append(out)
        clip_idx += 1

    # Concat segment clips
    seg_list = temp_dir / f"{segment_id}_list.txt"
    seg_list.write_text("".join(f"file '{c}'\n" for c in clip_files))
    seg_visual = temp_dir / f"{segment_id}_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(seg_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(seg_visual)], f"{segment_id}-concat")

    # Merge voiceover
    vo_path = find_asset(segment_id, "voiceover", video_id)
    seg_merged = temp_dir / f"{segment_id}_merged.mp4"
    concat_video_audio(seg_visual, vo_path, seg_merged)
    return seg_merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Medvi v3 generic composer")
    parser.add_argument("--config", type=str, required=True, help="v3 config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = BASE / "config" / config_path.name
    if not config_path.exists():
        config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    storyboard = config["storyboard"]
    global_cfg = config["global"]
    bgm_cfg = config.get("bgm", {})

    out_dir = BASE / "output" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "temp_clips"
    temp_dir.mkdir(parents=True, exist_ok=True)

    final_output = out_dir / f"{video_id}-rough-cut.mp4"

    if args.dry_run:
        print(f"Dry run: {video_id}")
        for seg_entry in storyboard:
            seg_id = seg_entry["segment"]
            print(f"\n  {seg_id}: {len(seg_entry['clips'])} clips")
            for c in seg_entry["clips"]:
                print(f"    {c['type']} {c['ref']} zoom={c.get('zoom', False)} pct={c.get('pct', '-')}")
        return

    # Get voiceover durations
    print(f"Composing: {video_id}")
    vo_durations = {}
    for seg_entry in storyboard:
        seg_id = seg_entry["segment"]
        vo_path = find_asset(seg_id, "voiceover", video_id)
        vo_durations[seg_id] = get_duration(vo_path)

    total_vo = sum(vo_durations.values())
    print(f"Voiceover total: {total_vo:.1f}s")
    for seg_id, d in vo_durations.items():
        print(f"  {seg_id}: {d:.1f}s")

    clips: list[Path] = []

    # Opening hook
    opening_file = global_cfg.get("opening_file", "")
    if opening_file:
        opening_src = ASSET_DIRS["opening"] / opening_file
        if opening_src.exists():
            opening_24 = temp_dir / "opening_24fps.mp4"
            run([
                "ffmpeg", "-y", "-i", str(opening_src),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920",
                str(opening_24)
            ], "opening-24fps")
            clips.append(opening_24)
        else:
            print(f"  WARNING: opening file not found: {opening_src}")

    # Build each segment
    for seg_entry in storyboard:
        seg_id = seg_entry["segment"]
        vo_dur = vo_durations[seg_id]
        print(f"\n=== {seg_id} ({vo_dur:.1f}s) ===")
        merged = build_segment_clips(
            segment_id=seg_id,
            clips_config=seg_entry["clips"],
            vo_duration=vo_dur,
            video_id=video_id,
            temp_dir=temp_dir,
        )
        clips.append(merged)

    # Final concat
    concat_list = temp_dir / "final_list.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clips))
    no_bgm = temp_dir / "no_bgm.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(no_bgm)
    ], "FINAL-concat")

    # BGM mixing
    bgm_file = ASSET_DIRS["bgm"] / bgm_cfg.get("file", "") if bgm_cfg.get("file") else None
    if bgm_file and bgm_file.exists():
        video_dur = get_duration(no_bgm)
        bgm_volume = bgm_cfg.get("volume", 0.08)
        bgm_fade_in = bgm_cfg.get("fade_in", 2.0)
        bgm_fade_out = bgm_cfg.get("fade_out", 3.0)
        fade_out_start = max(0, video_dur - bgm_fade_out)

        print(f"  BGM: {bgm_file.name} at {bgm_volume*100:.0f}%")
        run([
            "ffmpeg", "-y",
            "-i", str(no_bgm),
            "-stream_loop", "-1", "-i", str(bgm_file),
            "-filter_complex",
            f"[1:a]volume={bgm_volume},afade=t=in:st=0:d={bgm_fade_in},"
            f"afade=t=out:st={fade_out_start:.3f}:d={bgm_fade_out}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_output)
        ], "FINAL+bgm")
    else:
        print("  No BGM, copying without music")
        import shutil
        shutil.copy2(str(no_bgm), str(final_output))

    # Report
    dur = get_duration(final_output)
    size = final_output.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {final_output}")
    print(f"  Duration: {dur:.1f}s")
    print(f"  Size: {size}MB")
    if dur > 90:
        print("  WARNING: Exceeds 90s target")
    elif dur < 60:
        print("  WARNING: Below 60s minimum!")


if __name__ == "__main__":
    main()
