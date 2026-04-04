"""Video service — generate vertical video with ASS subtitles via FFmpeg."""

import logging
import subprocess
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import OUTPUTS_DIR, SONGS_DIR
from ..models import Song, Segment, VoiceModel, Output

logger = logging.getLogger(__name__)

# Video parameters
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# Colors for different voices (ASS format: &HBBGGRR&)
VOICE_COLORS = [
    "&H6B6BFF",  # #FF6B6B red
    "&HC4C44E",  # #4ECDC4 teal
    "&HB745D1",  # #D145B7 -> #45B7D1 blue (ASS is BGR)
    "&HCE6B4E",  # not used, placeholder
    "&HEAFF4E",  # not used
]

# Standard colors for ASS (BGR format)
ASS_COLORS = ["&H6B6BFF", "&HC4CE4E", "&HD1B745", "&HCE964E", "&HA7EEFF"]


def generate(song_id: str, db: Session) -> Path:
    """Generate 1080x1920 video with ASS subtitles.

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

    # Get voice models for color mapping
    voice_ids = list({s.voice_model_id for s in segments if s.voice_model_id})
    voice_models = db.query(VoiceModel).filter(VoiceModel.id.in_(voice_ids)).all()
    voice_color_map = {vm.id: ASS_COLORS[i % len(ASS_COLORS)] for i, vm in enumerate(voice_models)}

    # Generate ASS subtitle file
    ass_path = _generate_ass(segments, voice_color_map, song_id)

    # Generate video with FFmpeg
    output_dir = OUTPUTS_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "final.mp4"

    _render_video(
        audio_path=Path(audio_output.file_path),
        ass_path=ass_path,
        output_path=output_path,
    )

    # Create Output record
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

    # Cleanup ASS file
    ass_path.unlink(missing_ok=True)

    logger.info(f"Video generated: {output_path} ({file_size / 1024 / 1024:.1f}MB)")
    return output_path


def _generate_ass(segments: list, voice_color_map: dict, song_id: str) -> Path:
    """Generate ASS subtitle file with per-voice colors."""
    ass_path = OUTPUTS_DIR / song_id / "subtitles.ass"
    ass_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "[Script Info]",
        "Title: FireSing",
        "ScriptType: v4.00+",
        f"PlayResX: {VIDEO_WIDTH}",
        f"PlayResY: {VIDEO_HEIGHT}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,30,1",
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


def _render_video(audio_path: Path, ass_path: Path, output_path: Path) -> None:
    """Render video using FFmpeg with black background + subtitles + audio."""
    # Generate a simple black background video with audio and subtitles
    cmd = [
        "ffmpeg", "-y",
        # Black background, 1080x1920, duration matches audio
        "-f", "lavfi", "-i", f"color=c=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d=3600:r={FPS}",
        # Audio input
        "-i", str(audio_path),
        # Subtitle filter
        "-vf", f"ass={ass_path}",
        # Video codec
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        # Audio codec
        "-c:a", "aac", "-b:a", "192k",
        # Shortest output (match audio length)
        "-shortest",
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
