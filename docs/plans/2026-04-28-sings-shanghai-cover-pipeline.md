# Sings Shanghai Cover Production Pipeline

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate the complete "今天你才知道上海" cover video: Suno Cover audio + Kling videos (from existing Seedream images) + FFmpeg concatenation.

**Architecture:** Three-stage pipeline: (1) Suno Cover API generates duet cover audio from original song + rewritten lyrics, (2) Kling 3.0 generates 4 video clips from existing Seedream reference images, (3) FFmpeg merges audio + video into final output for 剪映 post-production.

**Tech Stack:** Suno Cover API (V4_5), Kling 3.0 (Evolink), FFmpeg, Python 3

---

## Pre-flight: Fix Config Reference Paths

The config `city-shanghai-cover.json` has empty `reference_file` for all 4 segments. Kling script requires exact paths to find reference images. The Seedream images already exist at `docs/content/assets/references/sings-shanghai-cover/`.

**Files:**
- Modify: `docs/content/config/city-shanghai-cover.json` (segments S01-S04, add `reference_file`)

**Step 1: Update reference_file for each segment**

Set `reference_file` in each segment to point to the existing Seedream images:

```json
// S01: "reference_file": "sings-shanghai-cover/S01-playful.png"
// S02: "reference_file": "sings-shanghai-cover/S02-surprised.png"
// S03: "reference_file": "sings-shanghai-cover/S03-excited.png"
// S04: "reference_file": "sings-shanghai-cover/S04-warm.png"
```

**Step 2: Verify Kling dry-run finds all images**

Run: `source docs/content/.env && python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/city-shanghai-cover.json --dry-run`
Expected: All 4 shots show "found" status

**Step 3: Commit**

```bash
git add docs/content/config/city-shanghai-cover.json
git commit -m "fix: add reference_file paths to shanghai cover config for Kling"
```

---

## Task 1: Generate Cover Audio via Suno

**Files:**
- Input: `docs/content/assets/cover/今天你要嫁给我_original.mp3` (292s, 8.4MB)
- Input: `docs/content/assets/cover/sings-shanghai-cover-lyrics.txt`
- Script: `docs/content/scripts/suno-cover-demo.py`
- Output: `docs/content/assets/cover/sings-shanghai-cover_v{1,2}.mp3`

**Step 1: Run Suno Cover generation**

The script needs custom args for Shanghai cover (defaults are for 上弦月):

```bash
source docs/content/.env && \
python3 docs/content/scripts/suno-cover-demo.py \
  --audio "docs/content/assets/cover/今天你要嫁给我_original.mp3" \
  --lyrics "docs/content/assets/cover/sings-shanghai-cover-lyrics.txt" \
  --title "今天你才知道上海" \
  --style "Duet (Alternating). Female lead is airy and playful. Male lead is grounded and warm. Clear turn-taking each line. One shared hook in chorus only. sweet Chinese pop duet, mid-tempo, catchy, playful, romantic pop feel, 90 bpm" \
  --model V4_5 \
  --audio-weight 0.8
```

Expected: Script uploads original audio, submits cover generation, polls until done, downloads 2 MP3 versions.

**Step 2: Verify output files**

Run: `ls -lh docs/content/assets/cover/sings-shanghai-cover_v*.mp3`
Expected: 2 MP3 files, each ~30-60 seconds, reasonable file size

**Step 3: Check duration**

Run: `ffprobe -i docs/content/assets/cover/sings-shanghai-cover_v1.mp3 -show_entries format=duration -v quiet -of csv=p=0`
Expected: Duration should be >30s (user rejected 20s version previously)

**Step 4: Commit**

```bash
git add docs/content/assets/cover/sings-shanghai-cover_v*.mp3 docs/content/assets/cover/cover-log-*.json
git commit -m "feat: Suno Cover audio for 上海冷知识对唱 (今天你要嫁给我翻唱)"
```

---

## Task 2: Generate Kling Videos

**Files:**
- Input: `docs/content/assets/references/sings-shanghai-cover/S01-S04.png` (existing)
- Input: `docs/content/config/city-shanghai-cover.json`
- Script: `docs/content/scripts/kling-gen-batch.py`
- Output: `docs/content/output/sings-shanghai-cover/S01-S04.mp4`

**Step 1: Run Kling batch generation**

```bash
source docs/content/.env && \
python3 docs/content/scripts/kling-gen-batch.py \
  --config docs/content/config/city-shanghai-cover.json \
  --duration 5 \
  --quality 720p
```

Expected: 4 videos generated (5s each, 720p, 9:16). Cost: ~$1.58 (20s x $0.079/s)

**Step 2: Verify output files**

Run: `ls -lh docs/content/output/sings-shanghai-cover/*.mp4`
Expected: 4 MP4 files (S01.mp4, S02.mp4, S03.mp4, S04.mp4), each ~2-5MB

**Step 3: Commit**

```bash
git add docs/content/output/sings-shanghai-cover/
git commit -m "feat: Kling videos for sings-shanghai-cover (4 segments, 5s each)"
```

---

## Task 3: FFmpeg Concatenation

**Files:**
- Input: `docs/content/output/sings-shanghai-cover/S01-S04.mp4`
- Input: `docs/content/assets/cover/sings-shanghai-cover_v1.mp3` (or user's preferred version)
- Output: `docs/content/output/sings-shanghai-cover/sings-shanghai-cover-final.mp4`

**Step 1: Create FFmpeg concat file**

Create a temp concat list pointing to the 4 video clips in order:

```bash
cat > /tmp/shanghai-concat.txt << 'EOF'
file 'S01.mp4'
file 'S02.mp4'
file 'S03.mp4'
file 'S04.mp4'
EOF
```

**Step 2: Concatenate video clips and merge with cover audio**

The video total is 20s (4 x 5s). The cover audio may be longer. We trim audio to match video length:

```bash
OUTPUT_DIR="docs/content/output/sings-shanghai-cover"
AUDIO="docs/content/assets/cover/sings-shanghai-cover_v1.mp3"

ffmpeg -y \
  -f concat -safe 0 -i /tmp/shanghai-concat.txt \
  -i "$AUDIO" \
  -c:v libx264 -c:a aac -b:a 192k \
  -shortest \
  -movflags +faststart \
  "$OUTPUT_DIR/sings-shanghai-cover-final.mp4"
```

**Step 3: Verify final output**

Run: `ffprobe -i docs/content/output/sings-shanghai-cover/sings-shanghai-cover-final.mp4 -show_format -show_streams 2>&1 | grep -E "duration|codec_name|width|height"`

Expected: ~20s duration, h264 video 720x1280, aac audio

**Step 4: Commit**

```bash
git add docs/content/output/sings-shanghai-cover/sings-shanghai-cover-final.mp4
git commit -m "feat: FFmpeg concat sings-shanghai-cover final video (20s)"
```

---

## Task 4: 剪映后期 (Manual)

After FFmpeg output is ready, the user manually handles in 剪映:
- Add subtitles (from lyrics)
- Add transitions between clips
- Add AI watermark "AI生成内容" (top-left, 3s, font-size 28, opacity 0.8)
- Add title card "今天你才知道上海"
- Export final version

No script needed for this step.
