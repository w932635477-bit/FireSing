"""Lyrics service — LRC parsing, validation, and vocal segmentation."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import SEGMENTS_DIR
from ..models import Song, Segment

logger = logging.getLogger(__name__)

# Minimum segment duration in seconds
MIN_SEGMENT_DURATION = 0.3

# Default duration appended to last segment if no total_duration is known
DEFAULT_LAST_SEGMENT_DURATION = 5.0

# LRC timestamp pattern: [mm:ss.xx]
_LRC_TS_RE = re.compile(r"^\[(\d+):(\d+(?:\.\d+)?)\](.*)")


@dataclass
class LrcLine:
    """A parsed LRC line with timestamp and text."""
    time: float  # seconds
    text: str


def parse_lrc(lrc_path: Path) -> list[LrcLine]:
    """Parse an LRC file into a list of (time, text) entries.

    Skips metadata lines ([ti:], [ar:], [al:], etc.) and lines with no text.
    """
    lines: list[LrcLine] = []
    with open(lrc_path, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            # Skip metadata tags like [ti:title], [ar:artist], [al:album], [by:], [offset:]
            if re.match(r"^\[[a-z]+:", raw):
                continue
            m = _LRC_TS_RE.match(raw)
            if not m:
                continue
            minutes = int(m.group(1))
            seconds = float(m.group(2))
            text = m.group(3).strip()
            if not text:
                continue
            lines.append(LrcLine(time=minutes * 60 + seconds, text=text))
    return lines


def validate_segments(lines: list[LrcLine]) -> list[LrcLine]:
    """Validate parsed LRC lines. Returns valid lines or raises ValueError.

    Checks:
    - At least one line
    - Timestamps monotonically non-decreasing
    - Each segment > MIN_SEGMENT_DURATION (except the last, which has no end yet)
    """
    if not lines:
        raise ValueError("LRC file has no lyrics lines")

    for i in range(len(lines) - 1):
        if lines[i + 1].time < lines[i].time:
            raise ValueError(
                f"Timestamps not monotonic: line {i + 1} ({lines[i + 1].time}s) "
                f"< line {i} ({lines[i].time}s)"
            )
        duration = lines[i + 1].time - lines[i].time
        if duration < MIN_SEGMENT_DURATION:
            raise ValueError(
                f"Segment {i + 1} too short: {duration:.2f}s < {MIN_SEGMENT_DURATION}s "
                f"(\"{lines[i].text}\")"
            )

    return lines


def compute_end_times(
    lines: list[LrcLine], total_duration: float | None = None
) -> list[dict]:
    """Convert LRC lines to segment dicts with start_time and end_time.

    For the last segment, end_time = start_time + DEFAULT_LAST_SEGMENT_DURATION,
    or total_duration if provided.
    """
    segments = []
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            end_time = lines[i + 1].time
        else:
            end_time = line.time + DEFAULT_LAST_SEGMENT_DURATION
            if total_duration and end_time > total_duration:
                end_time = total_duration
        segments.append({
            "line_number": i + 1,
            "text": line.text,
            "start_time": line.time,
            "end_time": end_time,
        })
    return segments


def cut_vocals(
    vocals_path: Path, segments: list[dict], output_dir: Path
) -> list[Path]:
    """Cut vocals.wav into per-segment files using pydub.

    Returns list of paths to cut segment wav files.
    """
    audio = AudioSegment.from_wav(str(vocals_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for seg in segments:
        start_ms = int(seg["start_time"] * 1000)
        end_ms = int(seg["end_time"] * 1000)
        segment_audio = audio[start_ms:end_ms]

        filename = f"line_{seg['line_number']:03d}.wav"
        seg_path = output_dir / filename
        segment_audio.export(str(seg_path), format="wav")
        paths.append(seg_path)

    logger.info(f"Cut {len(segments)} segments to {output_dir}")
    return paths


def parse_and_cut(song_id: str, db: Session) -> list[Segment]:
    """Full pipeline: parse LRC, validate, cut vocals, save segments to DB.

    This is the sync entry point called via asyncio.to_thread().
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")
    if not song.lrc_path:
        raise ValueError(f"Song {song_id} has no LRC file")
    if not song.vocals_path:
        raise ValueError(f"Song {song_id} vocals not yet separated")

    # Check if already segmented with vocal files
    existing = db.query(Segment).filter(Segment.song_id == song_id).first()
    if existing and existing.vocal_path:
        logger.info(f"Song {song_id} already segmented with vocals, skipping")
        return db.query(Segment).filter(Segment.song_id == song_id).all()
    # Delete old segments without vocals so we can re-segment
    if existing:
        logger.info(f"Song {song_id} has segments without vocals, re-segmenting")
        db.query(Segment).filter(Segment.song_id == song_id).delete()
        db.flush()

    # Parse and validate
    lrc_lines = parse_lrc(Path(song.lrc_path))
    lrc_lines = validate_segments(lrc_lines)
    segments_data = compute_end_times(lrc_lines)

    # Cut vocals
    output_dir = SEGMENTS_DIR / song_id
    vocal_paths = cut_vocals(Path(song.vocals_path), segments_data, output_dir)

    # Save to database
    db_segments = []
    for seg_data, vocal_path in zip(segments_data, vocal_paths):
        db_seg = Segment(
            song_id=song_id,
            line_number=seg_data["line_number"],
            text=seg_data["text"],
            start_time=seg_data["start_time"],
            end_time=seg_data["end_time"],
            vocal_path=str(vocal_path),
        )
        db.add(db_seg)
        db_segments.append(db_seg)

    song.status = "segmented"
    db.commit()

    for seg in db_segments:
        db.refresh(seg)

    logger.info(f"Song {song_id}: {len(db_segments)} segments created")
    return db_segments
