"""Audio service — mix converted vocals, chorus, monologue, and instrumental."""

import logging
from pathlib import Path

import numpy as np
from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import OUTPUTS_DIR, SONGS_DIR
from ..models import Song, Segment, Output

logger = logging.getLogger(__name__)

# Audio mixing constants
CROSSFADE_MS = 50  # Crossfade between segments (50ms with squared-sine window)
MONOLOGUE_INSTRUMENTAL_REDUCTION_DB = 12  # Lower instrumental during monologue


def mix_all(
    song_id: str,
    chorus_segment_ids: list[str],
    monologue_position: str,
    db: Session,
) -> Path:
    """Full audio mixing pipeline.

    1. Concatenate converted vocals with crossfade
    2. Overlay grand chorus if available
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

    # Step 2: Overlay grand chorus if available
    from ..config import CONVERTED_DIR
    grand_chorus_path = CONVERTED_DIR / song_id / "grand_chorus.wav"
    if grand_chorus_path.exists():
        grand_chorus = AudioSegment.from_wav(str(grand_chorus_path))
        vocal_track = _overlay_grand_chorus(vocal_track, grand_chorus, segments, chorus_set)

    # Step 3: Load instrumental
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


def _squared_sine_crossfade(
    seg1: AudioSegment, seg2: AudioSegment, crossfade_ms: int
) -> AudioSegment:
    """Crossfade two segments using a squared-sine window (RVC best practice).

    Unlike pydub's default linear crossfade, squared-sine avoids volume dips
    at the midpoint and produces smoother transitions for voice segments.
    """
    cf_samples = int(crossfade_ms * seg1.frame_rate / 1000)

    # Get raw sample arrays
    seg1_raw = np.array(seg1.get_array_of_samples(), dtype=np.float64)
    seg2_raw = np.array(seg2.get_array_of_samples(), dtype=np.float64)

    # If either segment is too short, just concatenate without crossfade
    if len(seg1_raw) < cf_samples or len(seg2_raw) < cf_samples:
        return seg1 + seg2

    # Squared-sine fade curves
    fade_out = np.cos(0.5 * np.pi * np.linspace(0, 1, cf_samples)) ** 2
    fade_in = np.sin(0.5 * np.pi * np.linspace(0, 1, cf_samples)) ** 2

    channels = seg1.channels
    if channels > 1:
        seg1_2d = seg1_raw.reshape(-1, channels)
        seg2_2d = seg2_raw.reshape(-1, channels)
        overlap = (
            seg1_2d[-cf_samples:] * fade_out[:, np.newaxis]
            + seg2_2d[:cf_samples] * fade_in[:, np.newaxis]
        )
        result_samples = np.concatenate([
            seg1_2d[:-cf_samples],
            overlap,
            seg2_2d[cf_samples:],
        ], axis=0).flatten()
    else:
        overlap = (
            seg1_raw[-cf_samples:] * fade_out
            + seg2_raw[:cf_samples] * fade_in
        )
        result_samples = np.concatenate([
            seg1_raw[:-cf_samples],
            overlap,
            seg2_raw[cf_samples:],
        ])

    return AudioSegment(
        result_samples.astype(np.int16).tobytes(),
        frame_rate=seg1.frame_rate,
        sample_width=2,
        channels=channels,
    )


def _concatenate_vocals(segments: list, chorus_set: set) -> AudioSegment:
    """Concatenate converted vocal segments with squared-sine crossfade."""
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

    # Concatenate with squared-sine crossfade
    result = parts[0]
    for part in parts[1:]:
        result = _squared_sine_crossfade(result, part, CROSSFADE_MS)

    return result


def _overlay_grand_chorus(
    vocal_track: AudioSegment,
    grand_chorus: AudioSegment,
    segments: list,
    chorus_set: set,
) -> AudioSegment:
    """Overlay grand chorus audio at the correct position in the vocal track.

    The grand chorus was generated for specific segments. We need to find
    where those segments start in the concatenated track and overlay there.
    """
    if not chorus_set:
        return vocal_track

    # Find the start position of the first chorus segment in the vocal track
    # by accumulating durations of all preceding segments
    offset_ms = 0
    found_first_chorus = False
    for seg in segments:
        if seg.id in chorus_set:
            found_first_chorus = True
            break
        if seg.converted_vocal_path and Path(seg.converted_vocal_path).exists():
            seg_audio = AudioSegment.from_wav(seg.converted_vocal_path)
            offset_ms += len(seg_audio)

    if not found_first_chorus:
        return vocal_track

    # Trim or pad grand chorus to fit available space
    available_ms = len(vocal_track) - offset_ms
    if available_ms <= 0:
        return vocal_track

    if len(grand_chorus) > available_ms:
        grand_chorus = grand_chorus[:available_ms]

    # Overlay at -3dB (grand chorus should be prominent but not overpower lead)
    grand_chorus = grand_chorus - 3

    result = vocal_track.overlay(grand_chorus, position=offset_ms)
    logger.info(
        f"Grand chorus overlaid at {offset_ms}ms, "
        f"length {len(grand_chorus)}ms, available {available_ms}ms"
    )
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
    if monologue:
        monologue_len = len(monologue)
        total_len = len(instrumental)
        if monologue_position == "beginning":
            quiet_section = instrumental[:monologue_len] - MONOLOGUE_INSTRUMENTAL_REDUCTION_DB
            instrumental = quiet_section + instrumental[monologue_len:]
        elif monologue_position == "end":
            quiet_section = instrumental[total_len - monologue_len:] - MONOLOGUE_INSTRUMENTAL_REDUCTION_DB
            instrumental = instrumental[:total_len - monologue_len] + quiet_section
        elif monologue_position == "interlude":
            mid = total_len // 2
            half = monologue_len // 2
            start = max(0, mid - half)
            end = min(total_len, start + monologue_len)
            quiet_section = instrumental[start:end] - MONOLOGUE_INSTRUMENTAL_REDUCTION_DB
            instrumental = instrumental[:start] + quiet_section + instrumental[end:]

    # Mix vocals + instrumental
    mixed = vocals.overlay(instrumental)

    # Insert monologue at specified position
    if monologue:
        silence_gap = AudioSegment.silent(duration=1500)  # 1.5s gap
        if monologue_position == "beginning":
            mixed = monologue + silence_gap + mixed
        elif monologue_position == "interlude":
            mid = len(mixed) // 2
            mixed = mixed[:mid] + silence_gap + monologue + silence_gap + mixed[mid:]
        else:
            mixed = mixed + silence_gap + monologue

    return mixed
