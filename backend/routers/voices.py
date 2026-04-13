"""Voice profiles router — CRUD for voice parameter profiles."""

import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_auth
from ..models import VoiceModel, User
from ..schemas import VoiceModelResponse, VoiceModelListResponse, VoiceModelUpdateRequest

router = APIRouter()


@router.get("", response_model=VoiceModelListResponse)
async def list_voices(db: Session = Depends(get_db)):
    """List all voice profiles (presets + custom)."""
    voices = db.query(VoiceModel).order_by(VoiceModel.created_at.desc()).all()
    return {"voices": voices}


@router.post("", response_model=VoiceModelResponse, status_code=201)
async def create_voice(
    name: str,
    pitch_shift: float = 0.0,
    formant_shift: float = 0.0,
    eq_profile: str = "natural",
    color: str = "#4A90D9",
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a custom voice profile with parameter settings.

    No file upload needed — voice profiles are parameter-based.
    """
    if not -5.0 <= pitch_shift <= 5.0:
        raise HTTPException(400, "pitch_shift must be between -5.0 and 5.0")
    if not -3.0 <= formant_shift <= 3.0:
        raise HTTPException(400, "formant_shift must be between -3.0 and 3.0")
    valid_eq = {"natural", "bright", "dark", "nasal", "deep"}
    if eq_profile not in valid_eq:
        raise HTTPException(400, f"eq_profile must be one of: {', '.join(valid_eq)}")

    voice = VoiceModel(
        id=uuid.uuid4().hex[:12],
        name=name,
        is_preset=False,
        pitch_shift=pitch_shift,
        formant_shift=formant_shift,
        eq_profile=eq_profile,
        color=color,
    )
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
    """Update voice profile parameters."""
    voice = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
    if not voice:
        raise HTTPException(404, f"Voice profile {voice_id} not found")

    if data.name is not None:
        voice.name = data.name
    if data.pitch_shift is not None:
        voice.pitch_shift = data.pitch_shift
    if data.formant_shift is not None:
        voice.formant_shift = data.formant_shift
    if data.eq_profile is not None:
        voice.eq_profile = data.eq_profile
    if data.color is not None:
        voice.color = data.color

    db.commit()
    db.refresh(voice)
    return voice


@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Delete a voice profile. Presets cannot be deleted."""
    voice = db.query(VoiceModel).filter(VoiceModel.id == voice_id).first()
    if not voice:
        raise HTTPException(404, f"Voice profile {voice_id} not found")

    if voice.is_preset:
        raise HTTPException(400, "Cannot delete preset voice profiles")

    # Check if any segments are using this voice
    from ..models import Segment
    assigned = db.query(Segment).filter(Segment.voice_model_id == voice_id).first()
    if assigned:
        raise HTTPException(
            409,
            f"Voice profile '{voice.name}' is assigned to segments. "
            "Remove assignments before deleting."
        )

    db.delete(voice)
    db.commit()
    return {"deleted": True}
