# Medvi Story Images Enhancement — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add story scene images to the Medvi video pipeline so each video has 10-15 images instead of 5, and add TTS auto-fallback from Gemini to Doubao.

**Architecture:** Extend existing scripts (not rewrite). Each segment in the JSON config gets an optional `story_images` array. The compose script distributes audio duration evenly across main + story videos within each segment. TTS scripts get a fallback wrapper.

**Tech Stack:** Python 3, FFmpeg, Seedream 4.5 API (Evolink), Kling 3.0 API (Evolink), Gemini TTS API, Doubao TTS API

**Design doc:** `docs/plans/2026-04-23-medvi-story-images-design.md`

---

### Task 1: Add story_images to day7-yangmun.json config

**Files:**
- Modify: `docs/content/config/day7-yangmun.json`

**Step 1: Add story_images arrays to each segment**

Add `story_images` to S01 through S05. Each story image needs `id`, `trigger_text`, `reference_prompt`, and `motion_prompt`. The prompts follow the 6-layer structure from spec 6.3 but do NOT include the Yang Mun character anchor (they are scene images, not character portraits).

S01 (hook, shock): 2 story images
- `S01-01`: "80%机器已经能做了" → factory floor with robotic arms and a lone human worker
- `S01-02`: "方向错了" → person standing at crossroads in fog

S02 (body, tension): 2 story images
- `S02-01`: "你做100遍的表格" → exhausted office worker at cluttered desk
- `S02-02`: "AI只要3秒" → screen showing AI completing a spreadsheet instantly

S03 (body, reversal): 2 story images
- `S03-01`: "所有人都说回收不可能" → rocket on launchpad, crowd of skeptics
- `S03-02`: "燃料成本只占总成本的0.3%" → close-up of cost breakdown on screen

S04 (body, fear): 2 story images
- `S04-01`: "因为忙，没时间学新东西" → person drowning in papers while others learn on laptops
- `S04-02`: "把时间，留给机器做不到的事" → hands on keyboard with warm light, focused work

S05 (cta, warm): 0 story images (character close-up is enough for CTA)

Total: 8 story images + 5 main images = 13 images

Edit each segment in `day7-yangmun.json` to add the `story_images` array after `motion_prompt`.

**Step 2: Verify JSON is valid**

Run: `python3 -c "import json; json.load(open('docs/content/config/day7-yangmun.json')); print('Valid JSON')"`
Expected: `Valid JSON`

**Step 3: Dry-run seedream-story-images to verify config reads correctly**

Run: `cd docs/content && python3 scripts/seedream-story-images.py --config day7-yangmun.json --dry-run`
Expected: Lists 8 story images with their IDs and prompts

**Step 4: Commit**

```bash
git add docs/content/config/day7-yangmun.json
git commit -m "feat: add story_images to day7-yangmun config (8 story scenes)"
```

---

### Task 2: Verify Kling story video generation works

The `kling-gen-batch.py` script already has `--include-stories` support. We just need to verify it reads the new story_images correctly.

**Files:**
- Read-only: `docs/content/scripts/kling-gen-batch.py:56-96` (load_shots function)

**Step 1: Dry-run Kling with --include-stories**

First generate the story reference images (or use existing ones). Then:

Run: `cd docs/content && python3 scripts/kling-gen-batch.py --config day7-yangmun.json --include-stories --dry-run`
Expected: Lists 13 shots (5 character + 8 story), each showing its reference image status

**Step 2: If reference images are missing, generate them first**

Run: `source .env && python3 scripts/seedream-story-images.py --config day7-yangmun.json`
Expected: 8 story images generated in `assets/references/`

**Step 3: Commit (if any new images generated)**

```bash
git add docs/content/assets/references/S01-01.png docs/content/assets/references/S01-02.png docs/content/assets/references/S02-01.png docs/content/assets/references/S02-02.png docs/content/assets/references/S03-01.png docs/content/assets/references/S03-02.png docs/content/assets/references/S04-01.png docs/content/assets/references/S04-02.png
git commit -m "feat: generate Day7 story scene reference images (8 images)"
```

---

### Task 3: Update ffmpeg-compose-day1.py for multi-video segments

This is the biggest change. The current `prepare_segment` handles 1 video per segment. We need it to handle multiple videos per segment (main + story images) with uniform time distribution.

**Files:**
- Modify: `docs/content/scripts/ffmpeg-compose-day1.py:113-157` (load_segments function)
- Modify: `docs/content/scripts/ffmpeg-compose-day1.py:160-241` (prepare_segment function)

**Step 1: Update load_segments to discover story videos**

