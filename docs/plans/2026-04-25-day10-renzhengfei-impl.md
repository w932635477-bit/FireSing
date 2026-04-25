# Day10 任正非「备胎转正」实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成 Day10 任正非备胎转正视频的全部生产素材（config JSON → 参考图 → 视频 → 配音 → FFmpeg 拼接）

**Architecture:** 复用 Medvi 管线脚本（seedream-batch.py, seedream-story-images.py, kling-gen-batch.py, gemini-tts-batch.py, ffmpeg-compose-sings.py）。Day9 的 JSON 结构作为模板，替换文案/视觉/配音。

**Tech Stack:** Python 3, Evolink API (Seedream 4.5, Kling 3.0), Gemini TTS (Aoede), FFmpeg, 剪映 (手动)

**Design doc:** `docs/plans/2026-04-25-day10-renzhengfei-design.md`

---

### Task 1: Create day10-yangmun.json Config

**Files:**
- Create: `docs/content/config/day10-yangmun.json`
- Reference: `docs/content/config/day9-yangmun.json` (template)

**Step 1: Write the config JSON**

Copy Day9 structure, replace all content per design doc. Key changes:
- `video_id`: `"day10-yangmun"`
- `strategy_notes`: Day10 备胎转正 description
- `target_duration_sec`: 43
- 4 segments: S01 shock(10s), S02 tension(11s), S03 reversal(12s), S04 warm+CTA(10s)
- S01-S03 each have 2 story_images (6 total), S04 has none
- All voiceover_text, voiceover_pause_markers, subtitle_text from design doc Section 2
- All reference_prompt, motion_prompt from design doc Section 4
- Director's notes from design doc Section 3
- Publishing section with title candidates and tags from design doc Section 6

Use Day9's exact structure for voiceover, reference_images, video_generation, compositing, ai_labeling, post_production blocks (unchanged).

**Step 2: Validate JSON**

```bash
python3 -c "import json; c=json.load(open('docs/content/config/day10-yangmun.json')); assert c['video_id']=='day10-yangmun'; assert len(c['segments'])==4; assert len(c['segments'][0].get('story_images',[]))==2; print(f'OK: {len(c[\"segments\"])} segments, {sum(len(s.get(\"story_images\",[])) for s in c[\"segments\"]))} story images')"
```

Expected: `OK: 4 segments, 6 story images`

**Step 3: Validate scripts can read the config**

```bash
cd docs/content/scripts
python3 -c "
from pathlib import Path
import sys, json
from seedream_batch import load_shots_from_config
from seedream_story_images import load_story_images
from kling_gen_batch import load_shots

cfg = Path('../../config/day10-yangmun.json')
sd = load_shots_from_config(cfg)
si = load_story_images(cfg)
kl = load_shots(cfg)

print(f'Seedream main: {len(sd)} shots')
print(f'Story images: {len(si)} shots')
print(f'Kling: {len(kl)} shots')
"
```

Expected: 4 Seedream main, 6 story images, 4 Kling.

**Step 4: Commit**

```bash
git add docs/content/config/day10-yangmun.json
git commit -m "feat: Day10 任正非备胎转正 config JSON"
```

---

### Task 2: Generate Seedream Reference Images (4 main shots)

**Files:**
- Use: `docs/content/scripts/seedream-batch.py`
- Config: `docs/content/config/day10-yangmun.json`
- Output: `docs/content/assets/references/day10-yangmun/S01-shock.png`, `S02-tension.png`, `S03-reversal.png`, `S04-warm.png`

**Prerequisites:** Task 1 complete.

**Step 1: Source API keys**

```bash
source docs/content/.env
```

**Step 2: Dry-run**

