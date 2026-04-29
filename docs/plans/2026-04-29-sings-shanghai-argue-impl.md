# Sings 上海吵架段位表 — 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a 45-second duet cover video about Shanghai arguing levels using "今天你要嫁给我" melody.

**Architecture:** Update existing `city-shanghai-cover.json` config with new lyrics and visuals, then run the standard 7-stage Sings pipeline: lyrics → Suno cover → Seedream images → Kling videos → FFmpeg composite → 剪映 post.

**Tech Stack:** Suno Cover API, Seedream 4.5 (via Evolink), Kling 3.0 (via Evolink), FFmpeg, 剪映

**Design doc:** `docs/plans/2026-04-29-sings-shanghai-argue-design.md`

---

### Task 1: Update lyrics file

**Files:**
- Modify: `docs/content/assets/cover/sings-shanghai-cover-lyrics.txt`

**Step 1: Replace lyrics content**

Replace entire file with the approved 段位表 lyrics:

```
[Intro]
[Male] 你知道上海人吵架分几个段位吗
[Female] 十个段位 外地人扛不过三级

[Verse 1]
[Male] 一级"你脑子瓦特了" 外地人以为在骂人
[Female] 那是关心你懂不懂
[Male] 二级上海话开骂 语速快到像念咒
[Female] 三级弄堂阿姨开嗓 街坊全知道你欠了菜钱

[Chorus]
[Both] 上海人的嘴 段位一直在升
[Both] 吵着吵着就变成文化课了
[Male] 四级生煎小笼谁正宗 有人说上海是美食荒漠
[Female] 那是他没凌晨四点排过葱油葱的队

[Outro]
[Male] 十级 上海话快没人会说了
[Female] 你们那里吵架什么段位 来评论区比
```

**Step 2: Verify lyrics file**

Run: `cat docs/content/assets/cover/sings-shanghai-cover-lyrics.txt`
Expected: 14 lines matching above

**Step 3: Commit**

```bash
git add docs/content/assets/cover/sings-shanghai-cover-lyrics.txt
git commit -m "feat(sings): update Shanghai lyrics to 段位表 arguing levels"
```

---

### Task 2: Update config JSON

**Files:**
- Modify: `docs/content/config/city-shanghai-cover.json`

**Step 1: Update metadata fields**

Change these fields in the config:
- `video_id`: keep `"sings-shanghai-cover"` (same video slot)
- `strategy_notes`: `"上海吵架段位表对唱翻唱。用《今天你要嫁给我》旋律，歌词完全重写为上海吵架10段位。男声挑衅+女声反击。尖锐毒舌+争议槽点。"`
- `highlights`: replace with arguable points array:
  ```json
  [
    {"name": "脑子瓦特了（骂人还是关心）", "type": "controversy"},
    {"name": "上海话吵架（听不懂）", "type": "controversy"},
    {"name": "弄堂阿姨（街坊广播）", "type": "controversy"},
    {"name": "生煎vs小笼（谁正宗）", "type": "food_war"},
    {"name": "上海是美食荒漠（最大争议）", "type": "food_war"},
    {"name": "葱油饼排队（凌晨四点）", "type": "food"},
    {"name": "上海话消失（文化痛点）", "type": "culture"}
  ]
  ```
- `style`: `"cover_argue_duet"`
- `script.topic`: `"上海吵架段位表 — 10级递进争议吐槽"`
- `script.hook_type`: `"controversy_challenge"`
- `script.cta_action`: "评论区说你家乡吵架什么段位"
- `script.cta_keyword`: "你们那里吵架什么段位"

**Step 2: Update lyrics section**

Replace `lyrics.bars` array with 5 bars matching new lyrics:

```json
{
  "id": "B01",
  "beat_count": 4,
  "lines": ["[Male] 你知道上海人吵架分几个段位吗", "[Female] 十个段位 外地人扛不过三级"],
  "type": "intro",
  "segment_ref": "S01"
},
{
  "id": "B02",
  "beat_count": 4,
  "lines": ["[Male] 一级\"你脑子瓦特了\" 外地人以为在骂人", "[Female] 那是关心你懂不懂", "[Male] 二级上海话开骂 语速快到像念咒", "[Female] 三级弄堂阿姨开嗓 街坊全知道你欠了菜钱"],
  "type": "body",
  "segment_ref": "S02"
},
{
  "id": "B03",
  "beat_count": 4,
  "lines": ["[Both] 上海人的嘴 段位一直在升", "[Both] 吵着吵着就变成文化课了", "[Male] 四级生煎小笼谁正宗 有人说上海是美食荒漠", "[Female] 那是他没凌晨四点排过葱油饼的队"],
  "type": "chorus",
  "segment_ref": "S03"
},
{
  "id": "B04",
  "beat_count": 4,
  "lines": ["[Male] 十级 上海话快没人会说了", "[Female] 你们那里吵架什么段位 来评论区比"],
  "type": "outro",
  "segment_ref": "S04"
}
```

