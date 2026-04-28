# Day12 马斯克被赶出门 — 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute Day12 Medvi v2 production pipeline: 3 Seedream story images → 3 Kling story videos → 4 Gemini TTS voiceovers. Deliver all assets for 剪映 manual compositing.

**Architecture:** Config-driven pipeline. Each script reads `docs/content/config/day12-yangmun.json`, calls external APIs (Evolink for Seedream/Kling, Google for Gemini TTS), saves outputs to standard directories.

**Tech Stack:** Python 3 scripts (urllib, no external deps), Evolink API (Seedream 4.5 + Kling 3.0), Google Gemini 3.1 Flash TTS (Aoede voice)

---

### Task 1: Create reference image directories + verify yangmun clip library

**Files:**
- Create directory: `docs/content/assets/references/day12-yangmun/` (auto-created by script)

**Step 1: Verify required yangmun clips exist**

The config references these clips for 剪映 compositing:
- `day5-yangmun/S01-shock.mp4`
- `day5-yangmun/S02-determined.mp4`
- `day6-yangmun/S03.mp4`
- `day5-yangmun/S05-warm.mp4`

Run:
```bash
for f in day5-yangmun/S01-shock.mp4 day5-yangmun/S02-determined.mp4 day6-yangmun/S03.mp4 day5-yangmun/S05-warm.mp4; do
  if [ -f "docs/content/output/$f" ]; then
    echo "OK: $f ($(du -h "docs/content/output/$f" | cut -f1))"
  else
    echo "MISSING: $f"
  fi
done
```
Expected: all 4 files OK.

**Step 2: Verify config file loads correctly**

Run:
```bash
source docs/content/.env
python3 -c "
import json
with open('docs/content/config/day12-yangmun.json') as f:
    c = json.load(f)
print(f'video_id: {c[\"video_id\"]}')
print(f'workflow: v{c[\"global\"][\"workflow_version\"]}')
stories = []
for s in c['segments']:
    for img in s.get('story_images', []):
        stories.append(f'{img[\"id\"]}: {img[\"reference_file\"]}')
print(f'Story images: {len(stories)}')
for s in stories:
    print(f'  {s}')
print(f'Segments: {len(c[\"segments\"])}')
print(f'Voice: {c[\"voiceover\"][\"voice\"]}')
"
```
Expected: video_id=day12-yangmun, workflow=v2.0, 3 story images, 4 segments, voice=Aoede.

---

### Task 2: Generate 3 Seedream story images

**Files:**
- Read: `docs/content/config/day12-yangmun.json`
- Write: `docs/content/assets/references/day12-yangmun/S01-01.png`
- Write: `docs/content/assets/references/day12-yangmun/S02-01.png`
- Write: `docs/content/assets/references/day12-yangmun/S03-01.png`

**Step 1: Dry run to verify prompts**

Run:
```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day12-yangmun.json --dry-run
```
Expected: Shows 3 story images (S01-01, S02-01, S03-01) with prompts. Est. cost: $0.09.

**Step 2: Generate images**

Run:
```bash
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day12-yangmun.json
```
Expected: 3 PNG files saved to `docs/content/assets/references/day12-yangmun/`. Each ~200-500KB. Takes ~2-5 minutes (API polling with 5s intervals, 300s timeout per image).

**Step 3: Verify outputs**

Run:
```bash
ls -lh docs/content/assets/references/day12-yangmun/
```
Expected: 3 PNG files (S01-01.png, S02-01.png, S03-01.png), each > 100KB.

---

### Task 3: Generate 3 Kling story videos

**Depends on:** Task 2 (needs reference images)

**Files:**
- Read: `docs/content/config/day12-yangmun.json`
- Read: `docs/content/assets/references/day12-yangmun/S01-01.png`
- Read: `docs/content/assets/references/day12-yangmun/S02-01.png`
- Read: `docs/content/assets/references/day12-yangmun/S03-01.png`
- Write: `docs/content/output/day12-yangmun/S01-01.mp4`
- Write: `docs/content/output/day12-yangmun/S02-01.mp4`
- Write: `docs/content/output/day12-yangmun/S03-01.mp4`

**Step 1: Dry run to verify shots**

Run:
```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day12-yangmun.json --include-stories --dry-run
```
Expected: Shows 3 story shots only (no character shots since v2 has no reference_prompt). Each 5s, 720p.

