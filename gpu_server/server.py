"""FireSing GPU Inference Server.

Runs on AutoDL (or any GPU machine). Exposes Demucs and RVC inference endpoints.
The Mac backend sends audio bytes, this server processes on GPU and returns results.
"""

import os
import hashlib
import tempfile
import time
from pathlib import Path

import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

# PyTorch 2.6+ changed torch.load default to weights_only=True, breaking RVC.
# Monkey-patch to restore the old default.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

app = FastAPI(title="FireSing GPU Server", version="0.1.0")

# Model cache: hash -> local_path
_model_cache: dict[str, str] = {}

# F0 method priority: harvest (known-good) → crepe → rmvpe
_F0_FALLBACK_CHAIN = ["harvest", "crepe", "rmvpe"]
_available_f0_methods: list[str] = []

# Temp directory for inference I/O
TEMP_DIR = Path("/tmp/firesing_gpu")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


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
                import rvc_python.modules.rmvdpe  # noqa: F401
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

        # F0 method fallback: if requested method unavailable, use best available
        actual_f0 = f0_method
        if f0_method not in _available_f0_methods:
            if _available_f0_methods:
                actual_f0 = _available_f0_methods[0]
                print(
                    f"WARNING: f0 method '{f0_method}' unavailable, "
                    f"falling back to '{actual_f0}'"
                )
            else:
                raise HTTPException(500, f"No f0 methods available on this server")

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

        rvc.set_params(
            f0method=actual_f0,
            f0up_key=f0up_key,
            index_rate=index_rate,
            filter_radius=filter_radius,
            rms_mix_rate=rms_mix_rate,
            protect=protect,
        )

        rvc.infer_file(str(audio_path), str(output_path))
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
