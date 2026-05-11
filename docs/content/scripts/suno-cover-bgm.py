#!/usr/bin/env python3
"""Sings 方言说唱完整工作流：
1. sunoapi.org 上传BGM → 生成人声
2. Demucs 提取纯人声
3. FFmpeg 混合固定BGM → 最终音频
"""

import json
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

# Load .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ[key.strip()] = val.strip().strip('"').strip("'")

API_KEY = os.environ.get("SUNOAPI_ORG_KEY", "")
if not API_KEY:
    print("ERROR: SUNOAPI_ORG_KEY not set")
    sys.exit(1)

UPLOAD_URL = "https://sunoapiorg.redpandaai.co/api/file-stream-upload"
COVER_URL = "https://api.sunoapi.org/api/v1/generate/upload-cover"
POLL_URL = "https://api.sunoapi.org/api/v1/generate/record-info"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

# Load config
config_path = sys.argv[1] if len(sys.argv) > 1 else None
if not config_path:
    print("Usage: python suno-cover-bgm.py <config.json>")
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

video_id = config["video_id"]
output_dir = Path(__file__).parent.parent / "assets" / "output"
output_dir.mkdir(parents=True, exist_ok=True)

bgm_path = Path(__file__).parent.parent / "assets" / "bgm" / Path(config["bgm"]["file"]).name
if not bgm_path.exists():
    bgm_path = Path(config["bgm"]["file"])
if not bgm_path.exists():
    print(f"ERROR: BGM file not found: {bgm_path}")
    sys.exit(1)

bgm_volume = config["bgm"].get("volume", 0.35)
bgm_fade = config["bgm"].get("fade_out_s", 3)

print(f"BGM file: {bgm_path} ({bgm_path.stat().st_size / 1024 / 1024:.1f} MB)")

# Step 1: Upload BGM file to sunoapi.org
print("\n[1/5] Uploading BGM to sunoapi.org...")
with open(bgm_path, "rb") as f:
    files = {"file": (bgm_path.name, f, "audio/mpeg")}
    data = {"uploadPath": f"firesing/{bgm_path.name}"}
    resp = requests.post(UPLOAD_URL, headers=HEADERS, files=files, data=data, timeout=120)

if resp.status_code != 200:
    print(f"ERROR: Upload failed ({resp.status_code}): {resp.text}")
    sys.exit(1)

download_url = resp.json().get("data", {}).get("downloadUrl")
if not download_url:
    print(f"ERROR: No downloadUrl in response: {resp.json()}")
    sys.exit(1)

print(f"BGM uploaded: {download_url[:80]}...")

# Step 2: Generate cover audio via sunoapi.org
print("\n[2/5] Generating vocals via sunoapi.org...")
cover_payload = {
    "uploadUrl": download_url,
    "customMode": True,
    "instrumental": False,
    "model": "V4_5",
    "prompt": config["lyrics"]["suno_format"],
    "style": config["suno"]["style_tags"],
    "title": config["suno"]["title"],
    "negativeTags": config["suno"].get("negative_tags", ""),
    "vocalGender": config["suno"].get("vocal_gender", "f"),
    "audioWeight": 0.85,
    "callBackUrl": "https://httpbin.org/post",
}

cover_resp = requests.post(
    COVER_URL,
    headers={**HEADERS, "Content-Type": "application/json"},
    json=cover_payload,
    timeout=60,
)

if cover_resp.status_code != 200:
    print(f"ERROR: Cover generation failed ({cover_resp.status_code}): {cover_resp.text}")
    sys.exit(1)

task_id = cover_resp.json().get("data", {}).get("taskId")
if not task_id:
    print(f"ERROR: No taskId in response: {cover_resp.json()}")
    sys.exit(1)

print(f"Task ID: {task_id}")

# Step 3: Poll for completion
print("\n[3/5] Polling for completion...")
suno_output = output_dir / f"{video_id}-suno-raw.mp3"
audio_url = None

for attempt in range(40):  # ~10 min at 15s intervals
    poll_resp = requests.get(f"{POLL_URL}?taskId={task_id}", headers=HEADERS, timeout=30)
    if poll_resp.status_code != 200:
        print(f"  [{attempt * 15}s] poll error, retrying...")
        time.sleep(15)
        continue

    poll_data = poll_resp.json()
    status = poll_data.get("data", {}).get("status", "UNKNOWN")
    print(f"  [{attempt * 15}s] status={status}")

    if status == "SUCCESS":
        suno_data = poll_data.get("data", {}).get("response", {}).get("sunoData", [])
        if suno_data:
            for i, item in enumerate(suno_data):
                print(f"    Version {i+1}: {item.get('duration', '?')}s")
            best = min(suno_data, key=lambda x: x.get("duration", 999))
            audio_url = best.get("audioUrl")
        break
    elif status in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED", "CALLBACK_EXCEPTION", "SENSITIVE_WORD_ERROR"):
        print(f"ERROR: Generation failed: {status}")
        sys.exit(1)

    time.sleep(15)

if not audio_url:
    print("ERROR: Timed out waiting for generation")
    sys.exit(1)

# Download Suno output
print(f"\n  Downloading Suno output...")
dl_resp = requests.get(audio_url, timeout=120)
suno_output.write_bytes(dl_resp.content)
print(f"  Saved: {suno_output.name} ({suno_output.stat().st_size / 1024 / 1024:.1f} MB)")

# Step 4: Demucs extract vocals
print(f"\n[4/5] Demucs extracting vocals...")
demucs_out = output_dir / f"{video_id}-demucs"
demucs_cmd = [
    sys.executable, "-m", "demucs",
    "--two-stems=vocals",
    "-o", str(demucs_out),
    str(suno_output),
]
print(f"  Running: {' '.join(demucs_cmd)}")
result = subprocess.run(demucs_cmd, capture_output=True, text=True, timeout=300)
if result.returncode != 0:
    print(f"ERROR: Demucs failed: {result.stderr}")
    sys.exit(1)

# Find extracted vocals file
vocals_file = None
for p in demucs_out.rglob("vocals.wav"):
    vocals_file = p
    break

if not vocals_file or not vocals_file.exists():
    print(f"ERROR: Vocals file not found in {demucs_out}")
    sys.exit(1)

print(f"  Vocals extracted: {vocals_file.name} ({vocals_file.stat().st_size / 1024 / 1024:.1f} MB)")

# Step 5: FFmpeg mix vocals + fixed BGM
print(f"\n[5/5] FFmpeg mixing vocals + fixed BGM...")
final_output = output_dir / f"{video_id}-final.mp3"
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-i", str(vocals_file),
    "-i", str(bgm_path),
    "-filter_complex",
    f"[1:a]volume={bgm_volume},afade=t=out:st=90:d={bgm_fade}[bgm];"
    f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
    "-map", "[aout]",
    "-b:a", "192k",
    str(final_output),
]
print(f"  Running: {' '.join(ffmpeg_cmd)}")
result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
if result.returncode != 0:
    print(f"ERROR: FFmpeg failed: {result.stderr}")
    sys.exit(1)

print(f"\nDone! Final output: {final_output}")
print(f"  {final_output.name} ({final_output.stat().st_size / 1024 / 1024:.1f} MB)")
print(f"  BGM: {bgm_path.name} (volume={bgm_volume}, fade_out={bgm_fade}s)")