Also update `lyrics.file` to point to the updated lyrics file.

**Step 3: Update segments with new visual descriptions**

Replace `segments` array with 4 segments matching 段位表:

```json
[
  {
    "id": "S01",
    "type": "intro",
    "duration_sec": 6,
    "shot_type": "wide",
    "emotion": "playful",
    "visual_description": "杨梦在外滩，俏皮开场，'你知道上海人吵架分几个段位吗'",
    "reference_prompt": "Casual travel snapshot, portrait orientation, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing a trendy blazer over a graphic tee and jeans, standing on the Bund promenade with Pudong skyline behind her, arms crossed with a smug knowing look, golden hour warm light, wind gently moving her hair, a few flyaway hairs, uneven skin tone, natural shine on nose, visible pores, slight asymmetry, candid moment, slightly imperfect framing, natural color temperature, NOT retouched, NOT posed, vertical composition 9:16",
    "motion_prompt": "arms crossed confidently, looking directly at camera with a smirk, wind in hair, slight head tilt",
    "lyrics_refs": ["B01"],
    "reference_file": "sings-shanghai-cover/S01-playful.png"
  },
  {
    "id": "S02",
    "type": "body",
    "duration_sec": 10,
    "shot_type": "medium",
    "emotion": "exaggerated",
    "visual_description": "杨梦在老石库门弄堂里，夸张吵架表情，模拟上海话吵架场景",
    "reference_prompt": "Casual snapshot, portrait orientation, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing a casual hoodie, standing in a narrow Shanghai shikumen alley, red brick walls and stone archway, pointing finger aggressively as if mid-argument, exaggerated facial expression with wide eyes and open mouth, arms gesturing wildly, laundry hanging on bamboo poles overhead, messy uncommed hair, uneven skin tone, natural daylight, visible pores, slight asymmetry, candid unposed moment, slightly imperfect framing, NOT retouched, NOT posed, vertical composition 9:16",
    "motion_prompt": "pointing finger, exaggerated arguing gesture, animated hand movements, shifting weight between feet",
    "lyrics_refs": ["B02"],
    "reference_file": "sings-shanghai-cover/S02-surprised.png"
  },
  {
    "id": "S03",
    "type": "chorus",
    "duration_sec": 12,
    "shot_type": "medium",
    "emotion": "heated",
    "visual_description": "杨梦在夜市美食街，手持生煎，激动地为上海美食辩护",
    "reference_prompt": "Casual snapshot, portrait orientation, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing a warm jacket, holding a paper bag of shengjian bao (pan-fried buns) from a street stall, standing in front of a bustling Shanghai night food street with steam and neon lights, passionate defensive expression as if proving a point, a few flyaway hairs, food grease stain on jacket sleeve, uneven skin tone, warm artificial lighting mixed with neon, visible pores, slight asymmetry, candid unposed moment, slightly imperfect framing, NOT retouched, NOT posed, vertical composition 9:16",
    "motion_prompt": "holding up food bag triumphantly, gesturing with one hand while holding food, passionate expression, steam rising from food stall behind",
    "lyrics_refs": ["B03"],
    "reference_file": "sings-shanghai-cover/S03-excited.png"
  },
  {
    "id": "S04",
    "type": "outro",
    "duration_sec": 6,
    "shot_type": "close-up",
    "emotion": "challenging",
    "visual_description": "杨梦特写，直接对镜头挑衅，'你们那里吵架什么段位'",
    "reference_prompt": "Casual snapshot, portrait orientation, close-up portrait of a young Chinese woman, mid-twenties, round face, short black bob haircut, looking directly into camera with a challenging competitive smirk, one eyebrow slightly raised, finger pointing at viewer, blurred Shanghai street background with passing pedestrians, soft natural evening light, a few flyaway hairs, uneven skin tone, natural shine on nose, visible pores, slight asymmetry, candid unposed moment, slightly imperfect framing, NOT retouched, NOT posed, upper body filling frame, vertical composition 9:16",
    "motion_prompt": "pointing finger directly at camera, raising eyebrow, challenging smirk, leaning slightly forward",
    "lyrics_refs": ["B04"],
    "reference_file": "sings-shanghai-cover/S04-warm.png"
  }
]
```

**Step 4: Update publishing fields**

Update `publishing.title_candidates`:
```json
[
  "上海人吵架10个段位 你扛到几级",
  "外地人扛不过上海人吵架三级",
  "上海是美食荒漠？吵给你看"
]
```

