#!/usr/bin/env python3
"""
B+ Repeat Blast v3 — VO-Driven Timeline + Cover Crop.

Fixes v2 issues:
  - VO-driven shot timing (no more VO cutoff)
  - Cover crop scaling (no more letterboxing)
  - Video under every shot (no more black screens)
  - Dynamic BGM alignment

Usage:
  source .venv/bin/activate
  python3 compose-repeat-blast-v2.py --config unemploy-repeat-01-waitnotice.json
  python3 compose-repeat-blast-v2.py --config unemploy-repeat-01-waitnotice.json --dry-run
"""

import argparse
import json
import random
import sys
from pathlib import Path

import av as _av
import numpy as np
from movis import Easing, Motion
from movis.attribute import AttributeType
from movis.layer import Audio, Composition, Rectangle, StrokeProperty, Text, Video

# Patch Movis 0.7.1 bug: scalar attributes return array([x]) but drawing.py calls float()
import movis.attribute as _attr_mod

_orig_attr_call = _attr_mod.Attribute.__call__


def _patched_attr_call(self, time):
    result = _orig_attr_call(self, time)
    if self._value_type in (AttributeType.SCALAR, AttributeType.ANGLE):
        if isinstance(result, np.ndarray):
            return float(result.item())
    return result


_attr_mod.Attribute.__call__ = _patched_attr_call

BASE = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE / "config"
STOCK_DIR = BASE / "assets" / "stock"
VO_DIR = BASE / "assets" / "voiceover"
BGM_DIR = BASE / "assets" / "bgm"
OUTPUT_DIR = BASE / "output"

SEGMENT_VOLUME_DB = {
    "LINE01": -4, "LINE02": -4,
    "LINE03": -5, "LINE04": -5, "LINE05": -5,
    "LINE06": -17, "LINE07": -13, "LINE08": -9,
    "LINE09": -5, "LINE10": -3, "LINE11": -1,
    "LINE12": -20, "LINE13": -20, "LINE14": -20,
    "LINE15": -5,
}

W, H = 1080, 1920


# --- Utilities ---


def load_config(name: str) -> dict:
    p = CONFIG_DIR / name
    if not p.exists():
        print(f"ERROR: Config not found: {p}")
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def db2lin(db: float) -> float:
    return 10.0 ** (db / 20.0)


def get_vo_duration(video_id: str, vo_id: str) -> float:
    """Get actual duration of a voiceover file in seconds."""
    path = VO_DIR / video_id / f"{vo_id}.mp3"
    if not path.exists():
        return 0.0
    c = _av.open(str(path))
    s = c.streams.audio[0]
    return float(s.duration * s.time_base)


def get_video_info(path: Path) -> tuple:
    """Get (width, height, duration) of a video file."""
    c = _av.open(str(path))
    s = c.streams.video[0]
    w, h = s.width, s.height
    dur = float(s.duration * s.time_base)
    return w, h, dur


def cover_scale(vw: int, vh: int, cw: int = W, ch: int = H) -> float:
    """Scale factor for cover-crop: fill canvas, crop overflow."""
    return max(cw / vw, ch / vh)


# --- Motion helpers ---


def anim_fade_in(item, dur: float, hold: float = 0.0, ease=Easing.LINEAR) -> None:
    item.opacity.enable_motion()
    fade = min(0.5, dur * 0.3)
    m = item.opacity.motion
    m.append(hold, 0.0, ease)
    m.append(hold + fade, 1.0)
    m.append(hold + dur - fade, 1.0)
    m.append(hold + dur, 0.0)


def anim_fade_in_hold(item, dur: float) -> None:
    """Fade in and hold at full opacity (no fade out)."""
    item.opacity.enable_motion()
    fade = min(0.5, dur * 0.3)
    m = item.opacity.motion
    m.append(0.0, 0.0)
    m.append(fade, 1.0)
    m.append(dur, 1.0)


def anim_slow_fade_in(item, dur: float) -> None:
    item.opacity.enable_motion()
    m = item.opacity.motion
    m.append(0.0, 0.0, Easing.EASE_IN)
    m.append(dur, 0.8)


def anim_blink(item, dur: float) -> None:
    item.opacity.enable_motion()
    m = item.opacity.motion
    t, vis = 0.0, True
    step = 0.15
    while t < dur:
        v = 1.0 if vis else 0.0
        nt = t + step
        if nt > dur:
            nt = dur
        m.append(t, v)
        t = nt + 0.001
        if t >= dur:
            break
        vis = not vis
    m.append(dur, 0.0)