```bash
python3 docs/content/scripts/seedream-batch.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 4 planned generations (S01-S04) with prompt previews.

**Step 3: Generate (live)**

```bash
python3 docs/content/scripts/seedream-batch.py --config docs/content/config/day10-yangmun.json
```

Expected: Generates 4 PNG files. Takes ~2-4 minutes (Seedream API).

**Step 4: Verify output**

```bash
ls -la docs/content/assets/references/day10-yangmun/*.png
```

Expected: 4 main reference images (S01-shock, S02-tension, S03-reversal, S04-warm). Each ~1-3MB PNG.

**Step 5: Commit**

```bash
git add docs/content/assets/references/day10-yangmun/
git commit -m "feat: Day10 main reference images (4 shots)"
```

---

### Task 3: Generate Seedream Story Images (6 story shots)

**Files:**
- Use: `docs/content/scripts/seedream-story-images.py`
- Config: `docs/content/config/day10-yangmun.json`
- Output: `docs/content/assets/references/day10-yangmun/S01-01.png`, `S01-02.png`, `S02-01.png`, `S02-02.png`, `S03-01.png`, `S03-02.png`

**Step 1: Dry-run**

```bash
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 6 planned story image generations.

**Step 2: Generate (live)**

```bash
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day10-yangmun.json
```

Expected: Generates 6 story PNG files.

**Step 3: Verify output**

```bash
ls -la docs/content/assets/references/day10-yangmun/S*.png | wc -l
```

Expected: 10 files total (4 main + 6 story).

**Step 4: Commit**

```bash
git add docs/content/assets/references/day10-yangmun/
git commit -m "feat: Day10 story reference images (6 shots)"
```

---

### Task 4: Generate Kling Videos (4 main + 6 story = 10 clips)

**Files:**
- Use: `docs/content/scripts/kling-gen-batch.py`
- Config: `docs/content/config/day10-yangmun.json`
- Input: `docs/content/assets/references/day10-yangmun/*.png`
- Output: `docs/content/output/day10-yangmun/`

**Prerequisites:** Tasks 2+3 complete (all reference images exist).

**Step 1: Verify reference images**

```bash
ls docs/content/assets/references/day10-yangmun/*.png | wc -l
```

Expected: 10 PNG files.

**Step 2: Dry-run main shots**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 4 planned video generations.

**Step 3: Generate main shot videos**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day10-yangmun.json
```

Expected: 4 x 5-second video clips.

**Step 4: Generate story shot videos**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day10-yangmun.json --include-stories
```

Expected: 6 additional 5-second story video clips.

**Step 5: Verify output**

```bash
ls -la docs/content/output/day10-yangmun/*.mp4 | wc -l
for f in docs/content/output/day10-yangmun/*.mp4; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")
  echo "$(basename $f): ${dur}s"
done
```

Expected: 10 video files, each ~5s.

**Step 6: Commit**

```bash
git add docs/content/output/day10-yangmun/
git commit -m "feat: Day10 Kling video clips (10 clips)"
```

---

### Task 5: Generate Gemini TTS Voiceover (4 segments)

**Files:**
- Use: `docs/content/scripts/gemini-tts-batch.py`
- Config: `docs/content/config/day10-yangmun.json`
- Output: `docs/content/assets/voiceover/day10-yangmun/`

**Step 1: Dry-run**

```bash
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 4 planned TTS generations (S01-S04) with text previews.

**Step 2: Generate (live)**

```bash
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day10-yangmun.json
```

Expected: Generates 4 MP3 files. Takes ~1-2 minutes.

**Step 3: Verify output**

```bash
ls -la docs/content/assets/voiceover/day10-yangmun/*.mp3
for f in docs/content/assets/voiceover/day10-yangmun/*.mp3; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")
  echo "$(basename $f): ${dur}s"
done
```

Expected: 4 MP3 files. Total duration should be ~40-46s (near the 43s target).

**Step 4: If Gemini fails, fallback to Doubao**

```bash
python3 docs/content/scripts/doubao-tts-batch.py --config docs/content/config/day10-yangmun.json
```

**Step 5: Commit**

```bash
git add docs/content/assets/voiceover/day10-yangmun/
git commit -m "feat: Day10 Gemini TTS voiceover (4 segments)"
```

---

### Task 6: FFmpeg Compose Day10 Video

**Files:**
- Use: `docs/content/scripts/ffmpeg-compose-sings.py`
- Config: `docs/content/config/day10-yangmun.json`
- Input: Kling videos + TTS audio
- Output: `docs/content/output/day10-yangmun-sings.mp4`

**Prerequisites:** Tasks 4+5 complete.

**Step 1: Verify all inputs exist**

```bash
echo "=== Video clips ==="
ls docs/content/output/day10-yangmun/*.mp4 | wc -l
echo "=== Audio files ==="
ls docs/content/assets/voiceover/day10-yangmun/*.mp3 | wc -l
```

Expected: 10 video clips + 4 audio files.

**Step 2: Dry-run compose**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/day10-yangmun.json \
  --dry-run
```

Expected: Shows clip plan with timing.

**Step 3: Compose (live)**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/day10-yangmun.json
```

Expected: Produces `docs/content/output/day10-yangmun-sings.mp4`.

**Step 4: Verify output**

```bash
ffprobe -v quiet -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 docs/content/output/day10-yangmun-sings.mp4
```

Expected: Resolution 720x1280, duration ~43s.

**Step 5: Commit**

```bash
git add docs/content/output/day10-yangmun-sings.mp4
git commit -m "feat: compose Day10 video (FFmpeg)"
```

---

### Task 7: CapCut Post-Production (Manual)

**Files:**
- Input: `docs/content/output/day10-yangmun-sings.mp4`

**Manual steps in 剪映:**

1. Import `day10-yangmun-sings.mp4`
2. Add KTV-style dynamic lyrics subtitles (sync to Aoede voiceover)
3. Add text cards for key quotes: "所有备胎一夜转正" / "没有伤痕累累哪来皮糙肉厚"
4. Add transitions between segments (optional)
5. Add "AI生成内容" watermark label (3 seconds, top-left)
6. Color grade: S01 cold → S02 warm amber → S03 split warm-cold → S04 warm golden
7. Export: 1080x1920, 24fps, H.264

**Note:** Manual step, no code to write.

---

### Task 8: Generate Douyin Upload Copy

**Files:**
- Create: inline (no file needed)

**Douyin 文案:**

**推荐标题:** 备胎转正那天 全世界都安静了

**文案:**
十年没有名字，没有人鼓掌，没有人看见。但它一直在那里。你的备胎准备了几年？

#任正非 #华为 #备胎 #芯片 #海思 #逆袭 #自强

**备选标题:**
1. 被制裁那天 任正非什么也没说
2. 十年没有名字 但它一直在那里

**发布时间:** 12:00 或 18:00

---

### Task Summary

| Task | Description | Type | Est. Time |
|------|-------------|------|-----------|
| 1 | Create day10-yangmun.json config | config | 10 min |
| 2 | Generate Seedream main reference images (4) | API call | 5 min |
| 3 | Generate Seedream story images (6) | API call | 5 min |
| 4 | Generate Kling videos (10 clips) | API call | 10 min |
| 5 | Generate Gemini TTS voiceover (4 segments) | API call | 3 min |
| 6 | FFmpeg compose video | pipeline | 3 min |
| 7 | CapCut post-production | manual | 15-30 min |
| 8 | Generate upload copy | copywriting | 2 min |
