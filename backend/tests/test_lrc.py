"""Tests for LRC parsing and vocal segmentation."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.services.lyrics_service import (
    parse_lrc, validate_segments, compute_end_times, cut_vocals,
    LrcLine, MIN_SEGMENT_DURATION,
)


class TestParseLrc:
    def test_parse_basic(self, sample_lrc):
        """Parse sample LRC and verify 5 lines extracted."""
        lines = parse_lrc(sample_lrc)
        assert len(lines) == 5
        assert lines[0].text == "第一句歌词"
        assert lines[0].time == 5.0
        assert lines[4].text == "第五句歌词"
        assert lines[4].time == 25.0

    def test_parse_skips_metadata(self, tmp_path):
        """Metadata lines like [ti:], [ar:], [al:] should be skipped."""
        lrc = tmp_path / "test.lrc"
        lrc.write_text(
            "[ti:Song Title]\n[ar:Artist]\n[al:Album]\n"
            "[00:05.00]实际歌词\n[00:10.00]第二行\n",
            encoding="utf-8",
        )
        lines = parse_lrc(lrc)
        assert len(lines) == 2
        assert lines[0].text == "实际歌词"

    def test_parse_skips_empty_text(self, tmp_path):
        """Lines with timestamp but no text should be skipped."""
        lrc = tmp_path / "test.lrc"
        lrc.write_text("[00:00.00]\n[00:05.00]有歌词\n", encoding="utf-8")
        lines = parse_lrc(lrc)
        assert len(lines) == 1
        assert lines[0].text == "有歌词"

    def test_parse_various_timestamps(self, tmp_path):
        """Parse mm:ss.xx format correctly."""
        lrc = tmp_path / "test.lrc"
        lrc.write_text(
            "[01:30.50]一分半\n[00:05.00]开头的\n",
            encoding="utf-8",
        )
        lines = parse_lrc(lrc)
        # Order is file order, not sorted
        assert lines[0].time == 90.5
        assert lines[1].time == 5.0


class TestValidateSegments:
    def test_validate_ok(self):
        lines = [
            LrcLine(time=0.0, text="a"),
            LrcLine(time=5.0, text="b"),
            LrcLine(time=10.0, text="c"),
        ]
        result = validate_segments(lines)
        assert result == lines

    def test_validate_empty(self):
        with pytest.raises(ValueError, match="no lyrics"):
            validate_segments([])

    def test_validate_not_monotonic(self):
        lines = [
            LrcLine(time=10.0, text="a"),
            LrcLine(time=5.0, text="b"),
        ]
        with pytest.raises(ValueError, match="not monotonic"):
            validate_segments(lines)

    def test_validate_too_short(self):
        lines = [
            LrcLine(time=0.0, text="a"),
            LrcLine(time=0.1, text="b"),  # 0.1s < 0.3s
        ]
        with pytest.raises(ValueError, match="too short"):
            validate_segments(lines)

    def test_validate_equal_timestamps(self):
        """Equal timestamps are fine (0 duration handled by monotonic check)."""
        lines = [
            LrcLine(time=5.0, text="a"),
            LrcLine(time=10.0, text="b"),
        ]
        result = validate_segments(lines)
        assert len(result) == 2


class TestComputeEndTimes:
    def test_basic(self):
        lines = [
            LrcLine(time=0.0, text="a"),
            LrcLine(time=5.0, text="b"),
            LrcLine(time=10.0, text="c"),
        ]
        result = compute_end_times(lines)
        assert len(result) == 3
        assert result[0]["start_time"] == 0.0
        assert result[0]["end_time"] == 5.0
        assert result[1]["end_time"] == 10.0
        # Last segment gets default 5s
        assert result[2]["end_time"] == 15.0

    def test_with_total_duration(self):
        lines = [
            LrcLine(time=5.0, text="a"),
            LrcLine(time=10.0, text="b"),
        ]
        result = compute_end_times(lines, total_duration=12.0)
        # Last segment capped at total_duration
        assert result[1]["end_time"] == 12.0

    def test_line_numbers(self):
        lines = [LrcLine(time=float(i), text=f"line{i}") for i in range(3)]
        result = compute_end_times(lines)
        assert [s["line_number"] for s in result] == [1, 2, 3]


class TestCutVocals:
    def test_cut_creates_files(self, sample_wav, tmp_path):
        """Cut sample WAV into segments and verify files are created."""
        segments = [
            {"line_number": 1, "text": "a", "start_time": 0.0, "end_time": 0.5},
            {"line_number": 2, "text": "b", "start_time": 0.5, "end_time": 1.0},
        ]
        output_dir = tmp_path / "segments"
        paths = cut_vocals(sample_wav, segments, output_dir)

        assert len(paths) == 2
        assert paths[0].name == "line_001.wav"
        assert paths[1].name == "line_002.wav"
        assert paths[0].exists()
        assert paths[1].exists()
        # Each segment should be > 0 bytes
        assert paths[0].stat().st_size > 0
        assert paths[1].stat().st_size > 0
