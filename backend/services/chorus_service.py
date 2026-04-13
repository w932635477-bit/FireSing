"""Chorus detection and grand chorus synthesis.

Step 5 of the FireSing pipeline:
- detect() identifies chorus sections by lyric repetition
- detect_last_section() finds the final chorus/outro
- generate_grand_chorus() runs multi-voice RVC inference with stereo panning + reverb
"""

import asyncio
import io
import logging
import random
from collections import Counter
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from pydub import AudioSegment as PydubAudioSegment
from sqlalchemy.orm import Session

from ..config import CONVERTED_DIR
from ..models import Segment, VoiceModel, Song
from .rvc_service import convert_with_params

logger = logging.getLogger(__name__)

# Stereo panning positions for chorus voices (wider spread for grand chorus)
STEREO_PANS = [-0.5, 0.0, 0.5, -0.25, 0.25]

# Reverb settings (richer hall reverb with more taps)
REVERB_DELAY_MS = 60
REVERB_DECAY = 0.35
REVERB_MIX_DB = -3  # wet signal volume relative to dry

# Maximum chorus segments to process (prevents N segs x M voices explosion)
MAX_CHORUS_SEGMENTS = 8


def detect(segments: list) -> list[str]:
    """Detect chorus segments.

    Strategy 1: Find repeated lyric text (LRC-based segments).
    Strategy 2 (fallback for VAD segments): Use the last ~30% of segments
    as the "chorus section" based on typical song structure.

    Returns list of segment IDs identified as chorus.
    """
    if not segments:
        return []

    # Strategy 1: text repetition (works with LRC segments)
    text_counts = Counter(seg.text for seg in segments)
    repeated_texts = {text for text, count in text_counts.items() if count >= 2}

    chorus_ids = []
    for seg in segments:
        if seg.text in repeated_texts:
            chorus_ids.append(seg.id)

    if chorus_ids:
        logger.info(f"Detected {len(chorus_ids)} chorus segments via text repetition")
        return chorus_ids

    # Strategy 2: VAD fallback — last ~30% of segments
    # Most songs have the final chorus in the last third
    chorus_count = max(1, len(segments) // 3)
    chorus_ids = [seg.id for seg in segments[-chorus_count:]]
    logger.info(
        f"VAD fallback: using last {len(chorus_ids)}/{len(segments)} segments as chorus"
    )

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
        (REVERB_DELAY_MS * 5, REVERB_DECAY * 0.12),
        (REVERB_DELAY_MS * 7, REVERB_DECAY * 0.06),
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


def _apply_ensemble_variation(
    audio: PydubAudioSegment,
    voice_index: int,
) -> PydubAudioSegment:
    """Apply micro-variations to simulate natural ensemble singing.

    Real chorus sounds "big" because each singer has slightly different:
    - Timing: ±5-20ms offset
    - Pitch: ±5-12 cents offset (skipped for segments < 1.5s)
    - Volume: ±1-2dB variation

    Uses soundfile for round-trip to preserve original sample width.
    Must be called inside asyncio.to_thread() — this is a blocking function.
    """
    rng = random.Random(voice_index * 42)  # deterministic per voice

    # 1. Timing offset (±5-20ms)
    timing_offset_ms = rng.randint(5, 20) * rng.choice([-1, 1])

    if timing_offset_ms > 0:
        silence = PydubAudioSegment.silent(
            duration=timing_offset_ms, frame_rate=audio.frame_rate
        )
        audio = (silence + audio)[:len(audio)]
    elif timing_offset_ms < 0:
        audio = audio[abs(timing_offset_ms):]
        silence = PydubAudioSegment.silent(
            duration=abs(timing_offset_ms), frame_rate=audio.frame_rate
        )
        audio = (audio + silence)

    # 2. Pitch offset (±5-12 cents) — skip for short segments
    duration_s = len(audio) / 1000.0
    cents = rng.uniform(-12, 12)
    semitones = cents / 100.0

    if abs(semitones) > 0.01 and duration_s >= 1.5:
        # Round-trip via soundfile to preserve sample width
        buf_in = io.BytesIO()
        audio.export(buf_in, format="wav")
        buf_in.seek(0)
        samples, sr = sf.read(buf_in)

        if samples.ndim == 2:  # stereo
            shifted = np.column_stack([
                librosa.effects.pitch_shift(samples[:, ch], sr=sr, n_steps=semitones)
                for ch in range(samples.shape[1])
            ])
        else:
            shifted = librosa.effects.pitch_shift(samples, sr=sr, n_steps=semitones)

        buf_out = io.BytesIO()
        sf.write(buf_out, shifted, sr, format="WAV")
        buf_out.seek(0)
        audio = PydubAudioSegment.from_file(buf_out, format="wav")

    # 3. Volume variation (±1-2dB)
    volume_offset = rng.uniform(-2, 2)
    audio = audio + volume_offset

    return audio


def _mix_voices(voice_audios: list[PydubAudioSegment]) -> PydubAudioSegment:
    """Mix multiple voice audios into a tight chorus blend.

    Voices are panned slightly off-center for subtle width,
    not spread wide. All overlaid into one stereo mix.
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
        voice_audio = voice_audio.set_frame_rate(frame_rate)
        voice_audio = voice_audio.set_sample_width(sample_width)
        voice_audio = voice_audio.set_channels(2)

        # Slight pan for subtle width, tight center cluster
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

        # -2 dB per voice to prevent clipping when overlaid on lead
        panned = panned - 2
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
) -> list[str]:
    """Generate per-segment multi-voice chorus audio files.

    For each chorus segment:
    1. Load the original vocal audio
    2. Run RVC inference with each voice model (f0up_key=0)
    3. Mix voices with stereo panning
    4. Save as individual segment file (NOT concatenated)

    Returns list of paths to per-segment chorus audio files.
    """
    if not segment_ids:
        raise ValueError("No segment IDs provided for chorus")
    if not voice_model_ids:
        raise ValueError("No voice model IDs provided for chorus")

    logger.info(
        f"Generating grand chorus: {len(segment_ids)} segments x "
        f"{len(voice_model_ids)} voices for song {song_id}"
    )

    # Limit segments to prevent explosion
    if len(segment_ids) > MAX_CHORUS_SEGMENTS:
        logger.warning(
            f"Limiting chorus from {len(segment_ids)} to {MAX_CHORUS_SEGMENTS} segments"
        )
        segment_ids = segment_ids[:MAX_CHORUS_SEGMENTS]

    # Pre-load all voice models
    voices: list[VoiceModel] = []
    voice_data: list[tuple[bytes, bytes | None]] = []
    for vm_id in voice_model_ids:
        voice = await _load_voice_model(vm_id, db)
        pth_bytes, index_bytes = await _load_voice_model_bytes(voice)
        voices.append(voice)
        voice_data.append((pth_bytes, index_bytes))

    output_dir = CONVERTED_DIR / song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[str] = []

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

        vocal_bytes = await _read_audio_bytes(segment.vocal_path)

        # Run RVC with ALL voice models (everyone sings together)
        voice_audios: list[PydubAudioSegment] = []
        failed_voices = 0
        total_voices = len(voices)
        original_duration_ms = (segment.end_time - segment.start_time) * 1000

        for i, voice in enumerate(voices):
            pth_bytes, index_bytes = voice_data[i]
            f0_up_key = voice.f0up_key if voice.f0up_key else 0

            try:
                converted_bytes = await convert_with_params(
                    audio_bytes=vocal_bytes,
                    model_id=voice.id,
                    pth_bytes=pth_bytes,
                    index_bytes=index_bytes,
                    f0_method="rmvpe",
                    f0_up_key=f0_up_key,
                    index_rate=0.6,
                    filter_radius=3,
                    rms_mix_rate=0.5,
                    protect=0.5,
                    original_duration_ms=original_duration_ms,
                )

                audio_seg = await asyncio.to_thread(
                    PydubAudioSegment.from_file, io.BytesIO(converted_bytes), format="wav"
                )

                # Apply ensemble variation (micro-timing, micro-pitch, volume)
                audio_seg = await asyncio.to_thread(
                    _apply_ensemble_variation, audio_seg, i
                )
                voice_audios.append(audio_seg)

                logger.debug(
                    f"  Chorus line {segment.line_number}, voice {voice.name}: done"
                )
            except Exception as e:
                failed_voices += 1
                logger.error(
                    f"  RVC failed for chorus line {segment.line_number}, "
                    f"voice {voice.name}: {type(e).__name__}: {e}"
                )
                continue

        if not voice_audios:
            logger.error(
                f"Chorus line {segment.line_number}: ALL {total_voices} voices failed"
            )
            continue

        if failed_voices > 0:
            logger.warning(
                f"Chorus line {segment.line_number}: "
                f"{failed_voices}/{total_voices} voices failed, "
                f"mixing with {len(voice_audios)} voices"
            )

        # Mix all voices into one chorus audio
        mixed_segment = await asyncio.to_thread(_mix_voices, voice_audios)

        # Save and replace the segment's converted vocal with the chorus mix
        output_path = output_dir / f"chorus_line_{segment.line_number:03d}.wav"
        await asyncio.to_thread(
            mixed_segment.export, str(output_path), format="wav"
        )

        # Replace converted_vocal_path so _place_vocals_at_positions uses chorus
        segment.converted_vocal_path = str(output_path)
        db.commit()
        output_paths.append(str(output_path))

        logger.info(
            f"Chorus line {segment.line_number}: "
            f"{len(voice_audios)} voices mixed, {len(mixed_segment)}ms"
        )

    logger.info(
        f"Grand chorus done: {len(output_paths)} segments "
        f"with {len(voice_model_ids)} voices for song {song_id}"
    )

    return output_paths
