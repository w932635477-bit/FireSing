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

# Peak limit: prevent clipping distortion from RVC models with extreme peaks
_PEAK_LIMIT_DB = -1.0

# Maximum allowed duration drift before time-stretching (seconds)
_DURATION_TOLERANCE_S = 0.01  # 10ms — larger tolerance avoids unnecessary stretching

# Minimum segment duration for phase vocoder alignment (seconds)
# Below this, phase vocoder can produce audible artifacts on transients
_MIN_ALIGN_DURATION_S = 1.5


def _limit_audio(converted_bytes: bytes, peak_db: float = _PEAK_LIMIT_DB) -> bytes:
    """Peak-limit converted audio to prevent clipping distortion.

    Some RVC models produce extreme peaks (0.97+) with low RMS, causing
    audible distortion. This normalizes the peak to a safe level.
    """
    audio, sr = sf.read(io.BytesIO(converted_bytes))
    peak = np.max(np.abs(audio))
    target = 10 ** (peak_db / 20.0)
    if peak > target:
        audio = audio * (target / peak)
        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        return buf.getvalue()
    return converted_bytes


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

    # Auto-detect F0 and compute pitch shift
    from .f0_service import detect_mean_f0, compute_f0up_key
    source_f0 = await asyncio.to_thread(detect_mean_f0, segment.vocal_path)
    f0_up_key = compute_f0up_key(
        source_f0=source_f0,
        target_f0=voice.mean_f0_hz,
        manual_override=voice.f0up_key,
    )
    logger.info(
        f"Segment {segment.line_number}: source_f0={source_f0}, "
        f"voice_f0={voice.mean_f0_hz}, f0up_key={f0_up_key}"
    )

    # Call GPU server with duration alignment built in
    original_duration_ms = (segment.end_time - segment.start_time) * 1000
    converted_bytes = await _call_gpu_rvc(
        audio_bytes=audio_bytes,
        model_id=voice.id,
        pth_bytes=pth_bytes,
        index_bytes=index_bytes,
        original_duration_ms=original_duration_ms,
        f0_up_key=f0_up_key,
    )

    # Save converted audio
    output_dir = CONVERTED_DIR / segment.song_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"line_{segment.line_number:03d}_converted.wav"
    limited_bytes = await asyncio.to_thread(_limit_audio, converted_bytes)
    output_path.write_bytes(limited_bytes)

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


async def _is_model_cached(model_id: str) -> bool:
    """Check if GPU server already has this model cached in VRAM."""
    try:
        async with httpx.AsyncClient(timeout=3.0, proxy=None, trust_env=False) as client:
            resp = await client.get(f"{GPU_SERVER_URL}/model/has/{model_id}")
            if resp.status_code == 200:
                return resp.json().get("cached", False)
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    return False


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
    skip_cache_check: bool = False,
) -> bytes:
    """Send vocal + model to GPU server with custom RVC parameters.

    Returns converted WAV bytes.
    If original_duration_ms is provided, applies pitch-preserving duration alignment.

    Optimization: checks GPU model cache first and skips uploading pth_file (50-100MB)
    if the model is already loaded in VRAM.
    """
    url = f"{GPU_SERVER_URL}/infer/rvc"

    # Check if model is already cached on GPU — skip 50-100MB upload
    cached = not skip_cache_check and await _is_model_cached(model_id)

    files = {
        "audio": ("segment.wav", audio_bytes, "audio/wav"),
    }
    if not cached:
        files["pth_file"] = ("model.pth", pth_bytes, "application/octet-stream")
    data = {
        "model_id": model_id,
        "f0_method": f0_method,
        "f0up_key": str(f0_up_key),
        "index_rate": str(index_rate),
        "filter_radius": str(filter_radius),
        "rms_mix_rate": str(rms_mix_rate),
        "protect": str(protect),
    }
    if not cached and index_bytes:
        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")

    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=GPU_REQUEST_TIMEOUT, proxy=None, trust_env=False) as client:
                resp = await client.post(url, files=files, data=data)
                # If GPU says model not found (cache miss), retry with full upload
                if resp.status_code == 400 and cached:
                    cached = False
                    files["pth_file"] = ("model.pth", pth_bytes, "application/octet-stream")
                    if index_bytes:
                        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")
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
    f0_up_key: int = 0,
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
        f0_up_key=f0_up_key,
        index_rate=0.6,
        filter_radius=3,
        rms_mix_rate=0.25,
        protect=0.33,
        original_duration_ms=original_duration_ms,
    )


