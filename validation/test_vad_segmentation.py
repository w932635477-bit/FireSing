#!/usr/bin/env python3
"""VAD prototype — validate silero-vad + librosa onset detection on singing vocals.

Tests multiple segmentation strategies on real Demucs-separated vocals and compares
results to find the best approach for replacing LRC-based segmentation.

Test data: data/tmp_e2e_vocals.wav (9.28s stereo, 44100Hz)
"""

import numpy as np
import librosa
import soundfile as sf
import wave
import struct
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
VOCALS_PATH = DATA_DIR / "tmp_e2e_vocals.wav"


def load_audio_16k_mono(path: str) -> tuple[np.ndarray, int]:
    """Load audio as mono 16kHz float32 for silero-vad."""
    y, sr = librosa.load(path, sr=16000, mono=True)
    return y, sr


def load_audio_original(path: str) -> tuple[np.ndarray, int]:
    """Load audio at original sample rate, mono."""
    y, sr = librosa.load(path, sr=None, mono=True)
    return y, sr


# ── Strategy 1: Silero-VAD ──────────────────────────────────────────────────

def test_silero_vad(audio_16k: np.ndarray, sr_16k: int, label: str,
                    threshold: float = 0.5, min_silence_ms: int = 300,
                    min_speech_ms: int = 200) -> list[tuple[float, float]]:
    """Run silero-vad with configurable parameters.

    Returns list of (start_sec, end_sec) segments.
    """
    try:
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        (get_speech_timestamps, _, read_audio, _, _) = utils
    except Exception as e:
        print(f"  [{label}] Failed to load silero-vad: {e}")
        return []

    # silero-vad expects torch tensor
    audio_tensor = torch.from_numpy(audio_16k).float()

    speech_ts = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sr_16k,
        threshold=threshold,
        min_silence_duration_ms=min_silence_ms,
        min_speech_duration_ms=min_speech_ms,
    )

    segments = []
    for ts in speech_ts:
        start_s = ts["start"] / sr_16k
        end_s = ts["end"] / sr_16k
        segments.append((start_s, end_s))

    return segments


# ── Strategy 2: Librosa Onset Detection ─────────────────────────────────────

def test_onset_detection(audio: np.ndarray, sr: int, label: str,
                         hop_length: int = 512,
                         min_segment_s: float = 0.3) -> list[tuple[float, float]]:
    """Use librosa onset detection to find phrase boundaries.

    Returns list of (start_sec, end_sec) segments.
    """
    # Onset strength
    onset_env = librosa.onset.onset_strength(y=audio, sr=sr, hop_length=hop_length)

    # Detect onsets
    onset_frames = librosa.onset.onset_detect(
        y=audio, sr=sr, onset_envelope=onset_env,
        hop_length=hop_length, units="frames",
        backtrack=True,
    )

    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

    # Convert onset times to segments
    segments = []
    for i in range(len(onset_times)):
        start = onset_times[i]
        end = onset_times[i + 1] if i + 1 < len(onset_times) else len(audio) / sr
        if end - start >= min_segment_s:
            segments.append((float(start), float(end)))

    return segments


# ── Strategy 3: Combined VAD + Onset ────────────────────────────────────────

def test_combined(vad_segments: list[tuple[float, float]],
                  onset_segments: list[tuple[float, float]],
                  audio: np.ndarray, sr: int,
                  label: str) -> list[tuple[float, float]]:
    """Combine VAD and onset detection.

    Logic: Use VAD to find voiced regions, then split those regions
    at onset boundaries to get musically meaningful phrase segments.
    """
    result = []

    for vad_start, vad_end in vad_segments:
        # Find onset boundaries within this VAD region
        sub_onsets = []
        for os, oe in onset_segments:
            # Onset segment overlaps with VAD region
            overlap_start = max(vad_start, os)
            overlap_end = min(vad_end, oe)
            if overlap_end > overlap_start:
                sub_onsets.append((overlap_start, overlap_end))

        if sub_onsets:
            result.extend(sub_onsets)
        else:
            # No onset split within this VAD region, keep it whole
            result.append((vad_start, vad_end))

    return result