In `load_segments()`, after finding the main video for each segment, also search for story videos. Story videos are named like `S02-01.mp4`, `S02-02.mp4` in the output directory.

Change the segment dict to include a `video_clips` list instead of a single `video_path`:

```python
# In load_segments, replace video_path logic with:
video_clips = []
# Main video
for ext in [".mp4"]:
    for p in video_dir.glob(f"{seg_id}{ext}"):
        video_clips.append({"path": p, "type": "main", "clip_id": seg_id})
        break

# Story videos (S02-01.mp4, S02-02.mp4, etc.)
for p in sorted(video_dir.glob(f"{seg_id}-*.mp4")):
    story_id = p.stem  # e.g. "S02-01"
    video_clips.append({"path": p, "type": "story", "clip_id": story_id})
```

Then in the segment dict, replace `"video_path"` with `"video_clips"`:
```python
segments.append({
    "id": seg_id,
    "audio_path": audio_path,
    "video_clips": video_clips,
    # ... rest unchanged
})
```

Keep `video_path` as a backwards-compatible property: set it to the main video path if it exists, or None.

**Step 2: Rewrite prepare_segment to handle multiple clips**

The current `prepare_segment` takes one video and adjusts its duration. The new version needs to:

1. Get target_duration from audio
2. Count the number of video clips (main + story)
3. Calculate per_clip_duration = target_duration / num_clips
4. For each clip, loop/trim to per_clip_duration
5. Concat the clips in order (main first, then stories)
6. Return the combined segment

New function signature: `prepare_segment(seg, temp_dir, output_path, all_segs=None) -> bool`

The function body:

```python
def prepare_segment(seg, temp_dir, output_path, all_segs=None):
    if not seg["audio_path"].exists():
        print(f"  {seg['id']}: SKIP — no audio")
        return False

    target_duration = get_duration(seg["audio_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Route 1: text_card
    if seg.get("shot_type") == "text_card":
        return generate_text_card(seg, output_path, target_duration, all_segs=all_segs)

    # Route 2: multi-clip segment
    clips = seg.get("video_clips", [])
    # Backwards compat: if video_clips is empty but video_path exists
    if not clips and seg.get("video_path") and seg["video_path"].exists():
        clips = [{"path": seg["video_path"], "type": "main", "clip_id": seg["id"]}]

    if not clips:
        print(f"  {seg['id']}: SKIP — no video clips")
        return False

    # Filter to existing clips
    clips = [c for c in clips if c["path"].exists()]
    if not clips:
        print(f"  {seg['id']}: SKIP — no video clips found on disk")
        return False

    num_clips = len(clips)
    per_clip_dur = target_duration / num_clips

    print(f"  {seg['id']}: audio={target_duration:.1f}s, {num_clips} clips, {per_clip_dur:.1f}s each")

    # Prepare each clip to per_clip_dur
    prepared_clips = []
    for clip in clips:
        clip_id = clip["clip_id"]
        clip_path = clip["path"]
        clip_out = temp_dir / f"{seg['id']}_{clip_id}_trimmed.mp4"
        clip_actual_dur = get_duration(clip_path)

        if per_clip_dur <= clip_actual_dur * 1.05:
            # Trim
            cmd = ["ffmpeg", "-y", "-i", str(clip_path),
                    "-t", str(per_clip_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-an", "-pix_fmt", "yuv420p", "-r", "24",
                    str(clip_out)]
        elif per_clip_dur <= clip_actual_dur * 2.0:
            # Slow down
            speed = clip_actual_dur / per_clip_dur
            cmd = ["ffmpeg", "-y", "-i", str(clip_path),
                    "-filter:v", f"setpts={1/speed}*PTS",
                    "-t", str(per_clip_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-an", "-pix_fmt", "yuv420p", "-r", "24",
                    str(clip_out)]
        else:
            # Loop: forward + reverse to fill duration
            loops_needed = int(per_clip_dur / clip_actual_dur) + 1
            parts = []
            for i in range(loops_needed):
                part_path = temp_dir / f"{seg['id']}_{clip_id}_loop_{i}.mp4"
                if i % 2 == 0:
                    loop_cmd = ["ffmpeg", "-y", "-i", str(clip_path),
                                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                                "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path)]
                else:
                    loop_cmd = ["ffmpeg", "-y", "-i", str(clip_path),
                                "-vf", "reverse",
                                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                                "-an", "-pix_fmt", "yuv420p", "-r", "24", str(part_path)]
                subprocess.run(loop_cmd, check=True, capture_output=True)
                parts.append(part_path)

            concat_f = temp_dir / f"{seg['id']}_{clip_id}_loops.txt"
            with open(concat_f, "w") as f:
                for p in parts:
                    f.write(f"file '{p.resolve()}'\n")
            cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", str(concat_f),
                    "-t", str(per_clip_dur),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    str(clip_out)]
            subprocess.run(cmd, check=True, capture_output=True)
            for p in parts:
                p.unlink(missing_ok=True)
            prepared_clips.append(clip_out)
            continue

        subprocess.run(cmd, check=True, capture_output=True)
        prepared_clips.append(clip_out)

    # If only 1 clip, just rename to output
    if len(prepared_clips) == 1:
        prepared_clips[0].rename(output_path)
        return True

    # Concat all clips for this segment
    concat_f = temp_dir / f"{seg['id']}_clips.txt"
    with open(concat_f, "w") as f:
        for p in prepared_clips:
            f.write(f"file '{p.resolve()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_f),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path)]
    subprocess.run(cmd, check=True, capture_output=True)

    # Cleanup
    for p in prepared_clips:
        p.unlink(missing_ok=True)

    return True
```

