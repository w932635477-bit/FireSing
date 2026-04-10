"""RVC service — voice conversion via GPU server."""

import asyncio
import io
import logging
from pathlib import Path

import httpx
import librosa
import numpy as np
import soundfile as sf
from sqlalchemy.orm import Session

from ..config import GPU_SERVER_URL, GPU_REQUEST_TIMEOUT, CONVERTED_DIR
from ..models import Segment, VoiceModel, Song

logger = logging.getLogger(__name__)

# Maximum allowed duration drift before time-stretching (seconds)
_DURATION_TOLERANCE_S = 0.01  # 10ms — larger tolerance avoids unnecessary stretching

# Minimum segment duration for phase vocoder alignment (seconds)
# Below this, phase vocoder can produce audible artifacts on transients
_MIN_ALIGN_DURATION_S = 1.5


def _align_duration(
    converted_bytes: bytes, original_duration_ms: float
) -> bytes:
    """Time-stretch converted audio to match original segment duration.

    Uses librosa phase vocoder which preserves pitch, unlike the old
    resampling approach which changed pitch proportionally to the stretch ratio.

    RVC inference can change segment duration due to frame boundary effects
    and F0 processing. This function corrects the drift without affecting pitch.
    """
    audio, sr = sf.read(io.BytesIO(converted_bytes))
    current_duration_s = len(audio) / sr
    target_duration_s = original_duration_ms / 1000.0

    drift_s = abs(current_duration_s - target_duration_s)
    if drift_s < _DURATION_TOLERANCE_S:
        return converted_bytes

    # Skip alignment for very short segments (phase vocoder artifacts)
    if current_duration_s < _MIN_ALIGN_DURATION_S:
        logger.debug(
            f"Segment too short for alignment ({current_duration_s:.3f}s), "
            f"accepting {drift_s*1000:.1f}ms drift"
        )
        return converted_bytes

    rate = current_duration_s / target_duration_s

    # Only stretch if ratio is within reasonable range (0.5x to 2x)
    if rate < 0.5 or rate > 2.0:
        logger.warning(
            f"Duration drift too large: {current_duration_s:.3f}s -> {target_duration_s:.3f}s "
            f"(ratio {rate:.3f}), skipping alignment"
        )
        return converted_bytes

    logger.info(
        f"Aligning duration: {current_duration_s:.3f}s -> {target_duration_s:.3f}s "
        f"(ratio {rate:.4f}, drift {drift_s*1000:.1f}ms)"
    )

    # Phase vocoder: preserves pitch while stretching time
    if audio.ndim == 1:
        stretched = librosa.effects.time_stretch(audio, rate=rate)
    else:
        # Stereo: process each channel independently
        stretched = np.stack([
            librosa.effects.time_stretch(audio[:, c], rate=rate)
            for c in range(audio.shape[1])
        ], axis=1)

    buf = io.BytesIO()
    sf.write(buf, stretched, sr, format="WAV")
    return buf.getvalue()


async def convert(segment_id: str, db: Session) -> Path:
    """Convert a single segment's vocal using its assigned voice model.

    Returns path to the converted audio file.
    """
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise ValueError(f"Segment {segment_id} not found")
    if not segment.voice_model_id:
        raise ValueError(f"Segment {segment_id} has no voice model assigned")
    if not segment.vocal_path:
        raise ValueError(f"Segment {segment_id} has no vocal file")

    # Idempotent: skip if already converted
    if segment.converted_vocal_path and Path(segment.converted_vocal_path).exists():
        return Path(segment.converted_vocal_path)

    voice = db.query(VoiceModel).filter(VoiceModel.id == segment.voice_model_id).first()
    if not voice:
        raise ValueError(f"Voice model {segment.voice_model_id} not found")

    # Read source vocal
    with open(segment.vocal_path, "rb") as f:
        audio_bytes = f.read()

    # Read model files
    pth_path = Path(voice.model_path)
    with open(pth_path, "rb") as f:
        pth_bytes = f.read()

    index_bytes = None
    if voice.index_path and Path(voice.index_path).exists():
        with open(voice.index_path, "rb") as f:
            index_bytes = f.read()

    # Call GPU server with duration alignment built in
    original_duration_ms = (segment.end_time - segment.start_time) * 1000
    converted_bytes = await _call_gpu_rvc(
        audio_bytes=audio_bytes,
        model_id=voice.id,
        pth_bytes=pth_bytes,
        index_bytes=index_bytes,
        original_duration_ms=original_duration_ms,
    )

    # Save converted audio
    output_dir = CONVERTED_DIR / segment.song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"line_{segment.line_number:03d}_converted.wav"
    output_path.write_bytes(converted_bytes)

    # Update database
    segment.converted_vocal_path = str(output_path)
    db.commit()

    logger.info(
        f"RVC convert done: segment {segment.line_number}, "
        f"{len(converted_bytes)/1024:.1f}KB"
    )
    return output_path


