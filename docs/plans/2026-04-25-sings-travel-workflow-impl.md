# Sings 旅行对唱工作流统一实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成三个目标：1) 提交未跟踪文件 2) 验证新的 sings-travel-template.json 与现有脚本兼容 3) 完成重庆 pilot 视频（Kling → FFmpeg → 剪映）

**Architecture:** 复用现有管线脚本（seedream-batch.py, suno-rap-batch.py, kling-gen-batch.py, ffmpeg-compose-sings.py）。模板已重写为旅行格式，重庆 pilot 的音乐+图片已生成。

**Tech Stack:** Python 3, Evolink API (Seedream 4.5, Kling 3.0, Suno v4.5), FFmpeg, 剪映 (手动)

**Design doc:** `docs/plans/2026-04-25-sings-travel-template-design.md`

---

### Task 1: Commit Untracked Files (outfit-day2 + yangmun configs)

**Files:**
- Add: `docs/content/assets/rap/outfit-day2-meet-parents/`
- Add: `docs/content/assets/references/outfit-day2-meet-parents/`
- Add: `docs/content/config/outfit-day2-meet-parents.json`

**Step 1: Verify files exist and are valid JSON**

```bash
python3 -c "import json; json.load(open('docs/content/config/outfit-day2-meet-parents.json')); print('OK')"
ls docs/content/assets/rap/outfit-day2-meet-parents/*.mp3
ls docs/content/assets/references/outfit-day2-meet-parents/*.png
```

Expected: OK, at least 1 mp3 and 1 png.

**Step 2: Commit outfit-day2 files**

```bash
git add docs/content/assets/rap/outfit-day2-meet-parents/ docs/content/assets/references/outfit-day2-meet-parents/ docs/content/config/outfit-day2-meet-parents.json
git commit -m "feat: add outfit-day2-meet-parents assets and config (deprecated outfit series)"
```

---

### Task 2: Commit Unstaged Yangmun Config Changes

**Files:**
- Modified: `docs/content/config/day4-yangmun.json` through `day9-yangmun.json`
- Modified: `docs/content/config/outfit-day1-date.json`, `outfit-day1-interview.json`
- Modified: `docs/content/scripts/suno-rap-batch.py`

**Step 1: Review what changed**

```bash
git diff --stat
```

Expected: 9 files modified. Review each briefly.

**Step 2: Commit yangmun and script changes**

```bash
git add docs/content/config/day4-yangmun.json docs/content/config/day5-yangmun.json docs/content/config/day6-yangmun.json docs/content/config/day7-yangmun.json docs/content/config/day8-yangmun.json docs/content/config/day9-yangmun.json docs/content/config/outfit-day1-date.json docs/content/config/outfit-day1-interview.json docs/content/scripts/suno-rap-batch.py
git commit -m "chore: update yangmun configs and suno-rap-batch script"
```

---

### Task 3: Validate sings-travel-template.json with Existing Scripts

**Files:**
- Test: `docs/content/config/sings-template.json`
- Use: `docs/content/scripts/seedream-batch.py`, `docs/content/scripts/suno-rap-batch.py`

**Step 1: Validate JSON structure**

```bash
python3 -c "import json; c=json.load(open('docs/content/config/sings-template.json')); assert c['video_id']=='sings-travel-template'; assert c['series']=='sings-travel'; assert len(c['segments'])==4; assert len(c['lyrics']['bars'])==6; print(f'OK: {len(c[\"segments\"])} segments, {len(c[\"lyrics\"][\"bars\"])} bars')"
```

Expected: `OK: 4 segments, 6 bars`

**Step 2: Validate seedream-batch.py reads the template**

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'docs/content/scripts')
from seedream_batch import load_shots_from_config
shots = load_shots_from_config(Path('docs/content/config/sings-template.json'))
print(f'Loaded {len(shots)} shots:')
for s in shots:
    print(f'  {s[\"id\"]}: {s[\"output_file\"]} ({len(s[\"prompt\"])} chars)')
"
```

Expected: 4 shots (S01-S04), each with a reference_prompt. Templates with `{outfit}` and `{city}` placeholders will show as literal strings (that's OK, they get replaced when creating a real city config).

**Step 3: Validate suno-rap-batch.py reads the template**

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'docs/content/scripts')
from suno_rap_batch import bars_to_suno_lyrics
import json
c = json.load(open('docs/content/config/sings-template.json'))
lyrics = bars_to_suno_lyrics(c['lyrics']['bars'])
print(lyrics)
"
```

