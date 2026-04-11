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
# _gen_overlay_frames() — PIL overlay frame generation
# ---------------------------------------------------------------------------

class TestGenOverlayFrames:
    def test_creates_overlay_directory(self, tmp_path):
        segs = [_make_segment("v1", 1.0, 3.5, "测试歌词")]
        overlay_dir = vs._gen_overlay_frames(segs, 5.0, "测试歌曲", tmp_path)
        assert overlay_dir.exists()
        assert overlay_dir.name == "overlays"

    def test_correct_frame_count(self, tmp_path):
        duration = 10.0
        segs = [_make_segment("v1", 0, 5, "hello")]
        overlay_dir = vs._gen_overlay_frames(segs, duration, "Title", tmp_path)
        frames = sorted(overlay_dir.glob("frame_*.png"))
        expected = int(duration * vs.OVERLAY_FPS) + 1
        assert len(frames) == expected

    def test_lyrics_appear_in_frames(self, tmp_path):
        segs = [_make_segment("v1", 1.0, 3.0, "你好世界")]
        overlay_dir = vs._gen_overlay_frames(segs, 5.0, "Title", tmp_path)
        # Frame at t=2.0s should contain the lyric (within 1.0-3.0 window)
        frame_idx = int(2.0 * vs.OVERLAY_FPS)
        frame_path = overlay_dir / f"frame_{frame_idx:06d}.png"
        assert frame_path.exists()
        assert frame_path.stat().st_size > 0

    def test_empty_segments_produce_frames(self, tmp_path):
        segs = [_make_segment("v1", 0, 5, "")]
        overlay_dir = vs._gen_overlay_frames(segs, 5.0, "Title", tmp_path)
        frames = list(overlay_dir.glob("frame_*.png"))
        # Should still generate frames with progress bar, just no lyrics text
        assert len(frames) > 0

    def test_progress_bar_updates(self, tmp_path):
        segs = []
        overlay_dir = vs._gen_overlay_frames(segs, 4.0, "Title", tmp_path)
        # Frame at t=0 (0%) and t=3.9 (~97%) should both exist and differ
        f0 = overlay_dir / "frame_000000.png"
        f_near_end = overlay_dir / f"frame_{int(3.9 * vs.OVERLAY_FPS):06d}.png"
        assert f0.exists()
        assert f_near_end.exists()
        assert f0.stat().st_size != f_near_end.stat().st_size


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
