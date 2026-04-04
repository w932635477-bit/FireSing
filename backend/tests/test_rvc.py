"""Tests for RVC voice conversion — upload, assignment, conversion."""

import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from io import BytesIO

from backend.models import Song, Segment, VoiceModel


class TestUploadVoice:
    def test_upload_voice_model(self, client, db_session):
        """Upload a .pth file and verify it's registered."""
        pth_content = b"fake pth model data"
        resp = client.post(
            "/api/voices",
            files={"pth_file": ("test_voice.pth", BytesIO(pth_content), "application/octet-stream")},
            data={"name": "Test Voice"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Voice"
        assert data["is_preset"] is False
        assert "id" in data

    def test_upload_rejects_non_pth(self, client):
        """Reject non-.pth model files."""
        resp = client.post(
            "/api/voices",
            files={"pth_file": ("model.bin", BytesIO(b"data"), "application/octet-stream")},
            data={"name": "Bad"},
        )
        assert resp.status_code == 400

    def test_upload_with_index(self, client, db_session):
        """Upload .pth + optional .index together."""
        resp = client.post(
            "/api/voices",
            files={
                "pth_file": ("voice.pth", BytesIO(b"pth data"), "application/octet-stream"),
                "index_file": ("voice.index", BytesIO(b"index data"), "application/octet-stream"),
            },
            data={"name": "With Index"},
        )
        assert resp.status_code == 201
        data = resp.json()
        # Verify DB record has index_path
        voice = db_session.query(VoiceModel).filter(VoiceModel.id == data["id"]).first()
        assert voice.index_path is not None


class TestListVoices:
    def test_list_voices_empty(self, client):
        """Empty list when no voices uploaded."""
        resp = client.get("/api/voices")
        assert resp.status_code == 200
        assert resp.json()["voices"] == []

    def test_list_after_upload(self, client, db_session):
        """List returns uploaded voice models."""
        for i in range(3):
            client.post(
                "/api/voices",
                files={"pth_file": (f"v{i}.pth", BytesIO(f"data{i}".encode()), "application/octet-stream")},
                data={"name": f"Voice {i}"},
            )
        resp = client.get("/api/voices")
        assert resp.status_code == 200
        assert len(resp.json()["voices"]) == 3


class TestAssignVoices:
    def _setup_song_with_segments(self, db_session):
        """Create a song with 5 segments for testing."""
        song = Song(
            id="test_assign_song",
            title="Test",
            original_audio_path="/tmp/test.wav",
            status="segmented",
        )
        db_session.add(song)

        # Create 3 voice models
        for i in range(3):
            vm = VoiceModel(
                id=f"voice_{i}",
                name=f"Voice {i}",
                model_path=f"/tmp/voice_{i}.pth",
                is_preset=False,
            )
            db_session.add(vm)

        # Create 5 segments
        for i in range(5):
            seg = Segment(
                id=f"seg_{i}",
                song_id="test_assign_song",
                line_number=i + 1,
                text=f"Line {i+1}",
                start_time=float(i * 5),
                end_time=float((i + 1) * 5),
                vocal_path=f"/tmp/seg_{i}.wav",
            )
            db_session.add(seg)
        db_session.commit()

    def test_assign_round_robin(self, client, db_session):
        """Round-robin: 3 voices × 5 segments = pattern [0,1,2,0,1]."""
        self._setup_song_with_segments(db_session)

        resp = client.put(
            "/api/songs/test_assign_song/voices",
            json={
                "strategy": "round-robin",
                "assignments": [],
                "voice_pool": ["voice_0", "voice_1", "voice_2"],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_count"] == 5

        # Verify assignment pattern
        segments = db_session.query(Segment).filter(
            Segment.song_id == "test_assign_song"
        ).order_by(Segment.line_number).all()

        assert segments[0].voice_model_id == "voice_0"
        assert segments[1].voice_model_id == "voice_1"
        assert segments[2].voice_model_id == "voice_2"
        assert segments[3].voice_model_id == "voice_0"
        assert segments[4].voice_model_id == "voice_1"

    def test_assign_manual(self, client, db_session):
        """Manual assignment with explicit line_number -> voice mapping."""
        self._setup_song_with_segments(db_session)

        resp = client.put(
            "/api/songs/test_assign_song/voices",
            json={
                "strategy": "manual",
                "assignments": [
                    {"line_number": 1, "voice_model_id": "voice_2"},
                    {"line_number": 3, "voice_model_id": "voice_0"},
                ],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_count"] == 2

        segments = db_session.query(Segment).filter(
            Segment.song_id == "test_assign_song"
        ).order_by(Segment.line_number).all()

        assert segments[0].voice_model_id == "voice_2"  # line 1
        assert segments[1].voice_model_id is None        # line 2, not assigned
        assert segments[2].voice_model_id == "voice_0"  # line 3

    def test_assign_nonexistent_voice(self, client, db_session):
        """Assignment with invalid voice ID returns 400."""
        self._setup_song_with_segments(db_session)

        resp = client.put(
            "/api/songs/test_assign_song/voices",
            json={
                "strategy": "round-robin",
                "assignments": [],
                "voice_pool": ["nonexistent"],
            },
        )
        assert resp.status_code == 400


class TestRvcConversion:
    @pytest.mark.asyncio
    async def test_convert_segment_mock_gpu(self, db_session, sample_wav):
        """Mock GPU call, verify converted file saved and DB updated."""
        from backend.services import rvc_service

        # Setup
        song = Song(
            id="convert_song",
            title="Test",
            original_audio_path=str(sample_wav),
            status="segmented",
        )
        db_session.add(song)

        voice = VoiceModel(
            id="convert_voice",
            name="Test",
            model_path=str(sample_wav),  # reuse sample wav as fake pth
            is_preset=False,
        )
        db_session.add(voice)

        segment = Segment(
            id="convert_seg",
            song_id="convert_song",
            line_number=1,
            text="Test line",
            start_time=0.0,
            end_time=1.0,
            vocal_path=str(sample_wav),
            voice_model_id="convert_voice",
        )
        db_session.add(segment)
        db_session.commit()

        # Mock GPU call
        fake_wav = sample_wav.read_bytes()
        with patch("backend.services.rvc_service._call_gpu_rvc", new_callable=AsyncMock) as mock_gpu:
            mock_gpu.return_value = fake_wav
            result = await rvc_service.convert("convert_seg", db_session)

        assert result.exists()
        assert "converted" in str(result)
        assert segment.converted_vocal_path == str(result)

    @pytest.mark.asyncio
    async def test_convert_skips_already_done(self, db_session, sample_wav, tmp_path):
        """Skip conversion if converted file already exists."""
        from backend.services import rvc_service

        existing_path = tmp_path / "line_001_converted.wav"
        existing_path.write_bytes(b"already converted")

        song = Song(
            id="skip_song",
            title="Test",
            original_audio_path=str(sample_wav),
            status="segmented",
        )
        db_session.add(song)

        voice = VoiceModel(
            id="skip_voice",
            name="Test",
            model_path=str(sample_wav),
            is_preset=False,
        )
        db_session.add(voice)

        segment = Segment(
            id="skip_seg",
            song_id="skip_song",
            line_number=1,
            text="Skip",
            start_time=0.0,
            end_time=1.0,
            vocal_path=str(sample_wav),
            voice_model_id="skip_voice",
            converted_vocal_path=str(existing_path),
        )
        db_session.add(segment)
        db_session.commit()

        with patch("backend.services.rvc_service._call_gpu_rvc", new_callable=AsyncMock) as mock_gpu:
            result = await rvc_service.convert("skip_seg", db_session)
            mock_gpu.assert_not_called()

        assert str(result) == str(existing_path)
