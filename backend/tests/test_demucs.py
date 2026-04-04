"""Tests for Demucs vocal separation service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from backend.services.demucs_service import separate


class TestDemucsService:
    @pytest.mark.asyncio
    async def test_separate_success(self, db_session, sample_wav):
        """Test successful vocal separation."""
        from backend.models import Song

        song = Song(
            id="test123",
            title="test song",
            original_audio_path=str(sample_wav),
            status="uploaded",
        )
        db_session.add(song)
        db_session.commit()

        # Mock GPU server response
        mock_vocals = b"MOCK_VOCALS_WAV_DATA"
        mock_instrumental = b"MOCK_INSTRUMENTAL_WAV_DATA"

        with patch("backend.services.demucs_service._call_gpu_demucs") as mock_gpu:
            mock_gpu.return_value = (
                Path("/tmp/test/vocals.wav"),
                Path("/tmp/test/instrumental.wav"),
            )

            result = await separate("test123", db_session)
            assert result is not None

            # Verify status updated
            db_session.refresh(song)
            assert song.status == "separated"

    @pytest.mark.asyncio
    async def test_separate_already_done(self, db_session, sample_wav, tmp_path):
        """Skip separation if vocals already exist."""
        from backend.models import Song

        vocals = tmp_path / "vocals.wav"
        vocals.write_bytes(b"fake")
        instrumental = tmp_path / "instrumental.wav"
        instrumental.write_bytes(b"fake")

        song = Song(
            id="test456",
            title="test song",
            original_audio_path=str(sample_wav),
            vocals_path=str(vocals),
            instrumental_path=str(instrumental),
            status="separated",
        )
        db_session.add(song)
        db_session.commit()

        result = await separate("test456", db_session)
        assert result == (vocals, instrumental)
