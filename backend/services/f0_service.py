"""F0 (fundamental frequency) detection for vocal segments.

Detects the mean pitch of a vocal segment and computes the optimal f0up_key
for RVC voice conversion to match the target voice model's natural range.
"""

import io
import logging

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# Human singing range
FMIN_HZ = 65.0    # C2
FMAX_HZ = 2093.0  # C7


def detect_mean_f0(audio_path: str) -> float | None:
    """Detect mean F0 from a vocal audio file path.

    Returns median F0 of voiced frames in Hz, or None if no voiced frames.
    """
    audio, sr = librosa.load(audio_path, sr=None, mono=True)
    return _detect_from_array(audio, sr)


def detect_mean_f0_from_bytes(wav_bytes: bytes) -> float | None:
    """Detect mean F0 from WAV bytes."""
    audio, sr = sf.read(io.BytesIO(wav_bytes))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return _detect_from_array(audio.astype(np.float32), sr)


def _detect_from_array(audio: np.ndarray, sr: int) -> float | None:
    """Core F0 detection using librosa.pyin.

    Returns median F0 of voiced frames, or None.
    """
    if len(audio) < sr * 0.1:
        return None

    f0, voiced, probs = librosa.pyin(
        audio,
        fmin=FMIN_HZ,
        fmax=FMAX_HZ,
        sr=sr,
        frame_length=2048,
    )
    voiced_f0 = f0[~np.isnan(f0)]
    if len(voiced_f0) == 0:
        return None
    return float(np.median(voiced_f0))


def compute_f0up_key(
    source_f0: float | None,
    target_f0: float | None,
    manual_override: int = 0,
) -> int:
    """Compute optimal f0up_key to match source pitch to target.

    Formula: f0up_key = round(12 * log2(target_f0 / source_f0)) + manual_override
    Clamped to [-12, 12].

    If target_f0 or source_f0 is None, returns manual_override only.
    """
    if source_f0 is None or source_f0 <= 0 or target_f0 is None or target_f0 <= 0:
        return max(-12, min(12, manual_override))

    shift = round(12 * np.log2(target_f0 / source_f0))
    shift += manual_override
    result = max(-12, min(12, shift))

    if shift != 0:
        logger.info(
            f"F0 pitch shift: source={source_f0:.1f}Hz, target={target_f0:.1f}Hz, "
            f"auto_shift={shift - manual_override}, manual={manual_override}, "
            f"final={result}"
        )

    return result
