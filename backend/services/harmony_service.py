"""Harmony service — generate multi-part vocal harmonies.

Creates harmony parts by pitch-shifting the already-converted lead vocal
using librosa. This ensures perfect sync and preserves the voice timbre.

Approach: take the converted vocal (RVC output), shift pitch by N semitones
with librosa.effects.pitch_shift, mix back at reduced volume.

This is faster than re-running RVC (no GPU call), perfectly synchronized
(exact same source), and preserves voice character (formants stay natural).
"""

import asyncio
import io
import logging
from pathlib import Path

import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import CONVERTED_DIR

logger = logging.getLogger(__name__)

# Harmony intervals in semitones
HARMONY_INTERVALS = {
    "minor_third_above": 3,
    "major_third_above": 4,
    "perfect_fourth_above": 5,
    "perfect_fifth_above": 7,
    "minor_third_below": -3,
    "major_third_below": -4,
    "octave_above": 12,
    "octave_below": -12,
}

# Volume reduction in dB for harmony parts (behind lead vocal)
HARMONY_VOLUME_DB = -12

# Default harmony: octave below (natural backing vocal sound)
DEFAULT_HARMONY_PARTS = ["octave_below"]


def _pitch_shift_audio(audio_bytes: bytes, n_semitones: int) -> bytes:
    """Pitch-shift WAV audio by n semitones using librosa.

    Returns WAV bytes of the same duration. Preserves sample rate and channels.
    """
    audio, sr = sf.read(io.BytesIO(audio_bytes))
    duration_s = len(audio) / sr

    if audio.ndim == 1:
        shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_semitones)
    else:
        # Stereo: shift each channel
        shifted = np.stack([
            librosa.effects.pitch_shift(audio[:, c], sr=sr, n_steps=n_semitones)
            for c in range(audio.shape[1])
        ], axis=1)

    # Trim or pad to match original duration exactly
    target_len = int(duration_s * sr)
    if len(shifted) > target_len:
        shifted = shifted[:target_len]
    elif len(shifted) < target_len:
        pad = target_len - len(shifted)
        if shifted.ndim == 1:
            shifted = np.pad(shifted, (0, pad))
        else:
            shifted = np.pad(shifted, ((0, pad), (0, 0)))

    buf = io.BytesIO()
    sf.write(buf, shifted, sr, format="WAV")
    return buf.getvalue()


async def generate_harmonies(
    song_id: str,
    segment_ids: list[str],
    harmony_parts: list[str] | None = None,
    db: Session = None,
) -> list[Path]:
    """Generate harmony vocals for specified segments.

    For each segment, pitch-shifts the converted lead vocal to create harmony
    parts, then mixes them at reduced volume behind the lead.

    Args:
        song_id: Song ID
        segment_ids: List of segment IDs to add harmonies to
        harmony_parts: Which harmony intervals to generate (default: octave below)
        db: Database session

    Returns:
        List of paths to harmony-enhanced segment audio files.
    """
    from ..models import Segment

    if not harmony_parts:
        harmony_parts = DEFAULT_HARMONY_PARTS

    for part in harmony_parts:
        if part not in HARMONY_INTERVALS:
            raise ValueError(f"Unknown harmony part: {part}. Choose from: {list(HARMONY_INTERVALS.keys())}")

    segments = db.query(Segment).filter(
        Segment.id.in_(segment_ids),
        Segment.song_id == song_id,
    ).all()

    if not segments:
        logger.warning(f"No segments found for harmony generation: {song_id}")
        return []

    output_paths = []
    for seg in segments:
        if not seg.converted_vocal_path:
            logger.warning(f"Segment {seg.id} missing converted vocal, skipping harmony")
            continue

        converted_path = Path(seg.converted_vocal_path)
        if not converted_path.exists():
            logger.warning(f"Segment {seg.id} converted file missing: {converted_path}")
            continue

        # Load the lead vocal bytes
        lead_bytes = await asyncio.to_thread(converted_path.read_bytes)

        # Generate each harmony part by pitch-shifting the converted vocal
        harmony_tracks = []
        for part_name in harmony_parts:
            interval = HARMONY_INTERVALS[part_name]
            try:
                shifted_bytes = await asyncio.to_thread(
                    _pitch_shift_audio, lead_bytes, interval
                )
                harmony_audio = await asyncio.to_thread(
                    AudioSegment, shifted_bytes, format="wav"
                )
                # Reduce volume for harmony part
                harmony_audio = harmony_audio + HARMONY_VOLUME_DB
                # Add 30ms fade-in for smooth blend
                harmony_audio = harmony_audio.fade_in(30).fade_out(30)
                harmony_tracks.append(harmony_audio)
            except Exception as e:
                logger.warning(f"Harmony part {part_name} failed for segment {seg.id}: {e}")
                continue

        if not harmony_tracks:
            output_paths.append(converted_path)
            continue

        # Load lead vocal as pydub AudioSegment
        lead_vocal = await asyncio.to_thread(AudioSegment.from_wav, str(converted_path))

        # Mix lead vocal with harmony parts
        def _mix(lead, tracks):
            result = lead
            for track in tracks:
                # Pad shorter track with silence to match lead length
                if len(track) < len(result):
                    silence = AudioSegment.silent(
                        duration=len(result) - len(track),
                        frame_rate=track.frame_rate,
                    )
                    silence = silence.set_sample_width(track.sample_width).set_channels(track.channels)
                    track = track + silence
                elif len(track) > len(result):
                    track = track[:len(result)]
                result = result.overlay(track)
            return result

        mixed = await asyncio.to_thread(_mix, lead_vocal, harmony_tracks)

        # Save harmony-enhanced segment
        output_dir = CONVERTED_DIR / song_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"line_{seg.line_number:03d}_harmony.wav"
        await asyncio.to_thread(mixed.export, str(output_path), format="wav")

        # Update segment path
        seg.converted_vocal_path = str(output_path)
        db.commit()

        output_paths.append(output_path)
        logger.info(f"Harmony generated for segment {seg.line_number}: {len(harmony_tracks)} parts")

    logger.info(f"Harmony generation complete: {len(output_paths)} segments for song {song_id}")
    return output_paths
