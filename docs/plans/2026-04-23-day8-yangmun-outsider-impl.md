# Day 8 Yangmun "不合群才是超能力" Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Generate the complete day8-yangmun.json config and run the Medvi production pipeline (reference images → voiceover → video → compositing).

**Architecture:** JSON-driven pipeline. The config file is the single source of truth. Each batch script reads it to generate assets. Follow Day 7's exact config structure.

**Tech Stack:** Seedream 4.5 (reference images via Evolink), Doubao TTS (claire voice), Kling v3 (video via Evolink), FFmpeg (compositing), 剪映 (post-production).

**Pre-requisite:** `source docs/content/.env` before running any batch script.

---

### Task 1: Create day8-yangmun.json config

**Files:**
- Create: `docs/content/config/day8-yangmun.json`

**Step 1: Create the config file**

Write `docs/content/config/day8-yangmun.json` with the following content. This is derived from day7-yangmun.json with Day 8 specific content.

```json
{
  "video_id": "day8-yangmun",
  "version": "4.0",
  "created": "2026-04-23",
  "status": "script_draft",
  "strategy": "yangmun-emotion-ip",
  "strategy_notes": "Day8 不合群才是超能力。铁律三段式。流量优先策略，震撼→紧张→反转→赋能→参与。全部素材重新生成，不复用Day4/5/6/7，防平台查重",

  "global": {
    "target_duration_sec": 41,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": 89102,
    "style": "yangmun_minimalist_portrait",
    "color_temperature": "warm",
    "accent_color": "#c9a96e"
  },

  "script": {
    "topic": "不合群才是你的超能力",
    "hook_type": "personal_attack_plus_celebrity_quote",
    "cta_action": "评论",
    "cta_keyword": "你最不合群的那件事",
    "anti_ad_measures": [
      "不提AI Agent、代运营、智能体等业务关键词",
      "不引导私信、领取、关注",
      "CTA用开放式问题，激发评论互动",
      "聚焦名人的故事和情绪，不卖任何东西"
    ]
  },

  "character_anchor": "a young Chinese woman in her late 20s, round face, short black bob haircut with straight bangs just above eyebrows, wearing a simple cream-colored linen shirt with a small collar",

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 7,
      "shot_type": "close-up",
      "emotion_arc": "shock",
      "reference_file": "day8-yangmun/S01-shock.png",
      "reference_prompt": "35mm documentary film still grainy imperfect focus, a young Chinese woman in her late 20s round face short black bob haircut with straight bangs just above eyebrows wearing a simple cream-colored linen shirt with a small collar, confrontational direct gaze with raised chin lips pressed tight one eyebrow slightly raised in challenge, dark charcoal background with no visible objects, cold directional side light from the left creating strong chiaroscuro effect with deep shadows on the right side of her face, visible film grain especially in shadow areas desaturated cool tones, subject in lower two-thirds, vertical composition 9:16",
      "motion_prompt": "slow zoom in, subtle head tilt, dramatic light shift",
      "voiceover_text": "你装合群，装了多少年？马斯克说过：我的童年非常孤独。他小学被推下楼梯打到住院。但不合群的人，看到的和你不一样。",
      "voiceover_pause_markers": "你装合群<#0.2#>装了多少年？<#0.5#>马斯克说过<#0.2#>我的童年非常孤独。<#0.3#>他小学被推下楼梯打到住院。<#0.5#>但不合群的人<#0.2#>看到的和你不一样。",
      "subtitle_text": "你装合群 装了多少年？",
      "story_images": [
        {
          "id": "S01-01",
          "trigger_text": "推下楼梯打到住院",
          "reference_prompt": "35mm documentary film still grainy imperfect focus, a young boy lying hurt at the bottom of concrete school stairs, scattered books and a torn backpack beside him, other children's blurred feet walking past without stopping, cold harsh fluorescent school corridor light from above creating clinical shadows, muted desaturated tones with slight blue cast, visible film grain, subject lower third, vertical composition 9:16",
          "motion_prompt": "slow zoom out from boy, subtle ambient dust particles in light"
        },
        {
          "id": "S01-02",
          "trigger_text": "不合群的人看到的",
          "reference_prompt": "shot on Canon 5D Mark IV 24mm f/2.0 Kodak Portra 400, one person standing alone on a rooftop at dusk looking out at a vast cityscape where one building glows warm amber while all others are dark silhouettes, golden hour light from the horizon casting long shadows, the solitary figure illuminated from behind, visible film grain, subject lower third, vertical composition 9:16",
          "motion_prompt": "slow push in on figure, city lights beginning to twinkle"
        }
      ]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 10,
      "shot_type": "medium",
      "emotion_arc": "tension",
      "reference_file": "day8-yangmun/S02-tension.png",
      "reference_prompt": "shot on Canon 5D Mark IV 50mm f/1.4 Kodak Portra 400, a young Chinese woman in her late 20s round face short black bob haircut with straight bangs just above eyebrows wearing a simple cream-colored linen shirt with a small collar, exhausted strained expression one hand touching her temple eyes half-closed with visible fatigue lines around the eyes jaw slightly slack, blurred restaurant background with out-of-focus warm string lights and wine glasses, warm but suffocating amber overhead light with no escape from the glow, visible film grain especially in shadow areas, subject in lower two-thirds, vertical composition 9:16",
      "motion_prompt": "slow push in, subtle head bow, warm light flickering",
      "voiceover_text": "铁律一：你为了合群放弃了什么。马斯克从来不合群，他把别人社交的时间全用在了思考上。而你呢？笑脸、应酬、群聊、陪笑。换来一张好人卡，丢掉了你唯一的优势。",
      "voiceover_pause_markers": "铁律一<#0.3#>你为了合群放弃了什么。<#0.5#>马斯克从来不合群<#0.2#>他把别人社交的时间全用在了思考上。<#0.5#>而你呢？<#0.3#>笑脸、应酬、群聊、陪笑。<#0.5#>换来一张好人卡<#0.2#>丢掉了你唯一的优势。",
      "subtitle_text": "铁律一：你为了合群放弃了什么",
      "story_images": [
        {
          "id": "S02-01",
          "trigger_text": "笑脸应酬群聊陪笑",
          "reference_prompt": "iPhone 15 Pro photo slightly underexposed natural lighting, a dinner table seen from above with twelve people toasting with forced smiles, one person at the end of the table looking drained and disconnected staring at their phone under the table, warm restaurant pendant lights creating pools of amber light, visible film grain, subject lower two-thirds, vertical composition 9:16",
          "motion_prompt": "slow tilt from group to the disconnected person"
        },
        {
          "id": "S02-02",
          "trigger_text": "丢掉了你唯一的优势",
          "reference_prompt": "shot on Sony A7III 85mm f/1.8 available light Fuji 400H, close-up of a person's hands holding a crumpled paper with handwritten words being dropped into a wastebasket, the paper catches warm side light revealing the word unique barely visible before it falls, dark room with only a desk lamp for light, visible film grain, subject center, vertical composition 9:16",
          "motion_prompt": "slow follow the paper falling, subtle camera drift downward"
        }
      ]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 9,
      "shot_type": "medium",
      "emotion_arc": "reversal",
      "reference_file": "day8-yangmun/S03-reversal.png",
      "reference_prompt": "shot on Sony A7III 85mm f/1.8 available light Fuji 400H, a young Chinese woman in her late 20s round face short black bob haircut with straight bangs just above eyebrows wearing a simple cream-colored linen shirt with a small collar, knowing confident expression with a slight asymmetrical smile one eyebrow raised higher than the other eyes bright with quiet certainty, window with soft natural light to the right sheer white curtain partially visible, natural side light from the window on the right warm light beginning to mix with cool ambient gentle falloff, visible film grain especially in shadow areas, subject in lower two-thirds, vertical composition 9:16",
      "motion_prompt": "slow push in, subtle head turn toward light, natural light shift",
      "voiceover_text": "铁律二：孤独的人看到别人看不到的。2018年特斯拉差点破产，所有分析师都说他完了。但他看到的是燃油车的终局。不是他更聪明，是他不用同意人群的结论。",
      "voiceover_pause_markers": "铁律二<#0.3#>孤独的人看到别人看不到的。<#0.5#>2018年特斯拉差点破产<#0.2#>所有分析师都说他完了。<#0.3#>但他看到的是燃油车的终局。<#0.5#>不是他更聪明<#0.2#>是他不用同意人群的结论。",
      "subtitle_text": "铁律二：孤独的人看到别人看不到的",
      "story_images": [
        {
          "id": "S03-01",
          "trigger_text": "特斯拉差点破产",
          "reference_prompt": "35mm documentary film still grainy imperfect focus, Tesla factory parking lot in 2018 with rows of unsold Model 3 cars stretching into the distance, a single executive standing alone looking at financial charts on a clipboard, overcast grey sky with flat depressing light, visible film grain, subject lower third, vertical composition 9:16",
          "motion_prompt": "slow zoom out revealing rows of unsold cars, clouds drifting"
        },
        {
          "id": "S03-02",
          "trigger_text": "不用同意人群的结论",
          "reference_prompt": "shot on Canon 5D Mark IV 35mm f/2.0 Kodak Portra 400, one person sitting alone at a library desk surrounded by stacks of books and papers with diagrams and equations, in sharp focus while blurred behind them through a glass wall a crowd of people all moving in the same direction, warm desk lamp light on the thinker cold ambient light on the crowd, visible film grain, subject lower two-thirds, vertical composition 9:16",
          "motion_prompt": "slow rack focus from crowd to the lone thinker"
        }
      ]
    },
    {
      "id": "S04",
      "type": "body",
      "duration_sec": 10,
      "shot_type": "close-up",
      "emotion_arc": "empowerment",
      "reference_file": "day8-yangmun/S04-empowerment.png",
      "reference_prompt": "cinematic portrait 85mm f/1.4 shallow depth of field, a young Chinese woman in her late 20s round face short black bob haircut with straight bangs just above eyebrows wearing a simple cream-colored linen shirt with a small collar, fierce determined expression eyes wide open with intensity jaw set firmly chin slightly raised in defiance a hint of fire in the gaze, dark background with warm amber bokeh orbs floating behind her, warm golden front light from left creating strong catchlights in eyes and a gentle halo on hair edges, visible film grain especially in shadow areas, subject in lower two-thirds, vertical composition 9:16",
      "motion_prompt": "slow zoom in, subtle chin raise, warm light intensifying",
      "voiceover_text": "铁律三：世界是被不合群的人改变的。乔布斯被自己公司赶走，回来做了iPhone。马斯克被嘲笑20年，公司值万亿。你不敢不合群，不是你弱，是你还没找到值得你坚持的那件事。",
      "voiceover_pause_markers": "铁律三<#0.3#>世界是被不合群的人改变的。<#0.5#>乔布斯被自己公司赶走<#0.2#>回来做了iPhone。<#0.3#>马斯克被嘲笑20年<#0.2#>公司值万亿。<#0.5#>你不敢不合群<#0.2#>不是你弱<#0.2#>是你还没找到值得你坚持的那件事。",
      "subtitle_text": "铁律三：世界是被不合群的人改变的",
      "story_images": [
        {
          "id": "S04-01",
          "trigger_text": "乔布斯被赶走",
          "reference_prompt": "35mm documentary film still grainy imperfect focus, a man in a dark turtleneck walking out of a glass office building carrying a cardboard box with personal items, other employees visible through the glass watching from inside, overcast daylight creating flat cold tones, visible film grain, subject lower third, vertical composition 9:16",
          "motion_prompt": "slow follow the figure walking away, glass reflections shifting"
        },
        {
          "id": "S04-02",
          "trigger_text": "你还没找到值得坚持的事",
          "reference_prompt": "iPhone 15 Pro photo natural lighting, close-up of a person's hand holding a small flame or candle in a completely dark room, the warm golden light from the flame illuminating only the hand and a hint of determination in the person's eyes in the background, strong warm amber light with deep surrounding darkness, visible film grain, subject center, vertical composition 9:16",
          "motion_prompt": "slow push in on the flame, warm light flickering"
        }
      ]
    },
    {
      "id": "S05",
      "type": "cta",
      "duration_sec": 5,
      "shot_type": "close-up",
      "emotion_arc": "warm",
      "reference_file": "day8-yangmun/S05-warm.png",
      "reference_prompt": "shot on Canon 5D Mark IV 85mm f/1.4 Kodak Portra 400, a young Chinese woman in her late 20s round face short black bob haircut with straight bangs just above eyebrows wearing a simple cream-colored linen shirt with a small collar, warm genuine smile eyes soft relaxed slight head tilt one shoulder slightly forward in openness, soft cream beige background with out-of-focus indoor plant leaves creating organic shapes, golden hour front light from left window with long warm shadows soft fill from right, visible film grain especially in shadow areas, subject in lower two-thirds, vertical composition 9:16",
      "motion_prompt": "gentle lean forward, warm light steady, soft blink",
      "voiceover_text": "杨梦问你：评论区打出你最不合群的那件事。不合群，不是你的错，是你的开始。",
      "voiceover_pause_markers": "杨梦问你<#0.2#>评论区打出你最不合群的那件事。<#0.5#>不合群<#0.2#>不是你的错<#0.2#>是你的开始。",
      "subtitle_text": "不合群不是你的错 是你的开始"
    }
  ],

  "voiceover": {
    "engine": "doubao_tts",
    "voice": "claire",
    "ref_audio": "claire",
    "emotion": "shock",
    "sample_rate": 24000,
    "format": "mp3",
    "normalize": true,
    "director_notes": "女声克隆，全部使用 shock 情绪参数保持音色一致。S01开头'你装合群'要锐利有力，'我的童年非常孤独'压低声线，'推下楼梯打到住院'带一丝愤怒，'看到的和你不一样'上扬带悬念。S02'换来一张好人卡'自嘲语气，'丢掉了你唯一的优势'加重。S03'不是他更聪明'开始加速，'不用同意人群的结论'用力收束。S04'公司值万亿'要有力量，'不是你弱'转为温暖，'值得你坚持的那件事'放慢。S05'不是你的错，是你的开始'真诚温暖"
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "api": "evolink",
    "resolution": "1440x2560",
    "candidates_per_segment": 2,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, perfect facial symmetry, symmetric face, centered perfectly symmetrical features, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, oil painting, watermark, text, logo, oversaturated, hyperrealistic, mannequin, doll-like, flawless, magazine cover, retouched, even skin tone, poreless skin, multiple people, group shot, changing face, different person, inconsistent features, aged, child, cartoon character, hands, hand visible"
  },

  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "post_processing": {
      "trim_unstable_frames": true,
      "handheld_shake_pct": 5,
      "upscale_4k": false
    }
  },

  "compositing": {
    "engine": "ffmpeg",
    "bgm_file": "assets/bgm/ambient_warm_01.mp3",
    "bgm_volume_pct": 8,
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_script"
  },

  "ai_labeling": {
    "enabled": true,
    "watermark_text": "AI生成内容",
    "watermark_duration_sec": 3,
    "watermark_position": "top_left",
    "watermark_font_size": 28,
    "watermark_opacity": 0.8,
    "metadata_key": "comment",
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和配音"
  },

  "post_production": {
    "film_grain_intensity_pct": 8,
    "lens_glow_intensity_pct": 8,
    "saturation_adjust": 5,
    "contrast_adjust": 5,
    "sharpness_adjust": -3,
    "vignette": 0.3,
    "note": "在剪映完成，FFmpeg 只做拼接+音频合并"
  },

  "publishing": {
    "platforms": ["douyin", "xiaohongshu"],
    "title_candidates": [
      "你装合群 装了多少年",
      "马斯克从小被打到住院 但他从来没装过",
      "不合群才是你最大的超能力"
    ],
    "tags": ["马斯克", "不合群", "做自己", "认知升级", "拒绝合群", "职场"],
    "xiaohongshu_title_candidates": [
      "被这句话点醒了：不合群才是超能力",
      "马斯克从不合群，但他看到了所有人看不到的",
      "你换来一张好人卡，丢掉了你唯一的优势"
    ],
    "xiaohongshu_tags": ["马斯克", "不合群", "做自己", "认知升级", "自我提升", "拒绝合群", "孤独"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "米白亚麻衫女性角色锐利眼神，暗色背景，文字'你装合群装了多少年'"
  }
}
```

**Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('docs/content/config/day8-yangmun.json')); print('VALID')"`
Expected: `VALID`

**Step 3: Commit**

```bash
git add docs/content/config/day8-yangmun.json
git commit -m "feat: add day8-yangmun config (不合群才是超能力)"
```

---

### Task 2: Create asset directories

**Step 1: Create reference image directory**

```bash
mkdir -p docs/content/assets/references/day8-yangmun
```

**Step 2: Create voiceover directory**

```bash
mkdir -p docs/content/assets/voiceover/day8-yangmun
```

**Step 3: Verify**

```bash
ls -d docs/content/assets/references/day8-yangmun docs/content/assets/voiceover/day8-yangmun
```

Expected: Both directories listed.

---

### Task 3: Generate reference images (character portraits)

**Step 1: Source env vars**

```bash
source docs/content/.env
```

**Step 2: Run Seedream batch for character portraits (S01-S05)**

```bash
cd docs/content/scripts
python seedream-batch.py --config ../config/day8-yangmun.json
```

This generates:
- `docs/content/assets/references/day8-yangmun/S01-shock.png`
- `docs/content/assets/references/day8-yangmun/S02-tension.png`
- `docs/content/assets/references/day8-yangmun/S03-reversal.png`
- `docs/content/assets/references/day8-yangmun/S04-empowerment.png`
- `docs/content/assets/references/day8-yangmun/S05-warm.png`

