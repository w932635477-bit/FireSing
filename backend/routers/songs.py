"""Songs router — upload, list, get, delete songs."""

import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import SONGS_DIR, SEGMENTS_DIR, CONVERTED_DIR, OUTPUTS_DIR, MAX_AUDIO_SIZE_MB, ALLOWED_AUDIO_FORMATS
from ..database import get_db
from ..models import Song, Segment, VoiceModel
from ..schemas import (
    SongResponse, SongListResponse, SongDeleteResponse,
    SegmentListResponse, VoiceAssignRequest, VoiceAssignResponse,
)
from ..services.lyrics_service import parse_lrc, validate_segments, compute_end_times

router = APIRouter()


@router.post("", response_model=SongResponse, status_code=201)
async def upload_song(
    audio: UploadFile = File(...),
    lrc: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Upload a new song with optional LRC lyrics file."""
    # Validate audio format
    audio_ext = Path(audio.filename).suffix.lower()
    if audio_ext not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(400, f"Audio format {audio_ext} not allowed. Use: {ALLOWED_AUDIO_FORMATS}")

    # Generate song ID and directory
    song_id = uuid.uuid4().hex[:12]
    song_dir = SONGS_DIR / song_id
    song_dir.mkdir(parents=True, exist_ok=True)

    # Save audio file
    audio_path = song_dir / f"original{audio_ext}"
    content = await audio.read()

    if len(content) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
        shutil.rmtree(song_dir, ignore_errors=True)
        raise HTTPException(400, f"Audio file too large. Max {MAX_AUDIO_SIZE_MB}MB")

    with open(audio_path, "wb") as f:
        f.write(content)

    # Save LRC file if provided
    lrc_path = None
    if lrc:
        lrc_ext = Path(lrc.filename).suffix.lower()
        if lrc_ext not in {".lrc", ".txt"}:
            raise HTTPException(400, "Lyrics file must be .lrc or .txt")
        lrc_path = song_dir / f"lyrics{lrc_ext}"
        lrc_content = await lrc.read()
        with open(lrc_path, "wb") as f:
            f.write(lrc_content)

    # Create database record
    title = Path(audio.filename).stem
    song = Song(
        id=song_id,
        title=title,
        original_audio_path=str(audio_path),
        lrc_path=str(lrc_path) if lrc_path else None,
        status="uploaded",
    )
    db.add(song)
    db.commit()
    db.refresh(song)

    return song


@router.get("", response_model=SongListResponse)
async def list_songs(db: Session = Depends(get_db)):
    """List all songs."""
    songs = db.query(Song).order_by(Song.created_at.desc()).all()
    return {"songs": songs}


@router.get("/{song_id}", response_model=SongResponse)
async def get_song(song_id: str, db: Session = Depends(get_db)):
    """Get song details."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")
    return song


