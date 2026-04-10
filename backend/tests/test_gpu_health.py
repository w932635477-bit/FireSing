"""Tests for GPU server connectivity handling."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


def _mock_async_client(response=None, side_effect=None):
    """Create a mock httpx.AsyncClient that works as a context manager."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    if side_effect:
        mock_client.get = AsyncMock(side_effect=side_effect)
    elif response:
        mock_client.get = AsyncMock(return_value=response)

    # Support async context manager protocol
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    return mock_client


class TestGpuHealthEndpoint:
    """Test /api/health/gpu endpoint."""

    def test_gpu_healthy(self, client):
        """GPU server responds normally."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "gpu": "NVIDIA RTX 4090D",
            "vram_total_gb": 24.0,
            "vram_used_gb": 2.1,
        }

        with patch("httpx.AsyncClient", return_value=_mock_async_client(response=mock_resp)):
            resp = client.get("/api/health/gpu")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["gpu"] == "NVIDIA RTX 4090D"

    def test_gpu_offline(self, client):
        """GPU server is unreachable."""
        with patch("httpx.AsyncClient", return_value=_mock_async_client(side_effect=httpx.ConnectError("Connection refused"))):
            resp = client.get("/api/health/gpu")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "offline"
        assert "not reachable" in data["detail"]

    def test_gpu_timeout(self, client):
        """GPU server times out."""
        with patch("httpx.AsyncClient", return_value=_mock_async_client(side_effect=httpx.TimeoutException("timed out"))):
            resp = client.get("/api/health/gpu")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "timeout"

    def test_gpu_returns_error(self, client):
        """GPU server responds but with error status."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("httpx.AsyncClient", return_value=_mock_async_client(response=mock_resp)):
            resp = client.get("/api/health/gpu")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "500" in data["detail"]


class TestPipelinePreflight:
    """Test pipeline pre-flight GPU check."""

    def test_pipeline_fails_gracefully_when_gpu_offline(self, client, db_session):
        """Pipeline sets error status when GPU server is unreachable."""
        from backend.models import Song
        import time

        # Create a song in the test DB
        song = Song(
            id="test-gpu-offline",
            title="Test Song",
            original_audio_path="/tmp/nonexistent.wav",
            status="uploaded",
        )
        db_session.add(song)
        db_session.commit()

        # Patch AsyncClient to simulate GPU offline
        # Also patch SessionLocal so the background task uses the same DB
        with (
            patch("httpx.AsyncClient", return_value=_mock_async_client(side_effect=httpx.ConnectError("Connection refused"))),
            patch("backend.database.SessionLocal", return_value=db_session),
        ):
            resp = client.post(
                f"/api/songs/{song.id}/process",
                json={"voice_pool": [], "output_format": "audio"},
            )

        assert resp.status_code == 200

        # Wait for background task to complete
        time.sleep(2)

        # Refresh from DB - use a fresh query to avoid detached instance issues
        db_session.rollback()
        db_session.expire_all()
        updated = db_session.query(Song).filter(Song.id == "test-gpu-offline").first()
        assert updated is not None
        assert updated.status == "error", f"Expected 'error', got '{updated.status}'"
        assert "GPU" in (updated.error_message or ""), f"Error message: {updated.error_message}"
