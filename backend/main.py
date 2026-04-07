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
from .routers import songs, voices, pipeline, outputs, music


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
               "converting", "chorus", "monologue", "mixing", "video"}
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


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
