"""VAD service — energy-based vocal segmentation.

Replaces LRC-based segmentation with automatic voice activity detection.
Uses energy-based segmentation at -30dB threshold, validated on real
Demucs-separated singing vocals (93.2% coverage, 0.87s avg segment duration).

Validated in validation/test_vad_segmentation.py.
"""

import logging
from pathlib import Path

import librosa
import numpy as np
from pydub import AudioSegment
from sqlalchemy.orm import Session

from ..config import SEGMENTS_DIR
from ..models import Song, Segment

logger = logging.getLogger(__name__)

# Segmentation parameters (validated on 9.28s test clip)
DEFAULT_ENERGY_THRESHOLD_DB = -30
DEFAULT_FRAME_LENGTH = 2048
DEFAULT_HOP_LENGTH = 512
DEFAULT_MIN_SEGMENT_S = 0.3
DEFAULT_MIN_SILENCE_S = 0.3


def segment_vocals(
    vocals_path: str | Path,
    energy_threshold_db: float = DEFAULT_ENERGY_THRESHOLD_DB,
    frame_length: int = DEFAULT_FRAME_LENGTH,
    hop_length: int = DEFAULT_HOP_LENGTH,
    min_segment_s: float = DEFAULT_MIN_SEGMENT_S,
    min_silence_s: float = DEFAULT_MIN_SILENCE_S,
) -> list[dict]:
    """Split vocals into segments at low-energy gaps (silences).

    Returns list of dicts with keys: line_number, start_time, end_time, text.

    This is the validated energy-based approach. Silero-VAD was tested and
    completely unsuitable for singing (treats entire vocal track as one segment).
    """
    # Load audio
    audio, sr = librosa.load(str(vocals_path), sr=None, mono=True)

    # Compute RMS energy per frame
    S = np.abs(librosa.stft(audio, n_fft=frame_length, hop_length=hop_length))
    rms = librosa.feature.rms(S=S)[0]

    # Handle pure silence: when max RMS is 0, ref=np.max gives 0 dB for all frames
    # (0/0 in dB scale). Treat pure silence as no speech.
    if rms.max() == 0:
        return []

    # Convert to dB
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Threshold: frames above threshold are "speech"
    is_speech = rms_db > energy_threshold_db

    # Find speech segments by detecting transitions
    segments = []
    in_speech = False
    start_frame = 0

    for i, speech in enumerate(is_speech):
        if speech and not in_speech:
            start_frame = i
            in_speech = True
        elif not speech and in_speech:
            start_s = start_frame * hop_length / sr
            end_s = i * hop_length / sr
            if end_s - start_s >= min_segment_s:
                segments.append((start_s, end_s))
            in_speech = False

    # Handle segment that extends to end of audio
    if in_speech:
        start_s = start_frame * hop_length / sr
        end_s = len(audio) / sr
        if end_s - start_s >= min_segment_s:
            segments.append((start_s, end_s))

    # Merge segments separated by very short silence (< min_silence_s)
    merged = []
    for start_s, end_s in segments:
        if merged and start_s - merged[-1][1] < min_silence_s:
            # Extend previous segment
            merged[-1] = (merged[-1][0], end_s)
        else:
            merged.append((start_s, end_s))

    # Convert to segment dicts
    result = []
    for i, (start_s, end_s) in enumerate(merged):
        result.append({
            "line_number": i + 1,
            "start_time": round(start_s, 3),
            "end_time": round(end_s, 3),
            "text": f"Segment {i + 1}",
        })

    total_audio = len(audio) / sr
    coverage = sum(e - s for s, e in merged) / total_audio * 100 if total_audio > 0 else 0
    logger.info(
        f"VAD segmentation: {len(result)} segments from {total_audio:.1f}s audio, "
        f"{coverage:.1f}% coverage"
    )

    return result


def cut_vocals(
    vocals_path: Path, segments: list[dict], output_dir: Path
) -> list[Path]:
    """Cut vocals.wav into per-segment files using pydub.

    Returns list of paths to cut segment wav files.
    """
    audio = AudioSegment.from_wav(str(vocals_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for seg in segments:
        start_ms = int(seg["start_time"] * 1000)
        end_ms = int(seg["end_time"] * 1000)
        segment_audio = audio[start_ms:end_ms]

        filename = f"line_{seg['line_number']:03d}.wav"
        seg_path = output_dir / filename
        segment_audio.export(str(seg_path), format="wav")
        paths.append(seg_path)

    logger.info(f"Cut {len(segments)} segments to {output_dir}")
    return paths


def segment_and_cut(song_id: str, db: Session) -> list[Segment]:
    """Full pipeline: segment vocals using energy VAD, cut, save to DB.

    This is the sync entry point called via asyncio.to_thread().
    Replaces lyrics_service.parse_and_cut().
    """
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise ValueError(f"Song {song_id} not found")
    if not song.vocals_path:
        raise ValueError(f"Song {song_id} vocals not yet separated")

    # Check if already segmented with vocal files
    existing = db.query(Segment).filter(Segment.song_id == song_id).first()
    if existing and existing.vocal_path:
        logger.info(f"Song {song_id} already segmented with vocals, skipping")
        return db.query(Segment).filter(Segment.song_id == song_id).all()
    # Delete old segments without vocals so we can re-segment
    if existing:
        logger.info(f"Song {song_id} has segments without vocals, re-segmenting")
        db.query(Segment).filter(Segment.song_id == song_id).delete()
        db.flush()

    # Energy-based segmentation
    segments_data = segment_vocals(song.vocals_path)

    if not segments_data:
        raise ValueError(
            f"VAD found no vocal segments in {song.vocals_path}. "
            f"Audio may be silent or corrupted."
        )

    # Cut vocal segments
    output_dir = SEGMENTS_DIR / song_id
    vocal_paths = cut_vocals(Path(song.vocals_path), segments_data, output_dir)

    # Save to database
    db_segments = []
    for seg_data, vocal_path in zip(segments_data, vocal_paths):
        db_seg = Segment(
            song_id=song_id,
            line_number=seg_data["line_number"],
            text=seg_data["text"],
            start_time=seg_data["start_time"],
            end_time=seg_data["end_time"],
            vocal_path=str(vocal_path),
        )
        db.add(db_seg)
        db_segments.append(db_seg)

    song.status = "segmented"
    db.commit()

    for seg in db_segments:
        db.refresh(seg)

    logger.info(f"Song {song_id}: {len(db_segments)} VAD segments created")
    return db_segments