Expected: Lyrics with [Chorus]/[Verse]/[Outro] section markers. Lines contain `[Female]`/`[Male]`/`[Both]` placeholder tags.

**Step 4: Validate kling-gen-batch.py reads the template**

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'docs/content/scripts')
from kling_gen_batch import load_shots
shots = load_shots(Path('docs/content/config/sings-template.json'))
print(f'Loaded {len(shots)} Kling shots:')
for s in shots:
    print(f'  {s[\"id\"]}: motion={s[\"prompt\"][:50]}...')
"
```

Expected: 4 shots with motion_prompt (S01-S04).

**Step 5: Validate city-chongqing.json with scripts**

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'docs/content/scripts')
from seedream_batch import load_shots_from_config
from kling_gen_batch import load_shots
import json

cfg_path = Path('docs/content/config/city-chongqing.json')
seedream_shots = load_shots_from_config(cfg_path)
kling_shots = load_shots(cfg_path)

print(f'Seedream: {len(seedream_shots)} shots')
print(f'Kling: {len(kling_shots)} shots')

for s in seedream_shots:
    print(f'  SD {s[\"id\"]}: {s[\"output_file\"]}')
for s in kling_shots:
    print(f'  KL {s[\"id\"]}: ref={s.get(\"reference_file\", \"none\")}')
"
```

Expected: 4 Seedream shots, 4 Kling shots. city-chongqing.json has real prompts (not placeholders).

---

### Task 4: Generate Kling Videos for Chongqing Pilot

**Files:**
- Use: `docs/content/scripts/kling-gen-batch.py`
- Config: `docs/content/config/city-chongqing.json`
- Input: `docs/content/assets/references/city-chongqing/S01-S04*.png`
- Output: `docs/content/output/city-chongqing/`

**Prerequisites:** Reference images must exist from yesterday's Seedream generation.

**Step 1: Verify reference images exist**

```bash
ls -la docs/content/assets/references/city-chongqing/*.png
```

Expected: 4 PNG files (S01-playful, S02-surprised, S03-excited, S04-warm).

**Step 2: Source API keys**

```bash
source docs/content/.env
```

**Step 3: Dry-run Kling video generation**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/city-chongqing.json --dry-run
```

Expected: Shows 4 planned video generations (S01-S04), each 5s from reference image.

**Step 4: Generate Kling videos (live)**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/city-chongqing.json
```

Expected: Generates 4 x 5-second video clips. Takes ~2-4 minutes (Kling API polling).

**Step 5: Verify output**

```bash
ls -la docs/content/output/city-chongqing/*.mp4
for f in docs/content/output/city-chongqing/*.mp4; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")
  echo "$f: ${dur}s"
done
```

Expected: 4 video files, each ~5s.

**Step 6: Commit**

```bash
git add docs/content/output/city-chongqing/
git commit -m "feat: generate Kling videos for city-chongqing pilot (4 clips)"
```

---

### Task 5: FFmpeg Compose Chongqing Pilot Video

**Files:**
- Use: `docs/content/scripts/ffmpeg-compose-sings.py`
- Config: `docs/content/config/city-chongqing.json`
- Audio: `docs/content/assets/rap/city-chongqing/city-chongqing_rap_v1.mp3`
- Output: `docs/content/output/city-chongqing-sings.mp4`

**Step 1: Verify audio file exists**

```bash
ls -la docs/content/assets/rap/city-chongqing/*.mp3
dur=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 docs/content/assets/rap/city-chongqing/city-chongqing_rap_v1.mp3)
echo "Audio duration: ${dur}s"
```

Expected: Audio file exists, duration ~156s (will be trimmed to target 28s for 4 clips).

**Step 2: Dry-run FFmpeg compose**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/city-chongqing.json \
  --audio docs/content/assets/rap/city-chongqing/city-chongqing_rap_v1.mp3 \
  --dry-run
```

Expected: Shows clip plan: S01 (5s) → S02 (5s) → S03 (5s) → S04 (5s) + audio. No errors.

**Step 3: Compose video**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/city-chongqing.json \
  --audio docs/content/assets/rap/city-chongqing/city-chongqing_rap_v1.mp3
```

Expected: Produces `docs/content/output/city-chongqing-sings.mp4`.

**Step 4: Verify output**

```bash
ffprobe -v quiet -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 docs/content/output/city-chongqing-sings.mp4
```

Expected: Resolution 720x1280 or 1080x1920, duration matches audio trim.

**Step 5: Commit**

