"""Chorus detection and grand chorus synthesis.

Step 5 of the FireSing pipeline:
- detect() identifies chorus sections by lyric repetition
- detect_last_section() finds the final chorus/outro
- generate_grand_chorus() runs multi-voice RVC inference with stereo panning + reverb
"""

import asyncio
import logging
from collections import Counter
from pathlib import Path

from pydub import AudioSegment as PydubAudioSegment
from sqlalchemy.orm import Session

from ..config import CONVERTED_DIR
from ..models import Segment, VoiceModel, Song
from .rvc_service import convert_with_params

logger = logging.getLogger(__name__)

# Stereo panning positions for up to 5 voices (left-to-right spread)
STEREO_PANS = [-0.8, -0.4, 0.0, 0.4, 0.8]

# Reverb settings (light hall reverb via pydub simple delay)
REVERB_DELAY_MS = 40
REVERB_DECAY = 0.3
REVERB_MIX_DB = -4  # wet signal volume relative to dry


def detect(segments: list) -> list[str]:
    """Detect chorus segments by finding repeated lyric text.

    A segment is chorus if its text appears >= 2 times across all segments.

    Returns list of segment IDs identified as chorus.
    """
    if not segments:
        return []

    # Count text occurrences
    text_counts = Counter(seg.text for seg in segments)
    repeated_texts = {text for text, count in text_counts.items() if count >= 2}

    chorus_ids = []
    for seg in segments:
        if seg.text in repeated_texts:
            chorus_ids.append(seg.id)

    if chorus_ids:
        logger.info(f"Detected {len(chorus_ids)} chorus segments out of {len(segments)}")

    return chorus_ids


