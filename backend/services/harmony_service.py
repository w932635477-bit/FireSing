"""Harmony service — generate multi-part vocal harmonies using RVC f0_up_key.

DESIGN.md Step 4: Generate harmony vocals by pitch-shifting converted segments
using RVC's f0_up_key parameter. Creates major third (+4), minor third (+3),
perfect fourth (+5), and perfect fifth (+7) voice parts, then mixes them at
reduced volume (-6 to -12 dB) behind the lead vocal.
"""

import asyncio
import logging
from pathlib import Path

from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import CONVERTED_DIR
from .rvc_service import convert_with_params as rvc_convert_with_params

logger = logging.getLogger(__name__)

# Harmony intervals in semitones (f0_up_key values)
HARMONY_INTERVALS = {
    "major_third": 4,
    "minor_third": 3,
    "perfect_fourth": 5,
    "perfect_fifth": 7,
}

# Volume reduction in dB for harmony parts (behind lead vocal)
HARMONY_VOLUME_DB = -8

# Default harmony set: third + fifth (classic two-part harmony)
DEFAULT_HARMONY_PARTS = ["major_third", "perfect_fifth"]


async def generate_harmonies(
    song_id: str,
    segment_ids: list[str],
    harmony_parts: list[str] | None = None,
    db: Session = None,
) -> list[Path]:
    """Generate harmony vocals for specified segments.

    For each segment, runs RVC inference with pitch-shifted f0_up_key to create
    harmony voice parts, then mixes them at reduced volume.

    Args:
        song_id: Song ID
        segment_ids: List of segment IDs to add harmonies to
        harmony_parts: Which harmony intervals to generate (default: major_third + perfect_fifth)
        db: Database session

    Returns:
        List of paths to harmony-enhanced segment audio files.
    """
    from ..models import Segment, VoiceModel

    if not harmony_parts:
        harmony_parts = DEFAULT_HARMONY_PARTS

    # Validate harmony parts
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
        if not seg.converted_vocal_path or not seg.voice_model_id:
            logger.warning(f"Segment {seg.id} missing converted vocal or voice model, skipping harmony")
            continue

        voice = db.query(VoiceModel).filter(VoiceModel.id == seg.voice_model_id).first()
        if not voice:
            logger.warning(f"Voice model {seg.voice_model_id} not found, skipping harmony")
            continue

        # Load the lead vocal (file I/O — offload to thread)
        lead_vocal = await asyncio.to_thread(
            AudioSegment.from_wav, seg.converted_vocal_path
        )

        # Generate each harmony part
        harmony_tracks = []
        for part_name in harmony_parts:
            interval = HARMONY_INTERVALS[part_name]
            try:
                harmony_audio = await _generate_harmony_part(
                    segment=seg,
                    voice_model=voice,
                    f0_up_key=interval,
                    song_id=song_id,
                    part_name=part_name,
                )
                if harmony_audio:
                    # Reduce volume for harmony part
                    harmony_tracks.append(harmony_audio + HARMONY_VOLUME_DB)
            except Exception as e:
                logger.warning(f"Harmony part {part_name} failed for segment {seg.id}: {e}")
                continue

        if not harmony_tracks:
            # No harmonies generated, keep original
            output_paths.append(Path(seg.converted_vocal_path))
            continue

        # Mix lead vocal with harmony parts (CPU-bound pydub overlay)
        def _mix_harmonies(lead, tracks):
            result = lead
            for track in tracks:
                result = result.overlay(track)
            return result

        mixed = await asyncio.to_thread(_mix_harmonies, lead_vocal, harmony_tracks)

        # Save harmony-enhanced segment (file I/O — offload to thread)
        output_dir = CONVERTED_DIR / song_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"line_{seg.line_number:03d}_harmony.wav"
        await asyncio.to_thread(mixed.export, str(output_path), format="wav")

        # Update segment path
        seg.converted_vocal_path = str(output_path)
        db.commit()

        output_paths.append(output_path)
        logger.info(f"Harmony generated for segment {seg.line_number}: {len(harmony_tracks)} parts")

    logger.info(f"Harmony generation complete: {len(output_paths)} segments processed for song {song_id}")
    return output_paths


async def _generate_harmony_part(
    segment,
    voice_model,
    f0_up_key: int,
    song_id: str,
    part_name: str,
) -> AudioSegment | None:
    """Generate a single harmony part by running RVC with pitch offset.

    Uses the original (pre-conversion) vocal as input and runs RVC again
    with f0_up_key set to the harmony interval.
    """
    if not segment.vocal_path:
        return None

    vocal_path = Path(segment.vocal_path)
    if not vocal_path.exists():
        return None

    # Read source vocal bytes (file I/O — offload to thread)
    audio_bytes = await asyncio.to_thread(vocal_path.read_bytes)

    # Read model files
    pth_path = Path(voice_model.model_path)
    if not await asyncio.to_thread(pth_path.exists):
        return None
    pth_bytes = await asyncio.to_thread(pth_path.read_bytes)

    index_bytes = None
    if voice_model.index_path:
        index_path = Path(voice_model.index_path)
        if await asyncio.to_thread(index_path.exists):
            index_bytes = await asyncio.to_thread(index_path.read_bytes)

    # Call RVC with pitch-shifted f0_up_key
    converted_bytes = await convert_with_params(
        audio_bytes=audio_bytes,
        model_id=f"{voice_model.id}_h{f0_up_key}",
        pth_bytes=pth_bytes,
        index_bytes=index_bytes,
        f0_method="harvest",
        f0_up_key=f0_up_key,
        index_rate=0.5,
        filter_radius=3,
    )

    if not converted_bytes:
        return None

    # Save to temp file (file I/O — offload to thread)
    output_dir = CONVERTED_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_path = output_dir / f"line_{segment.line_number:03d}_harm_{part_name}.wav"
    await asyncio.to_thread(temp_path.write_bytes, converted_bytes)

    # Load as AudioSegment (file I/O + CPU — offload to thread)
    harmony_audio = await asyncio.to_thread(AudioSegment.from_wav, str(temp_path))

    # Cleanup temp harmony file after loading (file I/O — offload to thread)
    await asyncio.to_thread(temp_path.unlink, missing_ok=True)

    return harmony_audio
