"""Audio service — mix converted vocals, chorus, monologue, and instrumental."""

import logging
from pathlib import Path

from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import OUTPUTS_DIR, SONGS_DIR
from ..models import Song, Segment, Output

logger = logging.getLogger(__name__)

# Audio mixing constants
CROSSFADE_MS = 100  # Crossfade between segments
MONOLOGUE_INSTRUMENTAL_REDUCTION_DB = 12  # Lower instrumental during monologue


def mix_all(
    song_id: str,
    chorus_segment_ids: list[str],
    monologue_position: str,
    db: Session,
) -> Path:
    """Full audio mixing pipeline.

    1. Concatenate converted vocals with crossfade
    2. Overlay chorus sections with volume boost
    3. Insert monologue at beginning or end
    4. Mix vocals + instrumental
    5. Save final output + create Output record

    Returns path to final mixed audio.
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")

    # Get segments sorted by line number
    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )
    if not segments:
        raise ValueError(f"Song {song_id} has no segments")

    chorus_set = set(chorus_segment_ids)

    # Step 1: Concatenate converted vocals with crossfade
    vocal_track = _concatenate_vocals(segments, chorus_set)

    # Step 2: Load instrumental
    if not song.instrumental_path or not Path(song.instrumental_path).exists():
        raise ValueError(f"Song {song_id} has no instrumental file")

    instrumental = AudioSegment.from_wav(song.instrumental_path)

    # Step 3: Handle monologue
    monologue_audio = None
    if song.monologue_audio_path and Path(song.monologue_audio_path).exists():
        monologue_audio = AudioSegment.from_mp3(song.monologue_audio_path)

    # Step 4: Mix everything
    final = _mix_tracks(vocal_track, instrumental, monologue_audio, monologue_position)

    # Step 5: Save output
    output_dir = OUTPUTS_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "final.wav"
    final.export(str(output_path), format="wav")

    file_size = output_path.stat().st_size
    duration = len(final) / 1000.0

    # Create or update Output record
    existing = db.query(Output).filter(
        Output.song_id == song_id, Output.format == "audio"
    ).first()

    if existing:
        existing.file_path = str(output_path)
        existing.file_size = file_size
        existing.duration = duration
    else:
        output = Output(
            song_id=song_id,
            format="audio",
            file_path=str(output_path),
            file_size=file_size,
            duration=duration,
        )
        db.add(output)

    song.status = "done"
    db.commit()

    logger.info(
        f"Audio mix done: {output_path} "
        f"({file_size / 1024 / 1024:.1f}MB, {duration:.1f}s)"
    )
    return output_path


def _concatenate_vocals(segments: list, chorus_set: set) -> AudioSegment:
    """Concatenate converted vocal segments with crossfade."""
    parts = []
    for seg in segments:
        if not seg.converted_vocal_path:
            logger.warning(f"Segment {seg.id} has no converted vocal, skipping")
            continue

        seg_audio = AudioSegment.from_wav(seg.converted_vocal_path)

        # Boost chorus sections by 1dB
        if seg.id in chorus_set:
            seg_audio = seg_audio + 1

        parts.append(seg_audio)

    if not parts:
        raise ValueError("No converted vocals available for mixing")

    # Concatenate with crossfade
    result = parts[0]
    for part in parts[1:]:
        result = result.append(part, crossfade=CROSSFADE_MS)

    return result


def _mix_tracks(
    vocals: AudioSegment,
    instrumental: AudioSegment,
    monologue: AudioSegment | None,
    monologue_position: str,
) -> AudioSegment:
    """Mix vocals, instrumental, and optional monologue."""
    # Make instrumental same length as vocals (pad or trim)
    if len(instrumental) < len(vocals):
        instrumental = instrumental + AudioSegment.silent(
            duration=len(vocals) - len(instrumental)
        )
    else:
        instrumental = instrumental[:len(vocals)]

    # Lower instrumental during monologue
    if monologue and monologue_position == "beginning":
        monologue_len = len(monologue)
        # Lower first section of instrumental
        quiet_section = instrumental[:monologue_len] - MONOLOGUE_INSTRUMENTAL_REDUCTION_DB
        instrumental = quiet_section + instrumental[monologue_len:]
    elif monologue and monologue_position == "end":
        monologue_len = len(monologue)
        total_len = len(instrumental)
        # Lower last section of instrumental
        quiet_section = instrumental[total_len - monologue_len:] - MONOLOGUE_INSTRUMENTAL_REDUCTION_DB
        instrumental = instrumental[:total_len - monologue_len] + quiet_section

    # Mix vocals + instrumental
    mixed = vocals.overlay(instrumental)

    # Prepend or append monologue
    if monologue:
        silence_gap = AudioSegment.silent(duration=1500)  # 1.5s gap
        if monologue_position == "beginning":
            mixed = monologue + silence_gap + mixed
        else:
            mixed = mixed + silence_gap + monologue

    return mixed