**Step 3: Update the readiness check in main()**

In the `main()` function, change the readiness check to use `video_clips`:

```python
# Replace:
video_ok = seg["video_path"] is not None and seg["video_path"].exists()
# With:
video_ok = bool(seg.get("video_clips")) or (seg.get("video_path") and seg["video_path"].exists())
```

**Step 4: Dry-run test**

Run: `cd docs/content && python3 scripts/ffmpeg-compose-day1.py --config day7-yangmun.json --dry-run`
Expected: Shows all segments with audio + video status, estimated total duration

**Step 5: Commit**

```bash
git add docs/content/scripts/ffmpeg-compose-day1.py
git commit -m "feat: ffmpeg-compose supports multi-clip segments (story images)"
```

---

### Task 4: Add TTS auto-fallback (Gemini → Doubao)

Add fallback logic to `gemini-tts-batch.py`. When Gemini API returns 429 or 403, automatically switch to calling `doubao-tts-batch.py` logic.

**Files:**
- Modify: `docs/content/scripts/gemini-tts-batch.py:320-340` (synthesis error handling)

**Step 1: Add fallback detection and Doubao integration**

At the top of `gemini-tts-batch.py`, add an import and helper:

```python
# Add after existing imports
FALLBACK_ENGINE = False
```

Add a function to detect quota errors:

```python
def is_quota_error(error: Exception) -> bool:
    """Check if error is a Gemini quota/auth error that should trigger fallback."""
    error_str = str(error).lower()
    return any(kw in error_str for kw in ["429", "quota", "resource_exhausted", "403", "permission"])
```

Modify the synthesis loop in `main()` to catch quota errors and trigger fallback. After the first quota error, set `FALLBACK_ENGINE = True` and call Doubao for all remaining segments.

In the main loop (around line 320), change the `except` block:

```python
        except Exception as e:
            if is_quota_error(e) and not FALLBACK_ENGINE:
                FALLBACK_ENGINE = True
                print(f"\n  Gemini TTS quota exceeded, falling back to Doubao TTS")
                print(f"  Re-generating this segment with Doubao...")
                # Retry with Doubao
                try:
                    from doubao_tts_integration import synthesize_doubao
                    info = synthesize_doubao(seg, dest, config)
                    total_duration += info["duration_s"]
                    print(f"done (Doubao, {info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                    results.append({...})
                except Exception as e2:
                    print(f"Doubao fallback also failed: {e2}")
                    results.append({"segment": seg["id"], "status": "error", "error": str(e2)})
            else:
                print(f"failed: {e}")
                results.append({"segment": seg["id"], "status": "error", "error": str(e)})
```

Also, before the loop, check `FALLBACK_ENGINE` and skip Gemini entirely if already fallen back:

```python
        if FALLBACK_ENGINE:
            # Use Doubao directly
            ...
```

**Step 2: Create the Doubao integration helper**

Create a small helper module `docs/content/scripts/doubao_tts_integration.py` that wraps the Doubao TTS logic into a single function call:

```python
def synthesize_doubao(seg: dict, output_path: Path, config: dict) -> dict:
    """Synthesize a single segment using Doubao TTS. Returns {duration_s, file_size}."""
    import base64, os, subprocess
    from doubao_tts_batch import (
        synthesize_segment, resolve_voice, get_emotion_params,
        pause_markers_to_punctuation,
    )
    api_key = os.environ.get("MODEL_SPEECH_API_KEY")
    if not api_key:
        raise RuntimeError("MODEL_SPEECH_API_KEY not set for Doubao fallback")

    voice = resolve_voice("default_female")
    emotion = seg.get("emotion", seg.get("emotion_arc", "shock"))
    text = seg.get("voiceover_pause_markers", seg.get("voiceover_text", ""))
    ref_audio_b64 = None
    # Load ref audio if claire is configured
    voiceover_cfg = config.get("voiceover", {})
    if voiceover_cfg.get("ref_audio") == "claire":
        ref_path = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / "_ref_audio" / "day4-gemini.mp3"
        if ref_path.exists():
            with open(ref_path, "rb") as f:
                ref_audio_b64 = base64.b64encode(f.read()).decode()

    return synthesize_segment(api_key, text, voice, emotion, output_path, ref_audio_b64=ref_audio_b64)
```

