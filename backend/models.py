"""FireSing SQLAlchemy models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Song(Base):
    __tablename__ = "songs"

    id = Column(String, primary_key=True, default=new_id)
    title = Column(String, nullable=False)
    original_audio_path = Column(String, nullable=False)
    lrc_path = Column(String)
    vocals_path = Column(String)
    instrumental_path = Column(String)
    monologue_text = Column(Text)
    monologue_position = Column(String)  # "beginning" or "end"
    monologue_audio_path = Column(String)
    status = Column(String, default="uploaded")
    # uploaded | separating | separated | segmented | assigning |
    # converting | chorus | monologue | mixing | video | done | error
    pipeline_step = Column(String)  # sub-step for resume on error
    error_message = Column(Text)
    source = Column(String, default="upload")   # "upload", "netease", "qq", "kugou", etc.
    source_id = Column(String)                  # Platform song ID
    source_url = Column(String)                 # Original platform link
    artist = Column(String)                     # Artist name (for search imports)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    segments = relationship("Segment", back_populates="song", cascade="all, delete-orphan")
    outputs = relationship("Output", back_populates="song", cascade="all, delete-orphan")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(String, primary_key=True, default=new_id)
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    line_number = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    vocal_path = Column(String)
    voice_model_id = Column(String, ForeignKey("voice_models.id"))
    converted_vocal_path = Column(String)

    song = relationship("Song", back_populates="segments")
    voice_model = relationship("VoiceModel")


class VoiceModel(Base):
    __tablename__ = "voice_models"

    id = Column(String, primary_key=True, default=new_id)
    name = Column(String, nullable=False)
    model_path = Column(String, nullable=False)
    index_path = Column(String)
    is_preset = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    segments = relationship("Segment", back_populates="voice_model")


class Output(Base):
    __tablename__ = "outputs"

    id = Column(String, primary_key=True, default=new_id)
    song_id = Column(String, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    format = Column(String, nullable=False)  # "video" | "audio" | "video_subtitled"
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    duration = Column(Float)
    created_at = Column(DateTime, default=utcnow)

    song = relationship("Song", back_populates="outputs")
