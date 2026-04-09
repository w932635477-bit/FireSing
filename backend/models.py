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
    monologue_position = Column(String)  # "beginning" | "end" | "interlude"
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

    user_id = Column(String, ForeignKey("users.id"))
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


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_id)
    wechat_openid = Column(String, unique=True, nullable=False)
    wechat_unionid = Column(String, index=True)
    wechat_nickname = Column(String)
    wechat_avatar_url = Column(String)
    credits = Column(Integer, default=3)  # 免费额度 3 首
    subscription_plan = Column(String, default="free")  # free | monthly | yearly
    subscription_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    orders = relationship("Order", back_populates="user")

    @property
    def has_unlimited(self) -> bool:
        if self.subscription_plan == "free":
            return False
        if self.subscription_expires_at and self.subscription_expires_at > utcnow():
            return True
        return False


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # "credits" | "subscription"
    amount = Column(Integer, nullable=False)  # 金额（分）
    credits_amount = Column(Integer)  # 购买的积分数量
    description = Column(String)
    status = Column(String, default="pending")  # pending | paid | failed | refunded
    wechat_prepay_id = Column(String)
    wechat_transaction_id = Column(String)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="orders")