# ── Strategy 4: Energy-based segmentation ────────────────────────────────────

def test_energy_segmentation(audio: np.ndarray, sr: int, label: str,
                             frame_length: int = 2048, hop_length: int = 512,
                             energy_threshold_db: float = -30,
                             min_segment_s: float = 0.3,
                             min_silence_s: float = 0.3) -> list[tuple[float, float]]:
    """Split audio at low-energy gaps (silences).

    Simpler than VAD but works well for clearly separated phrases.
    """
    # Compute RMS energy per frame
    S = np.abs(librosa.stft(audio, n_fft=frame_length, hop_length=hop_length))
    rms = librosa.feature.rms(S=S)[0]

    # Convert to dB
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Threshold
    is_speech = rms_db > energy_threshold_db

    # Find transitions
    frames = []
    in_speech = False
    start_frame = 0

    for i, speech in enumerate(is_speech):
        if speech and not in_speech:
            start_frame = i
            in_speech = True
        elif not speech and in_speech:
            frames.append((start_frame, i))
            in_speech = False
    if in_speech:
        frames.append((start_frame, len(is_speech)))

    # Convert to time and filter by minimum duration
    segments = []
    for sf, ef in frames:
        start_s = sf * hop_length / sr
        end_s = ef * hop_length / sr
        if end_s - start_s >= min_segment_s:
            segments.append((start_s, end_s))

    return segments


# ── Display helpers ──────────────────────────────────────────────────────────

def print_segments(label: str, segments: list[tuple[float, float]], total_dur: float):
    """Print segments in a readable format."""
    print(f"\n  [{label}] {len(segments)} segments:")
    for i, (s, e) in enumerate(segments):
        dur = e - s
        bar = "█" * int(dur * 10)
        gap = "·" * int((s - (segments[i-1][1] if i > 0 else 0)) * 10) if i > 0 else ""
        print(f"    {i+1:2d}. {s:5.2f}s - {e:5.2f}s  ({dur:.2f}s)  {gap}{bar}")

    total_speech = sum(e - s for s, e in segments)
    coverage = total_speech / total_dur * 100 if total_dur > 0 else 0
    print(f"    Coverage: {total_speech:.2f}s / {total_dur:.2f}s ({coverage:.1f}%)")