def anim_shake(item, dur: float, intensity: float = 15.0) -> None:
    item.position.enable_motion()
    m = item.position.motion
    cx, cy = W / 2, H / 2
    t = 0.0
    while t < dur:
        dx = random.uniform(-intensity, intensity)
        dy = random.uniform(-intensity, intensity)
        m.append(t, np.array([cx + dx, cy + dy]))
        t += 0.05
    m.append(dur, np.array([cx, cy]))


# --- Timeline builder ---


def build_timeline(config: dict) -> list:
    """Build VO-driven timeline from config. Returns list of shot dicts."""
    video_id = config["video_id"]
    stock = config["stock_clips"]
    storyboard = config["storyboard"]

    # Pre-compute clip info
    clip_info = {}
    for key, info in stock.items():
        path = STOCK_DIR / info["file"]
        if path.exists():
            vw, vh, vd = get_video_info(path)
            clip_info[key] = {"path": path, "w": vw, "h": vh, "dur": vd, "scale": cover_scale(vw, vh)}

    # Track clip seek positions to avoid overlap
    clip_cursor = {k: 0.0 for k in stock}

    def next_seek(clip_key: str, needed: float) -> float:
        if clip_key not in clip_info:
            return 0.0
        max_dur = clip_info[clip_key]["dur"]
        start = clip_cursor[clip_key]
        if start + needed > max_dur:
            start = 0.0
        clip_cursor[clip_key] = start + needed
        return start

    timeline = []
    cursor = 0.0

    for i, shot_cfg in enumerate(storyboard):
        vo_id = shot_cfg.get("vo", "")
        vo_dur = get_vo_duration(video_id, vo_id) if vo_id else 0.0
        min_dur = shot_cfg.get("len", 2.0)

        # Shot duration driven by VO
        shot_dur = max(vo_dur + 0.3, min_dur) if vo_dur > 0 else min_dur

        # Determine video clip
        clip_key = shot_cfg.get("clip", "")
        is_text_card = shot_cfg["type"] == "text_card"

        # For text_card shots, assign a video clip underneath
        if is_text_card:
            # Use clip1 as default background for text cards
            if not clip_key:
                clip_key = "clip1"

        entry = {
            "shot_cfg": shot_cfg,
            "shot_num": shot_cfg["shot"],
            "offset": cursor,
            "duration": shot_dur,
            "vo_id": vo_id,
            "vo_dur": vo_dur,
            "clip_key": clip_key,
            "is_text_card": is_text_card,
            "ref": shot_cfg.get("ref", ""),
        }

        # Calculate video seek position
        if clip_key and clip_key in clip_info:
            entry["seek"] = next_seek(clip_key, shot_dur)
            entry["clip_path"] = clip_info[clip_key]["path"]
            entry["clip_scale"] = clip_info[clip_key]["scale"]
        elif clip_key and clip_key in stock:
            path = STOCK_DIR / stock[clip_key]["file"]
            if path.exists():
                entry["seek"] = 0.0
                entry["clip_path"] = path
                vw, vh, _ = get_video_info(path)
                entry["clip_scale"] = cover_scale(vw, vh)

        timeline.append(entry)
        cursor += shot_dur

    return timeline, cursor


# --- Scene builder ---


