"""FireSing FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import (
    SONGS_DIR, SEGMENTS_DIR, CONVERTED_DIR, OUTPUTS_DIR, VOICES_DIR,
    CORS_ORIGINS,
)
from .database import init_db
from .routers import songs, voices, pipeline, outputs, music, auth, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Create data directories
    for d in [SONGS_DIR, SEGMENTS_DIR, CONVERTED_DIR, OUTPUTS_DIR, VOICES_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialize database
    init_db()

    # Detect stuck songs from previous server crash
    from .database import SessionLocal
    from .models import Song
    from datetime import datetime, timezone, timedelta
    _ACTIVE = {"separating", "segmented", "segmenting", "assigning",
               "converting", "harmony", "chorus", "monologue", "mixing", "video"}
    db = SessionLocal()
    try:
        stuck = db.query(Song).filter(Song.status.in_(_ACTIVE)).all()
        for song in stuck:
            age = (datetime.now(timezone.utc) - song.updated_at.replace(tzinfo=timezone.utc)
                   if song.updated_at else timedelta(hours=1))
            if age > timedelta(minutes=10):
                song.status = "interrupted"
                song.error_message = "处理被服务器重启中断，请重试"
        db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title="FireSing",
    description="AI-powered song modification platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(songs.router, prefix="/api/songs", tags=["songs"])
app.include_router(voices.router, prefix="/api/voices", tags=["voices"])
app.include_router(pipeline.router, prefix="/api/songs", tags=["pipeline"])
app.include_router(outputs.router, prefix="/api/songs", tags=["outputs"])
app.include_router(music.router, prefix="/api/music", tags=["music"])
app.include_router(auth.router, tags=["auth"])
app.include_router(orders.router, tags=["orders"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/health/gpu")
async def gpu_health():
    """Check if the GPU inference server is reachable and healthy."""
    import httpx
    from .config import GPU_SERVER_URL

    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            resp = await client.get(f"{GPU_SERVER_URL}/health")
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "ok", "gpu": data.get("gpu"), "vram_gb": data.get("vram_total_gb")}
            return {"status": "error", "detail": f"GPU server returned HTTP {resp.status_code}"}
    except httpx.ConnectError:
        return {"status": "offline", "detail": "GPU server not reachable — start it with: cd gpu_server && python server.py --port 8001"}
    except httpx.TimeoutException:
        return {"status": "timeout", "detail": "GPU server timed out"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