**Step 3: Verify images exist**

```bash
ls -la docs/content/assets/references/day8-yangmun/S*.png
```

Expected: 5 portrait PNG files.

**Step 4: Review images**

Use Read tool on each PNG to visually verify:
- Character consistency (same face, same bob haircut, same cream shirt)
- Emotion matches the segment (shock/tension/reversal/empowerment/warm)
- Film grain present, no plastic/airbrushed look
- Vertical 9:16 composition

**Step 5: Commit**

```bash
git add docs/content/assets/references/day8-yangmun/
git commit -m "feat: generate Day 8 yangmun character reference images (Seedream 4.5)"
```

---

### Task 4: Generate story images

**Step 1: Run Seedream story images batch**

```bash
cd docs/content/scripts
python seedream-story-images.py --config ../config/day8-yangmun.json
```

This generates:
- `docs/content/assets/references/day8-yangmun/S01-01.png` (楼梯霸凌场景)
- `docs/content/assets/references/day8-yangmun/S01-02.png` (天台独处)
- `docs/content/assets/references/day8-yangmun/S02-01.png` (聚餐应酬)
- `docs/content/assets/references/day8-yangmun/S02-02.png` (丢弃独特性)
- `docs/content/assets/references/day8-yangmun/S03-01.png` (2018特斯拉)
- `docs/content/assets/references/day8-yangmun/S03-02.png` (独自思考vs人群)
- `docs/content/assets/references/day8-yangmun/S04-01.png` (乔布斯离开)
- `docs/content/assets/references/day8-yangmun/S04-02.png` (黑暗中持火)

