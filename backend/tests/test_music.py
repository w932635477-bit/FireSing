"""Tests for music search and import router."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend.models import Song


@pytest.fixture
def client(db_session):
    """FastAPI test client with test database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- _merge_results tests ---

def test_merge_results_empty():
    from backend.routers.music import _merge_results
    assert _merge_results([]) == []


def test_merge_results_single():
    from backend.routers.music import _merge_results
    songs = [{"name": "稻香", "artist": "周杰伦", "source": "netease", "id": "1", "duration": 240}]
    results = _merge_results(songs)
    assert len(results) == 1
    assert results[0]["name"] == "稻香"
    assert results[0]["platform_count"] == 1


def test_merge_results_same_song_different_platforms():
    from backend.routers.music import _merge_results
    songs = [
        {"name": "稻香", "artist": "周杰伦", "source": "netease", "id": "1", "duration": 240},
        {"name": "稻香", "artist": "周杰伦", "source": "qq", "id": "2", "duration": 245},
        {"name": "稻香", "artist": "周杰伦", "source": "kugou", "id": "3", "duration": 230},
    ]
    results = _merge_results(songs)
    assert len(results) == 1
    assert results[0]["platform_count"] == 3
    # Should prefer the version with longest duration
    assert results[0]["source"] == "qq"


def test_merge_results_different_songs():
    from backend.routers.music import _merge_results
    songs = [
        {"name": "稻香", "artist": "周杰伦", "source": "netease", "id": "1", "duration": 240},
        {"name": "晴天", "artist": "周杰伦", "source": "netease", "id": "2", "duration": 270},
    ]
    results = _merge_results(songs)
    assert len(results) == 2
    # More platforms first, then longer duration
    names = [r["name"] for r in results]
    assert "稻香" in names
    assert "晴天" in names


def test_merge_results_sorts_by_platform_count():
    from backend.routers.music import _merge_results
    songs = [
        {"name": "A", "artist": "X", "source": "netease", "id": "1", "duration": 200},
        {"name": "B", "artist": "Y", "source": "netease", "id": "2", "duration": 200},
        {"name": "B", "artist": "Y", "source": "qq", "id": "3", "duration": 200},
        {"name": "B", "artist": "Y", "source": "kugou", "id": "4", "duration": 200},
    ]
    results = _merge_results(songs)
    assert results[0]["name"] == "B"  # 3 platforms > 1 platform
    assert results[0]["platform_count"] == 3


# --- check-existing endpoint ---

def test_check_existing_not_found(client, db_session):
    resp = client.get("/api/music/check-existing?source=netease&source_id=12345")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is False
    assert data["song_id"] is None


def test_check_existing_found(client, db_session):
    song = Song(
        title="测试歌曲",
        original_audio_path="/tmp/test.mp3",
        source="netease",
        source_id="12345",
        status="uploaded",
    )
    db_session.add(song)
    db_session.commit()

    resp = client.get("/api/music/check-existing?source=netease&source_id=12345")
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is True
    assert data["song_id"] == song.id


# --- search endpoint error handling ---

@patch("backend.routers.music._search_musicdl", new_callable=AsyncMock)
def test_search_service_unavailable(mock_search, client):
    from fastapi import HTTPException
    mock_search.side_effect = HTTPException(503, "Music search service unavailable")

    resp = client.get("/api/music/search?q=稻香")
    assert resp.status_code == 503


@patch("backend.routers.music._search_musicdl", new_callable=AsyncMock)
def test_search_returns_empty(mock_search, client):
    mock_search.return_value = []

    resp = client.get("/api/music/search?q=不存在的歌曲xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["songs"] == []
    assert data["count"] == 0


@patch("backend.routers.music._search_musicdl", new_callable=AsyncMock)
def test_search_returns_results(mock_search, client):
    mock_search.return_value = [
        {"name": "稻香", "artist": "周杰伦", "source": "netease", "id": "1", "duration": 240},
    ]

    resp = client.get("/api/music/search?q=稻香")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["songs"][0]["name"] == "稻香"


# --- import endpoint ---

def test_import_creates_task(client):
    with patch("backend.routers.music._run_import", new_callable=AsyncMock):
        resp = client.post("/api/music/import?source=netease&source_id=123&title=测试&artist=歌手")
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert data["task_id"].startswith("import_")
        assert data["status"] == "importing"


@pytest.mark.skip(reason="SSE streaming test hangs with TestClient; tested manually")
def test_import_progress_unknown_task(client):
    """SSE endpoint streams progress for unknown tasks. Skipped in CI due to hang."""
