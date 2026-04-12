"""Video service — relay chorus style video generator.

Visual language: Douyin relay chorus (接力合唱).
Each singer appears one at a time with avatar + name + lyrics.
When singer changes, new singer fades in smoothly.

Rendering pipeline (no libass needed):
  1. Extract cover art from audio ID3 → gblur → background
  2. PIL: base frame = background + dark overlay
  3. PIL: generate overlay frames for avatar + name + lyrics + progress at 2fps
  4. FFmpeg: overlays + showwaves waveform + audio → MP4
Target: 30-60s rendering time for ~3min song.
"""

import logging
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from sqlalchemy.orm import Session

from ..config import OUTPUTS_DIR
from ..models import Song, Segment, Output, VoiceModel

logger = logging.getLogger(__name__)

# --- Video dimensions ---
W, H = 1080, 1920
FPS = 30

# --- Layout zones (relay chorus style) ---
TITLE_Y = 80
AVATAR_SIZE = 280
AVATAR_BORDER = 6
AVATAR_CY = 580
NAME_Y = 760
LYRICS_Y = 920
LYRICS_PAD_X = 30
LYRICS_PAD_Y = 15
WAVEFORM_H = 180
LYRICS_H = 140
PROGRESS_H = 50
WAVEFORM_Y = H - LYRICS_H - PROGRESS_H - WAVEFORM_H  # ~1550
PROGRESS_BAR_W = 600
PROGRESS_BAR_Y = H - 25
FADE_DURATION = 0.5
TITLE_FADE_OUT = 4.0

# --- Alpha values ---
OVERLAY_ALPHA = 160

# --- Overlay frame rate ---
OVERLAY_FPS = 1  # frames per second for dynamic content (1fps saves 50% PIL + I/O time)

# --- Voice colors (one per unique singer) ---
VOICE_COLORS = [
    "#FF6B6B", "#4ECDC4", "#B745D1", "#FFB347",
    "#87CEEB", "#FF69B4", "#98FB98", "#DDA0DD",
    "#FFD700", "#00CED1", "#FF4500", "#7B68EE",
    "#32CD32", "#FF1493", "#00FA9A",
]