def build_scene(config: dict) -> Composition:
    video_id = config["video_id"]
    timeline, total_dur = build_timeline(config)

    # Add CTA tail
    cta_tail = 3.0
    final_dur = total_dur + cta_tail

    scene = Composition(size=(W, H), duration=final_dur)

    print(f"\nTimeline ({len(timeline)} shots, {final_dur:.1f}s total):")
    print(f"{'#':>3} {'Offset':>7} {'Dur':>6} {'VO':>6} {'Clip':>8} {'Type':>12} {'Ref':>15}")
    print("-" * 70)
    for e in timeline:
        print(f"{e['shot_num']:>3} {e['offset']:>7.1f}s {e['duration']:>5.1f}s "
              f"{e['vo_id']:>6} {e.get('clip_key',''):>8} "
              f"{'TEXT' if e['is_text_card'] else 'VIDEO':>12} {e.get('ref',''):>15}")

    # Background
    bg = Rectangle(size=(W, H), color=(15, 15, 20), duration=final_dur)
    scene.add_layer(bg, name="background")

    # Add video layers for each shot
    for e in timeline:
        sn = f"s{e['shot_num']:02d}"
        ts = e["offset"]
        dur = e["duration"]

        # Video layer (always present, cover-cropped)
        clip_path = e.get("clip_path")
        if clip_path and clip_path.exists():
            video = Video(str(clip_path))
            s = e.get("clip_scale", 1.0)
            seek = e.get("seek", 0.0)
            scene.add_layer(
                video, name=f"{sn}_vid", offset=ts,
                start_time=seek, end_time=seek + dur,
                scale=(s, s),
            )

        # Overlay text based on ref type
        ref = e.get("ref", "")
        if e["is_text_card"]:
            if ref == "TC01-hook":
                _add_hook_overlay(scene, ts, dur, sn)
            elif ref == "TC02-flash":
                _add_flash_overlay(scene, ts, dur, sn)
            elif ref in ("TC04-silence", "TC04-dark", "TC04-full"):
                _add_break_overlay(scene, ts, dur, sn, ref)
            elif ref == "TC05-cta":
                _add_cta_overlay(scene, ts, dur, sn)
        else:
            # Video clip overlays
            overlay = e["shot_cfg"].get("overlay")
            if overlay:
                _add_badge(scene, ts, dur, sn, overlay)

            ct = e["shot_cfg"].get("text_center")
            if ct:
                _add_center_text(scene, ts, dur, sn, ct)

            if e["shot_cfg"].get("text_rain"):
                _add_text_rain(scene, ts, dur, sn)

            ft = e["shot_cfg"].get("text_fade")
            if ft:
                _add_fade_text(scene, ts, dur, sn, ft)

        # Voiceover
        vo_id = e.get("vo_id", "")
        if vo_id:
            vo_path = VO_DIR / video_id / f"{vo_id}.mp3"
            if vo_path.exists():
                vo = Audio(str(vo_path))
                vol = db2lin(SEGMENT_VOLUME_DB.get(vo_id, -5))
                scene.add_layer(vo, name=f"{sn}_vo", offset=ts, audio_level=vol)

    # CTA tail text
    _add_cta_overlay(scene, total_dur, cta_tail, "tail_cta")

    # BGM
    _add_bgm(scene, config, final_dur)

    return scene


# --- Text overlays ---


def _make_text(text: str, size: int = 56, color: tuple = (255, 255, 255),
               stroke: StrokeProperty | None = None) -> Text:
    return Text(text, font_size=size, color=color,
                font_family="PingFang SC", contents=[stroke] if stroke else [])


def _add_hook_overlay(scene, ts, dur, sn) -> None:
    stroke = StrokeProperty(color=(30, 30, 30), width=3.0)

    t1 = _make_text("你已经听过这句话", 52, (220, 220, 220), stroke)
    i1 = scene.add_layer(t1, name=f"{sn}_l1", offset=ts, opacity=0.0)
    anim_fade_in(i1, dur * 0.5, hold=0.2)

    t2 = _make_text("____次了", 52, (255, 80, 80), stroke)
    i2 = scene.add_layer(t2, name=f"{sn}_l2", offset=ts + dur * 0.5, opacity=0.0)
    anim_blink(i2, dur * 0.5)


def _add_flash_overlay(scene, ts, dur, sn) -> None:
    stroke = StrokeProperty(color=(0, 0, 0), width=5.0)
    t = _make_text("回去等通知吧", 96, (255, 40, 40), stroke)
    i = scene.add_layer(t, name=sn, offset=ts, opacity=0.0)
    anim_fade_in(i, 0.3)
    anim_shake(i, dur - 0.3, 15.0)


def _add_break_overlay(scene, ts, dur, sn, ref) -> None:
    if ref == "TC04-silence":
        return

    stroke = StrokeProperty(color=(30, 30, 30), width=2.0)

    if ref == "TC04-dark":
        t = _make_text("半年了。", 56, (180, 180, 180), stroke)
        i = scene.add_layer(t, name=sn, offset=ts, opacity=0.0)
        anim_fade_in(i, dur, ease=Easing.EASE_IN)
    elif ref == "TC04-full":
        t = _make_text("还在等吗？", 64, (200, 200, 200), stroke)
        i = scene.add_layer(t, name=sn, offset=ts, opacity=0.0)
        anim_slow_fade_in(i, dur)


def _add_cta_overlay(scene, ts, dur, sn) -> None:
    stroke = StrokeProperty(color=(30, 30, 30), width=3.0)

    t1 = _make_text("你等了多久？", 72, (255, 220, 100), stroke)
    i1 = scene.add_layer(t1, name=f"{sn}_q", offset=ts, opacity=0.0)
    anim_fade_in_hold(i1, dur)

    t2 = _make_text("评论区说说", 32, (180, 180, 180))
    i2 = scene.add_layer(t2, name=f"{sn}_cta",
                         offset=ts + dur * 0.4, position=(W / 2, H / 2 + 120), opacity=0.0)
    anim_fade_in_hold(i2, dur * 0.6)


