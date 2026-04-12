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
ORIGINAL_BACKING_VOLUME_DB = -18  # Original vocals stem volume for harmony context


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

    # Step 1: Place converted vocals at their original time positions
    # (NOT concatenation — concatenation loses gaps between segments)
    vocal_track = _place_vocals_at_positions(segments, chorus_set, song)

    # Step 1.5: Overlay original vocals stem at reduced volume for harmony context
    # With f0up_key=0 the AI voice matches original pitch, so backing blends naturally
    if song.vocals_path and Path(song.vocals_path).exists():
        vocal_track = _overlay_original_backing(vocal_track, song.vocals_path)

    # Step 2: Chorus segments already have multi-voice audio in converted_vocal_path
    # (replaced by chorus_service.generate_grand_chorus), no separate overlay needed

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


def _place_vocals_at_positions(
    segments: list, chorus_set: set, song
) -> AudioSegment:
    """Place converted vocal segments at their original time positions.

    Instead of concatenating segments (which loses all silence/gaps),
    create a full-length track and overlay each segment at its original
    start time. This keeps the vocal track in sync with the instrumental.
    """
    # Determine total duration from instrumental or original vocals
    ref_path = song.instrumental_path or song.vocals_path
    if not ref_path or not Path(ref_path).exists():
        raise ValueError("No reference audio for duration")

    ref_audio = AudioSegment.from_file(ref_path)
    total_ms = len(ref_audio)
    frame_rate = ref_audio.frame_rate
    channels = ref_audio.channels
    sample_width = ref_audio.sample_width

    # Create silent track matching reference duration
    result = AudioSegment.silent(duration=total_ms, frame_rate=frame_rate)
    result = result.set_sample_width(sample_width).set_channels(channels)

    placed = 0
    for seg in segments:
        if not seg.converted_vocal_path:
            continue
        if not Path(seg.converted_vocal_path).exists():
            continue
        if seg.start_time is None:
            continue

        seg_audio = AudioSegment.from_wav(seg.converted_vocal_path)

        # Boost chorus sections by 1dB
        if seg.id in chorus_set:
            seg_audio = seg_audio + 1

        # Place at original position (start_time is in seconds)
        position_ms = int(seg.start_time * 1000)

        # Don't place beyond track length
        if position_ms >= total_ms:
            continue

        # Trim segment if it extends beyond track
        available_ms = total_ms - position_ms
        if len(seg_audio) > available_ms:
            seg_audio = seg_audio[:available_ms]

        result = result.overlay(seg_audio, position=position_ms)
        placed += 1

    logger.info(
        f"Placed {placed}/{len(segments)} segments at original positions, "
        f"track length {total_ms}ms"
    )
    return result


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


def _overlay_original_backing(
    vocal_track: AudioSegment,
    original_vocals_path: str,
) -> AudioSegment:
    """Overlay original vocals stem at reduced volume for natural harmony context.

    The Demucs vocals stem contains the original lead + harmony/backing vocals.
    At reduced volume (-10dB), the original harmony naturally comes through
    behind the AI-converted lead vocal. This is a vocal double tracking technique.
    """
    try:
        original = AudioSegment.from_file(original_vocals_path)
    except Exception as e:
        logger.warning(f"Failed to load original vocals for backing: {e}")
        return vocal_track

    # Reduce volume so it's heard but doesn't dominate
    backing = original + ORIGINAL_BACKING_VOLUME_DB

    # Match lengths
    if len(backing) > len(vocal_track):
        backing = backing[:len(vocal_track)]
    elif len(backing) < len(vocal_track):
        silence = AudioSegment.silent(
            duration=len(vocal_track) - len(backing),
            frame_rate=backing.frame_rate,
        )
        silence = silence.set_sample_width(backing.sample_width).set_channels(backing.channels)
        backing = backing + silence

    result = vocal_track.overlay(backing)
    logger.info(
        f"Original backing overlaid at {ORIGINAL_BACKING_VOLUME_DB}dB, "
        f"length {len(backing)}ms"
    )
    return result


def _overlay_grand_chorus(
    vocal_track: AudioSegment,
    segments: list,
    chorus_set: set,
    song_id: str,
) -> AudioSegment:
    """Overlay per-segment chorus audio at original positions.

    Each chorus segment has a separate multi-voice file (chorus_line_XXX.wav).
    We overlay each at the segment's original start_time position.
    This preserves timing and avoids concatenation artifacts.
    """
    from ..config import CONVERTED_DIR

    if not chorus_set:
        return vocal_track

    overlaid = 0
    for seg in segments:
        if seg.id not in chorus_set:
            continue
        if seg.start_time is None:
            continue

        chorus_path = CONVERTED_DIR / song_id / f"chorus_line_{seg.line_number:03d}.wav"
        if not chorus_path.exists():
            continue

        chorus_audio = AudioSegment.from_wav(str(chorus_path))

        # Chorus at -3dB behind the lead vocal
        chorus_audio = chorus_audio - 3

        position_ms = int(seg.start_time * 1000)
        if position_ms >= len(vocal_track):
            continue

        # Trim if extends beyond track
        available_ms = len(vocal_track) - position_ms
        if len(chorus_audio) > available_ms:
            chorus_audio = chorus_audio[:available_ms]

        vocal_track = vocal_track.overlay(chorus_audio, position=position_ms)
        overlaid += 1

    logger.info(f"Overlaid {overlaid} chorus segments at original positions")
    return vocal_track


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