def generate(song_id: str, db: Session) -> Path:
    """Generate 1080x1920 relay chorus video. Returns path to MP4."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")

    audio_out = db.query(Output).filter(
        Output.song_id == song_id, Output.format == "audio"
    ).first()
    if not audio_out or not Path(audio_out.file_path).exists():
        raise ValueError(f"Song {song_id} has no mixed audio")

    audio_path = Path(audio_out.file_path)
    duration = _audio_dur(audio_path)

    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )

    voice_info = _build_voice_info(segments, db)

    out_dir = OUTPUTS_DIR / song_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: background (cover art + blur, or dark gradient)
    bg = _prepare_bg(audio_path, out_dir)

    # Step 2: base frame (bg + dark overlay only, no tracks)
    base = _draw_static_bg(bg, out_dir)

    # Step 3: generate overlay frames (avatar + name + lyrics + progress)
    overlay_dir = _gen_overlay_frames(
        segments, voice_info, duration, song.title or "FireSing", out_dir,
    )

    # Step 4: render (overlays + showwaves waveform + audio → MP4)
    final = out_dir / "final.mp4"
    _render(base, overlay_dir, audio_path, final, duration)

    # Cleanup temp files
    base.unlink(missing_ok=True)
    _cleanup_dir(overlay_dir)

    # Step 5: update DB
    fsize = final.stat().st_size
    existing = db.query(Output).filter(
        Output.song_id == song_id, Output.format == "video"
    ).first()
    if existing:
        existing.file_path = str(final)
        existing.file_size = fsize
        existing.duration = audio_out.duration
    else:
        db.add(Output(
            song_id=song_id, format="video",
            file_path=str(final), file_size=fsize,
            duration=audio_out.duration,
        ))
    db.commit()

    logger.info(f"Video: {final} ({fsize/1024/1024:.1f}MB)")
    return final


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _build_voice_info(segments: list, db: Session) -> dict:
    """Map voice_model_id -> {name, color}."""
    vids = list(dict.fromkeys(s.voice_model_id for s in segments if s.voice_model_id))
    voice_models = {
        vm.id: vm for vm in db.query(VoiceModel).filter(VoiceModel.id.in_(vids)).all()
    }
    info = {}
    for i, vid in enumerate(vids):
        vm = voice_models.get(vid)
        info[vid] = {
            "name": vm.name if vm else f"Voice {i + 1}",
            "color": VOICE_COLORS[i % len(VOICE_COLORS)],
        }
    return info


def _build_segment_timeline(
    segments: list, voice_info: dict,
) -> list[tuple]:
    """Build sorted timeline of (start, end, text, voice_id, name, color)."""
    timeline = []
    for s in segments:
        if not s.voice_model_id or s.voice_model_id not in voice_info:
            continue
        vi = voice_info[s.voice_model_id]
        text = s.text.strip() if s.text else ""
        timeline.append((
            s.start_time, s.end_time, text,
            s.voice_model_id, vi["name"], vi["color"],
        ))
    timeline.sort(key=lambda x: x[0])
    return timeline


def _get_active_singer(
    timeline: list, t: float,
) -> tuple:
    """Return (voice_id, name, color, lyric) for time t, or Nones."""
    best = None
    for start, end, text, vid, name, color in timeline:
        if start <= t < end:
            if best is None or start > best[0]:
                best = (start, end, text, vid, name, color)
    if best:
        return best[3], best[4], best[5], best[2]
    return None, None, None, None


def _compute_transitions(timeline: list) -> list[float]:
    """Return list of times where singer changes."""
    transitions = []
    prev_vid = None
    for start, end, text, vid, name, color in timeline:
        if prev_vid is not None and vid != prev_vid:
            transitions.append(start)
        prev_vid = vid
    return transitions


def _compute_singer_alpha(
    t: float, transitions: list[float], fade_duration: float = FADE_DURATION,
) -> int:
    """Alpha for singer avatar/name at time t. Fades in at transitions."""
    half = fade_duration / 2
    for trans_time in transitions:
        if trans_time <= t < trans_time + half:
            return int(255 * (t - trans_time) / half)
    return 255


# ---------------------------------------------------------------------------
# Step 1: Background
# ---------------------------------------------------------------------------

def _prepare_bg(audio_path: Path, out_dir: Path) -> Path:
    """Extract cover art from audio, blur it. Fallback: dark gradient."""
    bg = out_dir / "bg.png"

    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0",
             str(audio_path)],
            capture_output=True, text=True, timeout=10,
        )
        if "video" in probe.stdout:
            cover = out_dir / "_cover.png"
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", str(audio_path),
                 "-an", "-vcodec", "copy", str(cover)],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0 and cover.exists():
                subprocess.run([
                    "ffmpeg", "-y", "-i", str(cover),
                    "-vf",
                    f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},gblur=sigma=25",
                    str(bg),
                ], capture_output=True, text=True, timeout=30)
                cover.unlink(missing_ok=True)
                if bg.exists():
                    return bg
    except Exception as e:
        logger.debug(f"Cover art extraction skipped: {e}")

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"gradients=s={W}x{H}:c0=0x080818:c1=0x180828:duration=1",
        "-frames:v", "1", str(bg),
    ], capture_output=True, text=True, timeout=30)

    if not bg.exists():
        Image.new("RGB", (W, H), (8, 8, 24)).save(str(bg))

    return bg


# ---------------------------------------------------------------------------
# Step 2: Base frame (PIL) — static background only
# ---------------------------------------------------------------------------

def _draw_static_bg(bg_path: Path, out_dir: Path) -> Path:
    """Create base frame: blurred background + semi-transparent dark overlay."""
    img = Image.open(str(bg_path)).convert("RGBA")
    dark = Image.new("RGBA", (W, H), (0, 0, 0, OVERLAY_ALPHA))
    img = Image.alpha_composite(img, dark)

    path = out_dir / "base_frame.png"
    img.save(str(path), "PNG")
    return path


# ---------------------------------------------------------------------------
# Step 3: Overlay frames (relay chorus style via PIL)
# ---------------------------------------------------------------------------

def _draw_avatar(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int, radius: int,
    name: str, color_hex: str, alpha: int = 255,
) -> None:
    """Draw circular avatar with voice-color border and name initial."""
    rgb = _hex2rgb(color_hex)
    # Lighter tint for fill
    lighter = tuple(min(255, c + 80) for c in rgb)

    # Outer circle (border color)
    r = radius
    b = AVATAR_BORDER
    draw.ellipse(
        [(cx - r - b, cy - r - b), (cx + r + b, cy + r + b)],
        fill=(*rgb, alpha),
    )
    # Inner circle (lighter fill)
    draw.ellipse(
        [(cx - r, cy - r), (cx + r, cy + r)],
        fill=(*lighter, alpha),
    )
    # Initial character
    ch = name[0] if name else "?"
    font = _font(int(radius * 0.85))
    draw.text((cx, cy), ch, fill=(255, 255, 255, alpha), font=font, anchor="mm")


def _gen_overlay_frames(
    segments: list, voice_info: dict,
    duration: float, title: str, out_dir: Path,
) -> Path:
    """Generate relay-style overlay frames at OVERLAY_FPS.

    Each frame shows the current singer's avatar + name + lyrics + progress bar.
    When singer changes, the new singer fades in over FADE_DURATION.
    """
    overlay_dir = out_dir / "overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    font_title = _font(40)
    font_lyrics = _font(46)
    font_name = _font(32)
    font_progress = _font(20)

    timeline = _build_segment_timeline(segments, voice_info)
    transitions = _compute_transitions(timeline)

    total_frames = int(duration * OVERLAY_FPS) + 1
    for i in range(total_frames):
        t = i / OVERLAY_FPS
        if t > duration:
            break

        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        # --- Title fade (first 4 seconds) ---
        if t < TITLE_FADE_OUT:
            alpha = 255
            if t < 0.5:
                alpha = int(255 * t / 0.5)
            elif t > 3.5:
                alpha = int(255 * (TITLE_FADE_OUT - t) / 0.5)
            if alpha > 0:
                draw.text((W // 2, TITLE_Y), title,
                          fill=(255, 255, 255, alpha),
                          font=font_title, anchor="mm")

        # --- Current singer ---
        voice_id, name, color, lyric = _get_active_singer(timeline, t)

        if voice_id:
            singer_alpha = _compute_singer_alpha(t, transitions)

            # Avatar
            _draw_avatar(
                draw, W // 2, AVATAR_CY,
                AVATAR_SIZE // 2, name, color, alpha=singer_alpha,
            )

            # Singer name
            rgb = _hex2rgb(color)
            draw.text((W // 2, NAME_Y), name,
                      fill=(*rgb, singer_alpha),
                      font=font_name, anchor="mm")

            # Lyrics
            if lyric:
                bbox = draw.textbbox((0, 0), lyric, font=font_lyrics)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                rx1 = (W - tw) // 2 - LYRICS_PAD_X
                ry1 = LYRICS_Y - th // 2 - LYRICS_PAD_Y
                rx2 = (W + tw) // 2 + LYRICS_PAD_X
                ry2 = LYRICS_Y + th // 2 + LYRICS_PAD_Y
                draw.rounded_rectangle(
                    [(rx1, ry1), (rx2, ry2)], radius=12,
                    fill=(0, 0, 0, 160),
                )
                draw.text((W // 2, LYRICS_Y), lyric,
                          fill=(255, 255, 255, 240),
                          font=font_lyrics, anchor="mm")

        # --- Progress bar ---
        pct = t / duration if duration > 0 else 0
        filled = int(PROGRESS_BAR_W * pct)
        bar_x = (W - PROGRESS_BAR_W) // 2
        draw.rounded_rectangle(
            [(bar_x, PROGRESS_BAR_Y - 4), (bar_x + PROGRESS_BAR_W, PROGRESS_BAR_Y + 4)],
            radius=4, fill=(255, 255, 255, 30),
        )
        if filled > 0:
            draw.rounded_rectangle(
                [(bar_x, PROGRESS_BAR_Y - 4), (bar_x + filled, PROGRESS_BAR_Y + 4)],
                radius=4, fill=(57, 255, 20, 180),
            )
        pct_text = f"{int(pct * 100)}%"
        draw.text((bar_x + PROGRESS_BAR_W + 15, PROGRESS_BAR_Y), pct_text,
                  fill=(255, 255, 255, 100), font=font_progress, anchor="lm")

        frame.save(str(overlay_dir / f"frame_{i:06d}.png"), "PNG")

    logger.info(f"Generated {total_frames} overlay frames at {OVERLAY_FPS}fps")
    return overlay_dir


# ---------------------------------------------------------------------------
# Step 4: FFmpeg rendering
# ---------------------------------------------------------------------------

def _render(
    base: Path, overlay_dir: Path, audio: Path,
    output: Path, duration: float,
) -> None:
    """FFmpeg: base frame + overlay frames + showwaves waveform + audio → MP4."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(base),
        "-framerate", str(OVERLAY_FPS),
        "-i", str(overlay_dir / "frame_%06d.png"),
        "-i", str(audio),
        "-filter_complex",
        (
            f"[1:v]fps={FPS}[overlay];"
            f"[2:a]showwaves=s={W}x{WAVEFORM_H}:rate={FPS}"
            f":colors=0x39FF14@0.5:mode=cline:scale=sqrt[wave];"
            f"[0:v][overlay]overlay=0:0:format=auto[merged];"
            f"[merged][wave]overlay=0:{WAVEFORM_Y}:format=auto[out]"
        ),
        "-map", "[out]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        str(output),
    ]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            logger.warning(f"showwaves failed, fallback: {r.stderr[-300:]}")
            _render_static(base, overlay_dir, audio, output, duration)
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Video rendering timed out (600s limit)")


def _render_static(
    base: Path, overlay_dir: Path, audio: Path,
    output: Path, duration: float,
) -> None:
    """Fallback: base + overlays, no waveform."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(base),
        "-framerate", str(OVERLAY_FPS),
        "-i", str(overlay_dir / "frame_%06d.png"),
        "-i", str(audio),
        "-filter_complex",
        (
            f"[1:v]fps={FPS}[overlay];"
            f"[0:v][overlay]overlay=0:0:format=auto[out]"
        ),
        "-map", "[out]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.3f}",
        "-movflags", "+faststart",
        str(output),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {r.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Video rendering timed out (600s limit)")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _audio_dur(p: Path) -> float:
    """Audio duration in seconds via ffprobe."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=30,
        )
        return float(r.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return 180.0


def _hex2rgb(h: str) -> tuple:
    """Hex color string -> (R, G, B)."""
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _font(size: int) -> ImageFont.FreeTypeFont:
    """Load system font, fallback to default."""
    for p in [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _cleanup_dir(d: Path) -> None:
    """Remove a directory and all its contents."""
    if d.exists():
        for f in d.iterdir():
            f.unlink(missing_ok=True)
        d.rmdir()
