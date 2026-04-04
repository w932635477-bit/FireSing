"""Tests for pipeline router — process trigger and SSE progress."""

import json
import pytest

from backend.routers import pipeline as pipeline_router
from backend.schemas import PipelineProgress


class TestProcessEndpoint:
    def test_process_triggers_pipeline(self, client, db_session, sample_wav):
        """POST /process returns 200 and status=processing."""
        from backend.models import Song
        song = Song(
            id="test_song_1",
            title="Test",
            original_audio_path=str(sample_wav),
            status="uploaded",
        )
        db_session.add(song)
        db_session.commit()

        resp = client.post(
            f"/api/songs/{song.id}/process",
            json={"voice_pool": ["v1"], "strategy": "round-robin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"

    def test_concurrent_process_rejected(self, client, db_session, sample_wav):
        """Second process request while first is running returns 409."""
        from backend.models import Song
        song = Song(
            id="test_song_2",
            title="Test",
            original_audio_path=str(sample_wav),
            status="separating",
        )
        db_session.add(song)
        db_session.commit()

        resp = client.post(
            f"/api/songs/{song.id}/process",
            json={"voice_pool": ["v1"], "strategy": "round-robin"},
        )
        assert resp.status_code == 409
        assert "already being processed" in resp.json()["detail"]

    def test_process_nonexistent_song(self, client):
        """Process request for nonexistent song returns 404."""
        resp = client.post(
            "/api/songs/nonexistent/process",
            json={"voice_pool": ["v1"], "strategy": "round-robin"},
        )
        assert resp.status_code == 404


class TestProgressEndpoint:
    def test_progress_sse_no_active_pipeline(self, client, db_session, sample_wav):
        """SSE progress stream returns song status when no pipeline is running."""
        from backend.models import Song
        song = Song(
            id="test_song_5",
            title="Test",
            original_audio_path=str(sample_wav),
            status="uploaded",
        )
        db_session.add(song)
        db_session.commit()

        # Set done state so SSE stream closes immediately
        pipeline_router._pipeline_progress[song.id] = PipelineProgress(
            step="done", pct=0, message="Song status: uploaded"
        )

        resp = client.get(f"/api/songs/{song.id}/progress")
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")

        # Parse SSE data
        body = resp.text
        assert "data:" in body

        # Cleanup
        pipeline_router._pipeline_progress.pop(song.id, None)

    def test_progress_sse_with_active_pipeline(self, client, db_session, sample_wav):
        """SSE stream returns progress data for active pipeline."""
        from backend.models import Song
        song = Song(
            id="test_song_6",
            title="Test",
            original_audio_path=str(sample_wav),
            status="separating",
        )
        db_session.add(song)
        db_session.commit()

        # Set done state so stream closes immediately
        pipeline_router._pipeline_progress[song.id] = PipelineProgress(
            step="done", pct=50, message="Working..."
        )

        resp = client.get(f"/api/songs/{song.id}/progress")
        assert resp.status_code == 200

        body = resp.text
        # Parse the SSE data line
        for line in body.split("\n"):
            if line.startswith("data:"):
                data = json.loads(line[5:].strip())
                assert data["step"] == "done"
                assert data["pct"] == 50
                break

        # Cleanup
        pipeline_router._pipeline_progress.pop(song.id, None)

    def test_progress_nonexistent_song(self, client):
        """Progress for nonexistent song returns 404."""
        resp = client.get("/api/songs/nonexistent/progress")
        assert resp.status_code == 404
