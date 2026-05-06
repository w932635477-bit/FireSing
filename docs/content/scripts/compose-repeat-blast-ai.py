#!/usr/bin/env python3
"""
B+ Repeat Blast AI — VO-Driven Timeline with AI-generated video clips.

Reads AI-generated video clips (from Kling I2V) and assembles with:
  - VO-driven shot timing
  - Text overlays (hook, badges, flash, text rain, CTA)
  - Heartbeat BGM
  - Cover-crop scaling

Usage:
  source .venv/bin/activate
  python3 compose-repeat-blast-ai.py --config unemploy-repeat-01-waitnotice-ai.json
  python3 compose-repeat-blast-ai.py --config unemploy-repeat-01-waitnotice-ai.json --dry-run
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
VO_DIR = BASE / "assets" / "voiceover"
BGM_DIR = BASE / "assets" / "bgm"
OUTPUT_DIR = BASE / "output"

# Original video_id for VO files (reuse existing voiceovers)
ORIGINAL_VIDEO_ID = "unemploy-repeat-01-waitnotice"

SEGMENT_VOLUME_DB = {
    "LINE01": -4, "LINE02": -4,
    "LINE03": -5, "LINE04": -5, "LINE05": -5,
    "LINE06": -17, "LINE07": -13, "LINE08": -9,
    "LINE09": -5, "LINE10": -3, "LINE11": -1,
    "LINE12": -20, "LINE13": -20, "LINE14": -20,
    "LINE15": -5,
}

W, H = 1080, 1920

# VO-to-shot mapping: which VO lines play under which AI shot
SHOT_VO_MAP = {
    "S01": ["LINE01"],
    "S02": ["LINE02"],
    "S03": ["LINE03"],
    "S04": ["LINE04"],
    "S05": ["LINE05"],
    "S06": ["LINE06", "LINE07", "LINE08"],
    "S07": ["LINE09"],
    "S08": ["LINE10"],
    "S09": ["LINE11"],
    "S10": ["LINE12"],
    "S11": ["LINE13", "LINE14"],
    "S12": ["LINE15"],
}

# Text overlays per shot
SHOT_OVERLAYS = {
    "S02": [{"type": "badge", "text": "第1次"}],
    "S03": [{"type": "badge", "text": "第7次"}],
    "S04": [{"type": "badge", "text": "第23次"}],
    "S05": [{"type": "badge", "text": "第47次"}],
    "S06": [{"type": "center_text", "text": "回去等通知吧"}],
    "S07": [{"type": "center_text", "text": "回去等通知吧"}],
    "S08": [{"type": "text_rain"}],
    "S09": [{"type": "flash", "text": "回去等通知吧"}],
    "S10": [{"type": "slow_text", "text": "半年了。"}],
    "S11": [{"type": "slow_text", "text": "还在等吗？"}],
    "S12": [],
}


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
    path = VO_DIR / video_id / f"{vo_id}.mp3"
    if not path.exists():
        return 0.0
    c = _av.open(str(path))
    s = c.streams.audio[0]
    return float(s.duration * s.time_base)


def get_video_duration(path: Path) -> float:
    c = _av.open(str(path))
    s = c.streams.video[0]
    return float(s.duration * s.time_base)


def cover_scale(vw: int, vh: int, cw: int = W, ch: int = H) -> float:
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


def build_timeline(config: dict) -> tuple:
    video_id = config["video_id"]
    segments = config["segments"]
    output_dir = OUTPUT_DIR / video_id

    timeline = []
    cursor = 0.0

    # Pre-scan hook: add 1.5s hook text before first shot
    hook_dur = 1.5
    hook_entry = {
        "shot_id": "hook",
        "offset": 0.0,
        "duration": hook_dur,
        "vo_lines": [],
        "vo_total_dur": 0.0,
        "clip_path": None,
        "clip_dur": 0.0,
        "overlays": [{"type": "hook_text"}],
    }
    timeline.append(hook_entry)
    cursor = hook_dur

    for seg in segments:
        shot_id = seg["id"]
        vo_lines = SHOT_VO_MAP.get(shot_id, [])

        # Sum VO durations
        vo_total = sum(get_vo_duration(ORIGINAL_VIDEO_ID, v) for v in vo_lines)

        # Shot duration = max(VO total + padding, min 2s)
        shot_dur = max(vo_total + 0.3, 2.0) if vo_total > 0 else 2.0

        # Find AI video clip (prefer processed version with film grain)
        clip_path = output_dir / f"{shot_id}-processed.mp4"
        if not clip_path.exists():
            clip_path = output_dir / f"{shot_id}.mp4"
        clip_dur = 0.0
        if clip_path.exists():
            clip_dur = get_video_duration(clip_path)

        # If clip shorter than needed, loop it
        if clip_dur > 0 and clip_dur < shot_dur:
            shot_dur = clip_dur  # trim to clip length instead of looping

        entry = {
            "shot_id": shot_id,
            "offset": cursor,
            "duration": shot_dur,
            "vo_lines": vo_lines,
            "vo_total_dur": vo_total,
            "clip_path": clip_path if clip_path.exists() else None,
            "clip_dur": clip_dur,
            "overlays": SHOT_OVERLAYS.get(shot_id, []),
            "emotion": seg.get("emotion", ""),
        }
        timeline.append(entry)
        cursor += shot_dur

    return timeline, cursor


# --- Text helpers ---


def _make_text(text: str, size: int = 56, color: tuple = (255, 255, 255),
               stroke: StrokeProperty | None = None) -> Text:
    return Text(text, font_size=size, color=color,
                font_family="PingFang SC", contents=[stroke] if stroke else [])


def _add_hook_text(scene, ts, dur, prefix) -> None:
    stroke = StrokeProperty(color=(30, 30, 30), width=3.0)
    t1 = _make_text("你已经听过这句话", 52, (220, 220, 220), stroke)
    i1 = scene.add_layer(t1, name=f"{prefix}_l1", offset=ts, opacity=0.0)
    anim_fade_in(i1, dur * 0.6, hold=0.1)

    t2 = _make_text("____次了", 52, (255, 80, 80), stroke)
    i2 = scene.add_layer(t2, name=f"{prefix}_l2", offset=ts + dur * 0.5, opacity=0.0)
    anim_blink(i2, dur * 0.5)


def _add_badge(scene, ts, dur, prefix, text: str) -> None:
    t = _make_text(text, 36, (255, 200, 50), StrokeProperty(color=(0, 0, 0), width=2.0))
    i = scene.add_layer(t, name=f"{prefix}_bdg", offset=ts + 0.3, position=(W / 2, 1689), opacity=0.0)
    anim_fade_in_hold(i, dur - 0.3)


def _add_center_text(scene, ts, dur, prefix, text: str) -> None:
    t = _make_text(text, 96, (255, 255, 255), StrokeProperty(color=(200, 0, 0), width=4.0))
    i = scene.add_layer(t, name=f"{prefix}_ctr", offset=ts, opacity=0.0)
    anim_fade_in_hold(i, dur)


def _add_flash_text(scene, ts, dur, prefix, text: str) -> None:
    stroke = StrokeProperty(color=(0, 0, 0), width=5.0)
    t = _make_text(text, 120, (255, 40, 40), stroke)
    i = scene.add_layer(t, name=prefix, offset=ts, opacity=0.0)
    anim_fade_in(i, 0.3)
    shake_dur = max(0.0, dur - 0.3)
    if shake_dur > 0:
        anim_shake(i, shake_dur, 15.0)


def _add_text_rain(scene, ts, dur, prefix) -> None:
    ys = [400, 600, 800, 1000, 1200]
    sizes = [48, 36, 56, 40, 52]
    for i, (y, sz) in enumerate(zip(ys, sizes)):
        t = _make_text("回去等通知吧", sz, (255, 60, 60),
                        StrokeProperty(color=(0, 0, 0), width=3.0))
        li = scene.add_layer(t, name=f"{prefix}_rain{i}",
                             offset=ts + i * 0.1, position=(W / 2, y), opacity=0.0)
        anim_fade_in_hold(li, dur - i * 0.1)


def _add_slow_text(scene, ts, dur, prefix, text: str) -> None:
    stroke = StrokeProperty(color=(30, 30, 30), width=2.0)
    t = _make_text(text, 56, (180, 180, 180), stroke)
    i = scene.add_layer(t, name=prefix, offset=ts, opacity=0.0)
    anim_slow_fade_in(i, dur)


def _add_cta(scene, ts, dur, prefix) -> None:
    stroke = StrokeProperty(color=(30, 30, 30), width=3.0)
    t1 = _make_text("你等了多久？", 72, (255, 220, 100), stroke)
    i1 = scene.add_layer(t1, name=f"{prefix}_q", offset=ts, opacity=0.0)
    anim_fade_in_hold(i1, dur)

    t2 = _make_text("评论区说说", 32, (180, 180, 180))
    i2 = scene.add_layer(t2, name=f"{prefix}_cta",
                         offset=ts + dur * 0.4, position=(W / 2, H / 2 + 120), opacity=0.0)
    anim_fade_in_hold(i2, dur * 0.6)


# --- BGM ---


def _add_audio_layer(scene, name: str, offset: float, dur: float, vol_db: float) -> None:
    f = BGM_DIR / name
    if not f.exists():
        print(f"  WARN: Audio missing: {f}")
        return
    a = Audio(str(f))
    vol = db2lin(vol_db)
    scene.add_layer(a, name=f"sfx_{name}_{offset:.0f}", offset=offset, end_time=dur, audio_level=vol)


def _add_bgm(scene, total_dur: float) -> None:
    # Timeline reference (from storyboard):
    #   HOOK        0-3s      AC hum + heartbeat 60bpm
    #   PATTERN     3-20s     AC hum + heartbeat 60bpm, subtle foley
    #   ESCALATION  20-35s    heartbeat 120→140→160 + clock tick + tinnitus
    #   BREAK       35-43s    absolute silence 1s, then piano C
    #   CTA         43-55s    warm pad, no heartbeat

    # --- HOOK + PATTERN (0-20s): AC hum bed + heartbeat 60bpm ---
    _add_audio_layer(scene, "ac-hum-25s.m4a", 0.0, 20.0, -20)
    _add_audio_layer(scene, "heartbeat-60bpm.m4a", 0.0, 20.0, -18)

    # --- ESCALATION early (20-25s): heartbeat 120bpm + clock tick ---
    _add_audio_layer(scene, "heartbeat-120bpm.m4a", 20.0, 5.0, -16)
    _add_audio_layer(scene, "clock-tick-15s.m4a", 20.0, 5.0, -20)

    # --- ESCALATION mid (25-30s): heartbeat 140bpm + clock tick ---
    _add_audio_layer(scene, "heartbeat-140bpm.m4a", 25.0, 5.0, -14)
    _add_audio_layer(scene, "clock-tick-15s.m4a", 25.0, 5.0, -18)

    # --- ESCALATION peak (30-35s): heartbeat 160bpm + tinnitus sweep ---
    _add_audio_layer(scene, "heartbeat-160bpm.m4a", 30.0, 5.0, -12)
    _add_audio_layer(scene, "tinnitus-8khz-5s.m4a", 30.0, 5.0, -22)

    # --- BREAK (35-36s silence, 36-43s piano C) ---
    _add_audio_layer(scene, "piano-c-note.mp3", 36.0, 7.0, -24)

    # --- CTA (43s → end): warm pad ---
    pad_dur = total_dur + 3.0 - 43.0
    if pad_dur > 0:
        _add_audio_layer(scene, "synth-pad-placeholder.mp3", 43.0, pad_dur, -22)


# --- Scene builder ---


def build_scene(config: dict) -> Composition:
    timeline, total_dur = build_timeline(config)

    # Add CTA tail
    cta_tail = 3.0
    final_dur = total_dur + cta_tail

    scene = Composition(size=(W, H), duration=final_dur)

    print(f"\nTimeline ({len(timeline)} shots, {final_dur:.1f}s total):")
    print(f"{'ID':>6} {'Offset':>7} {'Dur':>6} {'VO':>12} {'Clip':>8} {'Overlays':>20}")
    print("-" * 75)
    for e in timeline:
        vo_str = ",".join(e["vo_lines"]) if e["vo_lines"] else "-"
        clip_str = f"{e['clip_dur']:.1f}s" if e["clip_path"] else "NONE"
        ov_str = ",".join(o["type"] for o in e["overlays"]) if e["overlays"] else "-"
        print(f"{e['shot_id']:>6} {e['offset']:>7.1f}s {e['duration']:>5.1f}s "
              f"{vo_str:>12} {clip_str:>8} {ov_str:>20}")

    # Background
    bg = Rectangle(size=(W, H), color=(15, 15, 20), duration=final_dur)
    scene.add_layer(bg, name="background")

    # Add video + overlays for each shot
    for e in timeline:
        ts = e["offset"]
        dur = e["duration"]
        sid = e["shot_id"]

        # Video layer
        if e["clip_path"]:
            clip = Video(str(e["clip_path"]))
            c = _av.open(str(e["clip_path"]))
            vs = c.streams.video[0]
            vw, vh = vs.width, vs.height
            s = cover_scale(vw, vh)
            seek = 0.0
            scene.add_layer(
                clip, name=f"{sid}_vid", offset=ts,
                start_time=seek, end_time=seek + dur,
                scale=(s, s),
            )

        # Text overlays
        for ov in e["overlays"]:
            ov_type = ov["type"]
            if ov_type == "hook_text":
                _add_hook_text(scene, ts, dur, sid)
            elif ov_type == "badge":
                _add_badge(scene, ts, dur, sid, ov["text"])
            elif ov_type == "center_text":
                _add_center_text(scene, ts, dur, sid, ov["text"])
            elif ov_type == "flash":
                _add_flash_text(scene, ts, dur, sid, ov["text"])
            elif ov_type == "text_rain":
                _add_text_rain(scene, ts, dur, sid)
            elif ov_type == "slow_text":
                _add_slow_text(scene, ts, dur, sid, ov["text"])
            elif ov_type == "cta":
                _add_cta(scene, ts, dur, sid)

        # Voiceover — trim to shot boundary
        vo_offset = ts
        for vo_id in e["vo_lines"]:
            vo_path = VO_DIR / ORIGINAL_VIDEO_ID / f"{vo_id}.mp3"
            if vo_path.exists():
                vo = Audio(str(vo_path))
                vol = db2lin(SEGMENT_VOLUME_DB.get(vo_id, -5))
                remaining = max(0.0, (ts + dur) - vo_offset)
                vo_dur = get_vo_duration(ORIGINAL_VIDEO_ID, vo_id)
                vo_end = min(vo_dur, remaining)
                scene.add_layer(vo, name=f"{sid}_{vo_id}", offset=vo_offset,
                                end_time=vo_end, audio_level=vol)
                vo_offset += vo_end

    # CTA tail
    _add_cta(scene, total_dur, cta_tail, "tail")

    # BGM
    _add_bgm(scene, final_dur)

    return scene


# --- Main ---


def main() -> None:
    parser = argparse.ArgumentParser(description="B+ Repeat Blast AI (Kling I2V)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    vid = config["video_id"]

    print(f"B+ Repeat Blast AI — {vid}")
    print("=" * 50)

    out = OUTPUT_DIR / vid
    out.mkdir(parents=True, exist_ok=True)
    of = out / f"{vid}-rough-cut.mp4"

    if args.dry_run:
        timeline, total = build_timeline(config)
        final = total + 3.0
        print(f"\nFinal duration: {final:.1f}s")
        print(f"\nTimeline ({len(timeline)} shots, {final:.1f}s total):")
        print(f"{'ID':>6} {'Offset':>7} {'Dur':>6} {'VO':>12} {'Clip':>8} {'Overlays':>20}")
        print("-" * 75)
        for e in timeline:
            vo_str = ",".join(e["vo_lines"]) + f" ({e['vo_total_dur']:.1f}s)" if e["vo_lines"] else "-"
            clip_str = f"{e['clip_dur']:.1f}s" if e["clip_path"] else "NONE"
            ov_str = ",".join(o["type"] for o in e["overlays"]) if e["overlays"] else "-"
            print(f"{e['shot_id']:>6} {e['offset']:>7.1f}s {e['duration']:>5.1f}s "
                  f"{vo_str:>12} {clip_str:>8} {ov_str:>20}")
        print("DRY RUN — skipping render")
        return

    scene = build_scene(config)
    final_dur = scene.duration
    print(f"\nFinal: {final_dur:.1f}s, {W}x{H}")
    print(f"Layers: {len(scene.keys())}")

    print("Rendering...")
    scene.write_video(
        str(of), codec="libx264", fps=24.0, audio=True,
        output_params=["-b:v", "5500k", "-maxrate", "6000k", "-bufsize", "12000k", "-preset", "slow"],
    )
    mb = of.stat().st_size / 1024 / 1024
    print(f"\nDone: {of} ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
