"""Shared test fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

# Set test environment before importing app modules
os.environ.setdefault("GPU_SERVER_URL", "http://mock-gpu:8001")

from backend.database import Base, get_db
from backend.main import app  # noqa: F401 — must import to register routes
# Import all models so Base.metadata.create_all sees them
from backend.models import Song, Segment, VoiceModel, Output, User  # noqa: F401


@pytest.fixture
def db_session():
    """In-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)

    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user for authenticated endpoints."""
    user = User(
        id="test_user_001",
        wechat_openid="test_openid_001",
        wechat_nickname="Test User",
        credits=10,
        subscription_plan="free",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def client(db_session, test_user):
    """FastAPI test client with test database and auth overrides."""
    from fastapi.testclient import TestClient
    from backend.dependencies import get_current_user, require_auth, require_credits

    def override_get_db():
        yield db_session

    def override_get_current_user():
        return test_user

    def override_require_auth():
        return test_user

    def override_require_credits():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_auth] = override_require_auth
    app.dependency_overrides[require_credits] = override_require_credits

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_wav(tmp_path):
    """Create a minimal valid WAV file for testing."""
    import struct
    import io

    # Generate a 1-second sine wave at 440Hz, 44100Hz sample rate
    sample_rate = 44100
    duration = 1.0
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        import math
        value = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
        samples.append(struct.pack("<h", max(-32768, min(32767, value))))

    buf = io.BytesIO()
    # WAV header
    data_size = num_samples * 2  # 16-bit mono
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))  # chunk size
    buf.write(struct.pack("<H", 1))   # PCM
    buf.write(struct.pack("<H", 1))   # mono
    buf.write(struct.pack("<I", sample_rate))
    buf.write(struct.pack("<I", sample_rate * 2))  # byte rate
    buf.write(struct.pack("<H", 2))   # block align
    buf.write(struct.pack("<H", 16))  # bits per sample
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    for s in samples:
        buf.write(s)

    wav_path = tmp_path / "test.wav"
    wav_path.write_bytes(buf.getvalue())
    return wav_path


@pytest.fixture
def sample_lrc(tmp_path):
    """Create a sample LRC file."""
    lrc_content = """[00:00.00]
[00:05.00]第一句歌词
[00:10.00]第二句歌词
[00:15.00]第三句歌词
[00:20.00]第四句歌词
[00:25.00]第五句歌词
"""
    lrc_path = tmp_path / "test.lrc"
    lrc_path.write_text(lrc_content, encoding="utf-8")
    return lrc_path
