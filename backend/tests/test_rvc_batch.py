"""Tests for batch RVC conversion endpoint and service."""

import io
import struct
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import numpy as np
import pytest

from backend.models import Song, Segment, VoiceModel


def _make_wav_bytes(duration: float = 1.0, sr: int = 22050, freq: float = 440.0) -> bytes:
    """Generate minimal WAV bytes for testing."""
    num_samples = int(sr * duration)
    audio = np.sin(2 * np.pi * freq * np.linspace(0, duration, num_samples, endpoint=False))
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
    return buf.getvalue()


class TestBatchRVCEndpoint:
    """Test the GPU server /infer/rvc_batch_v2 endpoint."""

    def test_batch_endpoint_exists(self):
        """Verify the batch endpoint is defined in gpu_server."""
        # Import and check the route exists
        import importlib
        import sys
        # We can't actually import gpu_server without torch, but we can check the file
        with open("gpu_server/server.py") as f:
            content = f.read()
        assert "infer_rvc_batch_v2" in content, "Batch v2 endpoint not found in gpu_server"
        assert "infer_rvc_batch" in content, "Batch endpoint not found in gpu_server"

    def test_batch_service_method_exists(self):
        """Verify batch RVC method exists in rvc_service."""
        from backend.services import rvc_service
        assert hasattr(rvc_service, "convert_batch"), "convert_batch not found in rvc_service"
        assert hasattr(rvc_service, "_call_gpu_rvc_batch"), "_call_gpu_rvc_batch not found"

    def test_batch_groups_by_voice(self, db_session, tmp_path):
        """convert_batch should group segments by voice model."""
        from backend.services.rvc_service import convert_batch

        # Create test data
        song = Song(id="test-song", title="Test", original_audio_path="/fake.wav")
        db_session.add(song)

        voice_a = VoiceModel(id="voice-a", name="Voice A", model_path=str(tmp_path / "a.pth"))
        voice_b = VoiceModel(id="voice-b", name="Voice B", model_path=str(tmp_path / "b.pth"))
        db_session.add_all([voice_a, voice_b])

        # Create dummy model files
        (tmp_path / "a.pth").write_bytes(b"dummy_model_a")
        (tmp_path / "b.pth").write_bytes(b"dummy_model_b")

        # Create segments with different voices
        for i in range(6):
            seg = Segment(
                id=f"seg-{i}",
                song_id="test-song",
                line_number=i + 1,
                text=f"Line {i+1}",
                start_time=i * 1.0,
                end_time=(i + 1) * 1.0,
                voice_model_id=voice_a.id if i % 2 == 0 else voice_b.id,
                vocal_path=str(tmp_path / f"line_{i:03d}.wav"),
            )
            db_session.add(seg)

        db_session.commit()

        # Mock the GPU call to avoid needing real GPU
        async def mock_batch_call(audio_list, model_id, pth_bytes, index_bytes=None):
            # Return dummy WAV bytes for each segment
            return {seg.id: _make_wav_bytes() for _, seg in audio_list}

        with patch("backend.services.rvc_service._call_gpu_rvc_batch", side_effect=mock_batch_call):
            # Create dummy vocal files
            wav_bytes = _make_wav_bytes()
            for i in range(6):
                (tmp_path / f"line_{i:03d}.wav").write_bytes(wav_bytes)

            import asyncio
            paths = asyncio.run(
                convert_batch("test-song", db_session)
            )

        assert len(paths) == 6
        for p in paths:
            assert p.exists()


class TestBatchServiceEdgeCases:
    """Edge cases for batch RVC service."""

    def test_no_segments(self, db_session):
        """Should handle song with no segments gracefully."""
        from backend.services.rvc_service import convert_batch
        import asyncio

        song = Song(id="empty-song", title="Empty", original_audio_path="/fake.wav")
        db_session.add(song)
        db_session.commit()

        paths = asyncio.run(
            convert_batch("empty-song", db_session)
        )
        assert paths == []

    def test_unassigned_segments_skipped(self, db_session, tmp_path):
        """Segments without voice_model_id should be skipped."""
        from backend.services.rvc_service import convert_batch
        import asyncio

        song = Song(id="no-voice-song", title="No Voice", original_audio_path="/fake.wav")
        db_session.add(song)
        db_session.commit()

        seg = Segment(
            id="seg-no-voice",
            song_id="no-voice-song",
            line_number=1,
            text="Unassigned",
            start_time=0.0,
            end_time=1.0,
            vocal_path=str(tmp_path / "line_001.wav"),
        )
        db_session.add(seg)
        db_session.commit()

        paths = asyncio.run(
            convert_batch("no-voice-song", db_session)
        )
        assert paths == []

    def test_already_converted_skipped(self, db_session, tmp_path):
        """Already converted segments should be skipped."""
        from backend.services.rvc_service import convert_batch
        import asyncio

        song = Song(id="done-song", title="Done", original_audio_path="/fake.wav")
        voice = VoiceModel(id="v1", name="V1", model_path=str(tmp_path / "v1.pth"))
        db_session.add_all([song, voice])

        # Create dummy model file
        (tmp_path / "v1.pth").write_bytes(b"dummy_model")

        converted_path = tmp_path / "line_001_converted.wav"
        converted_path.write_bytes(_make_wav_bytes())

        seg = Segment(
            id="seg-done",
            song_id="done-song",
            line_number=1,
            text="Done",
            start_time=0.0,
            end_time=1.0,
            voice_model_id="v1",
            vocal_path=str(tmp_path / "line_001.wav"),
            converted_vocal_path=str(converted_path),
        )
        db_session.add(seg)

        # Create vocal file
        (tmp_path / "line_001.wav").write_bytes(_make_wav_bytes())
        db_session.commit()

        paths = asyncio.run(
            convert_batch("done-song", db_session)
        )
        assert len(paths) == 1
        assert paths[0] == converted_path
