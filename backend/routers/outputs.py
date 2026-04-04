"""Outputs router — list and download outputs."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Song, Output
from ..schemas import OutputListResponse

router = APIRouter()


@router.get("/{song_id}/outputs", response_model=OutputListResponse)
async def list_outputs(song_id: str, db: Session = Depends(get_db)):
    """List all outputs for a song."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(404, f"Song {song_id} not found")

    outputs = db.query(Output).filter(Output.song_id == song_id).all()

    # Add file_url based on output id
    result = []
    for o in outputs:
        result.append({
            "id": o.id,
            "format": o.format,
            "file_url": f"/api/songs/{song_id}/outputs/{o.id}/download",
            "file_size": o.file_size,
            "duration": o.duration,
        })
    return {"outputs": result}


@router.get("/{song_id}/outputs/{output_id}/download")
async def download_output(song_id: str, output_id: str, db: Session = Depends(get_db)):
    """Download an output file."""
    output = db.query(Output).filter(
        Output.id == output_id, Output.song_id == song_id
    ).first()
    if not output:
        raise HTTPException(404, f"Output {output_id} not found")

    file_path = Path(output.file_path)
    if not file_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    media_type = "video/mp4" if output.format == "video" else "audio/wav"
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
    )