async def convert_all(song_id: str, db: Session) -> list[Path]:
    """Convert all assigned segments for a song.

    Returns list of converted audio paths.
    """
    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )

    paths = []
    for seg in segments:
        if not seg.voice_model_id:
            logger.warning(f"Segment {seg.id} (line {seg.line_number}) has no voice, skipping")
            continue
        path = await convert(seg.id, db)
        paths.append(path)

    logger.info(f"RVC convert_all: {len(paths)}/{len(segments)} segments for song {song_id}")
    return paths


async def convert_with_params(
    audio_bytes: bytes,
    model_id: str,
    pth_bytes: bytes,
    index_bytes: bytes | None = None,
    f0_method: str = "rmvpe",
    f0_up_key: int = 0,
    index_rate: float = 0.5,
    filter_radius: int = 3,
    rms_mix_rate: float = 0.25,
    protect: float = 0.5,
    original_duration_ms: float | None = None,
) -> bytes:
    """Send vocal + model to GPU server with custom RVC parameters.

    Returns converted WAV bytes.
    If original_duration_ms is provided, applies pitch-preserving duration alignment.
    """
    url = f"{GPU_SERVER_URL}/infer/rvc"

    files = {
        "audio": ("segment.wav", audio_bytes, "audio/wav"),
        "pth_file": ("model.pth", pth_bytes, "application/octet-stream"),
    }
    data = {
        "model_id": model_id,
        "f0_method": f0_method,
        "f0up_key": str(f0_up_key),
        "index_rate": str(index_rate),
        "filter_radius": str(filter_radius),
        "rms_mix_rate": str(rms_mix_rate),
        "protect": str(protect),
    }
    if index_bytes:
        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")

    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=GPU_REQUEST_TIMEOUT, proxy=None) as client:
                resp = await client.post(url, files=files, data=data)
                resp.raise_for_status()
                result = resp.content

            # Apply pitch-preserving duration alignment if requested
            if original_duration_ms is not None:
                result = await asyncio.to_thread(
                    _align_duration, result, original_duration_ms
                )

            return result
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise ConnectionError(
                f"GPU server unreachable after 3 attempts: {last_error}"
            )

    raise ConnectionError(f"GPU server unreachable after 3 attempts: {last_error}")


async def _call_gpu_rvc(
    audio_bytes: bytes,
    model_id: str,
    pth_bytes: bytes,
    index_bytes: bytes | None = None,
    original_duration_ms: float | None = None,
) -> bytes:
    """Send vocal + model to GPU server, return converted WAV bytes.

    Uses model_id to reference cached models (avoid re-upload on subsequent calls).
    If original_duration_ms is provided, applies pitch-preserving duration alignment.
    """
    return await convert_with_params(
        audio_bytes=audio_bytes,
        model_id=model_id,
        pth_bytes=pth_bytes,
        index_bytes=index_bytes,
        f0_method="rmvpe",
        f0_up_key=0,
        index_rate=0.6,
        filter_radius=3,
        rms_mix_rate=0.25,
        protect=0.5,
        original_duration_ms=original_duration_ms,
    )


