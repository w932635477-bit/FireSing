"""Pipeline router — trigger processing, SSE progress tracking."""

import asyncio
import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Song
from ..schemas import ProcessRequest, ProcessResponse, PipelineProgress

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory progress store (single-process, no Redis needed)
_pipeline_progress: dict[str, PipelineProgress] = {}


def _update_progress(song_id: str, step: str, pct: int, message: str,
                     step_failed: str | None = None, error_detail: str | None = None):
    _pipeline_progress[song_id] = PipelineProgress(
        step=step, pct=pct, message=message,
        step_failed=step_failed, error_detail=error_detail,
    )


# Statuses that indicate active processing
_ACTIVE_STATUSES = {"separating", "segmented", "segmenting", "assigning",
                    "converting", "chorus", "monologue", "mixing", "video"}


def _assign_voices_for_pipeline(song_id: str, params, db):
    """Assign voices to segments using the strategy from ProcessRequest."""
    from ..models import Segment, VoiceModel

    if not params.voice_pool:
        logger.warning(f"No voice_pool provided for song {song_id}, skipping assignment")
        return

    existing = db.query(VoiceModel.id).filter(VoiceModel.id.in_(params.voice_pool)).all()
    existing_ids = {r[0] for r in existing}
    missing = set(params.voice_pool) - existing_ids
    if missing:
        raise ValueError(f"Voice models not found: {missing}")

    segments = db.query(Segment).filter(
        Segment.song_id == song_id
    ).order_by(Segment.line_number).all()

    import random
    for i, seg in enumerate(segments):
        if params.strategy == "round-robin":
            seg.voice_model_id = params.voice_pool[i % len(params.voice_pool)]
        elif params.strategy == "random":
            seg.voice_model_id = random.choice(params.voice_pool)
        else:
            seg.voice_model_id = params.voice_pool[i % len(params.voice_pool)]
    db.commit()


async def _run_pipeline(song_id: str, params: ProcessRequest):
    """Background pipeline execution — full 8-step pipeline."""
    from ..database import SessionLocal
    from ..services import demucs_service, lyrics_service, rvc_service
    from ..services import chorus_service, tts_service, audio_service, video_service
    from ..models import Segment

    db = SessionLocal()
    try:
        # Step 1: Demucs vocal separation
        _update_progress(song_id, "separating", 0, "Separating vocals...")
        await demucs_service.separate(song_id, db)

        # Step 2: LRC parse + segment cutting
        _update_progress(song_id, "segmenting", 15, "Cutting vocal segments...")
        await asyncio.to_thread(lyrics_service.parse_and_cut, song_id, db)

        # Step 3: Voice assignment
        _update_progress(song_id, "assigning", 25, "Assigning voice models...")
        _assign_voices_for_pipeline(song_id, params, db)

        # Step 4: RVC per-line conversion
        segments = db.query(Segment).filter(
            Segment.song_id == song_id, Segment.voice_model_id.isnot(None)
        ).order_by(Segment.line_number).all()

        total = len(segments)
        for i, seg in enumerate(segments):
            pct = 30 + int(50 * i / max(total, 1))
            _update_progress(song_id, "converting", pct,
                             f"Converting line {i+1}/{total}...")
            await rvc_service.convert(seg.id, db)

        # Refresh segments after conversion
        db.expire_all()
        segments = db.query(Segment).filter(
            Segment.song_id == song_id
        ).order_by(Segment.line_number).all()

        # Step 5: Chorus detection
        _update_progress(song_id, "chorus", 82, "Detecting chorus...")
        chorus_ids = chorus_service.detect(segments)

        # Step 6: Monologue generation
        if params.monologue_text:
            _update_progress(song_id, "monologue", 85, "Generating monologue...")
            await tts_service.generate(song_id, params.monologue_text, db)

        # Step 7: Audio mixing
        _update_progress(song_id, "mixing", 90, "Mixing audio...")
        await asyncio.to_thread(
            audio_service.mix_all, song_id, chorus_ids,
            params.monologue_position or "beginning", db
        )

        # Step 8: Video generation
        _update_progress(song_id, "video", 95, "Generating video...")
        await asyncio.to_thread(video_service.generate, song_id, db)

        _update_progress(song_id, "done", 100, "Complete!")

    except Exception as e:
        logger.error(f"Pipeline failed for song {song_id}: {e}")
        current = _pipeline_progress.get(song_id)
        _update_progress(
            song_id, "error",
            current.pct if current else 0,
            f"Failed: {e}",
            step_failed=current.step if current else "unknown",
            error_detail=str(e),
        )
        song = db.query(Song).filter(Song.id == song_id).first()
        if song:
            song.status = "error"
            song.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/{song_id}/process", response_model=ProcessResponse)
async def process_song(
    song_id: str,
    params: ProcessRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger full processing pipeline for a song."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    # Concurrency guard
    if song.status in _ACTIVE_STATUSES:
        raise HTTPException(409, f"Song is already being processed (status: {song.status})")

    if song.status == "error":
        song.error_message = None
        db.commit()

    background_tasks.add_task(_run_pipeline, song_id, params)
    return ProcessResponse(status="processing")


@router.get("/{song_id}/progress")
async def pipeline_progress(song_id: str, db: Session = Depends(get_db)):
    """SSE stream for real-time pipeline progress."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    async def event_generator():
        while True:
            progress = _pipeline_progress.get(song_id)
            if progress:
                data = progress.model_dump()
            else:
                data = {
                    "step": song.status or "uploaded",
                    "pct": 0,
                    "message": f"Song status: {song.status or 'uploaded'}",
                    "step_failed": None,
                    "error_detail": None,
                }
            yield f"data: {json.dumps(data)}\n\n"
            if data["step"] in ("done", "error"):
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
