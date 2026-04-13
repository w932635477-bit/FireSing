"""Voice modification service — parameter-based vocal processing.

Replaces RVC GPU inference with local CPU audio processing:
pitch shift + spectral shift + EQ + de-ess + normalize.

All operations are linear or near-linear, preserving audio quality.
"""

import io
import logging

import librosa
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)

# Minimum segment duration for spectral shift (phase vocoder artifacts below this)
_MIN_SPECTRAL_DURATION_S = 1.5

# EQ profiles: (frequency_hz, gain_db, Q_factor)
EQ_PROFILES = {
    "natural": [],  # no EQ change
    "bright": [
        (3500, 2.5, 1.5),   # presence boost +2.5dB
        (8000, 1.5, 2.0),   # air boost +1.5dB
    ],
    "dark": [
        (3500, -2.0, 1.5),  # presence cut -2dB
        (200, 2.0, 1.0),    # warmth boost +2dB
    ],
    "nasal": [
        (1000, 3.0, 2.0),   # nasal resonance boost +3dB
        (3500, -1.5, 1.5),  # presence cut
    ],
    "deep": [
        (200, 3.0, 1.0),    # warmth boost +3dB
        (3500, -2.0, 1.5),  # presence cut -2dB
        (8000, -3.0, 2.0),  # air cut -3dB
    ],
}


def modify_vocal(
    vocal_bytes: bytes,
    pitch_shift: float = 0.0,
    formant_shift: float = 0.0,
    eq_profile: str = "natural",
) -> bytes:
    """Apply voice modification to original vocal segment.

    Pipeline: spectral shift → pitch shift → EQ → de-ess → normalize

    For segments shorter than 1.5s, spectral shift is skipped to avoid
    phase vocoder artifacts on transients.
    """
    audio, sr = sf.read(io.BytesIO(vocal_bytes))
    is_stereo = audio.ndim == 2
    duration = len(audio) / sr

    # 1. Spectral shift (changes timbre, not fundamental pitch)
    #    Two-step: pitch shift up by N semitones, then time-stretch back.
    #    Skipped for segments < 1.5s to avoid phase vocoder artifacts.
    if abs(formant_shift) > 0.01 and duration >= _MIN_SPECTRAL_DURATION_S:
        if is_stereo:
            shifted = np.column_stack([
                _spectral_shift(audio[:, ch], sr, formant_shift)
                for ch in range(audio.shape[1])
            ])
        else:
            shifted = _spectral_shift(audio, sr, formant_shift)
        audio = shifted

    # 2. Pitch shift (changes pitch, preserves duration)
    if abs(pitch_shift) > 0.01:
        if is_stereo:
            shifted = np.column_stack([
                librosa.effects.pitch_shift(audio[:, ch], sr=sr, n_steps=pitch_shift)
                for ch in range(audio.shape[1])
            ])
        else:
            shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch_shift)
        audio = shifted

    # 3. EQ profile (linear, no quality loss)
    eq_params = EQ_PROFILES.get(eq_profile, EQ_PROFILES["natural"])
    for freq, gain_db, q in eq_params:
        b, a = _peaking_eq(freq, sr, gain_db, q)
        if is_stereo:
            for ch in range(audio.shape[1]):
                audio[:, ch] = _apply_iir(audio[:, ch], b, a)
        else:
            audio = _apply_iir(audio, b, a)

    # 4. De-ess (soft lowpass above 6kHz, 30% mix)
    b_lp, a_lp = _lowpass_biquad(6000, sr)
    if is_stereo:
        deessed = np.column_stack([
            _apply_iir(audio[:, ch], b_lp, a_lp) for ch in range(audio.shape[1])
        ])
    else:
        deessed = _apply_iir(audio, b_lp, a_lp)
    audio = 0.7 * audio + 0.3 * deessed

    # 5. Normalize
    peak = np.max(np.abs(audio))
    if peak > 0.95:
        audio = audio * (0.95 / peak)

    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return buf.getvalue()


def _spectral_shift(audio: np.ndarray, sr: float, semitones: float) -> np.ndarray:
    """Shift spectral envelope to simulate different vocal tract length.

    Two-step process:
    1. Pitch shift by N semitones (shifts both pitch and spectrum)
    2. Time-stretch back by 2^(N/12) (restores duration, keeps spectral shift)

    Does NOT preserve fundamental pitch. Both pitch and formants shift.
    The result is a timbre change that makes the same voice sound different.
    """
    # Step 1: pitch shift (changes pitch and duration)
    shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=semitones)

    # Step 2: time-stretch back to original duration
    rate = 2.0 ** (semitones / 12.0)
    stretched = librosa.effects.time_stretch(shifted, rate=rate)

    # Match original length
    orig_len = len(audio)
    if len(stretched) > orig_len:
        stretched = stretched[:orig_len]
    elif len(stretched) < orig_len:
        stretched = np.pad(stretched, (0, orig_len - len(stretched)))

    return stretched


# --- Biquad filter functions (pure numpy, no scipy) ---

def _apply_iir(x: np.ndarray, b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Apply IIR filter using direct form II transposed (lfilter equivalent)."""
    n = len(b)
    y = np.zeros_like(x)
    z = np.zeros(n - 1)

    for i in range(len(x)):
        y[i] = b[0] * x[i] + z[0]
        for j in range(n - 2):
            z[j] = b[j + 1] * x[i] - a[j + 1] * y[i] + z[j + 1]
        z[n - 2] = b[n - 1] * x[i] - a[n - 1] * y[i]

    return y


def _peaking_eq(freq: float, sr: float, gain_db: float, Q: float):
    """Design a peaking EQ biquad filter. Returns (b, a) coefficients."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * freq / sr
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha = sin_w0 / (2 * Q)

    b0 = 1 + alpha * A
    b1 = -2 * cos_w0
    b2 = 1 - alpha * A
    a0 = 1 + alpha / A
    a1 = -2 * cos_w0
    a2 = 1 - alpha / A

    return np.array([b0, b1, b2]) / a0, np.array([1, a1 / a0, a2 / a0])


def _lowpass_biquad(freq: float, sr: float):
    """Design a 2nd-order Butterworth lowpass biquad filter."""
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * 0.7071)

    b0 = (1 - np.cos(w0)) / 2
    b1 = 1 - np.cos(w0)
    b2 = (1 - np.cos(w0)) / 2
    a0 = 1 + alpha
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha

    return np.array([b0, b1, b2]) / a0, np.array([1, a1 / a0, a2 / a0])