def _add_badge(scene, ts, dur, sn, text: str) -> None:
    t = _make_text(text, 36, (255, 200, 50), StrokeProperty(color=(0, 0, 0), width=2.0))
    i = scene.add_layer(t, name=f"{sn}_bdg", offset=ts + 0.3, position=(W / 2, 200), opacity=0.0)
    anim_fade_in_hold(i, dur - 0.3)


def _add_center_text(scene, ts, dur, sn, text: str) -> None:
    t = _make_text(text, 72, (255, 255, 255), StrokeProperty(color=(200, 0, 0), width=4.0))
    i = scene.add_layer(t, name=f"{sn}_ctr", offset=ts, opacity=0.0)
    anim_fade_in_hold(i, dur)


def _add_text_rain(scene, ts, dur, sn) -> None:
    ys = [400, 600, 800, 1000, 1200]
    sizes = [48, 36, 56, 40, 52]
    for i, (y, sz) in enumerate(zip(ys, sizes)):
        t = _make_text("回去等通知吧", sz, (255, 60, 60),
                        StrokeProperty(color=(0, 0, 0), width=3.0))
        li = scene.add_layer(t, name=f"{sn}_rain{i}",
                             offset=ts + i * 0.1, position=(W / 2, y), opacity=0.0)
        anim_fade_in_hold(li, dur - i * 0.1)


def _add_fade_text(scene, ts, dur, sn, text: str) -> None:
    t = _make_text(text, 36, (200, 200, 200), StrokeProperty(color=(0, 0, 0), width=1.5))
    li = scene.add_layer(t, name=f"{sn}_fade",
                         offset=ts + dur * 0.5, position=(W / 2, H - 300), opacity=0.0)
    anim_fade_in_hold(li, dur * 0.5)


def _add_bgm(scene, config, total_dur: float) -> None:
    bgm = config.get("bgm", {})

    sections = [
        ("heartbeat_60",  0,               total_dur * 0.36),
        ("heartbeat_120", total_dur * 0.36, total_dur * 0.48),
        ("heartbeat_140", total_dur * 0.48, total_dur * 0.58),
        ("heartbeat_160", total_dur * 0.58, total_dur * 0.66),
        ("piano_c",       total_dur * 0.86, total_dur),
    ]

    for key, start, end in sections:
        info = bgm.get(key)
        if not info:
            continue
        f = BGM_DIR / info["file"]
        if not f.exists():
            f = f.with_suffix(".m4a")
        if not f.exists():
            print(f"  WARN: BGM missing: {f}")
            continue
        a = Audio(str(f))
        vol = db2lin(info.get("volume", 0.15))
        scene.add_layer(a, name=f"bgm_{key}", offset=start, end_time=end - start, audio_level=vol)


# --- Main ---


def main() -> None:
    parser = argparse.ArgumentParser(description="B+ Repeat Blast v3 (VO-driven)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    vid = config["video_id"]

    print(f"B+ Repeat Blast v3 — {vid}")
    print("=" * 50)

    out = OUTPUT_DIR / vid
    out.mkdir(parents=True, exist_ok=True)
    of = out / f"{vid}-rough-cut.mp4"

    if args.dry_run:
        # Just build timeline, don't render
        timeline, total = build_timeline(config)
        final = total + 3.0
        print(f"\nFinal duration: {final:.1f}s")
        print(f"\nTimeline ({len(timeline)} shots, {final:.1f}s total):")
        print(f"{'#':>3} {'Offset':>7} {'Dur':>6} {'VO':>8} {'Clip':>8} {'Type':>12} {'Ref':>15}")
        print("-" * 70)
        for e in timeline:
            print(f"{e['shot_num']:>3} {e['offset']:>7.1f}s {e['duration']:>5.1f}s "
                  f"{e['vo_id']+'('+str(e['vo_dur'])+'s)':>8} {e.get('clip_key',''):>8} "
                  f"{'TEXT' if e['is_text_card'] else 'VIDEO':>12} {e.get('ref',''):>15}")
        print("DRY RUN — skipping render")
        return

    scene = build_scene(config)
    final_dur = scene.duration
    print(f"\nFinal: {final_dur:.1f}s, {W}x{H}")
    print(f"Layers: {len(scene.keys())}")

    print("Rendering...")
    scene.write_video(
        str(of), codec="libx264", fps=24.0, audio=True,
        output_params=["-crf", "18", "-preset", "slow"],
    )
    mb = of.stat().st_size / 1024 / 1024
    print(f"\nDone: {of} ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
