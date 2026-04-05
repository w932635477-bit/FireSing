"""Video service — generate Douyin-style vertical video with ASS subtitles via FFmpeg.

DESIGN.md Step 7: Generate 9:16 vertical video mimicking Douyin (TikTok China) style.
Features:
- Gradient background (not plain black)
- Song title overlay at top
- ASS subtitles with per-voice colors positioned in lower third
- FFmpeg renders with looped background image
"""

import logging
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import OUTPUTS_DIR
from ..models import Song, Segment, Output

logger = logging.getLogger(__name__)

# Video parameters
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Douyin-style color palette (BGR format for ASS)
ASS_COLORS = [
    "&H6B6BFF",  # Coral red (#FF6B6B)
    "&HCE4EC4",  # Teal (#4ECDC4)
    "&HD145B7",  # Purple (#B745D1)
    "&HCE964E",  # Orange (#4E96CE)
    "&HA7EEFF",  # Pink (#FFEEA7)
    "&HFF6633",  # Cyan (#3366FF)
    "&H99CC66",  # Green (#66CC99)
    "&H6699FF",  # Salmon (#FF9966)
]

# Background gradient colors (hex for FFmpeg)
BG_COLOR_TOP = "0x0a0a0f"
BG_COLOR_BOTTOM = "0x1a0a1a"


def generate(song_id: str, db: Session) -> Path:
    """Generate 1080x1920 Douyin-style video with ASS subtitles.

    Returns path to generated MP4 file.
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")

    # Get audio output
    audio_output = db.query(Output).filter(
        Output.song_id == song_id, Output.format == "audio"
    ).first()
    if not audio_output or not Path(audio_output.file_path).exists():
        raise ValueError(f"Song {song_id} has no mixed audio output")

    # Get segments with voice assignments
    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )

    # Map unique voice_model_ids to colors (order-stable)
    unique_voices = list(dict.fromkeys(s.voice_model_id for s in segments if s.voice_model_id))
    voice_color_map = {vid: ASS_COLORS[i % len(ASS_COLORS)] for i, vid in enumerate(unique_voices)}

    # Get audio duration
    audio_path = Path(audio_output.file_path)
    audio_duration = _get_audio_duration(audio_path)

    # Generate ASS subtitle file (Douyin-style positioning)
    ass_path = _generate_ass(segments, voice_color_map, song_id)

    # Generate gradient background image
    bg_path = _generate_background(song.title or "FireSing", song_id)

    # Render video
    output_dir = OUTPUTS_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "final.mp4"

    _render_video(
        bg_path=bg_path,
        audio_path=audio_path,
        ass_path=ass_path,
        output_path=output_path,
        audio_duration=audio_duration,
    )

    # Create or update Output record
    file_size = output_path.stat().st_size
    duration = audio_output.duration

    existing = db.query(Output).filter(
        Output.song_id == song_id, Output.format == "video"
    ).first()

    if existing:
        existing.file_path = str(output_path)
        existing.file_size = file_size
        existing.duration = duration
    else:
        video_output = Output(
            song_id=song_id,
            format="video",
            file_path=str(output_path),
            file_size=file_size,
            duration=duration,
        )
        db.add(video_output)

    db.commit()

    # Cleanup temp files
    ass_path.unlink(missing_ok=True)

    logger.info(f"Video generated: {output_path} ({file_size / 1024 / 1024:.1f}MB)")
    return output_path


def _get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.TimeoutExpired, FileNotFoundError):
        return 180.0  # fallback 3 minutes


def _generate_background(title: str, song_id: str) -> Path:
    """Generate Douyin-style gradient background with title overlay."""
    output_dir = OUTPUTS_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    bg_path = output_dir / "background.png"

    # Escape special characters for FFmpeg drawtext
    safe_title = title.replace("'", "'\\''").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i",
        f"gradients=s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:c0={BG_COLOR_TOP}:c1={BG_COLOR_BOTTOM}:duration=1",
        "-frames:v", "1",
        "-vf", (
            f"drawtext=text='{safe_title}':"
            f"fontsize=42:fontcolor=white:"
            f"x=(w-text_w)/2:y=200:"
            f"borderw=2:bordercolor=black@0.5,"
            f"drawtext=text='FireSing':"
            f"fontsize=24:fontcolor=white@0.3:"
            f"x=(w-text_w)/2:y=260"
        ),
        str(bg_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            # Fallback: simple dark background if gradient filter or font unavailable
            logger.warning(f"Gradient bg failed, falling back: {result.stderr[-200:]}")
            cmd_simple = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i",
                f"color=c=0x0a0a0f:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d=1",
                "-frames:v", "1", str(bg_path),
            ]
            subprocess.run(cmd_simple, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")

    return bg_path


def _generate_ass(segments: list, voice_color_map: dict, song_id: str) -> Path:
    """Generate ASS subtitle file with per-voice colors, positioned for Douyin style."""
    ass_path = OUTPUTS_DIR / song_id / "subtitles.ass"
    ass_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "[Script Info]",
        "Title: FireSing",
        "ScriptType: v4.00+",
        f"PlayResX: {VIDEO_WIDTH}",
        f"PlayResY: {VIDEO_HEIGHT}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Lead vocal: bold, positioned lower-center (alignment 2 = bottom-center)
        "Style: Default,PingFang SC,56,&H00FFFFFF,&H000000FF,&H00000000,&HC0000000,-1,0,0,0,100,100,2,0,1,3,1,2,80,80,120,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for seg in segments:
        start = _format_ass_time(seg.start_time)
        end = _format_ass_time(seg.end_time)
        color = voice_color_map.get(seg.voice_model_id, "&H00FFFFFF") if seg.voice_model_id else "&H00FFFFFF"
        text = seg.text
        lines.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\c{color}}}{text}"
        )

    ass_path.write_text("\n".join(lines), encoding="utf-8")
    return ass_path


def _format_ass_time(seconds: float) -> str:
    """Format seconds as ASS timestamp: H:MM:SS.CC"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _render_video(bg_path: Path, audio_path: Path, ass_path: Path, output_path: Path, audio_duration: float) -> None:
    """Render Douyin-style video using FFmpeg.

    Loops background image for full audio duration, overlays ASS subtitles and audio.
    """
    duration = audio_duration + 5.0  # 5s padding

    cmd = [
        "ffmpeg", "-y",
        # Background image looped for full duration
        "-loop", "1", "-i", str(bg_path),
        # Audio input
        "-i", str(audio_path),
        # Subtitle filter
        "-vf", f"ass={ass_path}",
        # Video codec — tune for still image background
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-tune", "stillimage",
        # Audio codec
        "-c:a", "aac", "-b:a", "192k",
        # Match shortest stream (audio length)
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Install with: brew install ffmpeg")
