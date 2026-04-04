"""Tests for song CRUD operations."""

import io
import pytest
from pathlib import Path


class TestUploadSong:
    def test_upload_mp3(self, client, sample_wav):
        """Upload a song with audio only."""
        with open(sample_wav, "rb") as f:
            resp = client.post(
                "/api/songs",
                files={"audio": ("test.wav", f, "audio/wav")},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "uploaded"
        assert data["title"] == "test"
        assert data["id"]

    def test_upload_with_lrc(self, client, sample_wav, sample_lrc):
        """Upload a song with audio + LRC."""
        with open(sample_wav, "rb") as audio_f, open(sample_lrc, "rb") as lrc_f:
            resp = client.post(
                "/api/songs",
                files={
                    "audio": ("song.wav", audio_f, "audio/wav"),
                    "lrc": ("song.lrc", lrc_f, "text/plain"),
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["lrc_path"] is not None

    def test_upload_rejects_bad_format(self, client):
        """Reject non-audio file formats."""
        resp = client.post(
            "/api/songs",
            files={"audio": ("test.pdf", b"fake content", "application/pdf")},
        )
        assert resp.status_code == 400


class TestListSongs:
    def test_list_empty(self, client):
        """List returns empty when no songs."""
        resp = client.get("/api/songs")
        assert resp.status_code == 200
        assert resp.json()["songs"] == []

    def test_list_after_upload(self, client, sample_wav):
        """List shows uploaded song."""
        with open(sample_wav, "rb") as f:
            client.post("/api/songs", files={"audio": ("test.wav", f, "audio/wav")})

        resp = client.get("/api/songs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["songs"]) == 1
        assert data["songs"][0]["title"] == "test"


class TestGetSong:
    def test_get_existing(self, client, sample_wav):
        """Get an existing song."""
        with open(sample_wav, "rb") as f:
            upload_resp = client.post(
                "/api/songs", files={"audio": ("test.wav", f, "audio/wav")}
            )
        song_id = upload_resp.json()["id"]

        resp = client.get(f"/api/songs/{song_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == song_id

    def test_get_nonexistent(self, client):
        """404 for non-existent song."""
        resp = client.get("/api/songs/nonexistent123")
        assert resp.status_code == 404


class TestDeleteSong:
    def test_delete_existing(self, client, sample_wav):
        """Delete an existing song."""
        with open(sample_wav, "rb") as f:
            upload_resp = client.post(
                "/api/songs", files={"audio": ("test.wav", f, "audio/wav")}
            )
        song_id = upload_resp.json()["id"]

        resp = client.delete(f"/api/songs/{song_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify it's gone
        resp = client.get(f"/api/songs/{song_id}")
        assert resp.status_code == 404

    def test_delete_nonexistent(self, client):
        """404 for deleting non-existent song."""
        resp = client.delete("/api/songs/nonexistent123")
        assert resp.status_code == 404
