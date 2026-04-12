#!/usr/bin/env python3
"""E2E pipeline benchmark — measure performance with optimizations.

Usage: python3 benchmark_pipeline.py
Requires: backend on :8000, GPU tunnel on :8001
"""

import json
import sys
import time
import httpx
import asyncio

BASE = "http://localhost:8000/api"
GPU = "http://localhost:8001"

async def login():
    async with httpx.AsyncClient(timeout=10, trust_env=False) as c:
        r = await c.get(f"{BASE}/auth/dev-login")
        data = r.json()
        return data.get("token")

async def get_songs(token):
    async with httpx.AsyncClient(timeout=10, trust_env=False) as c:
        r = await c.get(f"{BASE}/songs", headers={"Authorization": f"Bearer {token}"})
        return r.json().get("songs", [])

async def get_segments(token, song_id):
    async with httpx.AsyncClient(timeout=10, trust_env=False) as c:
        r = await c.get(f"{BASE}/songs/{song_id}/segments", headers={"Authorization": f"Bearer {token}"})
        return r.json().get("segments", [])

async def get_voices(token):
    async with httpx.AsyncClient(timeout=10, trust_env=False) as c:
        r = await c.get(f"{BASE}/voices", headers={"Authorization": f"Bearer {token}"})
        return r.json().get("voices", [])

async def reset_song(token, song_id):
    """Reset a done song back to uploaded for re-testing."""
    async with httpx.AsyncClient(timeout=10, trust_env=False) as c:
        # Delete existing segments and outputs by triggering a reset
        # We'll use a song that's already in 'uploaded' state
        pass

async def watch_progress(song_id, token):
    """Watch SSE progress and record timing for each step."""
    timings = {}
    start_time = time.time()

    url = f"{BASE}/songs/{song_id}/progress?token={token}"
    async with httpx.AsyncClient(timeout=None, trust_env=False) as client:
        async with client.stream("GET", url) as resp:
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = json.loads(line[6:])
                step = data.get("step", "")
                pct = data.get("pct", 0)
                msg = data.get("message", "")
                elapsed = time.time() - start_time

                if step not in timings:
                    timings[step] = {"start": elapsed, "pct": pct, "msg": msg}
                timings[step]["end"] = elapsed
                timings[step]["pct"] = pct

                print(f"  [{elapsed:6.1f}s] {step:15s} {pct:3d}%  {msg}")

                if step in ("done", "error", "cancelled"):
                    return timings, elapsed
    return timings, time.time() - start_time

async def run_benchmark():
    print("=" * 60)
    print("FireSing E2E Pipeline Benchmark (with optimizations)")
    print("=" * 60)

    # Step 0: Check services
    print("\n[Step 0] Service health check")
    async with httpx.AsyncClient(timeout=5, trust_env=False) as c:
        try:
            r = await c.get(f"{GPU}/health")
            gpu = r.json()
            print(f"  GPU: {gpu.get('gpu')} ({gpu.get('vram_total_gb')}GB)")
            print(f"  Cache: {gpu.get('cache_size')}/{gpu.get('cache_max')} models")
        except Exception as e:
            print(f"  GPU: OFFLINE ({e})")
            return

    # Login
    token = await login()
    if not token:
        print("  ERROR: Login failed")
        return
    print(f"  Auth: OK")

    # Find a suitable song — prefer 'uploaded' status
    songs = await get_songs(token)

    # Prefer specific test song
    target_id = "9ae9fb849594"  # 晴天 (reset to uploaded)
    uploaded = [s for s in songs if s["status"] == "uploaded"]

    if uploaded:
        song = uploaded[0]
        print(f"\n  Using uploaded song: {song['title']} ({song['id'][:8]})")
    else:
        print("  No uploaded songs available for testing")
        print("  Songs:", [(s['id'][:8], s['status'], s['title'][:30]) for s in songs[:5]])
        return

    song_id = song["id"]

    # Check segments
    segs = await get_segments(token, song_id)
    print(f"  Segments: {len(segs)}")

    # Check voices
    voices = await get_voices(token)
    voice_ids = [v["id"] for v in voices[:2]]  # Use first 2 voices
    print(f"  Voices: {[v['name'] for v in voices[:2]]}")

    if not segs:
        print("  No segments — song needs demucs first (pipeline will handle)")

    # Step 1: Measure GPU model cache check latency
    print("\n[Step 1] GPU cache check latency")
    async with httpx.AsyncClient(timeout=3, trust_env=False) as c:
        t0 = time.time()
        r = await c.get(f"{GPU}/model/has/{voice_ids[0]}")
        t1 = time.time()
        cached = r.json()
        print(f"  /model/has/{voice_ids[0][:8]}: {cached} ({(t1-t0)*1000:.0f}ms)")

    # Step 2: Trigger pipeline and measure
    print(f"\n[Step 2] Pipeline execution")
    print(f"  Song: {song['title']} ({song_id[:8]})")
    print(f"  Voices: {voice_ids}")
    print(f"  Format: video")
    print(f"  Chorus: enabled, 5 voices")
    print()

    pipeline_start = time.time()
    async with httpx.AsyncClient(timeout=30, trust_env=False) as c:
        r = await c.post(
            f"{BASE}/songs/{song_id}/process",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "voice_pool": voice_ids,
                "strategy": "round-robin",
                "output_format": "video",
                "enable_chorus": True,
                "chorus_voice_count": 5,
            },
        )
        if r.status_code not in (200, 201):
            print(f"  ERROR: {r.status_code} {r.text}")
            return
        print(f"  Pipeline triggered: {r.json()}")

    # Watch progress
    timings, total = await watch_progress(song_id, token)

    # Step 3: Report
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"{'Step':<20s} {'Duration':>10s} {'Notes'}")
    print("-" * 50)

    prev_end = 0
    for step, info in timings.items():
        dur = info.get("end", info.get("start", 0)) - info.get("start", 0)
        total_pct = info.get("pct", 0)
        print(f"{step:<20s} {dur:>8.1f}s  {info.get('msg', '')}")

    print("-" * 50)
    print(f"{'TOTAL':<20s} {total:>8.1f}s")
    print()

    # Check GPU cache state after pipeline
    async with httpx.AsyncClient(timeout=5, trust_env=False) as c:
        r = await c.get(f"{GPU}/health")
        gpu = r.json()
        print(f"GPU cache after: {gpu.get('cached_models')} ({gpu.get('vram_used_gb')}GB used)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
