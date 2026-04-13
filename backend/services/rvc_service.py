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


def _apply_iir(x: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Apply IIR filter using direct form II transposed (lfilter equivalent).

    Same algorithm as scipy.signal.lfilter but pure numpy. No scipy dependency.
    """
    n = len(b)
    y = np.zeros_like(x)
    z = np.zeros(n - 1)

    for i in range(len(x)):
        y[i] = b[0] * x[i] + z[0]
        for j in range(n - 2):
            z[j] = b[j + 1] * x[i] - a[j + 1] * y[i] + z[j + 1]
        z[n - 2] = b[n - 1] * x[i] - a[n - 1] * y[i]

    return y


def _peaking_eq(freq: float, sr: float, gain_db: float, Q: float):
    """Design a peaking EQ biquad filter (boost or cut at specific frequency).

    Returns (b, a) coefficients for a second-order IIR filter.
    Reference: Audio EQ Cookbook by Robert Bristow-Johnson.
    """
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / (2 * Q)

    b0 = 1 + alpha * A
    b1 = -2 * cos_w0
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_w0
    a2 = 1 - alpha / A

    return np.array([b0, b1, b2]) / a0, np.array([1, a1 / a0, a2 / a0])


def _lowpass_biquad(freq: float, sr: float):
    """Design a 2nd-order Butterworth lowpass biquad filter."""
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * 0.7071)  # Q = 1/sqrt(2) for Butterworth

    b0 = (1 - np.cos(w0)) / 2
    b1 = 1 - np.cos(w0)
    b2 = (1 - np.cos(w0)) / 2
    a0 = 1 + alpha
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha

    return np.array([b0, b1, b2]) / a0, np.array([1, a1 / a0, a2 / a0])


def _process_vocal(converted_bytes: bytes) -> bytes:
    """Post-processing chain for RVC output.

    1. Compression + makeup gain — reduce dynamic range, boost overall level
    2. EQ presence boost (+2dB at 3.5kHz) — clarity and articulation
    3. De-ess (soft lowpass above 6kHz, -3dB) — reduce RVC sibilance

    Handles both mono (1D) and stereo (2D, shape Nx2) audio.
    No scipy dependency — all filters use raw biquad coefficients.
    """
    audio, sr = sf.read(io.BytesIO(converted_bytes))
    is_stereo = audio.ndim == 2

    # 1. Downward compression + makeup gain
    threshold = 0.3
    ratio = 2.0
    makeup_gain = 1.15  # +1.2dB

    if is_stereo:
        for ch in range(audio.shape[1]):
            channel = audio[:, ch]
            abs_ch = np.abs(channel)
            mask = abs_ch > threshold
            channel[mask] = np.sign(channel[mask]) * (
                threshold + (abs_ch[mask] - threshold) / ratio
            )
            audio[:, ch] = channel * makeup_gain
    else:
        abs_audio = np.abs(audio)
        mask = abs_audio > threshold
        audio[mask] = np.sign(audio[mask]) * (
            threshold + (abs_audio[mask] - threshold) / ratio
        )
        audio = audio * makeup_gain

    # 2. Presence EQ boost (+2dB at 3.5kHz, Q=1.5)
    b, a = _peaking_eq(3500, sr, 2.0, 1.5)
    if is_stereo:
        for ch in range(audio.shape[1]):
            audio[:, ch] = _apply_iir(audio[:, ch], b, a)
    else:
        audio = _apply_iir(audio, b, a)

    # 3. De-ess: soften sibilance band above 6kHz (30% mix)
    b_lp, a_lp = _lowpass_biquad(6000, sr)
    if is_stereo:
        deessed = np.column_stack([
            _apply_iir(audio[:, ch], b_lp, a_lp) for ch in range(audio.shape[1])
        ])
    else:
        deessed = _apply_iir(audio, b_lp, a_lp)
    audio = 0.7 * audio + 0.3 * deessed

    # Normalize to prevent clipping from EQ + makeup gain
    peak = np.max(np.abs(audio))
    if peak > 0.95:
        audio = audio * (0.95 / peak)

    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return buf.getvalue()


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

    # Use voice model's f0up_key override (default 0 = preserve original pitch)
    f0_up_key = voice.f0up_key if voice.f0up_key else 0
    logger.info(
        f"Segment {segment.line_number}: voice={voice.name}, "
        f"f0up_key={f0_up_key} (preserving original pitch)"
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
    processed_bytes = await asyncio.to_thread(_process_vocal, limited_bytes)
    output_path.write_bytes(processed_bytes)

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
    rms_mix_rate: float = 0.5,
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
        rms_mix_rate=0.5,
        protect=0.5,
        original_duration_ms=original_duration_ms,
    )


async def convert_batch(
    song_id: str, db: Session
) -> list[Path]:
    """Batch RVC conversion — preserves original pitch (f0up_key=0).

    For cover songs, preserving the original melody is critical.
    RVC handles different pitch ranges natively via its F0 detection (rmvpe).
    Auto pitch matching (shifting to match model's mean_f0) causes more harm
    than good: it shifts the melody away from the original, and MAX_SAFE_SHIFT
    truncation produces wrong pitches.

    Groups segments by voice_model_id for batch efficiency.
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

    # Group by voice_model_id (no per-segment pitch detection needed)
    voice_cache: dict[str, VoiceModel] = {}
    pitch_groups: dict[str, list[tuple[bytes, Segment]]] = {}
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

        # Use voice model's manual f0up_key override (default 0 = preserve original pitch)
        f0up_key = voice.f0up_key if voice.f0up_key else 0

        key = f"{vid}_{f0up_key}"
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
            result_bytes = await asyncio.to_thread(_process_vocal, result_bytes)

            output_path = output_dir / f"line_{seg.line_number:03d}_converted.wav"
            output_path.write_bytes(result_bytes)

            seg.converted_vocal_path = str(output_path)
            paths.append(output_path)

        return paths

    work_items = []
    for key, audio_list in pitch_groups.items():
        vid, fk_str = key.rsplit("_", 1)
        fk = int(fk_str)
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
        "rms_mix_rate": "0.5",
        "protect": "0.5",
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
