"""Tests for monologue audio upload and segment timestamp update endpoints."""

import io
import pytest


def _upload_song(client, sample_wav):
    """Helper: upload a song and return its ID."""
    with open(sample_wav, "rb") as f:
        resp = client.post("/api/songs", files={"audio": ("test.wav", f, "audio/wav")})
    assert resp.status_code == 201
    return resp.json()["id"]


class TestMonologueAudioUpload:
    def test_upload_wav(self, client, sample_wav, db_session):
        """Upload a monologue WAV recording."""
        from backend.models import Song

        song_id = _upload_song(client, sample_wav)
        with open(sample_wav, "rb") as f:
            resp = client.put(
                f"/api/songs/{song_id}/monologue-audio",
                files={"audio": ("intro.wav", f, "audio/wav")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["song_id"] == song_id
        assert "monologue" in data["monologue_audio_path"]

        # Verify DB updated
        song = db_session.query(Song).filter(Song.id == song_id).first()
        assert song.monologue_audio_path is not None

    def test_upload_mp3(self, client, sample_wav):
        """Accept mp3 extension."""
        song_id = _upload_song(client, sample_wav)
        mp3_bytes = b"ID3\x03\x00\x00\x00" + b"\x00" * 100
        resp = client.put(
            f"/api/songs/{song_id}/monologue-audio",
            files={"audio": ("monologue.mp3", mp3_bytes, "audio/mp3")},
        )
        assert resp.status_code == 200

    def test_reject_bad_format(self, client, sample_wav):
        """Reject non-audio file."""
        song_id = _upload_song(client, sample_wav)
        resp = client.put(
            f"/api/songs/{song_id}/monologue-audio",
            files={"audio": ("file.pdf", b"fake", "application/pdf")},
        )
        assert resp.status_code == 400
        assert "mp3" in resp.json()["detail"].lower()

    def test_song_not_found(self, client):
        """404 for nonexistent song."""
        resp = client.put(
            "/api/songs/nonexistent/monologue-audio",
            files={"audio": ("test.wav", b"fake", "audio/wav")},
        )
        assert resp.status_code == 404

    def test_reject_too_large(self, client, sample_wav):
        """Reject files over 10MB (tested via Content-Length header)."""
        song_id = _upload_song(client, sample_wav)
        large_content = b"\x00" * (10 * 1024 * 1024 + 1)
        resp = client.put(
            f"/api/songs/{song_id}/monologue-audio",
            files={"audio": ("big.wav", large_content, "audio/wav")},
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"].lower()


class TestSegmentTimestampUpdate:
    def _setup_segments(self, client, db_session):
        """Create a song with segments and return (song_id, segment_ids)."""
        from backend.models import Segment

        song_id = _upload_song(client, None if False else __import__("pathlib").Path(__import__("tempfile").mkdtemp())  # skip

        # Directly insert segments via DB
        seg1 = Segment(id="seg-1", song_id=song_id, line_number=1,
                        text="第一句", start_time=1.0, end_time=3.0)
        seg2 = Segment(id="seg-2", song_id=song_id, line_number=2,
                        text="第二句", start_time=4.0, end_time=6.5)
        db_session.add_all([seg1, seg2])
        db_session.commit()
        return song_id, ["seg-1", "seg-2"]

    def test_update_start_time(self, client, db_session):
        """Update only start_time."""
        from backend.models import Segment

        song_id = _upload_song(client, __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
        seg = Segment(id="seg-a", song_id=song_id, line_number=1,
                       text="测试", start_time=1.0, end_time=5.0)
        db_session.add(seg)
        db_session.commit()

        resp = client.patch(
            f"/api/songs/{song_id}/segments/seg-a",
            json={"start_time": 2.5},
        )
        assert resp.status_code == 200
        assert resp.json()["start_time"] == 2.5
        assert resp.json()["end_time"] == 5.0  # unchanged

    def test_update_both(self, client, db_session):
        """Update both start and end."""
        from backend.models import Segment

        song_id = _upload_song(client, __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
        seg = Segment(id="seg-b", song_id=song_id, line_number=1,
                       text="测试", start_time=1.0, end_time=5.0)
        db_session.add(seg)
        db_session.commit()

        resp = client.patch(
            f"/api/songs/{song_id}/segments/seg-b",
            json={"start_time": 2.0, "end_time": 7.5},
        )
        assert resp.status_code == 200
        assert resp.json()["start_time"] == 2.0
        assert resp.json()["end_time"] == 7.5

    def test_reject_negative(self, client, db_session):
        """Reject negative timestamps."""
        from backend.models import Segment

        song_id = _upload_song(client, __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
        seg = Segment(id="seg-c", song_id=song_id, line_number=1,
                       text="测试", start_time=1.0, end_time=5.0)
        db_session.add(seg)
        db_session.commit()

        resp = client.patch(
            f"/api/songs/{song_id}/segments/seg-c",
            json={"start_time": -1.0},
        )
        assert resp.status_code == 400

    def test_reject_start_ge_end(self, client, db_session):
        """Reject start_time >= end_time."""
        from backend.models import Segment

        song_id = _upload_song(client, __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
        seg = Segment(id="seg-d", song_id=song_id, line_number=1,
                       text="测试", start_time=1.0, end_time=5.0)
        db_session.add(seg)
        db_session.commit()

        resp = client.patch(
            f"/api/songs/{song_id}/segments/seg-d",
            json={"start_time": 6.0},
        )
        assert resp.status_code == 400

    def test_segment_not_found(self, client, db_session):
        """404 for nonexistent segment."""
        song_id = _upload_song(client, __import__("pathlib").Path(__import__("tempfile").mkdtemp()))
        resp = client.patch(
            f"/api/songs/{song_id}/segments/nonexistent",
            json={"start_time": 1.0},
        )
        assert resp.status_code == 404
