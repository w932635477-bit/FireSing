"""FireSing API schemas (Pydantic v2)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Songs ---

class SongResponse(BaseModel):
    id: str
    title: str
    status: str
    lrc_path: Optional[str] = None
    vocals_path: Optional[str] = None
    instrumental_path: Optional[str] = None
    monologue_text: Optional[str] = None
    monologue_position: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SongListResponse(BaseModel):
    songs: list[SongResponse]


class SongDeleteResponse(BaseModel):
    deleted: bool


# --- Segments ---

class SegmentResponse(BaseModel):
    id: str
    line_number: int
    text: str
    start_time: float
    end_time: float
    vocal_path: Optional[str] = None
    voice_model_id: Optional[str] = None
    converted_vocal_path: Optional[str] = None

    model_config = {"from_attributes": True}


class SegmentListResponse(BaseModel):
    segments: list[SegmentResponse]


# --- Voice Models ---

class VoiceModelResponse(BaseModel):
    id: str
    name: str
    is_preset: bool

    model_config = {"from_attributes": True}


class VoiceModelListResponse(BaseModel):
    voices: list[VoiceModelResponse]


class VoiceAssignment(BaseModel):
    line_number: int
    voice_model_id: str


class VoiceAssignRequest(BaseModel):
    assignments: list[VoiceAssignment] = []
    voice_pool: list[str] = []  # Used for round-robin/random strategies
    strategy: str = "manual"  # "round-robin" | "random" | "manual"


class VoiceAssignResponse(BaseModel):
    assigned_count: int


# --- Pipeline ---

class ProcessRequest(BaseModel):
    voice_pool: list[str]
    strategy: str = "round-robin"
    monologue_text: Optional[str] = None
    monologue_position: str = "beginning"  # "beginning" | "end"


class ProcessResponse(BaseModel):
    status: str


class PipelineProgress(BaseModel):
    step: str
    pct: int
    message: str
    step_failed: Optional[str] = None
    error_detail: Optional[str] = None


# --- Outputs ---

class OutputResponse(BaseModel):
    id: str
    format: str
    file_url: str
    file_size: Optional[int] = None
    duration: Optional[float] = None

    model_config = {"from_attributes": True}


class OutputListResponse(BaseModel):
    outputs: list[OutputResponse]


# --- GPU Server ---

class GPUHealthResponse(BaseModel):
    status: str
    gpu: str
    vram_total_gb: float
    vram_used_gb: float