```bash
git add docs/content/output/city-chongqing-sings.mp4
git commit -m "feat: compose city-chongqing pilot video (FFmpeg)"
```

---

### Task 6: CapCut Post-Production (Manual)

**Files:**
- Input: `docs/content/output/city-chongqing-sings.mp4`

**Manual steps in 剪映:**

1. Import `city-chongqing-sings.mp4`
2. Add KTV-style dynamic lyrics subtitles (sync to Suno duet audio)
3. Add city info cards: "重庆" 城市名卡, "李子坝轻轨" / "九宫格火锅" highlight labels
4. Add transitions between segments (optional)
5. Add "AI生成内容" watermark label (3 seconds, top-left)
6. Color grade: warm tones for Chongqing scenes
7. Export: 1080x1920, 24fps, H.264

**Note:** Manual step, no code to write. This is where the video gets its final polish.

---

### Task 7: Validate Complete Pipeline with Template

**Files:**
- Use: All scripts
- Test: `docs/content/config/sings-template.json`

**Step 1: Create a test config from template (dry-run only)**

Replace placeholders in sings-template.json with test values to confirm the entire pipeline can parse it. This is a validation-only step, no generation.

```bash
python3 -c "
import json

with open('docs/content/config/sings-template.json') as f:
    template = json.load(f)

# Replace placeholders with test values
template['video_id'] = 'test-city-validation'
template['city'] = 'TestCity'
template['highlights'] = [
    {'name': 'TestSpot', 'type': 'attraction'},
    {'name': 'TestFood', 'type': 'food'}
]

# Replace prompt placeholders
for seg in template['segments']:
    seg['reference_prompt'] = seg['reference_prompt'].replace('{outfit}', 'red dress')
    seg['reference_prompt'] = seg['reference_prompt'].replace('{city}', 'TestCity')
    seg['reference_prompt'] = seg['reference_prompt'].replace('{highlightA location}', 'TestSpot')
    seg['reference_prompt'] = seg['reference_prompt'].replace('{highlightB location}', 'TestFood')

# Replace lyrics placeholders
for bar in template['lyrics']['bars']:
    bar['lines'] = ['[Female] TestCity line one', '[Male] TestCity line two']

with open('/tmp/test-city-validation.json', 'w') as f:
    json.dump(template, f, indent=2, ensure_ascii=False)

print('Test config written to /tmp/test-city-validation.json')
"
```

**Step 2: Validate all scripts can parse the test config**

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'docs/content/scripts')
from seedream_batch import load_shots_from_config
from kling_gen_batch import load_shots
from suno_rap_batch import bars_to_suno_lyrics
import json

cfg_path = Path('/tmp/test-city-validation.json')
config = json.load(open(cfg_path))

# Seedream
sd_shots = load_shots_from_config(cfg_path)
assert len(sd_shots) == 4, f'Expected 4 seedream shots, got {len(sd_shots)}'

# Kling
kl_shots = load_shots(cfg_path)
assert len(kl_shots) == 4, f'Expected 4 kling shots, got {len(kl_shots)}'

# Suno
lyrics = bars_to_suno_lyrics(config['lyrics']['bars'])
assert '[Chorus]' in lyrics
assert '[Female]' in lyrics or '[Male]' in lyrics

# Check negative prompt is present
neg = config['reference_images']['negative_prompt']
assert 'professional photography' in neg
assert 'studio quality' in neg

print('ALL VALIDATIONS PASSED')
print(f'  Seedream shots: {len(sd_shots)}')
print(f'  Kling shots: {len(kl_shots)}')
print(f'  Lyrics sections: {lyrics.count(chr(91))} bracket markers')
print(f'  Negative prompt: {len(neg)} chars, {len(neg.split(\",\"))} items')
"
```

Expected: `ALL VALIDATIONS PASSED` with 4/4/4 shots and valid lyrics/negative prompt.

**Step 3: Cleanup test file**

```bash
rm /tmp/test-city-validation.json
```

---

### Task Summary

| Task | Description | Type | Est. Time |
|------|-------------|------|-----------|
| 1 | Commit untracked outfit-day2 files | git | 1 min |
| 2 | Commit unstaged yangmun configs | git | 1 min |
| 3 | Validate template with scripts | validation | 5 min |
| 4 | Generate Kling videos (Chongqing) | API call | 5 min |
| 5 | FFmpeg compose pilot video | pipeline | 3 min |
| 6 | CapCut post-production | manual | 15-30 min |
| 7 | Validate complete pipeline | validation | 3 min |