async def convert_batch(
    song_id: str, db: Session
) -> list[Path]:
    """Batch RVC conversion: group segments by voice model, process in parallel.

    Phase 2 optimization: uses asyncio.gather() to send batch requests for all
    voice models concurrently. The GPU server caches models in VRAM, so subsequent
    requests skip the ~2s model load overhead.

    Returns list of converted audio paths.
    """
    segments = (
        db.query(Segment)
        .filter(
            Segment.song_id == song_id,
            Segment.voice_model_id.isnot(None),
        )
        .order_by(Segment.line_number)
        .all()
    )

    if not segments:
        logger.warning(f"No assigned segments for song {song_id}")
        return []

    # Group segments by voice model
    voice_segments: dict[str, list[Segment]] = {}
    for seg in segments:
        vid = seg.voice_model_id
        if vid not in voice_segments:
            voice_segments[vid] = []
        voice_segments[vid].append(seg)

    logger.info(
        f"Batch RVC: {len(segments)} segments across {len(voice_segments)} voices "
        f"for song {song_id}"
    )

    # Separate already-converted segments from those needing processing
    all_paths: list[Path] = []
    voice_work: list[tuple[str, list[tuple[bytes, Segment]], bytes, bytes | None]] = []

    for voice_id, voice_segs in voice_segments.items():
        voice = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
        if not voice:
            logger.error(f"Voice model {voice_id} not found, skipping segments")
            continue

        # Read model files
        pth_path = Path(voice.model_path)
        with open(pth_path, "rb") as f:
            pth_bytes = f.read()

        index_bytes = None
        if voice.index_path and Path(voice.index_path).exists():
            with open(voice.index_path, "rb") as f:
                index_bytes = f.read()

        # Collect audio for segments needing conversion
        audio_list: list[tuple[bytes, Segment]] = []
        for seg in voice_segs:
            if seg.converted_vocal_path and Path(seg.converted_vocal_path).exists():
                all_paths.append(Path(seg.converted_vocal_path))
                continue
            if not seg.vocal_path:
                logger.warning(f"Segment {seg.id} has no vocal file, skipping")
                continue
            with open(seg.vocal_path, "rb") as f:
                audio_bytes = f.read()
            audio_list.append((audio_bytes, seg))

        if audio_list:
            voice_work.append((voice_id, audio_list, pth_bytes, index_bytes))

    if not voice_work:
        logger.info(f"Batch RVC: all segments already converted for song {song_id}")
        return all_paths

    # Process all voices in parallel via asyncio.gather()
    logger.info(f"Launching {len(voice_work)} parallel batch RVC requests")

    async def _process_voice(voice_id, audio_list, pth_bytes, index_bytes):
        """Process one voice model's segments via batch endpoint."""
        converted_map = await _call_gpu_rvc_batch(
            audio_list=audio_list,
            model_id=voice_id,
            pth_bytes=pth_bytes,
            index_bytes=index_bytes,
        )

        # Save results
        output_dir = CONVERTED_DIR / song_id
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for audio_bytes, seg in audio_list:
            result_bytes = converted_map[seg.id]

            # Apply duration alignment
            original_duration_ms = (seg.end_time - seg.start_time) * 1000
            result_bytes = await asyncio.to_thread(
                _align_duration, result_bytes, original_duration_ms
            )

            output_path = output_dir / f"line_{seg.line_number:03d}_converted.wav"
            output_path.write_bytes(result_bytes)

            seg.converted_vocal_path = str(output_path)
            paths.append(output_path)

        return paths

    results = await asyncio.gather(
        *[_process_voice(*args) for args in voice_work],
        return_exceptions=True,
    )

    # Collect results, log any failures
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            voice_id = voice_work[i][0]
            logger.error(f"Batch RVC failed for voice {voice_id}: {result}")
            continue
        all_paths.extend(result)

    db.commit()

    logger.info(
        f"Batch RVC done: {len(all_paths)} segments converted for song {song_id}"
    )
    return all_paths


async def _call_gpu_rvc_batch(
    audio_list: list[tuple[bytes, Segment]],
    model_id: str,
    pth_bytes: bytes,
    index_bytes: bytes | None = None,
) -> dict[str, bytes]:
    """Call GPU server batch endpoint. Returns {segment_id: wav_bytes}.

    Groups all segments for one voice model into a single request.
    Model loaded once on GPU side, all segments processed sequentially.
    """
    url = f"{GPU_SERVER_URL}/infer/rvc_batch_v2"

    # Build multipart form data
    files = {
        "pth_file": ("model.pth", pth_bytes, "application/octet-stream"),
    }
    data = {
        "model_id": model_id,
        "f0_method": "rmvpe",
        "f0up_key": "0",
        "index_rate": "0.6",
        "filter_radius": "3",
        "rms_mix_rate": "0.25",
        "protect": "0.5",
    }
    if index_bytes:
        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")

    # Add audio files as audio_0, audio_1, ...
    seg_order = []
    for idx, (audio_bytes, seg) in enumerate(audio_list):
        files[f"audio_{idx}"] = (
            f"segment_{idx}.wav", audio_bytes, "audio/wav"
        )
        seg_order.append(seg)

    # Retry logic (same as single-segment)
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=GPU_REQUEST_TIMEOUT, proxy=None) as client:
                resp = await client.post(url, files=files, data=data)
                resp.raise_for_status()

            # Parse multipart response
            content_type = resp.headers.get("content-type", "")
            boundary = content_type.split("boundary=")[-1]
            body = resp.content
            parts = body.split(f"--{boundary}".encode())

            # Extract converted audio from multipart
            result_map = {}
            for part in parts:
                if b'name="converted_' not in part:
                    continue
                # Parse index from name
                name_start = part.find(b'name="converted_')
                name_end = part.find(b'"', name_start + 7)
                name = part[name_start + 7:name_end].decode()
                idx = int(name.replace("converted_", ""))

                # Extract audio bytes
                audio_start = part.find(b"\r\n\r\n")
                if audio_start == -1:
                    continue
                audio_bytes = part[audio_start + 4:].rsplit(b"\r\n", 1)[0]

                if idx < len(seg_order):
                    result_map[seg_order[idx].id] = audio_bytes

            if len(result_map) != len(audio_list):
                logger.warning(
                    f"Batch response mismatch: expected {len(audio_list)}, "
                    f"got {len(result_map)} results"
                )

            return result_map

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise ConnectionError(
                f"GPU server unreachable after 3 attempts: {last_error}"
            )

    raise ConnectionError(f"GPU server unreachable after 3 attempts: {last_error}")