**Step 2: Verify**

```bash
ls -la docs/content/assets/references/day8-yangmun/S*-*.*.png 2>/dev/null
```

Expected: 8 story image PNG files.

**Step 3: Review story images**

Use Read tool on each story image to verify:
- Matches the trigger_text narrative
- No character inconsistency (story images don't have yangmun, they're scene images)
- Film aesthetic maintained
- Vertical 9:16 composition

**Step 4: Commit**

```bash
git add docs/content/assets/references/day8-yangmun/
git commit -m "feat: generate Day 8 yangmun story images (8 scenes, Seedream 4.5)"
```

---

### Task 5: Generate voiceover (Doubao TTS)

**Step 1: Run Doubao TTS batch**

```bash
cd docs/content/scripts
python doubao-tts-batch.py --config ../config/day8-yangmun.json
```

This generates:
- `docs/content/assets/voiceover/day8-yangmun/S01.mp3`
- `docs/content/assets/voiceover/day8-yangmun/S02.mp3`
- `docs/content/assets/voiceover/day8-yangmun/S03.mp3`
- `docs/content/assets/voiceover/day8-yangmun/S04.mp3`
- `docs/content/assets/voiceover/day8-yangmun/S05.mp3`

**Step 2: Check durations**

```bash
for f in docs/content/assets/voiceover/day8-yangmun/S0*.mp3; do
  echo "$f: $(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f" 2>/dev/null)s"
done
```

