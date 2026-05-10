#!/usr/bin/env python3
"""
SunoAPI.org Add Vocals Test
Uploads BGM → calls add-vocals with Northeast dialect comedic rap style → polls → downloads result.

Usage:
    source docs/content/.env
    python docs/content/scripts/suno-add-vocals-test.py
"""

import base64
import json
import os
import sys
import time
import logging

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Bypass local proxy for SSL compatibility
NO_PROXY = {"http": None, "https": None}

UPLOAD_BASE = "https://sunoapiorg.redpandaai.co"
API_BASE = "https://api.sunoapi.org"

CONFIG_PATH = "docs/content/config/sings-dialect-rap-ep01.json"
BGM_PATH = "docs/content/assets/bgm/杨梦.bgm_副本.mp3"
OUTPUT_DIR = "docs/content/assets/voiceover/sings-dialect-rap-ep01"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_api_key():
    key = os.environ.get("SUNOAPI_ORG_KEY", "")
    if not key:
        logger.error("SUNOAPI_ORG_KEY not set. Run: source docs/content/.env")
        sys.exit(1)
    return key


def upload_bgm(api_key: str) -> str:
    """Upload BGM via base64 upload, return public downloadUrl."""
    logger.info("Uploading BGM (base64): %s", BGM_PATH)

    with open(BGM_PATH, "rb") as f:
        bgm_bytes = f.read()

    bgm_b64 = base64.b64encode(bgm_bytes).decode("utf-8")
    bgm_name = os.path.basename(BGM_PATH)
    data_url = f"data:audio/mpeg;base64,{bgm_b64}"

    payload = {
        "base64Data": data_url,
        "uploadPath": "bgm",
        "fileName": bgm_name,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        f"{UPLOAD_BASE}/api/file-base64-upload",
        headers=headers,
        json=payload,
        timeout=120,
        proxies=NO_PROXY,
    )

    resp.raise_for_status()
    result = resp.json()
    logger.info("Upload response: %s", json.dumps(result, indent=2, ensure_ascii=False))

    if not result.get("success"):
        logger.error("Upload failed: %s", result.get("msg"))
        sys.exit(1)

    download_url = result["data"].get("downloadUrl") or result["data"].get("fileUrl")
    if not download_url:
        logger.error("No download URL in response")
        sys.exit(1)

    logger.info("BGM uploaded to: %s", download_url)
    return download_url