@router.delete("/{song_id}", response_model=SongDeleteResponse)
async def delete_song(song_id: str, db: Session = Depends(get_db)):
    """Delete a song and all associated files."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    # Delete files from all data directories
    for data_dir in [SONGS_DIR, SEGMENTS_DIR, CONVERTED_DIR, OUTPUTS_DIR]:
        song_dir = data_dir / song_id
        if song_dir.exists():
            shutil.rmtree(song_dir, ignore_errors=True)

    db.delete(song)
    db.commit()
    return {"deleted": True}


@router.put("/{song_id}/lrc")
async def upload_lrc(
    song_id: str,
    lrc: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload or replace LRC lyrics file for a song, parse and return segments."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    lrc_ext = Path(lrc.filename).suffix.lower()
    if lrc_ext not in {".lrc", ".txt"}:
        raise HTTPException(400, "Lyrics file must be .lrc or .txt")

    song_dir = SONGS_DIR / song_id
    lrc_path = song_dir / f"lyrics{lrc_ext}"
    content = await lrc.read()
    with open(lrc_path, "wb") as f:
        f.write(content)

    song.lrc_path = str(lrc_path)
    db.commit()

    # Parse LRC and return segment info
    try:
        lrc_lines = parse_lrc(lrc_path)
        lrc_lines = validate_segments(lrc_lines)
        segments_data = compute_end_times(lrc_lines)
    except ValueError as e:
        raise HTTPException(400, f"LRC parse error: {e}")

    return {"song_id": song_id, "lrc_path": str(lrc_path), "segments": segments_data}


@router.put("/{song_id}/monologue-audio")
async def upload_monologue_audio(
    song_id: str,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a recorded monologue audio file for a song."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    audio_ext = Path(audio.filename).suffix.lower()
    if audio_ext not in {".mp3", ".wav", ".ogg", ".m4a", ".webm"}:
        raise HTTPException(400, "Monologue audio must be mp3, wav, ogg, m4a, or webm")

    song_dir = SONGS_DIR / song_id
    song_dir.mkdir(parents=True, exist_ok=True)
    audio_path = song_dir / f"monologue{audio_ext}"

    # Check size from Content-Length header before reading into memory
    if audio.size is not None and audio.size > 10 * 1024 * 1024:
        raise HTTPException(400, "Monologue audio too large. Max 10MB")

    content = await audio.read()

    if len(content) > 10 * 1024 * 1024:  # 10MB limit for monologue
        raise HTTPException(400, "Monologue audio too large. Max 10MB")

    with open(audio_path, "wb") as f:
        f.write(content)

    song.monologue_audio_path = str(audio_path)
    db.commit()

    return {"song_id": song_id, "monologue_audio_path": str(audio_path)}


@router.get("/{song_id}/segments", response_model=SegmentListResponse)
async def list_segments(song_id: str, db: Session = Depends(get_db)):
    """List all segments for a song."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )
    return {"segments": segments}


class _SegmentUpdateBody(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@router.patch("/{song_id}/segments/{segment_id}")
async def update_segment_timestamps(
    song_id: str,
    segment_id: str,
    body: _SegmentUpdateBody,
    db: Session = Depends(get_db),
):
    """Update a segment's start/end timestamps for manual calibration."""
    seg = db.query(Segment).filter(
        Segment.id == segment_id,
        Segment.song_id == song_id,
    ).first()
    if not seg:
        raise HTTPException(404, f"Segment {segment_id} not found in song {song_id}")

    new_start = body.start_time if body.start_time is not None else seg.start_time
    new_end = body.end_time if body.end_time is not None else seg.end_time

    if new_start < 0 or new_end < 0:
        raise HTTPException(400, "Timestamps must be non-negative")
    if new_start >= new_end:
        raise HTTPException(400, "start_time must be less than end_time")

    seg.start_time = new_start
    seg.end_time = new_end

    db.commit()
    db.refresh(seg)
    return {
        "id": seg.id,
        "start_time": seg.start_time,
        "end_time": seg.end_time,
    }


@router.put("/{song_id}/voices", response_model=VoiceAssignResponse)
async def assign_voices(
    song_id: str,
    request: VoiceAssignRequest,
    db: Session = Depends(get_db),
):
    """Assign voice models to segments. Supports round-robin, random, or manual."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    segments = (
        db.query(Segment)
        .filter(Segment.song_id == song_id)
        .order_by(Segment.line_number)
        .all()
    )
    if not segments:
        raise HTTPException(400, f"Song {song_id} has no segments")

    if request.strategy == "manual":
        return _assign_manual(segments, request.assignments, db)

    # Auto strategies use voice_pool
    return _assign_auto(segments, request.voice_pool, request.strategy, db)


def _assign_manual(segments, assignments, db):
    """Assign voices based on explicit user mapping."""
    lookup = {a.line_number: a.voice_model_id for a in assignments}

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
    import random

    if not voice_pool:
        raise HTTPException(400, "voice_pool is required for auto assignment")

    existing = db.query(VoiceModel.id).filter(VoiceModel.id.in_(voice_pool)).all()
    existing_ids = {r[0] for r in existing}
    missing = set(voice_pool) - existing_ids
    if missing:
        raise HTTPException(400, f"Voice models not found: {missing}")

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
