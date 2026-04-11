"""Demucs service — calls GPU server for vocal separation."""

import asyncio
import logging
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from ..config import GPU_SERVER_URL, SONGS_DIR, GPU_REQUEST_TIMEOUT
from ..models import Song

logger = logging.getLogger(__name__)


async def separate(song_id: str, db: Session) -> tuple[Path, Path]:
    """Call GPU server to separate vocals from instrumental.

    Returns (vocals_path, instrumental_path).
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")

    # Skip if already separated
    if song.vocals_path and Path(song.vocals_path).exists():
        return Path(song.vocals_path), Path(song.instrumental_path)

    song_dir = SONGS_DIR / song_id
    song_dir.mkdir(parents=True, exist_ok=True)

    # Update status
    song.status = "separating"
    db.commit()

    try:
        audio_path = Path(song.original_audio_path)
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        vocals_path, instrumental_path = await _call_gpu_demucs(
            audio_bytes, audio_path.suffix, song_dir
        )

        song.vocals_path = str(vocals_path)
        song.instrumental_path = str(instrumental_path)
        song.status = "separated"
        db.commit()

        return vocals_path, instrumental_path

    except Exception as e:
        song.status = "error"
        song.error_message = f"Demucs separation failed: {e}"
        db.commit()
        raise


async def _call_gpu_demucs(
    audio_bytes: bytes, suffix: str, output_dir: Path
) -> tuple[Path, Path]:
    """Send audio to GPU server and save returned vocals + instrumental."""

    url = f"{GPU_SERVER_URL}/infer/demucs"
    filename = f"audio{suffix}"

    # Retry: 3 attempts with exponential backoff
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=GPU_REQUEST_TIMEOUT, proxy=None, trust_env=False) as client:
                resp = await client.post(
                    url,
                    files={"audio": (filename, audio_bytes, "audio/mpeg")},
                )
                resp.raise_for_status()
                break
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
                continue
            raise ConnectionError(
                f"GPU server unreachable after 3 attempts: {last_error}"
            )

    # Parse multipart response
    content_type = resp.headers.get("content-type", "")
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part.split("=", 1)[1].strip('"')
            break

    if not boundary:
        raise ValueError("No boundary in GPU server response")

    body = resp.content
    boundary_bytes = f"--{boundary}".encode()
    parts = body.split(boundary_bytes)

    vocals_bytes = None
    instrumental_bytes = None

    for part in parts:
        header_region = part[:200].lower()
        header_end = part.find(b"\r\n\r\n")
        if header_end < 0:
            continue
        content_body = part[header_end + 4:].rstrip(b"\r\n")

        if b"vocals" in header_region and b"instrumental" not in header_region:
            vocals_bytes = content_body
        elif b"instrumental" in header_region or b"no_vocals" in header_region:
            instrumental_bytes = content_body

    if not vocals_bytes or not instrumental_bytes:
        raise ValueError("Failed to parse vocals/instrumental from GPU response")

    vocals_path = output_dir / "vocals.wav"
    instrumental_path = output_dir / "instrumental.wav"

    with open(vocals_path, "wb") as f:
        f.write(vocals_bytes)
    with open(instrumental_path, "wb") as f:
        f.write(instrumental_bytes)

    logger.info(
        f"Demucs done: vocals={len(vocals_bytes)/1024/1024:.1f}MB, "
        f"instrumental={len(instrumental_bytes)/1024/1024:.1f}MB"
    )

    return vocals_path, instrumental_path