**Step 2: Generate videos**

Run:
```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day12-yangmun.json --include-stories
```
Expected: 3 MP4 files saved to `docs/content/output/day12-yangmun/`. Each ~3-8MB, 720x1280, 5s. Takes ~3-8 minutes (API polling with 5s intervals).

**Step 3: Verify outputs**

Run:
```bash
ls -lh docs/content/output/day12-yangmun/
for f in docs/content/output/day12-yangmun/*.mp4; do
  echo "$f: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)s"
done
```
Expected: 3 MP4 files, each ~5.0s duration.

---

### Task 4: Generate 4 TTS voiceovers

**Files:**
- Read: `docs/content/config/day12-yangmun.json`
- Write: `docs/content/output/day12-yangmun/S01.mp3`
- Write: `docs/content/output/day12-yangmun/S02.mp3`
- Write: `docs/content/output/day12-yangmun/S03.mp3`
- Write: `docs/content/output/day12-yangmun/S04.mp3`

**Step 1: Dry run to verify segments**

Run:
```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day12-yangmun.json --dry-run
```
Expected: Shows 4 segments (S01-S04) with text preview. Voice: Aoede.

**Step 2: Generate voiceovers**

Run:
```bash
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day12-yangmun.json
```
Expected: 4 MP3 files saved to `docs/content/output/day12-yangmun/`. Takes ~2-4 minutes (25s delay between API calls to avoid rate limits).

**Step 3: Verify outputs**

Run:
```bash
ls -lh docs/content/output/day12-yangmun/*.mp3
for f in docs/content/output/day12-yangmun/S0*.mp3; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  echo "$f: ${dur}s"
done
```
Expected: 4 MP3 files. Total duration ~45-55s:
- S01: ~12s
- S02: ~14s
- S03: ~14s
- S04: ~10s

---

### Task 5: Final asset inventory + open for 剪映

**Depends on:** Tasks 2, 3, 4

**Step 1: List all Day12 assets**

Run:
```bash
echo "=== Story Images (Seedream) ==="
ls -lh docs/content/assets/references/day12-yangmun/

echo ""
echo "=== Story Videos (Kling) ==="
ls -lh docs/content/output/day12-yangmun/*-*.mp4 2>/dev/null

echo ""
echo "=== TTS Voiceovers ==="
ls -lh docs/content/output/day12-yangmun/S0*.mp3 2>/dev/null

echo ""
echo "=== Yangmun Clips (素材库) ==="
for f in day5-yangmun/S01-shock.mp4 day5-yangmun/S02-determined.mp4 day6-yangmun/S03.mp4 day5-yangmun/S05-warm.mp4; do
  echo "  $f"
done

echo ""
echo "=== Total Duration ==="
total=0
for f in docs/content/output/day12-yangmun/S0*.mp3; do
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  total=$(echo "$total + $d" | bc)
done
echo "TTS total: ${total}s"
```

**Step 2: Open output folder in Finder for 剪映**

Run:
```bash
open docs/content/output/day12-yangmun/
open docs/content/assets/references/day12-yangmun/
```

**Step 3: Print 剪映混剪顺序 for reference**

```
杨梦(shock/S01-shock.mp4) → 故事视频(S01-01.mp4) → TTS(S01.mp3)
杨梦(tension/S02-determined.mp4) → 故事视频(S02-01.mp4) → TTS(S02.mp3)
杨梦(reversal/S03.mp4) → 故事视频(S03-01.mp4) → TTS(S03.mp3)
杨梦(warm/S05-warm.mp4) → TTS(S04.mp3) + 字幕"你还没有死"
```

**Step 4: Commit generated assets**

```bash
git add docs/content/assets/references/day12-yangmun/
git add docs/content/output/day12-yangmun/
git commit -m "feat: Day12 素材生成完成（3张Seedream图+3个Kling视频+4段TTS配音）"
```

---

## Parallelization

Tasks 2, 3, 4 can partially overlap:
- **Task 2** (Seedream) must complete before **Task 3** (Kling, which needs the images)
- **Task 4** (TTS) is independent — can run in parallel with Task 2

Recommended execution order:
```
Task 1 (verify) → Task 2 (Seedream) + Task 4 (TTS) in parallel → Task 3 (Kling) → Task 5 (inventory)
```