def print_timeline(segments_list: list[tuple[str, list[tuple[float, float]]]], total_dur: float):
    """Print a combined timeline view for comparison."""
    print(f"\n{'='*80}")
    print("TIMELINE COMPARISON (each char = ~0.1s)")
    print(f"{'='*80}")
    width = int(total_dur * 10)

    for label, segments in segments_list:
        line = [" "] * width
        for s, e in segments:
            for pos in range(int(s * 10), min(int(e * 10), width)):
                line[pos] = "█"
        # Mark boundaries with |
        for s, e in segments:
            si = int(s * 10)
            ei = int(e * 10)
            if 0 <= si < width:
                line[si] = "|"
            if 0 <= ei - 1 < width:
                line[ei - 1] = "|"

        print(f"  {label:35s} {''.join(line)}")

    # Time ruler
    ruler = [" "] * width
    for i in range(0, width, 10):  # every 1s
        ruler[i] = str(i // 10) if i // 10 < 10 else str(i // 10)
    print(f"  {'':35s} {''.join(ruler)}")
    tick_str = '0123456789' * (width // 10 + 1)
    print(f"  {'':35s} {tick_str[:width]}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    global torch
    import torch

    print("FireSing VAD Prototype — Segmentation Comparison\n")
    print(f"Input: {VOCALS_PATH}")
    print(f"Exists: {VOCALS_PATH.exists()}")

    if not VOCALS_PATH.exists():
        print("ERROR: No test vocals found. Run test_e2e_gpu.py first.")
        return

    # Load audio
    audio_16k, sr_16k = load_audio_16k_mono(str(VOCALS_PATH))
    audio_orig, sr_orig = load_audio_original(str(VOCALS_PATH))
    total_dur = len(audio_orig) / sr_orig
    print(f"Duration: {total_dur:.2f}s (16kHz mono for VAD, {sr_orig}Hz for onset)")

    all_results = []

    # ── Strategy 1: Silero-VAD (multiple thresholds) ──
    print("\n" + "="*60)
    print("STRATEGY 1: Silero-VAD")
    print("="*60)

    for threshold in [0.3, 0.5, 0.7]:
        for min_silence in [200, 300, 500]:
            label = f"VAD thr={threshold} sil={min_silence}ms"
            try:
                segs = test_silero_vad(audio_16k, sr_16k, label,
                                       threshold=threshold,
                                       min_silence_ms=min_silence)
                print_segments(label, segs, total_dur)
                all_results.append((label, segs))
            except Exception as e:
                print(f"  [{label}] Error: {e}")

    # ── Strategy 2: Librosa Onset Detection ──
    print("\n" + "="*60)
    print("STRATEGY 2: Librosa Onset Detection")
    print("="*60)

    for method in ["default", "spectral_flux"]:
        label = f"Onset ({method})"
        try:
            if method == "spectral_flux":
                # Custom: spectral flux onset
                S = np.abs(librosa.stft(audio_orig))
                flux = np.diff(S, axis=1)
                flux = np.mean(np.maximum(flux, 0), axis=0)
                onset_frames = librosa.onset.onset_detect(
                    y=audio_orig, sr=sr_orig,
                    onset_envelope=flux,
                    units="frames", backtrack=True,
                )
                onset_times = librosa.frames_to_time(onset_frames, sr=sr_orig)
                segs = []
                for i in range(len(onset_times)):
                    start = float(onset_times[i])
                    end = float(onset_times[i + 1]) if i + 1 < len(onset_times) else total_dur
                    if end - start >= 0.3:
                        segs.append((start, end))
            else:
                segs = test_onset_detection(audio_orig, sr_orig, label)

            print_segments(label, segs, total_dur)
            all_results.append((label, segs))
        except Exception as e:
            print(f"  [{label}] Error: {e}")

    # ── Strategy 3: Energy-based ──
    print("\n" + "="*60)
    print("STRATEGY 3: Energy-based Segmentation")
    print("="*60)

    for threshold_db in [-40, -30, -20]:
        label = f"Energy thr={threshold_db}dB"
        try:
            segs = test_energy_segmentation(audio_orig, sr_orig, label,
                                            energy_threshold_db=threshold_db)
            print_segments(label, segs, total_dur)
            all_results.append((label, segs))
        except Exception as e:
            print(f"  [{label}] Error: {e}")

    # ── Strategy 4: Combined VAD + Onset ──
    print("\n" + "="*60)
    print("STRATEGY 4: Combined VAD + Onset")
    print("="*60)

    # Use best VAD config (thr=0.5, sil=300) + default onset
    vad_segs = None
    onset_segs = None
    for label, segs in all_results:
        if "VAD thr=0.5 sil=300" in label:
            vad_segs = segs
        if label == "Onset (default)":
            onset_segs = segs

    if vad_segs and onset_segs:
        label = "VAD(0.5,300ms) + Onset"
        combined = test_combined(vad_segs, onset_segs, audio_orig, sr_orig, label)
        print_segments(label, combined, total_dur)
        all_results.append((label, combined))

    # ── Timeline comparison ──
    # Pick top candidates for visual comparison
    candidates = [
        (l, s) for l, s in all_results
        if any(k in l for k in ["VAD thr=0.5 sil=300", "Onset (default)",
                                  "Energy thr=-30dB", "VAD(0.5,300ms) + Onset"])
    ]
    if candidates:
        print_timeline(candidates, total_dur)

    # ── Summary ──
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for label, segs in all_results:
        n = len(segs)
        avg_dur = np.mean([e - s for s, e in segs]) if segs else 0
        total_speech = sum(e - s for s, e in segs)
        coverage = total_speech / total_dur * 100 if total_dur > 0 else 0
        print(f"  {label:40s} → {n:2d} segs, avg {avg_dur:.2f}s, {coverage:.0f}% coverage")

    print("\n✓ VAD prototype complete. Review segment boundaries above.")


if __name__ == "__main__":
    main()
