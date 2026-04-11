"""Unit tests for video_service.py — pure Python logic, no FFmpeg needed.

Tests: track building, voice info, ASS generation, timestamp formatting,
color conversion, and edge cases.
"""

import pytest
from unittest.mock import MagicMock, patch

from backend.services import video_service as vs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_segment(voice_id, start, end, text="lyrics line"):
    seg = MagicMock(spec=["voice_model_id", "start_time", "end_time", "text", "line_number"])
    seg.voice_model_id = voice_id
    seg.start_time = start
    seg.end_time = end
    seg.text = text
    seg.line_number = 0
    return seg


def _make_voice_model(vid, name):
    vm = MagicMock()
    vm.id = vid
    vm.name = name
    return vm


# ---------------------------------------------------------------------------
# _f() — ASS timestamp formatting
# ---------------------------------------------------------------------------

class TestTimestampFormat:
    def test_zero(self):
        assert vs._f(0.0) == "0:00:00.00"

    def test_seconds_only(self):
        assert vs._f(5.5) == "0:00:05.50"

    def test_minutes(self):
        assert vs._f(125.0) == "0:02:05.00"

    def test_hours(self):
        assert vs._f(3661.25) == "1:01:01.25"

    def test_fractional_cs(self):
        assert vs._f(0.999) == "0:00:00.99"

    def test_large_value(self):
        result = vs._f(7200.0)
        assert result == "2:00:00.00"


# ---------------------------------------------------------------------------
# _hex2rgb() — color conversion
# ---------------------------------------------------------------------------

class TestHexToRgb:
    def test_red(self):
        assert vs._hex2rgb("#FF0000") == (255, 0, 0)

    def test_no_hash(self):
        assert vs._hex2rgb("00FF00") == (0, 255, 0)

    def test_blue(self):
        assert vs._hex2rgb("#0000FF") == (0, 0, 255)

    def test_mixed(self):
        assert vs._hex2rgb("#FF6B6B") == (255, 107, 107)


# ---------------------------------------------------------------------------
# _build_voice_info() — voice mapping
# ---------------------------------------------------------------------------

class TestBuildVoiceInfo:
    def test_single_voice(self):
        segs = [_make_segment("v1", 0, 5)]
        db = MagicMock()
        vm = _make_voice_model("v1", "小红")
        db.query.return_value.filter.return_value.all.return_value = [vm]

        info = vs._build_voice_info(segs, db)
        assert "v1" in info
        assert info["v1"]["name"] == "小红"
        assert info["v1"]["color"] == vs.VOICE_COLORS[0]

    def test_multiple_voices(self):
        segs = [_make_segment("v1", 0, 5), _make_segment("v2", 5, 10)]
        db = MagicMock()
        vm1 = _make_voice_model("v1", "小红")
        vm2 = _make_voice_model("v2", "小明")
        db.query.return_value.filter.return_value.all.return_value = [vm1, vm2]

        info = vs._build_voice_info(segs, db)
        assert len(info) == 2
        assert info["v1"]["color"] != info["v2"]["color"]

    def test_missing_voice_model_fallback(self):
        segs = [_make_segment("v1", 0, 5)]
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        info = vs._build_voice_info(segs, db)
        assert info["v1"]["name"] == "Voice 1"

    def test_no_segments(self):
        info = vs._build_voice_info([], MagicMock())
        assert info == {}

    def test_single_db_query(self):
        """Verify N+1 fix: only one query for all voices."""
        segs = [_make_segment(f"v{i}", i * 5, i * 5 + 5) for i in range(5)]
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        vs._build_voice_info(segs, db)
        # Should call db.query exactly once (the .all() call)
        db.query.return_value.filter.return_value.all.assert_called_once()


# ---------------------------------------------------------------------------
# _build_tracks() — track building with cap
# ---------------------------------------------------------------------------