def detect_last_section(segments: list) -> list[str]:
    """Detect the last section of a song (final chorus or outro).

    Strategy:
    1. Find all chorus segments (repeated lyrics) using detect().
    2. If the last N segments are all chorus, return them (final chorus block).
    3. Otherwise, return the last contiguous block of repeated lyrics.
    4. Fallback: return the last 4-8 segments as the outro section.

    Returns list of segment IDs for the final section.
    """
    if not segments:
        return []

    chorus_ids = set(detect(segments))

    # Try to find the last contiguous block of chorus segments
    # Walk backwards from the end
    last_chorus_block = []
    for seg in reversed(segments):
        if seg.id in chorus_ids:
            last_chorus_block.insert(0, seg.id)
        else:
            break

    if last_chorus_block:
        logger.info(
            f"Last section: {len(last_chorus_block)} chorus segments "
            f"(lines {segments[-len(last_chorus_block)].line_number}-"
            f"{segments[-1].line_number})"
        )
        return last_chorus_block

    # Fallback: last 4-8 segments (or all if fewer than 4)
    fallback_count = min(max(4, len(segments) // 5), 8, len(segments))
    fallback_ids = [seg.id for seg in segments[-fallback_count:]]
    logger.info(f"Last section (fallback): {len(fallback_ids)} segments from end")
    return fallback_ids


def _pan_audio(audio: PydubAudioSegment, pan: float) -> PydubAudioSegment:
    """Pan a mono or stereo audio segment across the stereo field.

    pan: -1.0 (full left) to 1.0 (full right), 0.0 = center.
    """
    # Ensure stereo
    if audio.channels == 1:
        audio = audio.set_channels(2)

    # pydub pan takes -1.0 to 1.0
    return audio.pan(pan)


def _add_reverb(audio: PydubAudioSegment) -> PydubAudioSegment:
    """Add light reverb by mixing delayed/decayed copies.

    Simple echo-based reverb: a few delay taps with decreasing volume.
    """
    if audio.channels == 1:
        audio = audio.set_channels(2)

    result = audio
    # Multiple delay taps for a richer reverb tail
    taps = [
        (REVERB_DELAY_MS, REVERB_DECAY),
        (REVERB_DELAY_MS * 2, REVERB_DECAY * 0.5),
        (REVERB_DELAY_MS * 3, REVERB_DECAY * 0.25),
    ]
    for delay_ms, decay in taps:
        silence = PydubAudioSegment.silent(duration=delay_ms, frame_rate=audio.frame_rate)
        # Ensure matching channel count before concatenation
        delayed = silence + audio
        delayed = delayed[: len(audio)]  # trim to same length
        delayed = delayed - abs(REVERB_MIX_DB)  # attenuate wet signal
        # Apply additional decay attenuation
        decay_db = int(-6 * (1 - decay))  # approx per-tap decay
        delayed = delayed + decay_db
        result = result.overlay(delayed)

    return result


def _mix_voices(voice_audios: list[PydubAudioSegment]) -> PydubAudioSegment:
    """Mix multiple voice audio segments with stereo panning.

    Each voice is panned to a different position across the stereo field
    using the STEREO_PANS positions. All are overlaid into one stereo mix.
    """
    if not voice_audios:
        raise ValueError("No voice audios to mix")

    # Normalize all to same parameters
    frame_rate = voice_audios[0].frame_rate
    sample_width = voice_audios[0].sample_width
    max_duration = max(len(a) for a in voice_audios)

    # Start with silence
    mixed = PydubAudioSegment.silent(
        duration=max_duration, frame_rate=frame_rate
    ).set_sample_width(sample_width).set_channels(2)

    for i, voice_audio in enumerate(voice_audios):
        # Ensure consistent format
        voice_audio = voice_audio.set_frame_rate(frame_rate)
        voice_audio = voice_audio.set_sample_width(sample_width)
        voice_audio = voice_audio.set_channels(2)

        # Pan to position
        pan = STEREO_PANS[i % len(STEREO_PANS)]
        panned = _pan_audio(voice_audio, pan)

        # Pad or trim to match mix length
        if len(panned) < max_duration:
            panned = panned + PydubAudioSegment.silent(
                duration=max_duration - len(panned),
                frame_rate=frame_rate,
            )
            panned = panned.set_sample_width(sample_width).set_channels(2)
        else:
            panned = panned[:max_duration]

        # Overlay at reduced volume (-3 dB per voice to avoid clipping)
        panned = panned - 3
        mixed = mixed.overlay(panned)

    return mixed


async def _read_audio_bytes(path: str) -> bytes:
    """Read audio file bytes."""
    return await asyncio.to_thread(lambda: Path(path).read_bytes())


async def _load_voice_model(
    voice_model_id: str, db: Session
) -> VoiceModel:
    """Load a VoiceModel from the database."""
    voice = db.query(VoiceModel).filter(VoiceModel.id == voice_model_id).first()
    if not voice:
        raise ValueError(f"Voice model {voice_model_id} not found")
    return voice


async def _load_voice_model_bytes(voice: VoiceModel) -> tuple[bytes, bytes | None]:
    """Read voice model files (pth + optional index) from disk."""
    pth_bytes = await asyncio.to_thread(lambda: Path(voice.model_path).read_bytes())
    index_bytes = None
    if voice.index_path and Path(voice.index_path).exists():
        index_bytes = await asyncio.to_thread(lambda: Path(voice.index_path).read_bytes())
    return pth_bytes, index_bytes


async def generate_grand_chorus(
    song_id: str,
    segment_ids: list[str],
    voice_model_ids: list[str],
    db: Session,
) -> Path:
    """Generate grand chorus audio for a section of the song.

    For each chorus segment:
    1. Load the original vocal audio
    2. Run RVC inference with each of the N voice models
    3. Pan each voice across the stereo field
    4. Add light reverb
    5. Mix all voices together

    Returns path to the final mixed chorus audio file.
    """
    if not segment_ids:
        raise ValueError("No segment IDs provided for chorus")
    if not voice_model_ids:
        raise ValueError("No voice model IDs provided for chorus")

    logger.info(
        f"Generating grand chorus: {len(segment_ids)} segments x "
        f"{len(voice_model_ids)} voices for song {song_id}"
    )

    # Pre-load all voice models (pth + index bytes)
    voices: list[VoiceModel] = []
    voice_data: list[tuple[bytes, bytes | None]] = []
    for vm_id in voice_model_ids:
        voice = await _load_voice_model(vm_id, db)
        pth_bytes, index_bytes = await _load_voice_model_bytes(voice)
        voices.append(voice)
        voice_data.append((pth_bytes, index_bytes))

    # Process each segment
    segment_audios: list[PydubAudioSegment] = []

    for seg_id in segment_ids:
        segment = db.query(Segment).filter(Segment.id == seg_id).first()
        if not segment:
            logger.warning(f"Segment {seg_id} not found, skipping")
            continue
        if not segment.vocal_path or not Path(segment.vocal_path).exists():
            logger.warning(
                f"Segment {seg_id} (line {segment.line_number}) has no vocal, skipping"
            )
            continue

        # Read source vocal bytes
        vocal_bytes = await _read_audio_bytes(segment.vocal_path)

        # Run RVC inference with each voice model (sequentially to avoid GPU overload)
        voice_audios: list[PydubAudioSegment] = []
        original_duration_ms = (segment.end_time - segment.start_time) * 1000
        for i, voice in enumerate(voices):
            pth_bytes, index_bytes = voice_data[i]
            try:
                converted_bytes = await convert_with_params(
                    audio_bytes=vocal_bytes,
                    model_id=voice.id,
                    pth_bytes=pth_bytes,
                    index_bytes=index_bytes,
                    f0_method="crepe",
                    f0_up_key=0,
                    index_rate=0.6,
                    filter_radius=3,
                    rms_mix_rate=0.25,
                    protect=0.5,
                    original_duration_ms=original_duration_ms,
                )

                # Convert bytes to pydub AudioSegment (offload to thread)
                audio_seg = await asyncio.to_thread(
                    PydubAudioSegment, converted_bytes, format="wav"
                )
                voice_audios.append(audio_seg)

                logger.debug(
                    f"  Segment line {segment.line_number}, voice {voice.name}: "
                    f"{len(converted_bytes)/1024:.1f}KB"
                )
            except Exception as e:
                logger.error(
                    f"  RVC failed for segment {segment.line_number}, "
                    f"voice {voice.name}: {e}"
                )
                continue

        if not voice_audios:
            logger.warning(
                f"No voices generated for segment {seg_id}, skipping"
            )
            continue

        # Mix voices with stereo panning
        mixed_segment = await asyncio.to_thread(_mix_voices, voice_audios)

        # Add light reverb
        mixed_segment = await asyncio.to_thread(_add_reverb, mixed_segment)

        segment_audios.append(mixed_segment)

    if not segment_audios:
        raise RuntimeError("No chorus audio segments were generated")

    # Concatenate all segments in order
    logger.info(f"Concatenating {len(segment_audios)} chorus segments")
    full_chorus = segment_audios[0]
    for seg_audio in segment_audios[1:]:
        full_chorus = full_chorus + seg_audio

    # Export to file
    output_dir = CONVERTED_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "grand_chorus.wav"

    await asyncio.to_thread(
        full_chorus.export, str(output_path), format="wav"
    )

    logger.info(
        f"Grand chorus generated: {output_path} "
        f"({len(full_chorus)/1000:.1f}s, "
        f"{len(segment_audios)} segments, "
        f"{len(voice_model_ids)} voices)"
    )

    return output_path
