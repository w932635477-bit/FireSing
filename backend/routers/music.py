"""Music search and import router — powered by go-music-dl."""

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import Song
from ..schemas import SongResponse
from ..config import SONGS_DIR, MAX_AUDIO_SIZE_MB

logger = logging.getLogger(__name__)
router = APIRouter()

# go-music-dl service URL
MUSIC_DL_URL = "http://localhost:8090/music"

# Allowed music sources
ALLOWED_SOURCES = {"netease", "qq", "kugou", "kuwo"}

# In-memory import progress (cleaned up after 10 min)
_import_progress: dict[str, dict] = {}
_progress_max_age = 600  # seconds

# Event-based notification for SSE (replaces polling)
_import_progress_events: dict[str, asyncio.Event] = {}


async def _search_musicdl(keyword: str, sources: list[str]) -> list[dict]:
    """Call go-music-dl JSON search API."""
    async with httpx.AsyncClient(timeout=15, proxy=None) as client:
        params = [("q", keyword)]
        for s in sources:
            params.append(("sources", s))
        resp = await client.get(f"{MUSIC_DL_URL}/api/search", params=params)
        if resp.status_code != 200:
            raise HTTPException(503, "Music search service unavailable")
        data = resp.json()
        return data.get("songs", [])


def _merge_results(songs: list[dict]) -> list[dict]:
    """Merge search results: group by song name+artist, annotate platforms.

    Songs with the same (name, artist) are merged into one entry with a
    'platforms' field listing all available sources. The entry with the
    highest quality is used as the primary.
    """
    groups: dict[str, list[dict]] = {}
    for s in songs:
        # Normalize key: lowercase, strip whitespace
        key = f"{s.get('name', '').strip().lower()}||{s.get('artist', '').split(';')[0].split('/')[0].strip().lower()}"
        if key not in groups:
            groups[key] = []
        groups[key].append(s)

    results = []
    for key, entries in groups.items():
        # Sort by duration (prefer full versions over short clips)
        entries.sort(key=lambda x: x.get("duration", 0), reverse=True)
        primary = entries[0].copy()

        # Build platforms list
        platforms = []
        for e in entries:
            platforms.append({
                "source": e.get("source", ""),
                "id": e.get("id", ""),
                "name": e.get("name", ""),
                "duration": e.get("duration", 0),
                "cover_url": e.get("cover_url", ""),
            })

        primary["platforms"] = platforms
        primary["platform_count"] = len(platforms)
        # Use the cover from the first entry that has one
        for e in entries:
            if e.get("cover_url"):
                primary["cover_url"] = e["cover_url"]
                break
        results.append(primary)

    # Sort: more platforms first (more available sources), then by duration
    results.sort(key=lambda x: (-x.get("platform_count", 0), -x.get("duration", 0)))
    return results


@router.get("/search")
async def search_music(
    q: str = Query(..., min_length=1, description="Search keyword"),
    sources: list[str] = Query(
        default=["netease", "qq", "kugou"],
        description="Music sources to search"
    ),
    merge: bool = Query(default=True, description="Merge results across platforms"),
):
    """Search songs across multiple music platforms."""
    raw = await _search_musicdl(q, sources)
    if merge:
        results = _merge_results(raw)
    else:
        results = raw
    return {"songs": results, "count": len(results)}


