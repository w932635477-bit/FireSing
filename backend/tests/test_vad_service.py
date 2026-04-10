"""Tests for VAD service — energy-based vocal segmentation."""

import math
import struct
import io
import tempfile
from pathlib import Path

import numpy as np
import pytest

from backend.services.vad_service import segment_vocals, cut_vocals


def _make_wav(
    audio: np.ndarray,
    sr: int = 44100,
    path: Path | None = None,
) -> Path:
    """Write a numpy array as a mono 16-bit WAV file."""
    if path is None:
        fd, path_str = tempfile.mkstemp(suffix=".wav")
        path = Path(path_str)
    # Normalize to int16
    audio_int = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    data = audio_int.tobytes()
    data_size = len(data)

    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<H", 1))   # PCM
    buf.write(struct.pack("<H", 1))   # mono
    buf.write(struct.pack("<I", sr))
    buf.write(struct.pack("<I", sr * 2))
    buf.write(struct.pack("<H", 2))
    buf.write(struct.pack("<H", 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(data)

    path.write_bytes(buf.getvalue())
    return path


def _sine(sr: int, duration: float, freq: float = 440.0) -> np.ndarray:
    """Generate a sine wave."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _silence(sr: int, duration: float) -> np.ndarray:
    """Generate silence."""
    return np.zeros(int(sr * duration))


class TestSegmentVocals:
    """Test energy-based segmentation."""

    def test_basic_segmentation(self, tmp_path):
        """Two vocal phrases separated by silence should produce 2 segments."""
        sr = 22050
        # 2s vocal + 1s silence + 2s vocal
        audio = np.concatenate([
            _sine(sr, 2.0, 440),
            _silence(sr, 1.0),
            _sine(sr, 2.0, 880),
        ])
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path)
        assert len(segments) == 2, f"Expected 2 segments, got {len(segments)}"
        assert segments[0]["line_number"] == 1
        assert segments[1]["line_number"] == 2

        # Coverage should be reasonable
        total = len(audio) / sr
        coverage = sum(s["end_time"] - s["start_time"] for s in segments) / total * 100
        assert coverage > 60, f"Coverage too low: {coverage:.1f}%"

    def test_single_continuous_vocal(self, tmp_path):
        """Continuous vocal with no silence should produce 1 segment."""
        sr = 22050
        audio = _sine(sr, 3.0, 440)
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path)
        assert len(segments) >= 1
        # Coverage should be high
        total = len(audio) / sr
        coverage = sum(s["end_time"] - s["start_time"] for s in segments) / total * 100
        assert coverage > 80

    def test_all_silence(self, tmp_path):
        """Pure silence should produce 0 segments."""
        sr = 22050
        audio = _silence(sr, 5.0)
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path)
        assert len(segments) == 0

    def test_many_segments(self, tmp_path):
        """Multiple short vocal bursts should produce multiple segments."""
        sr = 22050
        parts = []
        for i in range(5):
            parts.append(_sine(sr, 0.5, 440 + i * 100))
            parts.append(_silence(sr, 0.5))
        audio = np.concatenate(parts)
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path)
        assert len(segments) >= 3, f"Expected >=3 segments, got {len(segments)}"

    def test_short_segment_filtered(self, tmp_path):
        """Segments shorter than min_segment_s should be filtered out."""
        sr = 22050
        # Very short burst (0.1s) + silence + longer burst
        audio = np.concatenate([
            _sine(sr, 0.1, 440),
            _silence(sr, 0.5),
            _sine(sr, 1.0, 880),
        ])
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path, min_segment_s=0.3)
        # The 0.1s segment should be filtered
        for seg in segments:
            assert seg["end_time"] - seg["start_time"] >= 0.3

    def test_segment_structure(self, tmp_path):
        """Each segment should have required fields."""
        sr = 22050
        audio = np.concatenate([_sine(sr, 1.0, 440), _silence(sr, 0.5), _sine(sr, 1.0, 880)])
        wav_path = _make_wav(audio, sr, tmp_path / "test.wav")

        segments = segment_vocals(wav_path)
        for seg in segments:
            assert "line_number" in seg
            assert "start_time" in seg
            assert "end_time" in seg
            assert "text" in seg
            assert seg["end_time"] > seg["start_time"]
            assert seg["line_number"] > 0


class TestCutVocals:
    """Test vocal cutting into segment files."""

    def test_cut_creates_files(self, tmp_path):
        """cut_vocals should create WAV files for each segment."""
        sr = 44100
        audio = np.concatenate([
            _sine(sr, 2.0, 440),
            _silence(sr, 0.5),
            _sine(sr, 2.0, 880),
        ])
        wav_path = _make_wav(audio, sr, tmp_path / "vocals.wav")

        segments = segment_vocals(wav_path)
        output_dir = tmp_path / "segments"
        paths = cut_vocals(wav_path, segments, output_dir)

        assert len(paths) == len(segments)
        for p in paths:
            assert p.exists()
            assert p.suffix == ".wav"
            assert p.stat().st_size > 0

    def test_cut_preserves_order(self, tmp_path):
        """Output files should be in line order."""
        sr = 44100
        audio = np.concatenate([
            _sine(sr, 1.0, 440),
            _silence(sr, 0.5),
            _sine(sr, 1.0, 880),
            _silence(sr, 0.5),
            _sine(sr, 1.0, 660),
        ])
        wav_path = _make_wav(audio, sr, tmp_path / "vocals.wav")

        segments = segment_vocals(wav_path)
        output_dir = tmp_path / "segments"
        paths = cut_vocals(wav_path, segments, output_dir)

        # Filenames should be line_001.wav, line_002.wav, etc.
        for i, p in enumerate(paths):
            assert p.name == f"line_{i+1:03d}.wav"
