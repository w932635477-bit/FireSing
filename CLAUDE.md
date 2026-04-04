# FireSing

AI-powered song modification platform. Takes existing songs and replaces vocals line-by-line with different AI voice models.

## Architecture

Dual-server: Mac (FastAPI + SQLite + Next.js) + AutoDL GPU (inference API).

See TECHNICAL.md for full architecture details.

## Project Structure

- `backend/` — FastAPI backend (main API server)
- `gpu_server/` — GPU inference server (runs on AutoDL)
- `frontend/` — Next.js web UI
- `validation/` — Technical validation scripts (8/8 PASS)
- `data/` — Runtime data (gitignored)

## Development

```bash
# Backend
cd backend && uvicorn main:app --reload

# GPU Server (on AutoDL)
cd gpu_server && python server.py --port 8001

# Frontend
cd frontend && npm run dev

# Tests
pytest backend/tests/
```

## MVP Sprint Plan

Sprint 1: Foundation + Upload + Demucs
Sprint 2: LRC Parsing + Segmentation
Sprint 3: RVC Voice Conversion
Sprint 4: Full Audio Pipeline
Sprint 5: Video + Output
Sprint 6: Frontend

## Validation Status

8/8 PASS. See validation/VALIDATION_REPORT.md for details.

## Key Constraints

- RVC uses harvest f0 (4.60s/segment). rmvpe has PyTorch 2.11 compat issues.
- LRC lyrics required. No Whisper in MVP.
- Single GPU, single user, no auth.
- pydub/FFmpeg are sync — wrap in asyncio.to_thread().
