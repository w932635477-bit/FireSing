#!/usr/bin/env python3
"""
FireSing 音质修复验证测试

验证 3 个核心修复:
1. _align_duration: librosa phase vocoder vs 旧 resampling 方法的音高保持
2. _squared_sine_crossfade: 等功率 crossfade vs 线性 crossfade
3. 短 segment 保护逻辑

无需 GPU 服务器，用合成音频在本地运行。
"""

import io
import numpy as np
import soundfile as sf
import librosa
from pydub import AudioSegment

# ========== Constants (same as production) ==========

_DURATION_TOLERANCE_S = 0.01
_MIN_ALIGN_DURATION_S = 1.5
CROSSFADE_MS = 50


# ========== Core Functions (standalone, identical to production) ==========

def _align_duration(converted_bytes, original_duration_ms):
    """Pitch-preserving duration alignment via librosa phase vocoder."""
    audio, sr = sf.read(io.BytesIO(converted_bytes))
    current_duration_s = len(audio) / sr
    target_duration_s = original_duration_ms / 1000.0
    drift_s = abs(current_duration_s - target_duration_s)
    if drift_s < _DURATION_TOLERANCE_S:
        return converted_bytes
    if current_duration_s < _MIN_ALIGN_DURATION_S:
        return converted_bytes
    rate = current_duration_s / target_duration_s
    if rate < 0.5 or rate > 2.0:
        return converted_bytes
    if audio.ndim == 1:
        stretched = librosa.effects.time_stretch(audio, rate=rate)
    else:
        stretched = np.stack([
            librosa.effects.time_stretch(audio[:, c], rate=rate)
            for c in range(audio.shape[1])
        ], axis=1)
    buf = io.BytesIO()
    sf.write(buf, stretched, sr, format="WAV")
    return buf.getvalue()


def _old_align_duration(converted_bytes, original_duration_ms):
    """OLD method: resampling (changes pitch — this is the bug)."""
    seg = AudioSegment.from_wav(io.BytesIO(converted_bytes))
    current_ms = len(seg)
    if abs(current_ms - original_duration_ms) < 5:
        return converted_bytes
    speed_ratio = current_ms / original_duration_ms
    if speed_ratio < 0.5 or speed_ratio > 2.0:
        return converted_bytes
    new_frame_rate = int(seg.frame_rate * speed_ratio)
    stretched = seg._spawn(seg.raw_data, overrides={"frame_rate": new_frame_rate})
    stretched = stretched.set_frame_rate(seg.frame_rate)
    buf = io.BytesIO()
    stretched.export(buf, format="wav")
    return buf.getvalue()


def _squared_sine_crossfade(seg1_bytes, seg2_bytes, crossfade_ms):
    """Squared-sine crossfade (RVC best practice)."""
    seg1 = AudioSegment.from_wav(io.BytesIO(seg1_bytes))
    seg2 = AudioSegment.from_wav(io.BytesIO(seg2_bytes))
    cf_samples = int(crossfade_ms * seg1.frame_rate / 1000)
    seg1_raw = np.array(seg1.get_array_of_samples(), dtype=np.float64)
    seg2_raw = np.array(seg2.get_array_of_samples(), dtype=np.float64)
    if len(seg1_raw) < cf_samples or len(seg2_raw) < cf_samples:
        result = seg1 + seg2
        buf = io.BytesIO()
        result.export(buf, format="wav")
        return buf.getvalue()
    fade_out = np.cos(0.5 * np.pi * np.linspace(0, 1, cf_samples)) ** 2
    fade_in = np.sin(0.5 * np.pi * np.linspace(0, 1, cf_samples)) ** 2
    channels = seg1.channels
    if channels > 1:
        seg1_2d = seg1_raw.reshape(-1, channels)
        seg2_2d = seg2_raw.reshape(-1, channels)
        overlap = seg1_2d[-cf_samples:] * fade_out[:, np.newaxis] + seg2_2d[:cf_samples] * fade_in[:, np.newaxis]
        result_samples = np.concatenate([seg1_2d[:-cf_samples], overlap, seg2_2d[cf_samples:]], axis=0).flatten()
    else:
        overlap = seg1_raw[-cf_samples:] * fade_out + seg2_raw[:cf_samples] * fade_in
        result_samples = np.concatenate([seg1_raw[:-cf_samples], overlap, seg2_raw[cf_samples:]])
    result = AudioSegment(
        result_samples.astype(np.int16).tobytes(),
        frame_rate=seg1.frame_rate, sample_width=2, channels=channels
    )
    buf = io.BytesIO()
    result.export(buf, format="wav")
    return buf.getvalue()


# ========== Helpers ==========

def make_sine_wav_bytes(freq, duration_s, sr=44100):
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    audio = (np.sin(2 * np.pi * freq * t) * 0.3 * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, audio, sr, format="WAV")
    return buf.getvalue()


def get_peak_freq(wav_bytes):
    audio, sr = sf.read(io.BytesIO(wav_bytes))
    if audio.ndim > 1:
        audio = audio[:, 0]
    spectrum = np.abs(np.fft.rfft(audio.astype(float)))
    freqs = np.fft.rfftfreq(len(audio), 1 / sr)
    peak_idx = np.argmax(spectrum[1:]) + 1
    return freqs[peak_idx]


def get_duration_ms(wav_bytes):
    audio, sr = sf.read(io.BytesIO(wav_bytes))
    return len(audio) / sr * 1000


# ========== Tests ==========

