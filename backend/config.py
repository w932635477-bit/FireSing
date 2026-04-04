"""FireSing configuration."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Data subdirectories
SONGS_DIR = DATA_DIR / "songs"
SEGMENTS_DIR = DATA_DIR / "segments"
CONVERTED_DIR = DATA_DIR / "converted"
OUTPUTS_DIR = DATA_DIR / "outputs"
VOICES_DIR = DATA_DIR / "voices"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'firesing.db'}")

# GPU Server
GPU_SERVER_URL = os.getenv("GPU_SERVER_URL", "http://localhost:8001")
GPU_REQUEST_TIMEOUT = int(os.getenv("GPU_REQUEST_TIMEOUT", "300"))  # 5 min

# Upload limits
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
ALLOWED_AUDIO_FORMATS = {".mp3", ".wav", ".flac"}
ALLOWED_LYRICS_FORMATS = {".lrc", ".txt"}

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
