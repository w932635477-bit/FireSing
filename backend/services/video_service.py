"""Video service — DAW multi-track style video generator.

V1: Multi-track static layout + mixed audio waveform.
Visual language: audio editing software (DAW) multi-track view.
Each singer = one horizontal track with colored blocks at their segment positions.
Single showwaves waveform from mixed audio at bottom.
Blurred background image, ASS lyrics, progress bar.

Rendering pipeline:
  1. Extract cover art from audio ID3 → gblur → background
  2. PIL: base frame = background + tracks + labels + title
  3. FFmpeg: base frame (looped) + showwaves waveform + ASS + audio → MP4
  Target: 20-30s rendering time.
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

    # Step 3: ASS subtitles (lyrics + progress bar)
    ass = _gen_ass(segments, voice_info, song.title or "FireSing", song_id, duration)

    # Step 4: render (base looped + showwaves waveform + ASS + audio)
    final = out_dir / "final.mp4"
    _render(base, audio_path, ass, final, duration)

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

    # Cleanup temp files
    for p in [base, ass]:
        p.unlink(missing_ok=True)

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
# Step 3: ASS subtitles
# ---------------------------------------------------------------------------

def _gen_ass(
    segments: list, voice_info: dict, title: str,
    song_id: str, duration: float,
) -> Path:
    """ASS file: per-line lyrics highlight + progress bar."""
    p = OUTPUTS_DIR / song_id / "sub.ass"
    p.parent.mkdir(parents=True, exist_ok=True)

    def esc(t):
        return (t.replace("\\", "\\\\").replace("{", "\\{")
                 .replace("}", "\\}").replace("\n", "\\N"))

    lyrics_y = H - LYRICS_H - PROGRESS_H + 50
    lines = [
        "[Script Info]", "Title: FireSing", "ScriptType: v4.00+",
        f"PlayResX: {W}", f"PlayResY: {H}",
        "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        # Title style
        f"Style: Title,PingFang SC,40,&H40FFFFFF,&H000000FF,&H00000000,"
        f"&HC0000000,-1,0,0,0,100,100,2,0,1,2,0,8,80,80,30,1",
        # Lyrics (current line, bright)
        f"Style: Lyrics,PingFang SC,46,&H00FFFFFF,&H000000FF,&H00000000,"
        f"&HB0000000,-1,0,0,0,100,100,2,0,1,3,1,2,80,80,80,1",
        # Dim (progress bar text)
        f"Style: Dim,PingFang SC,20,&H60FFFFFF,&H000000FF,&H00000000,"
        f"&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,50,50,20,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, "
        "MarginV, Effect, Text",
    ]

    # Title (fade in/out over first 4 seconds)
    lines.append(
        f"Dialogue: 0,{_f(0)},{_f(4)},Title,,0,0,0,,"
        f"{{\\fad(500,500)\\pos({W // 2},60)}}{esc(title)}"
    )

    # Lyrics: one dialogue per segment
    for seg in segments:
        if not seg.text or not seg.text.strip():
            continue
        txt = esc(seg.text.strip())
        s, e = seg.start_time, seg.end_time
        lines.append(
            f"Dialogue: 2,{_f(s)},{_f(e)},Lyrics,,0,0,0,,"
            f"{{\\pos({W // 2},{lyrics_y})\\fad(200,200)}}{txt}"
        )

    # Progress bar (update every 5%)
    progress_y = H - 25
    ticks = 20
    for t in range(ticks + 1):
        ts = t / ticks * duration
        te = min((t + 1) / ticks * duration, duration)
        bar = "\u2501" * t + "\u257a" + "\u2574" * (ticks - t)
        pct = f"{t * 5}%"
        lines.append(
            f"Dialogue: 5,{_f(ts)},{_f(te)},Dim,,0,0,0,,"
            f"{{\\pos({W // 2},{progress_y})}}{bar} {pct}"
        )

    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Step 4: FFmpeg rendering
# ---------------------------------------------------------------------------

def _render(
    base: Path, audio: Path, ass_path: Path,
    output: Path, duration: float,
) -> None:
    """FFmpeg: base frame + showwaves waveform overlay + ASS + audio."""
    # Escape path for filter_complex (colons and backslashes)
    ass_esc = str(ass_path).replace("\\", "\\\\\\\\").replace(":", "\\\\:")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(base),
        "-i", str(audio),
        "-filter_complex",
        (
            f"[1:a]showwaves=s={W}x{WAVEFORM_H}:rate={FPS}"
            f":colors=0x39FF14@0.5:mode=cline:scale=sqrt[wave];"
            f"[0:v][wave]overlay=0:{WAVEFORM_Y}:format=auto[tmp];"
            f"[tmp]ass={ass_esc}[out]"
        ),
        "-map", "[out]", "-map", "1:a",
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
            _render_no_wave(base, audio, ass_path, output, duration)
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Video rendering timed out (600s limit)")


def _render_no_wave(
    base: Path, audio: Path, ass_path: Path,
    output: Path, duration: float,
) -> None:
    """Fallback: static frame + ASS, no waveform."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(base),
        "-i", str(audio),
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-t", f"{duration:.3f}",
        "-shortest", "-movflags", "+faststart",
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
