"""Tests for outputs router — list and download."""

import pytest
from pathlib import Path

from backend.models import Song, Output


class TestListOutputs:
    def test_list_outputs_empty(self, client, db_session, sample_wav):
        """Song with no outputs returns empty list."""
        song = Song(
            id="output_song_1",
            title="Test",
            original_audio_path=str(sample_wav),
            status="done",
        )
        db_session.add(song)
        db_session.commit()

        resp = client.get(f"/api/songs/{song.id}/outputs")
        assert resp.status_code == 200
        assert resp.json()["outputs"] == []

    def test_list_outputs_with_records(self, client, db_session, sample_wav):
        """Song with outputs returns correct list."""
        song = Song(
            id="output_song_2",
            title="Test",
            original_audio_path=str(sample_wav),
            status="done",
        )
        db_session.add(song)

        output = Output(
            id="out_1",
            song_id="output_song_2",
            format="audio",
            file_path=str(sample_wav),
            file_size=1000,
            duration=1.0,
        )
        db_session.add(output)
        db_session.commit()

        resp = client.get(f"/api/songs/{song.id}/outputs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["outputs"]) == 1
        assert data["outputs"][0]["format"] == "audio"
        assert "download" in data["outputs"][0]["file_url"]

    def test_list_outputs_nonexistent_song(self, client):
        """Nonexistent song returns 404."""
        resp = client.get("/api/songs/nonexistent/outputs")
        assert resp.status_code == 404


class TestDownloadOutput:
    def test_download_existing(self, client, db_session, sample_wav):
        """Download returns the file."""
        song = Song(
            id="dl_song",
            title="Test",
            original_audio_path=str(sample_wav),
            status="done",
        )
        db_session.add(song)

        output = Output(
            id="dl_out",
            song_id="dl_song",
            format="audio",
            file_path=str(sample_wav),
            file_size=1000,
        )
        db_session.add(output)
        db_session.commit()

        resp = client.get(f"/api/songs/{song.id}/outputs/{output.id}/download")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/wav"

    def test_download_nonexistent_output(self, client, db_session, sample_wav):
        """Nonexistent output returns 404."""
        song = Song(
            id="dl_song_2",
            title="Test",
            original_audio_path=str(sample_wav),
            status="done",
        )
        db_session.add(song)
        db_session.commit()

        resp = client.get(f"/api/songs/{song.id}/outputs/nonexistent/download")
        assert resp.status_code == 404
