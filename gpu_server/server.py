"""FireSing GPU Inference Server.

Runs on AutoDL (or any GPU machine). Exposes Demucs and RVC inference endpoints.
The Mac backend sends audio bytes, this server processes on GPU and returns results.
"""

import os
import hashlib
import logging
import tempfile
import time
from pathlib import Path

import torch
from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

logger = logging.getLogger(__name__)

# PyTorch 2.6+ changed torch.load default to weights_only=True, breaking RVC.
# Monkey-patch to restore the old default.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

app = FastAPI(title="FireSing GPU Server", version="0.1.0")

# Model file cache: hash -> local_path
_model_cache: dict[str, str] = {}

# Model instance cache: model_id -> RVCInference (model kept in VRAM)
_rvc_cache: dict[str, object] = {}
_MAX_CACHED_MODELS = 8

# F0 method priority: rmvpe (best) → harvest (reliable fallback)
_F0_FALLBACK_CHAIN = ["rmvpe", "harvest"]
_available_f0_methods: list[str] = []

# Temp directory for inference I/O
TEMP_DIR = Path("/tmp/firesing_gpu")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _get_or_load_rvc(model_id: str, local_pth: Path, local_index: Path | None = None):
    """Get cached RVC instance or load model into VRAM.

    Keeps models loaded between requests to avoid ~2s model load overhead.
    LRU eviction when cache is full.
    """
    from rvc_python.infer import RVCInference
    import glob as _glob

    if model_id in _rvc_cache:
        logger.info(f"Model '{model_id}' found in VRAM cache, reusing")
        return _rvc_cache[model_id]

    # Evict oldest if at capacity
    while len(_rvc_cache) >= _MAX_CACHED_MODELS:
        evict_id = next(iter(_rvc_cache))
        evict_rvc = _rvc_cache.pop(evict_id)
        try:
            evict_rvc.unload_model()
        except Exception:
            pass
        logger.info(f"Evicted model '{evict_id}' from VRAM cache")

    rvc = RVCInference(
        models_dir=str(local_pth.parent),
        device="cuda:0",
        version="v2",
    )
    pth_files = _glob.glob(str(local_pth))
    if pth_files:
        rvc.load_model(
            pth_files[0], version="v2",
            index_path=str(local_index) if local_index else None,
        )

    _rvc_cache[model_id] = rvc
    logger.info(
        f"Loaded model '{model_id}' into VRAM cache "
        f"({len(_rvc_cache)}/{_MAX_CACHED_MODELS})"
    )
    return rvc


@app.on_event("startup")
def startup():
    global _available_f0_methods
    if not torch.cuda.is_available():
        print("WARNING: No CUDA GPU detected!")
    else:
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Test which f0 methods are importable
    for method in _F0_FALLBACK_CHAIN:
        try:
            if method == "rmvpe":
                import rvc_python.lib.rmvpe  # noqa: F401
            elif method == "crepe":
                import crepe  # noqa: F401
            elif method == "harvest":
                import pyworld  # noqa: F401
            _available_f0_methods.append(method)
            print(f"  f0 method '{method}': OK")
        except ImportError:
            print(f"  f0 method '{method}': NOT AVAILABLE (import failed)")

    if not _available_f0_methods:
        print("WARNING: No f0 methods available! RVC inference will fail.")
    else:
        print(f"  f0 fallback chain: {' → '.join(_available_f0_methods)}")


@app.get("/health")
async def health():
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU"
    vram_total = torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0
    vram_used = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    return {
        "status": "ok",
        "gpu": gpu_name,
        "vram_total_gb": round(vram_total, 1),
        "vram_used_gb": round(vram_used, 2),
        "cached_models": list(_rvc_cache.keys()),
        "cache_size": len(_rvc_cache),
        "cache_max": _MAX_CACHED_MODELS,
    }


