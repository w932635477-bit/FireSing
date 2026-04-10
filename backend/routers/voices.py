"""Voice models router — CRUD for RVC voice models."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session

from ..config import VOICES_DIR
from ..database import get_db
from ..models import VoiceModel
from ..schemas import VoiceModelResponse, VoiceModelListResponse

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
    name: str = Form(...),
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
    db.add(voice)
    db.commit()
    db.refresh(voice)

    return voice


def _assign_manual(segments, assignments, db):
    """Assign voices based on explicit user mapping."""
    # Build lookup: line_number -> voice_model_id
    lookup = {a.line_number: a.voice_model_id for a in assignments}

    # Validate all voice model IDs exist
    voice_ids = set(lookup.values())
    existing = db.query(VoiceModel.id).filter(VoiceModel.id.in_(voice_ids)).all()
    existing_ids = {r[0] for r in existing}
    missing = voice_ids - existing_ids
    if missing:
        raise HTTPException(400, f"Voice models not found: {missing}")

    count = 0
    for seg in segments:
        if seg.line_number in lookup:
            seg.voice_model_id = lookup[seg.line_number]
            count += 1

    db.commit()
    return VoiceAssignResponse(assigned_count=count)


def _assign_auto(segments, voice_pool, strategy, db):
    """Assign voices using round-robin or random strategy."""
    if not voice_pool:
        raise HTTPException(400, "voice_pool is required for auto assignment")

    # Validate voice pool
    existing = db.query(VoiceModel.id).filter(VoiceModel.id.in_(voice_pool)).all()
    existing_ids = {r[0] for r in existing}
    missing = set(voice_pool) - existing_ids
    if missing:
        raise HTTPException(400, f"Voice models not found: {missing}")

    import random

    count = 0
    for i, seg in enumerate(segments):
        if strategy == "round-robin":
            seg.voice_model_id = voice_pool[i % len(voice_pool)]
        elif strategy == "random":
            seg.voice_model_id = random.choice(voice_pool)
        else:
            raise HTTPException(400, f"Unknown strategy: {strategy}")
        count += 1

    db.commit()
    return VoiceAssignResponse(assigned_count=count)
