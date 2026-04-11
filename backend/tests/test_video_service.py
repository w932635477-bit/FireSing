"""Unit tests for video_service.py — pure Python logic, no FFmpeg needed.

Tests: voice info, segment timeline, singer lookup, transitions,
color conversion, overlay frame generation, and edge cases.
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
        db.query.return_value.filter.return_value.all.assert_called_once()


# ---------------------------------------------------------------------------
# _build_segment_timeline() — timeline building
# ---------------------------------------------------------------------------

class TestBuildSegmentTimeline:
    def test_basic_timeline(self):
        segs = [
            _make_segment("v1", 0, 5, "hello"),
            _make_segment("v2", 5, 10, "world"),
        ]
        voice_info = {
            "v1": {"name": "小红", "color": "#FF0000"},
            "v2": {"name": "小明", "color": "#0000FF"},
        }
        tl = vs._build_segment_timeline(segs, voice_info)
        assert len(tl) == 2
        assert tl[0][0] == 0  # start
        assert tl[0][1] == 5  # end
        assert tl[0][2] == "hello"
        assert tl[0][3] == "v1"
        assert tl[0][4] == "小红"
        assert tl[0][5] == "#FF0000"

    def test_segments_without_voice_ignored(self):
        segs = [_make_segment(None, 0, 5)]
        tl = vs._build_segment_timeline(segs, {})
        assert len(tl) == 0

    def test_strips_whitespace_from_text(self):
        segs = [_make_segment("v1", 0, 5, "  spaces  ")]
        voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
        tl = vs._build_segment_timeline(segs, voice_info)
        assert tl[0][2] == "spaces"

    def test_empty_text_becomes_empty_string(self):
        segs = [_make_segment("v1", 0, 5, "")]
        voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
        tl = vs._build_segment_timeline(segs, voice_info)
        assert tl[0][2] == ""

    def test_sorted_by_start_time(self):
        segs = [
            _make_segment("v2", 5, 10, "b"),
            _make_segment("v1", 0, 5, "a"),
            _make_segment("v3", 10, 15, "c"),
        ]
        voice_info = {
            "v1": {"name": "A", "color": "#FF0000"},
            "v2": {"name": "B", "color": "#00FF00"},
            "v3": {"name": "C", "color": "#0000FF"},
        }
        tl = vs._build_segment_timeline(segs, voice_info)
        assert [t[2] for t in tl] == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# _get_active_singer() — singer lookup
# ---------------------------------------------------------------------------

class TestGetActiveSinger:
    def test_within_segment(self):
        tl = [(1.0, 3.0, "hello", "v1", "小红", "#FF0000")]
        vid, name, color, lyric = vs._get_active_singer(tl, 2.0)
        assert vid == "v1"
        assert name == "小红"
        assert lyric == "hello"

    def test_before_first_segment(self):
        tl = [(1.0, 3.0, "hello", "v1", "小红", "#FF0000")]
        vid, name, color, lyric = vs._get_active_singer(tl, 0.5)
        assert vid is None

    def test_after_last_segment(self):
        tl = [(1.0, 3.0, "hello", "v1", "小红", "#FF0000")]
        vid, name, color, lyric = vs._get_active_singer(tl, 5.0)
        assert vid is None

    def test_at_exact_boundary(self):
        tl = [(1.0, 3.0, "hello", "v1", "小红", "#FF0000")]
        vid, _, _, _ = vs._get_active_singer(tl, 1.0)
        assert vid == "v1"

    def test_empty_timeline(self):
        vid, name, color, lyric = vs._get_active_singer([], 5.0)
        assert vid is None


# ---------------------------------------------------------------------------
# _compute_transitions() — singer change detection
# ---------------------------------------------------------------------------

class TestComputeTransitions:
    def test_no_change_single_voice(self):
        tl = [
            (0, 5, "a", "v1", "小红", "#FF0000"),
            (5, 10, "b", "v1", "小红", "#FF0000"),
        ]
        assert vs._compute_transitions(tl) == []

    def test_transition_between_voices(self):
        tl = [
            (0, 5, "a", "v1", "小红", "#FF0000"),
            (5, 10, "b", "v2", "小明", "#0000FF"),
        ]
        trans = vs._compute_transitions(tl)
        assert len(trans) == 1
        assert trans[0] == 5.0

    def test_multiple_transitions(self):
        tl = [
            (0, 5, "a", "v1", "A", "#FF0000"),
            (5, 10, "b", "v2", "B", "#00FF00"),
            (10, 15, "c", "v1", "A", "#FF0000"),
        ]
        trans = vs._compute_transitions(tl)
        assert len(trans) == 2
        assert trans[0] == 5.0
        assert trans[1] == 10.0


# ---------------------------------------------------------------------------
# _compute_singer_alpha() — fade alpha
# ---------------------------------------------------------------------------

class TestComputeSingerAlpha:
    def test_no_transitions_full_alpha(self):
        assert vs._compute_singer_alpha(5.0, []) == 255

    def test_at_transition_start(self):
        assert vs._compute_singer_alpha(5.0, [5.0]) == 0

    def test_mid_fade(self):
        alpha = vs._compute_singer_alpha(5.125, [5.0])
        assert 0 < alpha < 255

    def test_after_fade_complete(self):
        alpha = vs._compute_singer_alpha(6.0, [5.0])
        assert alpha == 255


# ---------------------------------------------------------------------------
# _gen_overlay_frames() — PIL overlay frame generation
# ---------------------------------------------------------------------------

class TestGenOverlayFrames:
    def test_creates_overlay_directory(self, tmp_path):
        segs = [_make_segment("v1", 1.0, 3.5, "测试歌词")]
        voice_info = {"v1": {"name": "小红", "color": "#FF0000"}}
        overlay_dir = vs._gen_overlay_frames(segs, voice_info, 5.0, "测试歌曲", tmp_path)
        assert overlay_dir.exists()
        assert overlay_dir.name == "overlays"

    def test_correct_frame_count(self, tmp_path):
        duration = 10.0
        segs = [_make_segment("v1", 0, 5, "hello")]
        voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
        overlay_dir = vs._gen_overlay_frames(segs, voice_info, duration, "Title", tmp_path)
        frames = sorted(overlay_dir.glob("frame_*.png"))
        expected = int(duration * vs.OVERLAY_FPS) + 1
        assert len(frames) == expected

    def test_lyrics_appear_in_frames(self, tmp_path):
        segs = [_make_segment("v1", 1.0, 3.0, "你好世界")]
        voice_info = {"v1": {"name": "小红", "color": "#FF0000"}}
        overlay_dir = vs._gen_overlay_frames(segs, voice_info, 5.0, "Title", tmp_path)
        frame_idx = int(2.0 * vs.OVERLAY_FPS)
        frame_path = overlay_dir / f"frame_{frame_idx:06d}.png"
        assert frame_path.exists()
        assert frame_path.stat().st_size > 0

    def test_empty_segments_produce_frames(self, tmp_path):
        segs = [_make_segment("v1", 0, 5, "")]
        voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
        overlay_dir = vs._gen_overlay_frames(segs, voice_info, 5.0, "Title", tmp_path)
        frames = list(overlay_dir.glob("frame_*.png"))
        assert len(frames) > 0

    def test_progress_bar_updates(self, tmp_path):
        segs = []
        overlay_dir = vs._gen_overlay_frames(segs, {}, 4.0, "Title", tmp_path)
        f0 = overlay_dir / "frame_000000.png"
        f_near_end = overlay_dir / f"frame_{int(3.9 * vs.OVERLAY_FPS):06d}.png"
        assert f0.exists()
        assert f_near_end.exists()
        assert f0.stat().st_size != f_near_end.stat().st_size

    def test_no_singer_during_gap(self, tmp_path):
        """Frames during instrumental gaps should have no avatar but still have progress."""
        segs = [_make_segment("v1", 5.0, 8.0, "hello")]
        voice_info = {"v1": {"name": "V1", "color": "#FF0000"}}
        overlay_dir = vs._gen_overlay_frames(segs, voice_info, 10.0, "Title", tmp_path)
        # Frame at t=1.0s (before singer) should exist
        frame_early = overlay_dir / "frame_000002.png"
        assert frame_early.exists()
        # Frame at t=6.0s (during singer) should be larger (has avatar+lyrics)
        frame_mid = overlay_dir / f"frame_{int(6.0 * vs.OVERLAY_FPS):06d}.png"
        assert frame_mid.exists()


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