@app.post("/infer/demucs")
async def infer_demucs(audio: UploadFile = File(...)):
    """Demucs vocal separation. Returns vocals + instrumental as WAV bytes.

    Input: audio file (mp3/wav)
    Output: multipart response with vocals.wav and instrumental.wav
    Time: ~7s (RTX 4090D, 114s song)
    """
    import io
    import numpy as np
    import soundfile as sf
    from demucs.pretrained import get_model
    from demucs.apply import apply_model
    from demucs.audio import AudioFile

    # Save uploaded audio to temp file
    content = await audio.read()
    input_path = TEMP_DIR / f"input_{hashlib.md5(content).hexdigest()[:8]}{Path(audio.filename).suffix}"
    with open(input_path, "wb") as f:
        f.write(content)

    try:
        t_start = time.time()

        # Load model and separate
        model = get_model("htdemucs")
        model.to(torch.device("cuda:0"))
        model.eval()

        wav = AudioFile(str(input_path)).read(streams=0, samplerate=model.samplerate, channels=model.audio_channels)
        ref = wav.mean(0)
        wav_input = (wav - ref.mean()) / ref.std()

        with torch.no_grad():
            sources = apply_model(model, wav_input[None], device="cuda:0")[0]

        sources = sources * ref.std() + ref.mean()

        # Map sources: model.sources = ['drums', 'bass', 'other', 'vocals']
        source_map = {name: sources[i] for i, name in enumerate(model.sources)}
        vocals = source_map["vocals"]
        # Instrumental = everything except vocals
        instrumental = sum(source_map[k] for k in model.sources if k != "vocals")

        sr = model.samplerate

        # Convert to WAV bytes
        vocals_buf = io.BytesIO()
        sf.write(vocals_buf, vocals.cpu().numpy().T, sr, format="WAV")
        vocals_bytes = vocals_buf.getvalue()

        instr_buf = io.BytesIO()
        sf.write(instr_buf, instrumental.cpu().numpy().T, sr, format="WAV")
        instr_bytes = instr_buf.getvalue()

        elapsed = time.time() - t_start

        # Return as multipart (boundary-delimited)
        boundary = "----FireSingBoundary7MA4YWxkTrZu0gW"
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"vocals\"; filename=\"vocals.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode() + vocals_bytes + (
            f"\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"instrumental\"; filename=\"instrumental.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode() + instr_bytes + (
            f"\r\n--{boundary}--\r\n"
        ).encode()

        return Response(
            content=body,
            media_type=f"multipart/form-data; boundary={boundary}",
            headers={"X-Inference-Time": f"{elapsed:.2f}"},
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Demucs inference failed: {str(e)}")
    finally:
        input_path.unlink(missing_ok=True)


# Also patch torch.load inside rvc_python
try:
    import rvc_python
    import rvc_python.modules.vc.modules as _rvc_mod
    # Patch any torch.load references
except ImportError:
    pass


@app.post("/infer/rvc")
async def infer_rvc(
    audio: UploadFile = File(...),
    pth_file: UploadFile = File(None),
    model_id: str = Form(None),
    index_file: UploadFile = File(None),
    f0_method: str = Form("rmvpe"),
    f0up_key: int = Form(0),
    index_rate: float = Form(0.5),
    filter_radius: int = Form(3),
    rms_mix_rate: float = Form(0.25),
    protect: float = Form(0.5),
):
    """RVC voice conversion. Returns converted audio as WAV bytes.

    Supports two modes:
    1. Upload model: pth_file + audio (model cached for future use)
    2. Reference cached model: model_id + audio (no re-upload needed)

    Time: ~4.6s per segment (rmvpe f0, RTX 4090D)
    """
    import io
    import soundfile as sf
    from rvc_python.infer import RVCInference

    # Resolve model path
    local_pth = None
    if model_id and model_id in _model_cache:
        local_pth = _model_cache[model_id]
    elif pth_file:
        content = await pth_file.read()
        model_hash = hashlib.md5(content).hexdigest()[:12]
        local_pth = TEMP_DIR / "models" / f"{model_hash}.pth"
        local_pth.parent.mkdir(parents=True, exist_ok=True)
        with open(local_pth, "wb") as f:
            f.write(content)
        _model_cache[model_hash] = str(local_pth)
        # Also store by provided model_id if given
        if model_id:
            _model_cache[model_id] = str(local_pth)
    else:
        raise HTTPException(400, "Need model_id or pth_file")

    # Save index file if provided
    local_index = None
    if index_file:
        idx_content = await index_file.read()
        local_index = TEMP_DIR / "models" / f"{model_id or 'tmp'}_index.index"
        with open(local_index, "wb") as f:
            f.write(idx_content)

    # Save input audio to temp file
    audio_content = await audio.read()
    audio_path = TEMP_DIR / f"rvc_input_{hashlib.md5(audio_content).hexdigest()[:8]}.wav"
    with open(audio_path, "wb") as f:
        f.write(audio_content)

    # Output path
    output_path = TEMP_DIR / f"rvc_output_{hashlib.md5(audio_content).hexdigest()[:8]}.wav"

    try:
        t_start = time.time()

        # Ensure local_pth is a Path (cache stores strings)
        local_pth = Path(local_pth)

        # RVC inference
        rvc = RVCInference(
            models_dir=str(local_pth.parent),
            device="cuda:0",
            version="v2",
        )

        # Load model
        import glob
        pth_files = glob.glob(str(local_pth))
        if pth_files:
            rvc.load_model(pth_files[0], version="v2",
                          index_path=str(local_index) if local_index else None)

        # Try f0 methods with runtime fallback
        methods_to_try = []
        if f0_method in _available_f0_methods:
            methods_to_try.append(f0_method)
        for m in _available_f0_methods:
            if m != f0_method:
                methods_to_try.append(m)

        if not methods_to_try:
            raise HTTPException(500, "No f0 methods available on this server")

        last_error = None
        for actual_f0 in methods_to_try:
            try:
                rvc.set_params(
                    f0method=actual_f0,
                    f0up_key=f0up_key,
                    index_rate=index_rate,
                    filter_radius=filter_radius,
                    rms_mix_rate=rms_mix_rate,
                    protect=protect,
                )
                rvc.infer_file(str(audio_path), str(output_path))
                # Success
                if actual_f0 != f0_method:
                    print(
                        f"WARNING: f0 '{f0_method}' failed at runtime, "
                        f"fell back to '{actual_f0}'"
                    )
                break
            except Exception as f0_err:
                last_error = f0_err
                print(f"WARNING: f0 method '{actual_f0}' failed: {f0_err}")
                if actual_f0 != methods_to_try[-1]:
                    print(f"  Retrying with next f0 method...")
                continue
        else:
            raise last_error

        rvc.unload_model()

        elapsed = time.time() - t_start
        print(
            f"RVC inference: f0={actual_f0}, pitch={f0up_key}, "
            f"index_rate={index_rate}, model={model_id}, "
            f"time={elapsed:.2f}s"
        )

        # Read output and return as WAV bytes
        with open(output_path, "rb") as f:
            result_bytes = f.read()

        return Response(
            content=result_bytes,
            media_type="audio/wav",
            headers={"X-Inference-Time": f"{elapsed:.2f}"},
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"RVC inference failed: {str(e)}")
    finally:
        audio_path.unlink(missing_ok=True)
        output_path.unlink(missing_ok=True)
        if local_index:
            local_index.unlink(missing_ok=True)


@app.post("/infer/rvc_batch")
async def infer_rvc_batch(
    pth_file: UploadFile = File(...),
    model_id: str = Form(...),
    index_file: UploadFile = File(None),
    f0_method: str = Form("rmvpe"),
    f0up_key: int = Form(0),
    index_rate: float = Form(0.5),
    filter_radius: int = Form(3),
    rms_mix_rate: float = Form(0.25),
    protect: float = Form(0.5),
):
    """Batch RVC voice conversion. Load model once, process N audio segments.

    Accepts one model + multiple audio files. Returns all converted audio
    packed into a multipart response.

    Form fields:
    - pth_file: RVC model (.pth)
    - model_id: Cache key for the model
    - index_file: Optional feature index file
    - f0_method, f0up_key, etc.: RVC parameters (same as /infer/rvc)

    Audio files are submitted as "audio_0", "audio_1", ..., "audio_N".
    Duration info as "duration_0", "duration_1", etc. (ms, for alignment).

    Returns multipart with converted_0.wav, converted_1.wav, etc.
    Headers: X-Inference-Time, X-Segment-Count
    """
    from rvc_python.infer import RVCInference

    # --- Resolve model path (same logic as infer_rvc) ---
    local_pth = None
    if model_id and model_id in _model_cache:
        local_pth = _model_cache[model_id]
    elif pth_file:
        content = await pth_file.read()
        model_hash = hashlib.md5(content).hexdigest()[:12]
        local_pth = TEMP_DIR / "models" / f"{model_hash}.pth"
        local_pth.parent.mkdir(parents=True, exist_ok=True)
        with open(local_pth, "wb") as f:
            f.write(content)
        _model_cache[model_hash] = str(local_pth)
        if model_id:
            _model_cache[model_id] = str(local_pth)
    else:
        raise HTTPException(400, "Need model_id or pth_file")

    # Save index file if provided
    local_index = None
    if index_file:
        idx_content = await index_file.read()
        local_index = TEMP_DIR / "models" / f"{model_id}_index.index"
        with open(local_index, "wb") as f:
            f.write(idx_content)

    # --- Collect audio segments from form data ---
    # FastAPI doesn't support dynamic file fields, so we parse from raw request
    # Using a convention: audio_0, audio_1, ... and duration_0, duration_1, ...
    from fastapi import Request
    # We need the raw form, so we accept files as a list
    # Alternative: accept a tar/zip of audio files

    # Actually, FastAPI Form + File mixing is limited for dynamic counts.
    # We'll use a simpler approach: accept a multipart with files named audio_0..N
    # and durations as form fields duration_0..N

    # Since FastAPI doesn't easily handle dynamic multipart fields,
    # we use the Request object directly via a workaround:
    # Accept the files as a single tar archive or use the starlette form parser.

    raise HTTPException(
        501,
        "Use /infer/rvc_batch_v2 which accepts a multipart with audio_N files"
    )


@app.post("/model/clear_cache")
async def clear_model_cache():
    """Unload all cached RVC models from VRAM."""
    evicted = []
    for mid, rvc in list(_rvc_cache.items()):
        try:
            rvc.unload_model()
        except Exception:
            pass
        evicted.append(mid)
    _rvc_cache.clear()
    vram_used = torch.cuda.memory_allocated() / 1024**3 if torch.cuda.is_available() else 0
    return {"cleared": evicted, "vram_used_gb": round(vram_used, 2)}


@app.post("/infer/rvc_batch_v2")
async def infer_rvc_batch_v2(request: Request):
    """Batch RVC: load model once, infer N segments.

    Multipart form data:
    - pth_file: RVC model (.pth) — required
    - model_id: string cache key — required
    - index_file: .index file — optional
    - f0_method: string (default "rmvpe")
    - f0up_key: int (default 0)
    - index_rate: float (default 0.5)
    - filter_radius: int (default 3)
    - rms_mix_rate: float (default 0.25)
    - protect: float (default 0.5)
    - audio_0, audio_1, ...: WAV files — at least 1 required
    - duration_0, duration_1, ...: float ms — optional (for alignment)

    Returns multipart response:
    - converted_0.wav, converted_1.wav, ...
    - X-Inference-Time header (total)
    - X-Segment-Count header
    """
    from fastapi import Request as _Req
    import glob

    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        raise HTTPException(400, "Expected multipart/form-data")

    # Parse multipart using Starlette's built-in form parser
    form = await request.form()

    # Extract model params
    model_id = form.get("model_id")
    if not model_id:
        raise HTTPException(400, "model_id is required")

    pth_upload = form.get("pth_file")
    if not pth_upload:
        raise HTTPException(400, "pth_file is required")

    # RVC params
    f0_method = str(form.get("f0_method", "rmvpe"))
    f0up_key = int(form.get("f0up_key", 0))
    index_rate = float(form.get("index_rate", 0.5))
    filter_radius = int(form.get("filter_radius", 3))
    rms_mix_rate = float(form.get("rms_mix_rate", 0.25))
    protect = float(form.get("protect", 0.5))

    # --- Resolve model path ---
    local_pth = None
    if model_id in _model_cache:
        local_pth = _model_cache[model_id]
    else:
        pth_content = await pth_upload.read()
        model_hash = hashlib.md5(pth_content).hexdigest()[:12]
        local_pth = TEMP_DIR / "models" / f"{model_hash}.pth"
        local_pth.parent.mkdir(parents=True, exist_ok=True)
        with open(local_pth, "wb") as f:
            f.write(pth_content)
        _model_cache[model_hash] = str(local_pth)
        _model_cache[model_id] = str(local_pth)

    # Save index if provided
    local_index = None
    index_upload = form.get("index_file")
    if index_upload:
        idx_content = await index_upload.read()
        local_index = TEMP_DIR / "models" / f"{model_id}_index.index"
        with open(local_index, "wb") as f:
            f.write(idx_content)

    # --- Collect audio segments ---
    audio_files = {}  # index -> (bytes, duration_ms|None)
    idx = 0
    while True:
        key = f"audio_{idx}"
        if key not in form:
            break
        audio_upload = form[key]
        audio_bytes = await audio_upload.read()
        duration_key = f"duration_{idx}"
        duration_ms = float(form.get(duration_key)) if duration_key in form else None
        audio_files[idx] = (audio_bytes, duration_ms)
        idx += 1

    if not audio_files:
        raise HTTPException(400, "No audio files provided (use audio_0, audio_1, ...)")

    segment_count = len(audio_files)
    logger.info(f"Batch RVC: model={model_id}, segments={segment_count}")

    # --- Load model (use VRAM cache) ---
    local_pth = Path(local_pth)
    t_load_start = time.time()
    rvc = _get_or_load_rvc(model_id, local_pth, local_index)
    load_time = time.time() - t_load_start
    logger.info(f"Model load: {load_time:.2f}s (cache_hit={model_id in _rvc_cache or load_time < 0.1})")

    # Determine f0 method with fallback
    methods_to_try = []
    if f0_method in _available_f0_methods:
        methods_to_try.append(f0_method)
    for m in _available_f0_methods:
        if m != f0_method:
            methods_to_try.append(m)
    if not methods_to_try:
        raise HTTPException(500, "No f0 methods available on this server")

    t_start = time.time()
    results = {}  # idx -> WAV bytes

    try:
        # --- Process each segment with the same model loaded ---
        for idx, (audio_bytes, duration_ms) in audio_files.items():
            # Write input to temp file
            audio_path = TEMP_DIR / f"batch_{model_id}_{idx}_input.wav"
            output_path = TEMP_DIR / f"batch_{model_id}_{idx}_output.wav"
            audio_path.write_bytes(audio_bytes)

            # Try f0 methods with runtime fallback
            actual_f0 = None
            last_error = None
            for m in methods_to_try:
                try:
                    rvc.set_params(
                        f0method=m,
                        f0up_key=f0up_key,
                        index_rate=index_rate,
                        filter_radius=filter_radius,
                        rms_mix_rate=rms_mix_rate,
                        protect=protect,
                    )
                    rvc.infer_file(str(audio_path), str(output_path))
                    actual_f0 = m
                    break
                except Exception as f0_err:
                    last_error = f0_err
                    continue

            if actual_f0 is None:
                raise last_error

            # Read result
            result_bytes = output_path.read_bytes()
            results[idx] = result_bytes

            # Cleanup per-segment temp files
            audio_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

        # Keep model in VRAM cache (don't unload)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Batch RVC failed on segment: {str(e)}")
    finally:
        if local_index:
            local_index.unlink(missing_ok=True)

    elapsed = time.time() - t_start
    logger.info(
        f"Batch RVC done: {segment_count} segments in {elapsed:.2f}s "
        f"({elapsed/segment_count:.2f}s/seg), f0={f0_method}"
    )

    # --- Build multipart response ---
    boundary = "----FireSingBatchBoundary7MA4YWxkTrZu0gW"
    parts = []
    for idx in sorted(results.keys()):
        part_header = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"converted_{idx}\"; "
            f"filename=\"converted_{idx}.wav\"\r\n"
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode()
        parts.append(part_header + results[idx])

    body = b"\r\n".join(parts) + f"\r\n--{boundary}--\r\n".encode()

    return Response(
        content=body,
        media_type=f"multipart/form-data; boundary={boundary}",
        headers={
            "X-Inference-Time": f"{elapsed:.2f}",
            "X-Segment-Count": str(segment_count),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