def test_new_align_preserves_pitch():
    """New method: phase vocoder preserves pitch during duration alignment."""
    original_freq = 440.0
    rvc_output = make_sine_wav_bytes(original_freq, 3.05)

    aligned = _align_duration(rvc_output, 3000.0)
    peak = get_peak_freq(aligned)
    duration = get_duration_ms(aligned)
    cents = abs(1200 * np.log2(peak / original_freq))

    print(f"  New method: 440Hz → {peak:.1f}Hz ({cents:.1f} cents drift), duration {duration:.1f}ms")

    assert abs(duration - 3000.0) < 10, f"Duration wrong: {duration:.1f}ms"
    assert cents < 5, f"Pitch drift too large: {cents:.1f} cents"
    return cents


def test_old_align_shifts_pitch():
    """Old method: resampling changes pitch."""
    original_freq = 440.0
    rvc_output = make_sine_wav_bytes(original_freq, 3.05)

    aligned = _old_align_duration(rvc_output, 3000.0)
    peak = get_peak_freq(aligned)
    cents = abs(1200 * np.log2(peak / original_freq))

    print(f"  Old method: 440Hz → {peak:.1f}Hz ({cents:.1f} cents drift)")
    return cents


def test_crossfade_no_silence():
    """Squared-sine crossfade produces non-silent output."""
    seg1 = make_sine_wav_bytes(440, 2.0)
    seg2 = make_sine_wav_bytes(523, 2.0)

    result = _squared_sine_crossfade(seg1, seg2, CROSSFADE_MS)
    audio, sr = sf.read(io.BytesIO(result))
    rms = np.sqrt(np.mean(audio.astype(float) ** 2))

    expected_ms = 2000 + 2000 - CROSSFADE_MS
    actual_ms = len(audio) / sr * 1000

    print(f"  Duration: {actual_ms:.0f}ms (expected {expected_ms}ms)")
    print(f"  RMS: {rms:.0f} (non-silent)")

    assert rms > 0.01, f"Near-silent output: RMS={rms}"
    assert abs(actual_ms - expected_ms) < 5, f"Duration wrong: {actual_ms:.0f}ms"
    return True


def test_crossfade_short_segments():
    """Short segments (< crossfade duration) don't crash."""
    seg1 = make_sine_wav_bytes(440, 0.03)
    seg2 = make_sine_wav_bytes(523, 0.03)

    result = _squared_sine_crossfade(seg1, seg2, CROSSFADE_MS)
    audio, sr = sf.read(io.BytesIO(result))
    assert len(audio) > 0

    print(f"  30ms segments: output {len(audio)/sr*1000:.0f}ms")
    return True


def test_short_segment_skip():
    """Segments < 1.5s skip alignment (no phase vocoder artifacts)."""
    short = make_sine_wav_bytes(440, 1.0)
    aligned = _align_duration(short, 1050.0)
    assert aligned == short, "Short segment should be unchanged"

    print(f"  1.0s segment: skipped alignment")
    return True


def test_no_drift_passthrough():
    """Exact duration match returns original bytes."""
    audio = make_sine_wav_bytes(440, 3.0)
    aligned = _align_duration(audio, 3000.0)
    assert aligned == audio, "Should return original"

    print(f"  3.0s exact match: passthrough")
    return True


# ========== Run ==========

def run_all():
    results = []
    tests = [
        ("Phase vocoder 保音高", test_new_align_preserves_pitch),
        ("旧方法改音高 (对照)", test_old_align_shifts_pitch),
        ("Squared-sine crossfade", test_crossfade_no_silence),
        ("短 segment crossfade", test_crossfade_short_segments),
        ("短 segment 跳过 alignment", test_short_segment_skip),
        ("无偏移 passthrough", test_no_drift_passthrough),
    ]

    print("=" * 60)
    print("  FireSing 音质修复验证")
    print("=" * 60)
    print()

    for name, fn in tests:
        print(f"[TEST] {name}")
        try:
            fn()
            results.append((name, "PASS", None))
            print(f"  PASS\n")
        except AssertionError as e:
            results.append((name, "FAIL", str(e)))
            print(f"  FAIL: {e}\n")
        except Exception as e:
            results.append((name, "ERROR", str(e)))
            print(f"  ERROR: {e}\n")

    # Summary
    print("=" * 60)
    print("  结果汇总")
    print("=" * 60)

    passed = sum(1 for _, s, _ in results if s == "PASS")
    for name, status, error in results:
        mark = "✓" if status == "PASS" else "✗"
        print(f"  {mark} {name}: {status}")
        if error:
            print(f"    {error}")
    print(f"\n  {passed}/{len(results)} 通过")

    # Quantitative comparison
    print("\n" + "=" * 60)
    print("  量化对比: 新旧方法音高偏移 (50ms drift, 3s segment)")
    print("=" * 60)

    try:
        new_cents = test_new_align_preserves_pitch()
        old_cents = test_old_align_shifts_pitch()
        print(f"\n  新方法 (phase vocoder): {new_cents:.1f} cents")
        print(f"  旧方法 (resampling):    {old_cents:.1f} cents")
        print(f"  改善: {old_cents - new_cents:.1f} cents")
        print(f"\n  人耳可分辨阈值: ~10 cents")
        if old_cents > 10:
            print(f"  旧方法 {old_cents:.1f} cents > 10 → 跑调 (可听出)")
        if new_cents < 10:
            print(f"  新方法 {new_cents:.1f} cents < 10 → 不跑调")
    except Exception as e:
        print(f"  量化对比失败: {e}")

    print("\n" + "=" * 60)
    print(f"  最终结果: {'ALL PASS' if passed == len(results) else f'{len(results) - passed} FAILED'}")
    print("=" * 60)

    return passed == len(results)


if __name__ == "__main__":
    import sys
    success = run_all()
    sys.exit(0 if success else 1)