async def convert_batch(
    song_id: str, db: Session
) -> list[Path]:
    """Batch RVC conversion with auto pitch detection.

    Groups segments by (voice_model_id, f0up_key) for batch efficiency.
    Detects source F0 per segment and computes optimal pitch shift.
    """
    from .f0_service import detect_mean_f0, compute_f0up_key

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

    # Detect F0 for all segments in parallel
    seg_f0_map: dict[str, float | None] = {}
    f0_tasks = []
    f0_seg_ids = []
    for seg in segments:
        if seg.converted_vocal_path and Path(seg.converted_vocal_path).exists():
            continue
        if not seg.vocal_path:
            continue
        f0_tasks.append(asyncio.to_thread(detect_mean_f0, seg.vocal_path))
        f0_seg_ids.append(seg.id)

    if f0_tasks:
        f0_results = await asyncio.gather(*f0_tasks, return_exceptions=True)
        for seg_id, f0_result in zip(f0_seg_ids, f0_results):
            seg_f0_map[seg_id] = f0_result if not isinstance(f0_result, Exception) else None

    # Compute f0up_key per segment and group by (voice_id, f0up_key)
    voice_cache: dict[str, VoiceModel] = {}
    pitch_groups: dict[tuple[str, int], list[tuple[bytes, Segment]]] = {}
    group_model_data: dict[str, tuple[bytes, bytes | None]] = {}

    all_paths: list[Path] = []
    for seg in segments:
        if seg.converted_vocal_path and Path(seg.converted_vocal_path).exists():
            all_paths.append(Path(seg.converted_vocal_path))
            continue
        if not seg.vocal_path:
            continue

        vid = seg.voice_model_id
        if vid not in voice_cache:
            voice_cache[vid] = db.query(VoiceModel).filter(VoiceModel.id == vid).first()
        voice = voice_cache[vid]
        if not voice:
            continue

        # Cache model file bytes per voice
        if vid not in group_model_data:
            pth_path = Path(voice.model_path)
            pth_bytes = pth_path.read_bytes()
            index_bytes = None
            if voice.index_path and Path(voice.index_path).exists():
                index_bytes = Path(voice.index_path).read_bytes()
            group_model_data[vid] = (pth_bytes, index_bytes)

        # Compute f0up_key
        source_f0 = seg_f0_map.get(seg.id)
        f0up_key = compute_f0up_key(
            source_f0=source_f0,
            target_f0=voice.mean_f0_hz,
            manual_override=voice.f0up_key,
        )

        key = (vid, f0up_key)
        if key not in pitch_groups:
            pitch_groups[key] = []

        audio_bytes = Path(seg.vocal_path).read_bytes()
        pitch_groups[key].append((audio_bytes, seg))

    if not pitch_groups:
        logger.info(f"Batch RVC: all segments already converted for song {song_id}")
        return all_paths

    logger.info(
        f"Batch RVC: {sum(len(v) for v in pitch_groups.values())} segments "
        f"in {len(pitch_groups)} pitch groups for song {song_id}"
    )

    # Process each (voice, pitch) group in parallel
    async def _process_group(voice_id, f0up_key, audio_list, pth_bytes, index_bytes):
        converted_map = await _call_gpu_rvc_batch(
            audio_list=audio_list,
            model_id=voice_id,
            pth_bytes=pth_bytes,
            index_bytes=index_bytes,
            f0up_key=f0up_key,
        )

        output_dir = CONVERTED_DIR / song_id
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for audio_bytes, seg in audio_list:
            result_bytes = converted_map[seg.id]

            original_duration_ms = (seg.end_time - seg.start_time) * 1000
            result_bytes = await asyncio.to_thread(
                _align_duration, result_bytes, original_duration_ms
            )
            result_bytes = await asyncio.to_thread(_limit_audio, result_bytes)

            output_path = output_dir / f"line_{seg.line_number:03d}_converted.wav"
            output_path.write_bytes(result_bytes)

            seg.converted_vocal_path = str(output_path)
            paths.append(output_path)

        return paths

    work_items = []
    for (vid, fk), audio_list in pitch_groups.items():
        pth_bytes, index_bytes = group_model_data[vid]
        work_items.append((vid, fk, audio_list, pth_bytes, index_bytes))

    results = await asyncio.gather(
        *[_process_group(*args) for args in work_items],
        return_exceptions=True,
    )

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            vid, fk = work_items[i][0], work_items[i][1]
            logger.error(f"Batch RVC failed for voice {vid} f0up_key={fk}: {result}")
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
    f0up_key: int = 0,
) -> dict[str, bytes]:
    """Call GPU server batch endpoint. Returns {segment_id: wav_bytes}.

    Groups all segments for one voice model into a single request.
    Model loaded once on GPU side, all segments processed sequentially.
    """
    url = f"{GPU_SERVER_URL}/infer/rvc_batch_v2"

    # Build multipart form data — skip pth upload if model cached on GPU
    cached = await _is_model_cached(model_id)
    files = {}
    if not cached:
        files["pth_file"] = ("model.pth", pth_bytes, "application/octet-stream")
    data = {
        "model_id": model_id,
        "f0_method": "rmvpe",
        "f0up_key": str(f0up_key),
        "index_rate": "0.6",
        "filter_radius": "3",
        "rms_mix_rate": "0.25",
        "protect": "0.33",
    }
    if not cached and index_bytes:
        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")

    # Add audio files as audio_0, audio_1, ...
    seg_order = []
    for idx, (audio_bytes, seg) in enumerate(audio_list):
        files[f"audio_{idx}"] = (
            f"segment_{idx}.wav", audio_bytes, "audio/wav"
        )
        seg_order.append(seg)

    # Retry logic with cache-miss fallback
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=GPU_REQUEST_TIMEOUT, proxy=None, trust_env=False) as client:
                resp = await client.post(url, files=files, data=data)
                # If GPU says model not found (cache miss), retry with full upload
                if resp.status_code == 400 and cached:
                    cached = False
                    files["pth_file"] = ("model.pth", pth_bytes, "application/octet-stream")
                    if index_bytes:
                        files["index_file"] = ("model.index", index_bytes, "application/octet-stream")
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
                name_end = part.find(b'"', name_start + 6)
                name = part[name_start + 6:name_end].decode()
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