def call_add_vocals(api_key: str, bgm_url: str, config: dict) -> str:
    """Call add-vocals API, return taskId."""
    logger.info("Calling add-vocals API...")

    lyrics = config["lyrics"]["suno_format"]
    suno_cfg = config["suno"]

    prompt = (
        f"东北方言顺口溜喊麦，128BPM Tech House鼓点驱动。每句7字，4+3节奏，句句砸拍。歌词如下：\n{lyrics}\n\n"
        "演唱要求（参考阿建欢乐多/孙克杰喊麦风格）：\n"
        "- [Intro]：短促有力，像喊口号，每个词砸在拍子上\n"
        "- [Verse]：严格7字句，前4字砸1-2拍，后3字砸3-4拍，每句占2个bar，句尾押韵对齐鼓点下沿，不留拖腔不唱旋律，就是砸着说\n"
        "- [Hook]：'嘿！'用喊的，像阿建欢乐多那种方言喊麦，短促有力有记忆点\n"
        "- [Break]：放慢，像自言自语，给音乐留白\n"
        "- [Chorus]：能量最高，7字句机关枪节奏，句句砸拍不留气口\n"
        "- [Outro]：收尾带笑意，最后'柴油是实在的'像跟朋友开玩笑\n"
        "核心：顺口溜韵律，不是rap不是唱，是砸着说，每个音节对准鼓点，东北方言句尾上扬。"
    )

    payload = {
        "uploadUrl": bgm_url,
        "prompt": prompt,
        "title": suno_cfg.get("title", "杨梦东北话说唱-打工人"),
        "negativeTags": suno_cfg.get(
            "negative_tags",
            "slow ballad, sad, dramatic, rock, heavy metal, autotune, R&B, jazz, country",
        ),
        "style": "comedic spoken-word rap, Chinese Northeast dialect, electronic dance, half-spoken half-sung",
        "callBackUrl": "https://httpbin.org/post",
        "vocalGender": suno_cfg.get("vocal_gender", "f"),
        "styleWeight": 0.70,
        "weirdnessConstraint": 0.60,
        "audioWeight": 0.65,
        "model": "V4_5PLUS",
    }

    logger.info("Request payload (partial): %s", json.dumps(
        {k: v for k, v in payload.items() if k != "prompt"}, indent=2, ensure_ascii=False
    ))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(
        f"{API_BASE}/api/v1/generate/add-vocals",
        headers=headers,
        json=payload,
        timeout=60,
        proxies=NO_PROXY,
    )

    logger.info("Response status: %d", resp.status_code)
    result = resp.json()
    logger.info("Response: %s", json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("code") != 200:
        logger.error("API error: %s", result.get("msg"))
        sys.exit(1)

    task_id = result["data"]["taskId"]
    logger.info("Task created: %s", task_id)
    return task_id


def poll_task(api_key: str, task_id: str, max_wait: int = 600) -> dict:
    """Poll task status until complete, return final data."""
    headers = {"Authorization": f"Bearer {api_key}"}
    start = time.time()

    logger.info("Polling task %s (max %ds)...", task_id, max_wait)

    while time.time() - start < max_wait:
        resp = requests.get(
            f"{API_BASE}/api/v1/generate/record-info",
            params={"taskId": task_id},
            headers=headers,
            timeout=30,
            proxies=NO_PROXY,
        )

        result = resp.json()
        elapsed = int(time.time() - start)
        status = result.get("data", {}).get("status", "UNKNOWN")
        logger.info("[%ds] Status: %s", elapsed, status)

        if status in ("SUCCESS", "FIRST_SUCCESS"):
            logger.info("Task completed!")
            logger.info("Full response: %s", json.dumps(result, indent=2, ensure_ascii=False))
            return result.get("data", {})

        if status in ("CREATE_TASK_FAILED", "GENERATE_AUDIO_FAILED",
                      "CALLBACK_EXCEPTION", "SENSITIVE_WORD_ERROR"):
            logger.error("Task failed (%s): %s", status,
                         json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        time.sleep(15)

    logger.error("Timeout after %ds", max_wait)
    sys.exit(1)


def _extract_nested_audio_url(task_data: dict) -> str | None:
    """Try to extract audioUrl from response.sunoData[].audioUrl."""
    response = task_data.get("response")
    if not response or not isinstance(response, dict):
        return None
    suno_data = response.get("sunoData")
    if not suno_data or not isinstance(suno_data, list):
        return None
    for item in suno_data:
        url = item.get("audioUrl")
        if url:
            return url
    return None


def download_result(api_key: str, task_data: dict) -> str | None:
    """Download the generated audio file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    audio_url = (
        task_data.get("audio_url")
        or task_data.get("audioUrl")
        or _extract_nested_audio_url(task_data)
    )
    if not audio_url:
        logger.error("No audio URL in task data: %s", json.dumps(task_data, indent=2, ensure_ascii=False))
        return None

    output_path = os.path.join(OUTPUT_DIR, "ep01-add-vocals-test.mp3")
    logger.info("Downloading: %s", audio_url)

    resp = requests.get(audio_url, timeout=120, stream=True)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = os.path.getsize(output_path) / 1024
    logger.info("Saved: %s (%.0f KB)", output_path, size_kb)
    return output_path


def main():
    config = load_config()
    api_key = get_api_key()

    logger.info("=== SunoAPI.org Add Vocals Test ===")
    logger.info("BGM: %s (%s)", config["bgm"]["title"], config["bgm"]["artist"])
    logger.info("Lyrics preview: %s...", config["lyrics"]["suno_format"][:80])

    bgm_url = upload_bgm(api_key)

    task_id = call_add_vocals(api_key, bgm_url, config)

    task_data = poll_task(api_key, task_id)

    output = download_result(api_key, task_data)

    if output:
        logger.info("=== DONE ===")
        logger.info("Output: %s", output)
        logger.info("Next: listen to the file and evaluate quality")
    else:
        logger.error("Download failed")


if __name__ == "__main__":
    main()
