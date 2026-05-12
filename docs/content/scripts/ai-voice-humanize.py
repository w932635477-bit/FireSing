#!/usr/bin/env python3
"""
AI Voice Humanizer - 抖音AI配音识别规避

Processes AI-generated voiceover (Gemini TTS) to pass Douyin's AI content detection.
Techniques applied:
  1. Pink noise floor (simulates room tone)
  2. Micro pitch drift (natural vocal cord variation)
  3. Segment-level timing jitter (natural speech rhythm)
  4. Dynamic volume envelope (human loudness variation)
  5. Subtle room reverb (recording environment)
  6. Warm EQ + de-harsh (less "digital" sound)
  7. Subtle tape saturation (analog character)
  8. Bit-depth dithering (recording artifact)

Usage:
  python ai-voice-humanize.py <input_dir> [--output-dir <dir>] [--intensity light|medium|heavy]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal as sp_signal


def load_audio(filepath: str) -> tuple[np.ndarray, int]:
    """Load audio file, return (samples, sample_rate). Mono or stereo."""
    data, sr = sf.read(filepath, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr


def save_audio(filepath: str, data: np.ndarray, sr: int) -> None:
    """Save audio as WAV 16-bit."""
    data = np.clip(data, -1.0, 1.0)
    sf.write(filepath, data, sr, subtype="PCM_16")


def generate_pink_noise(length: int, sr: int, amplitude: float) -> np.ndarray:
    """Generate pink noise using Voss-McCartney algorithm."""
    n_rows = 16
    rng = np.random.default_rng()
    array = rng.standard_normal(n_rows)
    result = np.zeros(length)
    for i in range(length):
        if i % sr == 0:
            array = rng.standard_normal(n_rows)
        elif i % (sr // 2) == 0:
            array[:8] = rng.standard_normal(8)
        elif i % (sr // 4) == 0:
            array[:4] = rng.standard_normal(4)
        elif i % (sr // 8) == 0:
            array[:2] = rng.standard_normal(2)
        else:
            array[0] = rng.standard_normal()
        result[i] = np.sum(array)
    peak = np.max(np.abs(result))
    if peak > 0:
        result = result / peak * amplitude
    return result.astype(np.float32)


def apply_pitch_drift(data: np.ndarray, sr: int, max_cents: float = 15.0) -> np.ndarray:
    """Apply subtle pitch drift using slow sinusoidal modulation."""
    duration = len(data) / sr
    t = np.linspace(0, duration, len(data), dtype=np.float32)

    drift_hz = np.sin(2 * np.pi * 0.15 * t) * max_cents / 100 * 3.0
    drift_hz += np.sin(2 * np.pi * 0.07 * t + 1.3) * max_cents / 100 * 1.5
    drift_hz += np.sin(2 * np.pi * 0.31 * t + 0.7) * max_cents / 100 * 0.8

    phase = np.cumsum(2 * np.pi * drift_hz / sr).astype(np.float32)

    indices = np.arange(len(data), dtype=np.float32) + phase * sr * 0.001
    indices = np.clip(indices, 0, len(data) - 1)

    idx_floor = np.floor(indices).astype(int)
    idx_ceil = np.minimum(idx_floor + 1, len(data) - 1)
    frac = (indices - idx_floor).astype(np.float32)

    return data[idx_floor] * (1 - frac) + data[idx_ceil] * frac


def apply_timing_jitter(data: np.ndarray, sr: int, segment_ms: int = 300,
                        max_shift_ms: float = 8.0) -> np.ndarray:
    """Add micro-timing jitter at segment boundaries."""
    rng = np.random.default_rng()
    segment_samples = int(sr * segment_ms / 1000)
    max_shift = int(sr * max_shift_ms / 1000)

    if max_shift < 1 or segment_samples < 1:
        return data

    result = np.zeros_like(data)
    pos = 0
    out_pos = 0

    while pos < len(data):
        end = min(pos + segment_samples, len(data))
        shift = rng.integers(-max_shift, max_shift + 1)

        segment = data[pos:end]
        out_start = max(0, min(out_pos + shift, len(result) - len(segment)))
        out_end = min(out_start + len(segment), len(result))
        copy_len = out_end - out_start
        result[out_start:out_end] = segment[:copy_len]

        pos = end
        out_pos = out_start + copy_len

    return result


def apply_volume_envelope(data: np.ndarray, sr: int, variation_db: float = 1.5) -> np.ndarray:
    """Apply slow volume envelope to simulate natural loudness variation."""
    duration = len(data) / sr
    t = np.linspace(0, duration, len(data), dtype=np.float32)

    envelope = np.sin(2 * np.pi * 0.12 * t) * 0.4
    envelope += np.sin(2 * np.pi * 0.05 * t + 0.9) * 0.3
    envelope += np.sin(2 * np.pi * 0.23 * t + 2.1) * 0.2
    envelope += np.sin(2 * np.pi * 0.41 * t + 0.5) * 0.1

    gain_linear = 10 ** (envelope * variation_db / 20)
    return (data * gain_linear).astype(np.float32)


def apply_room_reverb(data: np.ndarray, sr: int, room_size: float = 0.08,
                      decay: float = 0.15) -> np.ndarray:
    """Apply subtle room reverb using early reflections."""
    n_taps = 6
    base_delay_ms = 11.0
    delays_ms = [base_delay_ms * (i + 1) * (1 + 0.1 * np.random.random())
                 for i in range(n_taps)]
    gains = [decay * (0.7 ** i) for i in range(n_taps)]

    max_delay = int(max(delays_ms) * sr / 1000) + 1
    ir = np.zeros(max_delay + 1, dtype=np.float32)
    ir[0] = 1.0

    for delay_ms, gain in zip(delays_ms, gains):
        idx = int(delay_ms * sr / 1000)
        if idx < len(ir):
            ir[idx] = gain

    reverbed = np.convolve(data, ir, mode="full")[:len(data)]
    wet = reverbed * room_size
    return (data + wet).astype(np.float32)


def apply_warm_eq(data: np.ndarray, sr: int) -> np.ndarray:
    """Apply warm EQ: slight low-mid boost, de-harsh high frequencies."""
    nyq = sr / 2.0

    sos_low = sp_signal.butter(2, [200 / nyq, 800 / nyq], btype="band",
                               output="sos")
    low_boost = sp_signal.sosfilt(sos_low, data) * 0.8

    sos_high = sp_signal.butter(2, [5000 / nyq, min(8000 / nyq, nyq * 0.99)],
                                btype="band", output="sos")
    high_cut = sp_signal.sosfilt(sos_high, data) * 0.6

    mid = data - low_boost - high_cut
    return ((low_boost * 1.15 + mid + high_cut * 0.85) / 1.0).astype(np.float32)


def apply_tape_saturation(data: np.ndarray, drive: float = 0.3) -> np.ndarray:
    """Apply subtle tape saturation (soft clipping with harmonics)."""
    gain = 1.0 + drive
    driven = data * gain
    saturated = np.tanh(driven * 1.5) / np.tanh(1.5)
    return (data * (1 - drive * 0.5) + saturated * drive * 0.5).astype(np.float32)


def apply_dither(data: np.ndarray, bits: int = 15) -> np.ndarray:
    """Apply triangular dither for natural quantization noise."""
    rng = np.random.default_rng()
    amplitude = 1.0 / (2 ** bits)
    dither = (rng.random(len(data)) + rng.random(len(data)) - 1) * amplitude
    return (data + dither).astype(np.float32)


INTENSITY_PRESETS = {
    "light": {
        "noise_db": -52,
        "pitch_cents": 10,
        "jitter_ms": 5,
        "volume_db": 1.0,
        "reverb_size": 0.05,
        "reverb_decay": 0.10,
        "saturation_drive": 0.15,
        "dither_bits": 14,
    },
    "medium": {
        "noise_db": -46,
        "pitch_cents": 18,
        "jitter_ms": 10,
        "volume_db": 2.0,
        "reverb_size": 0.10,
        "reverb_decay": 0.20,
        "saturation_drive": 0.30,
        "dither_bits": 13,
    },
    "heavy": {
        "noise_db": -40,
        "pitch_cents": 25,
        "jitter_ms": 15,
        "volume_db": 3.0,
        "reverb_size": 0.15,
        "reverb_decay": 0.25,
        "saturation_drive": 0.45,
        "dither_bits": 12,
    },
}


def humanize_audio(input_path: str, output_path: str, intensity: str = "medium",
                   log_fn=print) -> dict:
    """Process a single audio file to bypass AI detection."""
    preset = INTENSITY_PRESETS[intensity]
    log_fn(f"  Loading: {input_path}")

    data, sr = load_audio(input_path)
    original_peak = np.max(np.abs(data))
    log_fn(f"  SR={sr}Hz, samples={len(data)}, peak={original_peak:.4f}")

    steps = [
        ("pink_noise", lambda d: d + generate_pink_noise(
            len(d), sr, 10 ** (preset["noise_db"] / 20) * original_peak)),
        ("pitch_drift", lambda d: apply_pitch_drift(d, sr, preset["pitch_cents"])),
        ("timing_jitter", lambda d: apply_timing_jitter(d, sr, max_shift_ms=preset["jitter_ms"])),
        ("volume_envelope", lambda d: apply_volume_envelope(d, sr, preset["volume_db"])),
        ("warm_eq", lambda d: apply_warm_eq(d, sr)),
        ("room_reverb", lambda d: apply_room_reverb(
            d, sr, preset["reverb_size"], preset["reverb_decay"])),
        ("tape_saturation", lambda d: apply_tape_saturation(d, preset["saturation_drive"])),
        ("dither", lambda d: apply_dither(d, preset["dither_bits"])),
    ]

    report = {"input": input_path, "sr": sr, "samples": len(data), "steps": []}
    for name, fn in steps:
        before_peak = np.max(np.abs(data))
        data = fn(data)
        after_peak = np.max(np.abs(data))
        step_info = {"name": name, "peak_before": float(before_peak),
                     "peak_after": float(after_peak)}
        report["steps"].append(step_info)
        log_fn(f"  [{name}] peak: {before_peak:.4f} → {after_peak:.4f}")

    data = np.clip(data, -1.0, 1.0)
    save_audio(output_path, data, sr)
    log_fn(f"  Saved: {output_path} ({os.path.getsize(output_path)} bytes)")

    report["output"] = output_path
    report["output_size"] = os.path.getsize(output_path)
    return report


def concatenate_wavs(wav_files: list[str], output_path: str,
                     gap_ms: int = 300) -> None:
    """Concatenate WAV files with a short gap of silence."""
    segments = []
    gap_samples = None
    sr = None

    for f in wav_files:
        data, file_sr = load_audio(f)
        if sr is None:
            sr = file_sr
            gap_samples = np.zeros(int(sr * gap_ms / 1000), dtype=np.float32)
        segments.append(data)
        segments.append(gap_samples)

    segments.append(gap_samples)
    full = np.concatenate(segments)
    full = np.clip(full, -1.0, 1.0)
    save_audio(output_path, full, sr)


def main():
    parser = argparse.ArgumentParser(
        description="AI Voice Humanizer - 抖音AI配音识别规避")
    parser.add_argument("input_dir", help="Directory containing S01.wav..S06.wav")
    parser.add_argument("--output-dir", help="Output directory (default: <input_dir>/humanized)")
    parser.add_argument("--intensity", choices=["light", "medium", "heavy"],
                        default="medium",
                        help="Processing intensity (default: medium)")
    parser.add_argument("--concat", action="store_true",
                        help="Also create concatenated full narration")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else input_dir / "humanized"
    output_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(input_dir.glob("S[0-9][0-9].wav"))
    if not wav_files:
        print(f"No S01.wav..S06.wav found in {input_dir}")
        sys.exit(1)

    print(f"=== AI Voice Humanizer ===")
    print(f"Input:   {input_dir}")
    print(f"Output:  {output_dir}")
    print(f"Files:   {[f.name for f in wav_files]}")
    print(f"Mode:    {args.intensity}")
    print()

    log_path = output_dir / f"humanize-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    all_reports = []

    for wav in wav_files:
        out_file = output_dir / wav.name
        print(f"[{wav.name}]")
        report = humanize_audio(str(wav), str(out_file), args.intensity)
        all_reports.append(report)
        print()

    if args.concat:
        concat_wavs = sorted(output_dir.glob("S[0-9][0-9].wav"))
        concat_path = output_dir / "qidian-ep02-full-narration-humanized.wav"
        print(f"[Concatenating {len(concat_wavs)} segments]")
        concatenate_wavs([str(f) for f in concat_wavs], str(concat_path))
        print(f"  Saved: {concat_path} ({os.path.getsize(concat_path)} bytes)")
        print()

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "intensity": args.intensity,
        "preset": INTENSITY_PRESETS[args.intensity],
        "reports": all_reports,
    }
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    print(f"Log: {log_path}")
    print("\nDone. Use humanized WAV files in 剪映 as voiceover source.")


if __name__ == "__main__":
    main()
