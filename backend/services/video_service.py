"""Video service — DAW multi-track style video generator.

V1: Multi-track static layout + mixed audio waveform.
Visual language: audio editing software (DAW) multi-track view.
Each singer = one horizontal track with colored blocks at their segment positions.
Single showwaves waveform from mixed audio at bottom.
Blurred background image, PIL-rendered lyrics + progress bar.

Rendering pipeline (no libass needed):
  1. Extract cover art from audio ID3 → gblur → background
  2. PIL: base frame = background + tracks + labels + title
  3. PIL: generate overlay frames for lyrics + progress at 2fps
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

# --- Layout zones (pixels, top-down) ---
TITLE_H = 120
WAVEFORM_H = 180
LYRICS_H = 140
PROGRESS_H = 50
WAVEFORM_Y = H - LYRICS_H - PROGRESS_H - WAVEFORM_H  # ~1550
TRACK_TOP = TITLE_H + 10
TRACK_BOT = WAVEFORM_Y - 15
TRACK_AREA = TRACK_BOT - TRACK_TOP  # ~1405

TRACK_MIN = 70
TRACK_MAX = 200
TRACK_GAP = 4
LABEL_W = 220
BLOCK_PAD = 6

# --- Alpha values ---
OVERLAY_ALPHA = 160
BLOCK_ALPHA = 180
ROW_ALPHA = 35

# --- Voice colors (one per unique singer) ---
MAX_TRACKS = 15
OTHER_COLOR = "#808080"

VOICE_COLORS = [
    "#FF6B6B", "#4ECDC4", "#B745D1", "#FFB347",
    "#87CEEB", "#FF69B4", "#98FB98", "#DDA0DD",
    "#FFD700", "#00CED1", "#FF4500", "#7B68EE",
    "#32CD32", "#FF1493", "#00FA9A",
]


def generate(song_id: str, db: Session) -> Path:
    """Generate 1080x1920 DAW multi-track video. Returns path to MP4."""
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
    tracks = _build_tracks(segments, voice_info)

    out_dir = OUTPUTS_DIR / song_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: background (cover art + blur, or dark gradient)
    bg = _prepare_bg(audio_path, out_dir)

    # Step 2: base frame (bg + tracks + labels + title as PNG)
    base = _draw_base_frame(bg, tracks, song.title or "FireSing", duration, out_dir)

    # Step 3: generate overlay frames with lyrics + progress (PIL, no ASS needed)
    overlay_dir = _gen_overlay_frames(segments, duration, song.title or "FireSing", out_dir)

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
    # Single query instead of N queries
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


def _build_tracks(segments: list, voice_info: dict) -> list:
    """One track per unique voice, capped at MAX_TRACKS. Optional harmony track."""
    vids = list(dict.fromkeys(s.voice_model_id for s in segments if s.voice_model_id))
    tracks = []

    if len(vids) > MAX_TRACKS:
        # Cap: first MAX_TRACKS-1 get own tracks, rest merged into "其他"
        shown = vids[: MAX_TRACKS - 1]
        merged_ids = vids[MAX_TRACKS - 1 :]
        for vid in shown:
            segs = [s for s in segments if s.voice_model_id == vid]
            tracks.append({
                "id": vid,
                "name": voice_info[vid]["name"],
                "color": voice_info[vid]["color"],
                "segments": segs,
            })
        merged_segs = [s for s in segments if s.voice_model_id in merged_ids]
        tracks.append({
            "id": "other", "name": "其他",
            "color": OTHER_COLOR, "segments": merged_segs,
        })
    else:
        for vid in vids:
            segs = [s for s in segments if s.voice_model_id == vid]
            tracks.append({
                "id": vid,
                "name": voice_info[vid]["name"],
                "color": voice_info[vid]["color"],
                "segments": segs,
            })

    # Harmony track (if segments carry harmony marker)
    harmony = [s for s in segments if getattr(s, "harmony_voices", None)]
    if harmony:
        tracks.append({
            "id": "harmony", "name": "\u548c\u58f0",
            "color": "#9B59B6", "segments": harmony,
        })

    return tracks


# ---------------------------------------------------------------------------
# Step 1: Background
# ---------------------------------------------------------------------------

def _prepare_bg(audio_path: Path, out_dir: Path) -> Path:
    """Extract cover art from audio, blur it. Fallback: dark gradient."""
    bg = out_dir / "bg.png"

    # Try extracting embedded cover art
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

    # Fallback: dark gradient
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"gradients=s={W}x{H}:c0=0x080818:c1=0x180828:duration=1",
        "-frames:v", "1", str(bg),
    ], capture_output=True, text=True, timeout=30)

    if not bg.exists():
        Image.new("RGB", (W, H), (8, 8, 24)).save(str(bg))

    return bg


# ---------------------------------------------------------------------------
# Step 2: Base frame (PIL)
# ---------------------------------------------------------------------------

def _draw_base_frame(
    bg_path: Path, tracks: list, title: str,
    duration: float, out_dir: Path,
) -> Path:
    """Compose background + dark overlay + title + track blocks + singer labels."""
    img = Image.open(str(bg_path)).convert("RGBA")

    # Semi-transparent dark overlay for readability
    dark = Image.new("RGBA", (W, H), (0, 0, 0, OVERLAY_ALPHA))
    img = Image.alpha_composite(img, dark)

    draw = ImageDraw.Draw(img)
    font_title = _font(40)
    font_label = _font(26)

    # Title
    draw.text((W // 2, 60), title, fill=(255, 255, 255, 220),
              font=font_title, anchor="mm")

    # Track layout
    n = max(len(tracks), 1)
    th = max(TRACK_MIN, min(TRACK_MAX, (TRACK_AREA - (n - 1) * TRACK_GAP) // n))
    left = LABEL_W + 10
    tw = W - left - 15

    for i, t in enumerate(tracks):
        y = TRACK_TOP + i * (th + TRACK_GAP)
        rgb = _hex2rgb(t["color"])

        # Row background
        draw.rounded_rectangle(
            [(8, y), (W - 8, y + th)], radius=5,
            fill=(255, 255, 255, ROW_ALPHA),
        )

        # Label: colored dot + name
        cy = y + th // 2
        r = 8
        draw.ellipse([(18, cy - r), (18 + r * 2, cy + r)], fill=(*rgb, 255))
        draw.text((42, cy), t["name"], fill=(*rgb, 230),
                  font=font_label, anchor="lm")

        # Segment blocks (positioned by time on x-axis)
        for seg in t["segments"]:
            if duration <= 0:
                continue
            x1 = left + int(seg.start_time / duration * tw)
            x2 = left + int(seg.end_time / duration * tw)
            x1 = max(left, min(x1, W - 8))
            x2 = max(left, min(x2, W - 8))
            if x2 > x1:
                draw.rounded_rectangle(
                    [(x1, y + BLOCK_PAD), (x2, y + th - BLOCK_PAD)],
                    radius=3, fill=(*rgb, BLOCK_ALPHA),
                )

    # Separator lines
    draw.line([(15, WAVEFORM_Y - 8), (W - 15, WAVEFORM_Y - 8)],
              fill=(255, 255, 255, 25), width=1)
    lyrics_sep = H - LYRICS_H - PROGRESS_H
    draw.line([(15, lyrics_sep - 8), (W - 15, lyrics_sep - 8)],
              fill=(255, 255, 255, 25), width=1)

    path = out_dir / "base_frame.png"
    img.save(str(path), "PNG")
    return path


# ---------------------------------------------------------------------------
# Step 3: Overlay frames (lyrics + progress bar via PIL)
# ---------------------------------------------------------------------------

OVERLAY_FPS = 2  # frames per second for lyrics/progress overlay


def _gen_overlay_frames(
    segments: list, duration: float, title: str, out_dir: Path,
) -> Path:
    """Generate transparent PNG frames with lyrics text and progress bar.

    Creates frames at OVERLAY_FPS (2fps) — enough for smooth lyrics transitions.
    Each frame is a transparent PNG with only the lyrics text and progress bar drawn.
    FFmpeg will composite these over the base frame.
    """
    overlay_dir = out_dir / "overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)

    font_lyrics = _font(46)
    font_progress = _font(20)

    # Build segment lookup: for any time t, find the active lyric
    lyrics_segs = [(s.start_time, s.end_time, s.text.strip()) for s in segments
                   if s.text and s.text.strip()]

    lyrics_y = H - LYRICS_H - PROGRESS_H + 50
    progress_y = H - 25
    bar_w = 600

    total_frames = int(duration * OVERLAY_FPS) + 1
    for i in range(total_frames):
        t = i / OVERLAY_FPS
        if t > duration:
            break

        # Transparent overlay
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        # Title fade (first 4 seconds)
        if t < 4.0:
            alpha = 255
            if t < 0.5:
                alpha = int(255 * t / 0.5)
            elif t > 3.5:
                alpha = int(255 * (4.0 - t) / 0.5)
            if alpha > 0:
                draw.text((W // 2, 60), title,
                          fill=(255, 255, 255, alpha),
                          font=_font(40), anchor="mm")

        # Find current lyric
        current_lyric = ""
        for start, end, text in lyrics_segs:
            if start <= t < end:
                current_lyric = text
                break

        if current_lyric:
            # Lyrics background (semi-transparent black pill)
            bbox = draw.textbbox((0, 0), current_lyric, font=font_lyrics)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pad_x, pad_y = 30, 15
            rx1 = (W - tw) // 2 - pad_x
            ry1 = lyrics_y - th // 2 - pad_y
            rx2 = (W + tw) // 2 + pad_x
            ry2 = lyrics_y + th // 2 + pad_y
            draw.rounded_rectangle(
                [(rx1, ry1), (rx2, ry2)], radius=12,
                fill=(0, 0, 0, 160),
            )
            draw.text((W // 2, lyrics_y), current_lyric,
                      fill=(255, 255, 255, 240),
                      font=font_lyrics, anchor="mm")

        # Progress bar
        pct = t / duration if duration > 0 else 0
        filled = int(bar_w * pct)
        bar_x = (W - bar_w) // 2
        # Background track
        draw.rounded_rectangle(
            [(bar_x, progress_y - 4), (bar_x + bar_w, progress_y + 4)],
            radius=4, fill=(255, 255, 255, 30),
        )
        # Filled portion
        if filled > 0:
            draw.rounded_rectangle(
                [(bar_x, progress_y - 4), (bar_x + filled, progress_y + 4)],
                radius=4, fill=(57, 255, 20, 180),
            )
        # Percentage text
        pct_text = f"{int(pct * 100)}%"
        draw.text((bar_x + bar_w + 15, progress_y), pct_text,
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
    # Try with showwaves first
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
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
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
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
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


def _f(s: float) -> str:
    """Format seconds as ASS timestamp H:MM:SS.CC."""
    h, rem = divmod(int(s), 3600)
    m, sec = divmod(rem, 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"


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