Update `publishing.tags`:
```json
["上海吵架", "上海冷知识", "段位表", "美食荒漠", "上海话", "城市争议"]
```

**Step 5: Validate JSON**

Run: `python3 -c "import json; json.load(open('docs/content/config/city-shanghai-cover.json'))"`
Expected: no error

**Step 6: Commit**

```bash
git add docs/content/config/city-shanghai-cover.json
git commit -m "feat(sings): update Shanghai config to 段位表 argue duet format"
```

---

### Task 3: Generate Suno Cover audio

**Prerequisites:** `source docs/content/.env` (SUNO_API_KEY must be set)

**Files:**
- Input: `docs/content/assets/cover/今天你要嫁给我_45s.mp3` (reference audio)
- Input: `docs/content/assets/cover/sings-shanghai-cover-lyrics.txt` (new lyrics)
- Output: `docs/content/assets/cover/sings-shanghai-cover_v2.mp3`

**Step 1: Run Suno cover generation**

```bash
cd docs/content/scripts
source ../.env
python3 suno-cover-demo.py \
  --audio ../assets/cover/今天你要嫁给我_45s.mp3 \
  --lyrics ../assets/cover/sings-shanghai-cover-lyrics.txt \
  --title "上海吵架段位表" \
  --output ../assets/cover/sings-shanghai-cover_v2.mp3
```

Expected: New MP3 file generated, ~45 seconds, male+female duet with "今天你要嫁给我" melody.

**Step 2: Verify output**

Run: `ffprobe docs/content/assets/cover/sings-shanghai-cover_v2.mp3`
Expected: duration ~30-60s, audio format MP3

Listen to verify:
- Male and female voices alternate correctly
- Melody matches "今天你要嫁给我"
- Lyrics are intelligible
- BPM roughly matches

**Step 3: Commit**

```bash
git add docs/content/assets/cover/sings-shanghai-cover_v2.mp3
git commit -m "feat(sings): generate Suno cover v2 段位表 argue duet"
```

---

### Task 4: Generate Seedream reference images

**Prerequisites:** `source docs/content/.env` (EVOLINK_API_KEY must be set)

**Files:**
- Input: `docs/content/config/city-shanghai-cover.json` (reference_prompt per segment)
- Output: `docs/content/assets/references/sings-shanghai-cover/S01-playful.png` through `S04-challenging.png`

**Step 1: Run Seedream batch generation**

```bash
cd docs/content/scripts
source ../.env
python3 seedream-batch.py --config ../config/city-shanghai-cover.json --dry-run
```

Expected: Shows 4 shots planned (S01-S04), each with reference_prompt. Verify prompts match new 段位表 visuals.

**Step 2: Generate images**

```bash
python3 seedream-batch.py --config ../config/city-shanghai-cover.json
```

Expected: 4 PNG images generated at 1440x2560 resolution in `docs/content/assets/references/sings-shanghai-cover/`.

Note: The existing S01-S04 files from v1 will be overwritten. If you want to keep v1, rename them first.

**Step 3: Verify images**

Run: `ls -la docs/content/assets/references/sings-shanghai-cover/`
Expected: 4 new PNG files, each ~800KB-1.5MB

Visually check each image:
- S01: Woman on Bund with smug look (not just standing there)
- S02: Woman in shikumen alley with arguing gesture
- S03: Woman with food at night market
- S04: Close-up challenging expression pointing at camera

**Step 4: Commit**

```bash
git add docs/content/assets/references/sings-shanghai-cover/
git commit -m "feat(sings): generate Seedream reference images for 段位表 Shanghai argue duet"
```

---

### Task 5: Generate Kling videos

**Prerequisites:** `source docs/content/.env` (EVOLINK_API_KEY must be set), Seedream images from Task 4

**Files:**
- Input: `docs/content/assets/references/sings-shanghai-cover/S0*.png`
- Output: `docs/content/output/sings-shanghai-cover/S01-*.mp4` through `S04-*.mp4`

**Step 1: Dry run**

```bash
cd docs/content/scripts
source ../.env
python3 kling-gen-batch.py --config ../config/city-shanghai-cover.json --dry-run
```

Expected: Shows 4 video generation tasks, each 5 seconds, using reference images from Task 4.

**Step 2: Generate videos**

```bash
python3 kling-gen-batch.py --config ../config/city-shanghai-cover.json
```

Expected: 4 MP4 files at 720x1280, 24fps, 5 seconds each.

**Step 3: Verify videos**

Run: `for f in docs/content/output/sings-shanghai-cover/S0*.mp4; do echo "$f:"; ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$f"; done`
Expected: 4 files, each ~5 seconds