Expected durations (approximate):
- S01: ~7s
- S02: ~10s
- S03: ~9s
- S04: ~10s
- S05: ~5s
- Total: ~41s

**Step 3: Verify audio quality**

Listen to each segment (or have user listen) to check:
- Voice consistency (all segments use claire + shock emotion)
- Director's notes reflected in delivery
- Pause markers create natural rhythm
- No voice tearing or artifacts

**Step 4: Commit**

```bash
git add docs/content/assets/voiceover/day8-yangmun/
git commit -m "feat: generate Day 8 yangmun voiceover (Doubao TTS claire)"
```

---

### Task 6: Generate video clips (Kling v3)

**Step 1: Run Kling batch with story images**

```bash
cd docs/content/scripts
python kling-gen-batch.py --config ../config/day8-yangmun.json --include-stories
```

This generates video clips for each reference image (portraits + stories).

**Step 2: Verify video files**

```bash
ls -la docs/content/assets/video/day8-yangmun/ 2>/dev/null || echo "Check script output for video paths"
```

**Step 3: Review video quality**

- Motion matches motion_prompt
- No morphing or distortion in character face
- 5s duration per clip, 720x1280 resolution
- Subtle cinematic motion, not aggressive

**Step 4: Commit**

```bash
git add docs/content/assets/video/day8-yangmun/ 2>/dev/null
git commit -m "feat: generate Day 8 yangmun video clips (Kling v3)"
```