class TestBuildTracks:
    def test_basic_tracks(self):
        segs = [
            _make_segment("v1", 0, 5),
            _make_segment("v2", 5, 10),
        ]
        voice_info = {
            "v1": {"name": "小红", "color": "#FF0000"},
            "v2": {"name": "小明", "color": "#0000FF"},
        }
        tracks = vs._build_tracks(segs, voice_info)
        assert len(tracks) == 2
        assert tracks[0]["name"] == "小红"
        assert tracks[1]["name"] == "小明"

    def test_track_cap_at_15(self):
        """With 16+ voices, should cap at MAX_TRACKS (15) + '其他'."""
        voice_info = {
            f"v{i}": {"name": f"Voice {i}", "color": vs.VOICE_COLORS[i % len(vs.VOICE_COLORS)]}
            for i in range(20)
        }
        segs = [_make_segment(f"v{i}", i, i + 1) for i in range(20)]
        tracks = vs._build_tracks(segs, voice_info)
        assert len(tracks) == vs.MAX_TRACKS  # 14 individual + 1 其他
        assert tracks[-1]["name"] == "其他"
        assert tracks[-1]["color"] == vs.OTHER_COLOR
        # "其他" should contain segments from merged voices
        assert len(tracks[-1]["segments"]) > 0

    def test_exactly_15_no_merge(self):
        """Exactly MAX_TRACKS voices should not merge."""
        voice_info = {
            f"v{i}": {"name": f"V{i}", "color": vs.VOICE_COLORS[i % len(vs.VOICE_COLORS)]}
            for i in range(15)
        }
        segs = [_make_segment(f"v{i}", i, i + 1) for i in range(15)]
        tracks = vs._build_tracks(segs, voice_info)
        assert len(tracks) == 15
        assert all(t["name"] != "其他" for t in tracks)

    def test_harmony_track(self):
        segs = [_make_segment("v1", 0, 5)]
        segs[0].harmony_voices = ["h1"]
        voice_info = {"v1": {"name": "小红", "color": "#FF0000"}}
        tracks = vs._build_tracks(segs, voice_info)
        assert len(tracks) == 2
        assert tracks[-1]["id"] == "harmony"

    def test_no_harmony_when_none(self):
        segs = [_make_segment("v1", 0, 5)]
        voice_info = {"v1": {"name": "小红", "color": "#FF0000"}}
        tracks = vs._build_tracks(segs, voice_info)
        assert len(tracks) == 1

    def test_segments_without_voice_ignored(self):
        segs = [_make_segment(None, 0, 5)]
        tracks = vs._build_tracks(segs, {})
        assert len(tracks) == 0


# ---------------------------------------------------------------------------
# _gen_ass() — ASS subtitle generation
# ---------------------------------------------------------------------------

class TestGenAss:
    def test_ass_file_structure(self, tmp_path):
        with patch.object(vs, "OUTPUTS_DIR", tmp_path):
            segs = [_make_segment("v1", 1.0, 3.5, "测试歌词")]
            voice_info = {"v1": {"name": "小红", "color": "#FF0000"}}
            p = vs._gen_ass(segs, voice_info, "测试歌曲", "song1", 60.0)
            content = p.read_text(encoding="utf-8")
            assert "[Script Info]" in content
            assert "[V4+ Styles]" in content
            assert "[Events]" in content
            assert "测试歌词" in content
            assert "测试歌曲" in content
            p.unlink()

    def test_ass_timestamps(self, tmp_path):
        with patch.object(vs, "OUTPUTS_DIR", tmp_path):
            segs = [_make_segment("v1", 5.0, 10.0, "hello")]
            voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
            p = vs._gen_ass(segs, voice_info, "Title", "song1", 60.0)
            content = p.read_text(encoding="utf-8")
            assert "0:00:05.00" in content
            assert "0:00:10.00" in content
            p.unlink()

    def test_ass_escapes_special_chars(self, tmp_path):
        with patch.object(vs, "OUTPUTS_DIR", tmp_path):
            segs = [_make_segment("v1", 0, 5, "line with {brackets} and \\backslash")]
            voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
            p = vs._gen_ass(segs, voice_info, "Title", "song1", 60.0)
            content = p.read_text(encoding="utf-8")
            assert "\\{" in content
            assert "\\}" in content
            assert "\\\\" in content
            p.unlink()

    def test_ass_empty_segments_skip(self, tmp_path):
        with patch.object(vs, "OUTPUTS_DIR", tmp_path):
            segs = [_make_segment("v1", 0, 5, "")]
            voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
            p = vs._gen_ass(segs, voice_info, "Title", "song1", 60.0)
            content = p.read_text(encoding="utf-8")
            # Should not contain lyrics dialogue for empty text
            # But should still have title and progress bar
            lines = [l for l in content.split("\n") if l.startswith("Dialogue:")]
            # Title + progress bar entries only (no lyrics)
            assert len(lines) >= 20  # At least progress bar ticks
            p.unlink()

    def test_progress_bar_ticks(self, tmp_path):
        with patch.object(vs, "OUTPUTS_DIR", tmp_path):
            segs = []
            voice_info = {}
            p = vs._gen_ass(segs, voice_info, "Title", "song1", 120.0)
            content = p.read_text(encoding="utf-8")
            # Progress bar has 21 ticks (0% to 100% in 5% steps)
            progress_lines = [l for l in content.split("\n")
                              if l.startswith("Dialogue:") and "Dim" in l]
            assert len(progress_lines) == 21
            p.unlink()


# ---------------------------------------------------------------------------
# _audio_dur() — duration fallback
# ---------------------------------------------------------------------------

class TestAudioDuration:
    def test_fallback_on_error(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert vs._audio_dur("/nonexistent/file.wav") == 180.0

    def test_fallback_on_bad_output(self):
        mock = MagicMock()
        mock.stdout = "not_a_number\n"
        with patch("subprocess.run", return_value=mock):
            assert vs._audio_dur("/fake.wav") == 180.0
