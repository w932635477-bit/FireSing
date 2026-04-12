"""Voice models router — CRUD for RVC voice models."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from ..config import VOICES_DIR
from ..database import get_db
from ..dependencies import require_auth
from ..models import VoiceModel, User
from ..schemas import VoiceModelResponse, VoiceModelListResponse, VoiceModelUpdateRequest

router = APIRouter()


@router.get("", response_model=VoiceModelListResponse)
async def list_voices(db: Session = Depends(get_db)):
    """List all voice models."""
    voices = db.query(VoiceModel).order_by(VoiceModel.created_at.desc()).all()
    return {"voices": voices}


@router.post("", response_model=VoiceModelResponse, status_code=201)
async def upload_voice(
    pth_file: UploadFile = File(...),
    index_file: Optional[UploadFile] = File(None),
    reference_audio: Optional[UploadFile] = File(None),
    name: str = Form(...),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Upload a new voice model (.pth + optional .index).

    Validates model integrity before saving:
    - Minimum size: 10MB (real RVC v2 models are ~53-55MB)
    - torch.load() smoke test on CPU (catches truncated/corrupted files)
    """
    import torch

    if not pth_file.filename.endswith(".pth"):
        raise HTTPException(400, "Model file must be .pth")
    if index_file and not index_file.filename.endswith(".index"):
        raise HTTPException(400, "Index file must be .index")

    pth_content = await pth_file.read()

    # Size validation: real RVC models are 50MB+
    MIN_MODEL_BYTES = 10 * 1024 * 1024  # 10MB
    if len(pth_content) < MIN_MODEL_BYTES:
        raise HTTPException(
            400,
            f"Model file too small ({len(pth_content) / 1024 / 1024:.1f}MB). "
            f"Expected at least 10MB. File may be corrupted or incomplete."
        )

    # Integrity validation: verify torch can deserialize it
    import io
    try:
        torch.load(io.BytesIO(pth_content), map_location="cpu", weights_only=False)
    except Exception as e:
        raise HTTPException(
            400,
            f"Model file is not a valid PyTorch checkpoint: {str(e)}"
        )

    voice_id = uuid.uuid4().hex[:12]
    voice_dir = VOICES_DIR / voice_id
    voice_dir.mkdir(parents=True, exist_ok=True)

    pth_path = voice_dir / "model.pth"
    pth_path.write_bytes(pth_content)

    index_path = None
    if index_file:
        index_path = voice_dir / "model.index"
        index_content = await index_file.read()
        index_path.write_bytes(index_content)

    voice = VoiceModel(
        id=voice_id,
        name=name,
        model_path=str(pth_path),
        index_path=str(index_path) if index_path else None,
        is_preset=False,
    )

    # Auto-detect mean F0 from reference audio if provided
    if reference_audio:
        try:
            from ..services.f0_service import detect_mean_f0_from_bytes
            ref_bytes = await reference_audio.read()
            mean_f0 = detect_mean_f0_from_bytes(ref_bytes)
            if mean_f0:
                voice.mean_f0_hz = mean_f0
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"F0 detection failed for voice upload: {e}")

    db.add(voice)
    db.commit()
    db.refresh(voice)

    return voice


@router.patch("/{voice_id}", response_model=VoiceModelResponse)
async def update_voice(
    voice_id: str,
    data: VoiceModelUpdateRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update voice model settings (f0up_key, name)."""
    voice = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
    if not voice:
        raise HTTPException(404, f"Voice model {voice_id} not found")

    if data.name is not None:
        voice.name = data.name
    voice.f0up_key = data.f0up_key
    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Delete a voice model and its files."""
    voice = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
    if not voice:
        raise HTTPException(404, f"Voice model {voice_id} not found")

    # Check if any segments are using this voice
    from ..models import Segment
    assigned = db.query(Segment).filter(Segment.voice_model_id == voice_id).first()
    if assigned:
        raise HTTPException(
            409,
            f"Voice model '{voice.name}' is assigned to segments. "
            "Remove assignments before deleting."
        )

    # Delete files
    import shutil
    voice_dir = Path(voice.model_path).parent
    if voice_dir.exists():
        shutil.rmtree(voice_dir, ignore_errors=True)

    db.delete(voice)
    db.commit()
    return {"deleted": True}
