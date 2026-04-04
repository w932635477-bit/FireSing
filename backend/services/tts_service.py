"""TTS service — generate monologue audio with edge-tts."""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from ..config import SONGS_DIR
from ..models import Song

logger = logging.getLogger(__name__)

# Chinese male voice for monologue
TTS_VOICE = "zh-CN-YunxiNeural"


async def generate(song_id: str, text: str, db: Session) -> Path:
    """Generate monologue audio from text using edge-tts.

    Returns path to generated audio file.
    """
    import edge_tts

    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")

    output_path = SONGS_DIR / song_id / "monologue.mp3"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(str(output_path))

    song.monologue_text = text
    song.monologue_audio_path = str(output_path)
    db.commit()

    logger.info(f"Monologue generated: {output_path} ({output_path.stat().st_size / 1024:.1f}KB)")
    return output_path