---

### Task 7: FFmpeg compositing

**Step 1: Run FFmpeg compose**

```bash
cd docs/content/scripts
python ffmpeg-compose-day1.py --config ../config/day8-yangmun.json
```

Note: The compose script may need adjustment for Day 8's file structure. Check if it handles the day8-yangmun asset paths correctly.

**Step 2: Verify output**

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 docs/content/assets/output/day8-yangmun-composed.mp4 2>/dev/null
```

Expected: ~41s total duration.

**Step 3: Commit**

```bash
git add docs/content/assets/output/day8-yangmun*
git commit -m "feat: FFmpeg compose Day 8 yangmun (拼接+音频合并)"
```

---

### Task 8: Post-production handoff

**Step 1: Update config status**

Change `status` in day8-yangmun.json from `script_draft` to `ready_for_post_production`.

**Step 2: Commit**

```bash
git add docs/content/config/day8-yangmun.json
git commit -m "chore: update Day 8 yangmun status to ready_for_post_production"
```

**Step 3: Hand off to 剪映**

Tell user:
- Composed video is ready at `docs/content/assets/output/day8-yangmun-composed.mp4`
- 剪映 tasks: subtitles, text overlays, film grain, color grading, AI label, cover frame
- Publishing titles and tags are in the config under `publishing`

---

## Dependency Graph

```
Task 1 (config JSON)
  └→ Task 2 (directories)
       └→ Task 3 (reference images) ─── can run in parallel with ─→ Task 5 (voiceover)
            └→ Task 4 (story images)
                 └→ Task 6 (Kling video) — needs both Task 3 and Task 4 images
                      └→ Task 7 (FFmpeg compose) — needs Task 5 voiceover + Task 6 video
                           └→ Task 8 (post-production handoff)
```

Tasks 3, 4, and 5 can run in parallel once Task 2 is done. Task 6 needs Tasks 3+4. Task 7 needs Tasks 5+6.