**Step 3: Test with dry-run**

Run: `cd docs/content && python3 scripts/gemini-tts-batch.py --config day7-yangmun.json --dry-run`
Expected: Shows all segments planned (dry-run doesn't hit API, so no fallback needed)

**Step 4: Commit**

```bash
git add docs/content/scripts/gemini-tts-batch.py docs/content/scripts/doubao_tts_integration.py
git commit -m "feat: Gemini TTS auto-fallback to Doubao on quota errors"
```

---

### Task 5: Update video-production-spec.md

Add story_images documentation to the Medvi spec.

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md`

**Step 1: Update Stage 1 (Script) — add story image planning**

After the segment writing rules (around line 350), add:

```markdown
#### 故事图规划（story_images）

每段铁律在写脚本时同步规划 1-2 张故事场景图。故事图不包含角色肖像，而是展现文案提到的具体画面。

| 段落 | 故事图数量 | 内容来源 |
|------|-----------|---------|
| Hook | 1-2 | 钩子中的震撼画面（如工厂机器、数据爆发） |
| 铁律段 | 2 | 铁律中的"对比画面"（如人力 vs AI） |
| CTA | 0 | 角色特写已足够 |

故事图 prompt 遵循 6 层结构，但不包含 character_anchor。
```

**Step 2: Update Stage 2 (Reference Images) — add story image rules**

After section 6.2 (around line 490), add:

```markdown
### 6.4 故事图（Story Images）

| 规则 | 值 |
|------|-----|
| 每段可有 0-3 张故事图 | JSON config 中 `story_images` 数组 |
| 故事图不包含角色锚定 | 不需要 character_anchor |
| 故事图遵循 6 层 prompt 结构 | 摄影声明 + 场景主体 + 环境 + 光影 + 构图 |
| 总图数 10-15 张/条视频 | 主图 5 张 + 故事图 5-10 张 |
| 生成工具 | `seedream-story-images.py --config {video_id}.json` |
```

**Step 3: Update Stage 3 (Video) — mention --include-stories**

Add a note to the Kling section:

```markdown
故事图视频生成：`python3 kling-gen-batch.py --config {video_id}.json --include-stories`
```

**Step 4: Update Stage 5 (Compose) — document multi-clip logic**

```markdown
### 多图段合成

当一段有多张图（主图 + 故事图）时：
- 每张图均匀分配该段的配音时长
- Kling 视频（5s）短于分配时长时循环播放（正播+倒播交替）
- 所有图硬切拼接，主图在前，故事图按顺序排列
```

**Step 5: Update Stage 4 (Voiceover) — document fallback**

```markdown
### TTS 引擎降级

| 优先级 | 引擎 | 条件 |
|--------|------|------|
| 1 | Gemini TTS (Charon) | 默认 |
| 2 | Doubao TTS (claire) | Gemini 返回 429/403 时自动降级 |

同一条视频不混用两个 TTS 引擎。
```

**Step 6: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs: add story images and TTS fallback rules to Medvi spec"
```

---

### Task 6: End-to-end dry-run verification

Verify the entire pipeline works with the new story_images config.

**Step 1: Seedream story images dry-run**

Run: `cd docs/content && python3 scripts/seedream-story-images.py --config day7-yangmun.json --dry-run`
Expected: Lists 8 story images

**Step 2: Kling story videos dry-run**

Run: `cd docs/content && python3 scripts/kling-gen-batch.py --config day7-yangmun.json --include-stories --dry-run`
Expected: Lists 13 shots (5 main + 8 story)

**Step 3: FFmpeg compose dry-run**

Run: `cd docs/content && python3 scripts/ffmpeg-compose-day1.py --config day7-yangmun.json --dry-run`
Expected: Shows all segments with audio + video status

**Step 4: Gemini TTS dry-run**

Run: `cd docs/content && python3 scripts/gemini-tts-batch.py --config day7-yangmun.json --dry-run`
Expected: Lists all segments with emotion prompts

**Step 5: Commit any final fixes**

```bash
git add -A
git commit -m "fix: final adjustments for story images pipeline"
```
