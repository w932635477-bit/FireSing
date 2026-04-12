"""F0 (fundamental frequency) detection for vocal segments.

Detects the pitch of a vocal segment and computes the optimal f0up_key
for RVC voice conversion to match the target voice model's natural range.

Uses improved pYIN with octave error correction and mode-based aggregation.
Key improvements over naive pYIN:
1. Mode (most common pitch) instead of median — more stable for singing
2. Octave error detection — corrects common pYIN octave mistakes
3. Probability-weighted filtering — discards low-confidence frames
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

# Maximum pitch shift RVC can handle without severe quality degradation
MAX_SAFE_SHIFT = 5

# pYIN probability threshold for voiced frame detection
PROBABILITY_THRESHOLD = 0.3


def detect_mean_f0(audio_path: str) -> float | None:
    """Detect pitch from a vocal audio file path.

    Returns mode F0 of voiced frames in Hz, or None if no voiced frames.
    """
    audio, sr = librosa.load(audio_path, sr=None, mono=True)
    return _detect_from_array(audio, sr)


def detect_mean_f0_from_bytes(wav_bytes: bytes) -> float | None:
    """Detect pitch from WAV bytes."""
    audio, sr = sf.read(io.BytesIO(wav_bytes))
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return _detect_from_array(audio.astype(np.float32), sr)


def _detect_from_array(audio: np.ndarray, sr: int) -> float | None:
    """Core F0 detection using pYIN with octave error correction.

    Returns mode F0 of high-probability voiced frames, or None.
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

    # Filter: voiced frames with sufficient probability
    voiced_mask = (~np.isnan(f0)) & (probs > PROBABILITY_THRESHOLD)
    voiced_f0 = f0[voiced_mask]

    if len(voiced_f0) == 0:
        return None

    # Detect and correct octave errors before computing mode
    corrected_f0 = _correct_octave_errors(voiced_f0)

    return float(_circular_mode(corrected_f0))


def _correct_octave_errors(f0_values: np.ndarray) -> np.ndarray:
    """Detect and correct octave errors in pYIN output.

    pYIN commonly misidentifies the octave, especially for high-pitched
    or breathy vocals. This function detects bimodal distributions
    separated by exactly 1-2 octaves and picks the more likely one.

    Heuristic: if there are two strong clusters separated by ~12 or ~24
    semitones, the higher cluster is more likely correct for singing voice
    (pYIN tends to report too low).
    """
    if len(f0_values) < 5:
        return f0_values

    # Convert to semitones from C0 for binning
    semitones = 12 * np.log2(f0_values / 16.35)  # C0 ≈ 16.35 Hz

    # Bin into 1-semitone buckets
    bins = np.round(semitones).astype(int)
    unique_bins, counts = np.unique(bins, return_counts=True)

    if len(unique_bins) < 2:
        return f0_values

    # Find top 2 clusters
    sorted_idx = np.argsort(counts)[::-1]
    top1_bin = unique_bins[sorted_idx[0]]
    top1_count = counts[sorted_idx[0]]

    if len(sorted_idx) < 2:
        return f0_values

    top2_bin = unique_bins[sorted_idx[1]]
    top2_count = counts[sorted_idx[1]]

    # Check if top 2 clusters are ~12 semitones (1 octave) apart
    separation = abs(top1_bin - top2_bin)
    if separation in (11, 12, 13, 23, 24, 25):  # ~1 or ~2 octaves
        # Both clusters are significant (>20% of top cluster)
        if top2_count > top1_count * 0.2:
            # Pick the higher cluster — pYIN tends to report too low
            target_bin = max(top1_bin, top2_bin)
            target_f0 = 16.35 * 2 ** (target_bin / 12.0)

            # Shift all frames in the lower cluster up by the octave difference
            result = f0_values.copy()
            for i in range(len(result)):
                frame_bin = round(12 * np.log2(result[i] / 16.35))
                if abs(frame_bin - target_bin) in (11, 12, 13, 23, 24, 25):
                    if frame_bin < target_bin:
                        result[i] = result[i] * 2 ** (round((target_bin - frame_bin) / 12))

            return result

    return f0_values


def _circular_mode(f0_values: np.ndarray) -> float:
    """Compute the mode of F0 values, grouping into 1-semitone bins.

    Uses 100-cent (1 semitone) bin width to accommodate natural
    vibrato spread. Returns the centroid of the largest bin.
    """
    if len(f0_values) == 0:
        return 0.0

    # Convert to cents for better clustering
    cents = 1200 * np.log2(f0_values / 440.0)

    # Bin into 1-semitone buckets (100 cents) to handle vibrato
    bin_width = 100  # cents
    bins = np.round(cents / bin_width).astype(int)
    unique_bins, counts = np.unique(bins, return_counts=True)

    # Find the most common bin
    mode_bin = unique_bins[np.argmax(counts)]

    # Get the mean F0 of values in the mode bin
    mask = bins == mode_bin
    return float(np.exp2(np.mean(cents[mask]) / 1200) * 440.0)


def compute_f0up_key(
    source_f0: float | None,
    target_f0: float | None,
    manual_override: int = 0,
) -> int:
    """Compute optimal f0up_key to match source pitch to target.

    Formula: f0up_key = round(12 * log2(target_f0 / source_f0)) + manual_override
    Clamped to [-MAX_SAFE_SHIFT, MAX_SAFE_SHIFT] to avoid RVC quality degradation.

    If target_f0 or source_f0 is None, returns manual_override only.
    """
    if source_f0 is None or source_f0 <= 0 or target_f0 is None or target_f0 <= 0:
        return max(-MAX_SAFE_SHIFT, min(MAX_SAFE_SHIFT, manual_override))

    shift = round(12 * np.log2(target_f0 / source_f0))
    shift += manual_override
    result = max(-MAX_SAFE_SHIFT, min(MAX_SAFE_SHIFT, shift))

    if shift != 0:
        logger.info(
            f"F0 pitch shift: source={source_f0:.1f}Hz, target={target_f0:.1f}Hz, "
            f"auto_shift={shift - manual_override}, manual={manual_override}, "
            f"final={result}"
        )

    return result


def best_voice_for_segment(
    source_f0: float | None,
    voices: list[tuple[str, float | None]],
) -> str | None:
    """Pick the voice model whose mean_f0_hz is closest to source_f0.

    Args:
        source_f0: Detected F0 of the segment vocal.
        voices: List of (voice_model_id, mean_f0_hz) tuples.

    Returns the voice_model_id with the smallest required pitch shift,
    or the first voice if source_f0 is None.
    """
    if not voices:
        return None
    if source_f0 is None:
        return voices[0][0]

    best_id = None
    best_shift = float("inf")
    for vid, mean_f0 in voices:
        if mean_f0 is None:
            continue
        shift = abs(12 * np.log2(mean_f0 / source_f0))
        if shift < best_shift:
            best_shift = shift
            best_id = vid

    return best_id or voices[0][0]
