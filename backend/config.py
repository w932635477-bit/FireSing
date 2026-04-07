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

# Music Download Service (go-music-dl)
MUSIC_DL_URL = os.getenv("MUSIC_DL_URL", "http://localhost:8090/music")

# Upload limits
MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "50"))
ALLOWED_AUDIO_FORMATS = {".mp3", ".wav", ".flac"}
ALLOWED_LYRICS_FORMATS = {".lrc", ".txt"}

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# WeChat Open Platform (PC QR scan login)
WECHAT_OPEN_APP_ID = os.getenv("WECHAT_OPEN_APP_ID", "")
WECHAT_OPEN_APP_SECRET = os.getenv("WECHAT_OPEN_APP_SECRET", "")

# WeChat Official Account (in-app OAuth)
WECHAT_MP_APP_ID = os.getenv("WECHAT_MP_APP_ID", "")
WECHAT_MP_APP_SECRET = os.getenv("WECHAT_MP_APP_SECRET", "")

# WeChat Pay
WECHAT_PAY_MCH_ID = os.getenv("WECHAT_PAY_MCH_ID", "")
WECHAT_PAY_API_KEY = os.getenv("WECHAT_PAY_API_KEY", "")
WECHAT_PAY_NOTIFY_URL = os.getenv(
    "WECHAT_PAY_NOTIFY_URL", "https://firesing.cn/api/payments/wechat/callback"
)

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-to-a-random-32-char-string")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "168"))  # 7 days