@router.get("/check-existing")
async def check_existing(
    source: str = Query(...),
    source_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """Check if a song has already been imported from this source."""
    song = db.query(Song).filter(
        Song.source == source,
        Song.source_id == source_id,
    ).first()
    return {"exists": song is not None, "song_id": song.id if song else None}


async def _run_import(task_id: str, source: str, source_id: str,
                      title: str, artist: str):
    """Background task: download audio + lyrics from go-music-dl."""
    db = SessionLocal()
    try:
        _import_progress[task_id] = {"step": "creating", "pct": 10,
                                      "message": "Creating song record..."}
        evt = _import_progress_events.get(task_id)
        if evt:
            evt.set()

        song = Song(
            title=f"{title} - {artist}" if artist else title,
            original_audio_path="",
            status="importing",
            source=source,
            source_id=source_id,
            artist=artist,
        )
        db.add(song)
        db.commit()
        db.refresh(song)

        song_dir = SONGS_DIR / song.id
        song_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Download audio
        _import_progress[task_id] = {"step": "downloading_audio", "pct": 30,
                                      "message": "Downloading audio..."}
        evt = _import_progress_events.get(task_id)
        if evt:
            evt.set()

        async with httpx.AsyncClient(timeout=120, proxy=None) as client:
            async with client.stream(
                "GET",
                f"{MUSIC_DL_URL}/download",
                params={
                    "id": source_id,
                    "source": source,
                    "name": title,
                    "artist": artist,
                },
                follow_redirects=True,
            ) as audio_resp:
                if audio_resp.status_code != 200:
                    raise Exception(f"Audio download failed: HTTP {audio_resp.status_code}")

                # Check Content-Length against limit
                content_length = audio_resp.headers.get("content-length")
                if content_length and int(content_length) > MAX_AUDIO_SIZE_MB * 1024 * 1024:
                    raise Exception(f"Audio file too large ({int(content_length) // 1024 // 1024}MB > {MAX_AUDIO_SIZE_MB}MB)")

                audio_path = song_dir / "original.mp3"
                downloaded = 0
                with open(audio_path, "wb") as f:
                    async for chunk in audio_resp.aiter_bytes(65536):
                        downloaded += len(chunk)
                        if downloaded > MAX_AUDIO_SIZE_MB * 1024 * 1024:
                            raise Exception(f"Audio file too large (exceeded {MAX_AUDIO_SIZE_MB}MB during download)")
                        f.write(chunk)
                song.original_audio_path = str(audio_path)

        # Step 2: Download lyrics
        _import_progress[task_id] = {"step": "downloading_lyrics", "pct": 70,
                                      "message": "Downloading lyrics..."}
        evt = _import_progress_events.get(task_id)
        if evt:
            evt.set()

        async with httpx.AsyncClient(timeout=15, proxy=None) as client:
            try:
                lrc_resp = await client.get(
                    f"{MUSIC_DL_URL}/download_lrc",
                    params={"id": source_id, "source": source},
                )
                if lrc_resp.status_code == 200 and lrc_resp.content:
                    lrc_path = song_dir / "lyrics.lrc"
                    lrc_path.write_bytes(lrc_resp.content)
                    song.lrc_path = str(lrc_path)
            except Exception as e:
                logger.warning(f"Lyrics download failed for {song.id}: {e}")

        # Done
        song.status = "uploaded"
        if not song.lrc_path:
            song.status = "uploaded"  # Still uploaded, just needs LRC
        db.commit()

        _import_progress[task_id] = {
            "step": "done", "pct": 100,
            "message": "Import complete!",
            "song_id": song.id,
        }
        evt = _import_progress_events.get(task_id)
        if evt:
            evt.set()

    except Exception as e:
        logger.error(f"Music import failed for task {task_id}: {e}")
        current = _import_progress.get(task_id, {})
        _import_progress[task_id] = {
            "step": "error",
            "pct": current.get("pct", 0),
            "message": str(e),
        }
        evt = _import_progress_events.get(task_id)
        if evt:
            evt.set()
        # Clean up failed song and orphan files
        if 'song' in dir() and song and song.id:
            # Remove orphan audio files
            song_dir = SONGS_DIR / song.id
            if song_dir.exists():
                import shutil
                shutil.rmtree(song_dir, ignore_errors=True)
            # Delete the DB record so it doesn't point to deleted files
            db.delete(song)
            db.commit()
    finally:
        db.close()
        # Wake up SSE one last time and clean up event
        evt = _import_progress_events.pop(task_id, None)
        if evt:
            evt.set()
        # Schedule progress cleanup after 2 minutes
        import asyncio
        async def _cleanup():
            await asyncio.sleep(120)
            _import_progress.pop(task_id, None)
        try:
            asyncio.get_event_loop().create_task(_cleanup())
        except RuntimeError:
            pass


@router.post("/import")
async def import_music(
    source: str = Query(...),
    source_id: str = Query(..., alias="source_id"),
    title: str = Query(...),
    artist: str = Query(default=""),
    background_tasks: BackgroundTasks = None,
):
    """Import a song from a music platform. Returns a task_id for progress tracking."""
    # Validate source
    if source not in ALLOWED_SOURCES:
        raise HTTPException(400, f"Invalid source: {source}. Allowed: {', '.join(sorted(ALLOWED_SOURCES))}")

    import uuid
    task_id = f"import_{uuid.uuid4().hex[:8]}"

    _import_progress[task_id] = {"step": "queued", "pct": 0,
                                  "message": "Queued for import..."}
    _import_progress_events[task_id] = asyncio.Event()

    background_tasks.add_task(
        _run_import, task_id, source, source_id, title, artist
    )
    return {"task_id": task_id, "status": "importing"}


@router.get("/import/{task_id}/progress")
async def import_progress(task_id: str):
    """SSE stream for real-time import progress."""
    async def event_generator():
        elapsed = 0.0
        while elapsed < 300:  # 5 min max
            progress = _import_progress.get(task_id, {
                "step": "unknown", "pct": 0, "message": "Waiting..."
            })
            yield f"data: {json.dumps(progress)}\n\n"
            if progress.get("step") in ("done", "error"):
                break
            event = _import_progress_events.get(task_id)
            if event:
                event.clear()
                await event.wait()
            else:
                await asyncio.sleep(0.5)
            elapsed += 0.5

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/import/{task_id}/song")
async def get_imported_song(task_id: str, db: Session = Depends(get_db)):
    """Get the imported song details after import completes."""
    progress = _import_progress.get(task_id)
    if not progress or progress.get("step") != "done":
        raise HTTPException(404, "Import not complete or not found")

    song_id = progress.get("song_id")
    if not song_id:
        raise HTTPException(404, "Song ID not found in progress")

    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    return SongResponse.model_validate(song)