Quick visual check: motion should match motion_prompt for each segment (gesturing, arguing, holding food, pointing at camera).

**Step 4: Commit**

```bash
git add docs/content/output/sings-shanghai-cover/
git commit -m "feat(sings): generate Kling videos for 段位表 Shanghai argue duet"
```

---

### Task 6: FFmpeg composite

**Prerequisites:** Suno cover audio (Task 3) + Kling videos (Task 5)

**Files:**
- Input: `docs/content/assets/cover/sings-shanghai-cover_v2.mp3`
- Input: `docs/content/output/sings-shanghai-cover/S01-*.mp4` through `S04-*.mp4`
- Output: `docs/content/output/sings-shanghai-cover/sings-shanghai-argue-rough.mp4`

**Step 1: Run FFmpeg compose**

```bash
cd docs/content/scripts
python3 ffmpeg-compose-sings.py --config ../config/city-shanghai-cover.json --dry-run
```

Check: verify it picks up v2 audio and new video clips. If the script hardcodes audio filename, may need to update config `audio` section to point to v2.

If needed, update config:
```json
"audio": {
  "cover_audio_file": "docs/content/assets/cover/sings-shanghai-cover_v2.mp3"
}
```

Then run:
```bash
python3 ffmpeg-compose-sings.py --config ../config/city-shanghai-cover.json
```

**Step 2: Verify output**

Run: `ffprobe docs/content/output/sings-shanghai-cover/sings-shanghai-argue-rough.mp4`
Expected: 1080x1920, ~30-45 seconds, H.264, audio+video synced

Quick check:
- Audio plays correctly with video
- Videos switch at appropriate times
- Total duration matches audio duration

**Step 3: Commit**

```bash
git add docs/content/output/sings-shanghai-cover/sings-shanghai-argue-rough.mp4
git commit -m "feat(sings): FFmpeg rough composite for 段位表 Shanghai argue duet"
```

---

### Task 7: 剪映后期 (Manual)

**This is a manual task — no script can automate it.**

**Step 1: Open rough cut in 剪映**

Import `sings-shanghai-argue-rough.mp4` into 剪映.

**Step 2: Add subtitles**

- Use 剪映 auto-subtitle feature on the audio track
- Verify each line matches lyrics exactly
- Style: white text with colored highlight for key words (段位 numbers, 争议关键词)
- Position: lower third, not blocking visual focus

**Key subtitle emphasis points:**
- "脑子瓦特了" — highlight in yellow
- "美食荒漠" — highlight in red (biggest controversy)
- "段位一直在升" — highlight in gradient
- "上海话快没人会说了" — highlight in blue (culture sadness)
- CTA "来评论区比" — highlight in bright color

**Step 3: Add transitions**

- Between S01→S02: quick cut (matching argument escalation)
- Between S02→S03: quick cut
- Between S03→S04: slight slow-down before CTA

**Step 4: Add AI labeling watermark**

Per spec: "AI生成内容" in top-left, 3 seconds, font-size 28, opacity 0.8

**Step 5: Audio final check**

- Voice clarity: both male and female clearly audible
- No clipping or distortion
- Music bed not overpowering vocals
- Overall volume normalized

**Step 6: Export settings**

- Resolution: 1080x1920
- Frame rate: 24fps
- Codec: H.264
- Bitrate: ≥8Mbps
- Format: MP4

**Step 7: Save final export**

Save to: `docs/content/output/sings-shanghai-cover/sings-shanghai-argue-final.mp4`

**Step 8: Commit**

```bash
git add docs/content/output/sings-shanghai-cover/sings-shanghai-argue-final.mp4
git commit -m "feat(sings): 剪映 final export for 段位表 Shanghai argue duet"
```

---

### Task 8: Update config status and commit

**Files:**
- Modify: `docs/content/config/city-shanghai-cover.json`

**Step 1: Update status**

Change `status` from `"script_approved"` to `"ready_for_jianying"` (after Task 6) or `"completed"` (after Task 7).

**Step 2: Final commit**

```bash
git add docs/content/config/city-shanghai-cover.json
git commit -m "docs(config): update sings-shanghai-argue status to completed"
```

---

## Execution Notes

- **API costs:** ~$0.50-0.80 total (3 Seedream images + 3 Kling videos + 1 Suno cover)
- **Time estimate:** ~30 minutes (scripts) + 15 minutes (剪映) = 45 minutes total
- **Blocking dependencies:** Tasks 3-5 are independent of each other (can run in parallel). Task 6 depends on Tasks 3+5. Task 7 depends on Task 6.
- **Risk:** Suno Cover may not perfectly preserve "今天你要嫁给我" melody. If quality is poor, try with different audio_weight (0.6-0.9 range) or different clip of the original song.
