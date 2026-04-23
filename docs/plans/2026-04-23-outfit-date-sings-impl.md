# outfit-day1-date 实施计划 (初次约会穿搭对比对唱)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成 outfit-day1-date 小红书穿搭对比对唱短视频，从零开始走完 7 个 Stage。

**Architecture:** 从模板 JSON 填充具体歌词和 prompt，然后按顺序执行 seedream-batch → suno-rap-batch → kling-gen-batch → ffmpeg-compose-sings。最终在剪映做 A/B 分屏、KTV 歌词、投票 CTA 等后期。

**Tech Stack:** Seedream 4.5 (Evolink API), Suno v4.5 (Evolink API), Kling V3 (Evolink API), FFmpeg, 剪映

**Design Doc:** `docs/plans/2026-04-23-outfit-date-sings-design.md`

---

### Task 1: 创建 config JSON 文件

**Files:**
- Create: `docs/content/config/outfit-day1-date.json`

**Step 1: 基于 sings-template.json 创建完整 config**

从 `docs/content/config/sings-template.json` 复制模板，填充以下内容:

**video_id:** `outfit-day1-date`
**version:** `2.0`
**strategy_notes:** `小红书穿搭对比对唱第一期：初次约会穿搭。A套碎花裙+高跟(用力过猛) vs B套针织+牛仔(自然舒服)`

**global 字段:**
```json
{
  "target_duration_sec": 37,
  "max_duration_sec": 45,
  "min_duration_sec": 30,
  "resolution": "1080x1920",
  "fps": 24,
  "codec": "h264",
  "aspect_ratio": "9:16",
  "kling_seed": 12345,
  "style": "outfit_compare",
  "color_temperature": "warm_bright",
  "accent_color": "#e8a87c",
  "bg_color": "#f5e6d3"
}
```

**lyrics.bars (16 行):**
```json
[
  {"id": "B01", "beat_count": 4, "lines": ["初次约会到底怎么穿", "太用力反而让人难堪"], "rhyme": "an", "segment_ref": "S01", "type": "hook"},
  {"id": "B02", "beat_count": 4, "lines": ["A套碎花长裙细高跟", "精致是精致不像本人"], "rhyme": "en", "segment_ref": "S02", "type": "body"},
  {"id": "B03", "beat_count": 4, "lines": ["妆浓到走路不敢低头", "约会变成走红毯的秀"], "rhyme": "ou", "segment_ref": "S02", "type": "body"},
  {"id": "B04", "beat_count": 4, "lines": ["B套针织衫搭牛仔裤", "干净舒服自在不装酷"], "rhyme": "u", "segment_ref": "S03", "type": "body"},
  {"id": "B05", "beat_count": 4, "lines": ["小白鞋走哪都不紧张", "做自己就是最好的装"], "rhyme": "ang", "segment_ref": "S03", "type": "body"},
  {"id": "B06", "beat_count": 4, "lines": ["法则一 场合定基调", "约会穿太正式会吓跑"], "rhyme": "ao", "segment_ref": "S04", "type": "body"},
  {"id": "B07", "beat_count": 4, "lines": ["法则二 合身最重要", "穿得舒服才敢放开笑"], "rhyme": "ao", "segment_ref": "S04", "type": "body"},
  {"id": "B08", "beat_count": 4, "lines": ["初次约会你站A还是B", "评论区投票告诉我你的品味"], "rhyme": "ei", "segment_ref": "S05", "type": "cta"}
]
```

**lyrics.suno_tags:** 加 "fashion" 关键词
```
"catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm"
```

**script 字段:**
```json
{
  "topic": "初次约会穿搭：用力过猛 vs 自然舒服",
  "source": "原创穿搭对比",
  "hook_type": "scenario_question",
  "cta_action": "投票A/B",
  "cta_keyword": "评论区投票",
  "outfit_a": {
    "name": "碎花裙+高跟",
    "description": "navy blue floral chiffon midi dress + beige kitten heels",
    "keywords": ["碎花裙", "细高跟", "精致妆容"]
  },
  "outfit_b": {
    "name": "针织+牛仔",
    "description": "cream knit sweater + blue denim jeans + white sneakers",
    "keywords": ["针织衫", "牛仔裤", "小白鞋"]
  },
  "fashion_rules": [
    "场合定基调：约会不是走红毯，穿太正式适得其反",
    "合身最重要：舒服才能做自己，做自己才最好看"
  ],
  "anti_ad_measures": [
    "不提任何品牌或产品推荐",
    "不引导私信、领取、关注",
    "CTA用投票选择，激发评论互动",
    "聚焦穿搭逻辑和审美，不卖任何东西"
  ]
}
```

**segments (5 段):**

每个 segment 需要完整的 `reference_prompt`。所有 prompt 来自设计文档 Section 2.3，使用 7 层结构。注意 S04 是文字卡不需要 reference_prompt。

S01 (Hook):
```json
{
  "id": "S01",
  "type": "hook",
  "duration_sec": 6,
  "shot_type": "wide",
  "emotion": "playful",
  "visual_description": "杨梦 A套碎花裙全身 vs B套针织牛仔全身，咖啡馆背景",
  "reference_prompt": "Bright fashion lookbook editorial, a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a navy blue floral print chiffon midi dress with V-neckline and flutter sleeves, paired with beige suede pointed-toe kitten heels, delicate gold chain necklace, standing in a bright modern cafe with cream white walls, wooden tables, and green potted plants, hands clasped gently in front, confident but slightly nervous smile, natural daylight streaming through large windows, soft warm shadows, 5500K white balance, full-body shot, 50mm lens, model centered with negative space above, vertical composition 9:16",
  "reference_prompt_b": "Bright fashion lookbook editorial, a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream white ribbed knit sweater with relaxed fit, paired with medium blue straight-leg denim jeans and clean white canvas sneakers, silver stud earrings, standing in a bright modern cafe with cream white walls, wooden tables, and green potted plants, one hand in jeans pocket, relaxed natural smile, natural daylight streaming through large windows, soft warm shadows, 5500K white balance, full-body shot, 50mm lens, model centered with negative space above, vertical composition 9:16",
  "motion_prompt": "gentle sway, fashion lookbook style, bright lighting",
  "lyrics_refs": ["B01"]
}
```

S02 (Outfit A):
```json
{
  "id": "S02",
  "type": "body",
  "duration_sec": 6,
  "shot_type": "medium",
  "emotion": "confident",
  "visual_description": "杨梦穿A套碎花裙中景特写，展示面料和版型细节",
  "reference_prompt": "Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a navy blue floral print chiffon midi dress with V-neckline and flutter sleeves, delicate gold chain necklace, chiffon fabric catching light with natural drape, in a bright modern cafe, blurred cream white background with warm bokeh, standing with arms relaxed at sides, looking slightly to the side, natural daylight from left side, soft directional shadows on fabric texture, waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16",
  "motion_prompt": "slow turn, detail showcase, bright studio lighting",
  "lyrics_refs": ["B02", "B03"]
}
```

S03 (Outfit B):
```json
{
  "id": "S03",
  "type": "body",
  "duration_sec": 6,
  "shot_type": "medium",
  "emotion": "elegant",
  "visual_description": "杨梦穿B套针织衫牛仔裤中景特写，展示舒适自然风格",
  "reference_prompt": "Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream white ribbed knit sweater with relaxed fit, silver stud earrings, knit texture visible with natural yarn detail and soft drape, in a bright modern cafe, blurred cream white background with warm bokeh, standing casually with one hand touching hair, natural confident smile, natural daylight from left side, soft shadows, warm skin tones, waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16",
  "motion_prompt": "slow turn, detail showcase, bright studio lighting",
  "lyrics_refs": ["B04", "B05"]
}
```

S04 (法则文字卡):
```json
{
  "id": "S04",
  "type": "body",
  "duration_sec": 6,
  "shot_type": "text_card",
  "emotion": "educational",
  "visual_description": "穿搭法则文字卡",
  "reference_prompt": "text_card",
  "motion_prompt": "text_card",
  "text_card_config": {
    "lines": ["法则一 场合定基调", "法则二 合身最重要"],
    "font_size": 48,
    "font_color": "#2d2d2d",
    "bg_color": "#f5e6d3",
    "animation": "fade_in"
  },
  "lyrics_refs": ["B06", "B07"]
}
```

S05 (CTA):
```json
{
  "id": "S05",
  "type": "cta",
  "duration_sec": 6,
  "shot_type": "close-up",
  "emotion": "warm",
  "visual_description": "杨梦穿B套微笑特写，直视镜头，CTA投票画面",
  "reference_prompt": "Warm intimate fashion portrait, a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing cream white ribbed knit sweater, natural minimal makeup, in a bright modern cafe, soft blurred background, direct eye contact with camera, warm genuine smile, slightly tilted head, natural daylight, soft catchlight in eyes, warm skin tones, close-up face and shoulders, 85mm portrait lens, shallow depth of field, vertical composition 9:16",
  "motion_prompt": "warm smile, direct eye contact, gentle movement",
  "lyrics_refs": ["B08"]
}
```

**reference_images 字段:**
```json
{
  "engine": "seedream_4.5",
  "api": "evolink",
  "resolution": "1440x2560",
  "candidates_per_segment": 2,
  "style_suffix": "vertical composition 9:16",
  "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, cinematic, film grain, wrinkled clothes, fabric distortion, texture error, stiff pose, cropped, cut off, out of frame, tilted, cluttered"
}
```

**video_generation 字段 (穿搭模式参数):**
```json
{
  "engine": "kling_v3",
  "mode": "image_to_video",
  "resolution": "720x1280",
  "duration_sec": 5,
  "fps": 24,
  "fixed_seed": true,
  "iteration_model": "gen4_turbo",
  "final_model": "gen4",
  "candidates_per_segment": 2,
  "motion_intensity": 4,
  "post_processing": {
    "trim_unstable_frames": true,
    "handheld_shake_pct": 5,
    "upscale_4k": true
  }
}
```

**post_production (穿搭模式):**
```json
{
  "film_grain_intensity_pct": 0,
  "lens_glow_intensity_pct": 5,
  "saturation_adjust": 10,
  "contrast_adjust": 5,
  "sharpness_adjust": -2,
  "vignette": 0.05
}
```

**publishing:**
```json
{
  "platforms": ["xiaohongshu"],
  "title_candidates": [
    "初次约会穿A还是B？碎花裙vs针织牛仔",
    "约会穿搭翻车现场：用力过猛反而输了",
    "约会穿搭法则：场合定调 合身最重要"
  ],
  "tags": ["穿搭对比", "OOTD", "约会穿搭", "初次约会", "杨梦穿搭", "场景穿搭", "穿搭法则", "每日穿搭"],
  "xiaohongshu_tags": ["穿搭对比", "OOTD", "约会穿搭", "初次约会", "杨梦穿搭", "场景穿搭", "穿搭法则", "每日穿搭"],
  "publish_times": ["12:00", "18:00"],
  "cover_description": "杨梦A/B穿搭对比 + '初次约会穿搭' 大字 + 明亮奶油色背景"
}
```

**Step 2: 验证 JSON 格式**

Run: `python3 -c "import json; json.load(open('docs/content/config/outfit-day1-date.json')); print('JSON valid')"`
Expected: `JSON valid`

**Step 3: Commit**

```bash
git add docs/content/config/outfit-day1-date.json
git commit -m "feat: add outfit-day1-date config (初次约会穿搭对比对唱)"
```

---

### Task 2: Stage 1 - 验证歌词脚本

**Files:**
- Read: `docs/content/config/outfit-day1-date.json`

**Step 1: 读取 config，验证歌词质量**

逐项检查：
- 总行数 = 16 行（8 bars × 2 lines）
- 最长单行 ≤ 12 字
- 押韵对 ≥ 4
- 穿搭信息密度: 每 2 行 ≥ 1 个知识点
- 法则 = 2 条
- CTA = 投票 A/B 格式
- 大声唱一遍检查节奏是否自然

Run: `python3 -c "
import json
config = json.load(open('docs/content/config/outfit-day1-date.json'))
bars = config['lyrics']['bars']
total_lines = sum(len(b['lines']) for b in bars)
max_len = max(len(line) for b in bars for line in b['lines'])
print(f'Total lines: {total_lines}')
print(f'Max line length: {max_len}')
print(f'Bar count: {len(bars)}')
for b in bars:
    for line in b['lines']:
        print(f'  [{b[\"id\"]}] {line} ({len(line)} chars)')
"`
Expected: Total lines: 16, Max line length: ≤ 12

**Step 2: 确认通过**

如果验证失败，修复 config 中的歌词。如果通过，继续 Task 3。

---

### Task 3: Stage 2 - 生成参考图 (Seedream 4.5)

**Files:**
- Read: `docs/content/config/outfit-day1-date.json`
- Output: `docs/content/assets/references/outfit-day1-date/`

**Step 1: 环境准备**

```bash
source docs/content/.env
```

**Step 2: Dry run 预览**

```bash
python3 docs/content/scripts/seedream-batch.py \
  --config docs/content/config/outfit-day1-date.json \
  --dry-run
```

Expected: 显示将生成的图片列表（S01-2张, S02-2张, S03-2张, S05-2张 = 8 张）。S04 是 text_card 应跳过。

**Step 3: 批量生成 8 张参考图**

```bash
python3 docs/content/scripts/seedream-batch.py \
  --config docs/content/config/outfit-day1-date.json \
  --candidates 2
```

Expected: 8 张 PNG 图片 (1440x2560) 保存到 `docs/content/assets/references/outfit-day1-date/`

Cost: 8 × $0.030 = $0.24

**Step 4: 检查生成结果**

```bash
ls -la docs/content/assets/references/outfit-day1-date/
```

逐张检查：
- S01 图片: A套碎花裙全身，B套针织牛仔全身
- S02 图片: A套中景，面料细节可见
- S03 图片: B套中景，针织纹理清晰
- S05 图片: 杨梦微笑特写，眼神自然

**Step 5: 如果质量不满意，调整 prompt 重新生成特定 shot**

```bash
python3 docs/content/scripts/seedream-batch.py \
  --config docs/content/config/outfit-day1-date.json \
  --shot S02 \
  --candidates 2
```

**Step 6: Commit 参考图**

```bash
git add docs/content/assets/references/outfit-day1-date/
git commit -m "feat: generate 8 reference images for outfit-day1-date (Seedream 4.5)"
```

---

### Task 4: Stage 3 - 生成 Kling 视频

**Files:**
- Input: `docs/content/assets/references/outfit-day1-date/` (参考图)
- Output: `docs/content/output/outfit-day1-date/`

**Step 1: Dry run 预览**

```bash
python3 docs/content/scripts/kling-gen-batch.py \
  --config docs/content/config/outfit-day1-date.json \
  --dry-run
```

Expected: 显示将生成的视频列表（S01, S02, S03, S05 各 2 候选 = 8 段视频）。S04 text_card 跳过。

**Step 2: 批量生成 Kling 视频**

```bash
source docs/content/.env
python3 docs/content/scripts/kling-gen-batch.py \
  --config docs/content/config/outfit-day1-date.json
```

参数（已在 config 中设定）：
- 分辨率: 720x1280
- 每段时长: 5s
- 运动强度: 4/10（穿搭模式，稳定展示）
- Fixed seed: 12345
- 候选数: 2

Expected: 8 段视频保存到 `docs/content/output/outfit-day1-date/`

Cost: 8 × 5s × $0.079/s = $3.16

**Step 3: 检查视频质量**

```bash
ls -la docs/content/output/outfit-day1-date/
```

逐段检查：
- 运动自然不抖
- 面部无变形
- 服装细节清晰
- 无 AI 水印

**Step 4: 选出每个 segment 的最佳候选**

从 S01 的 2 候选中选 1 个，S02 选 1 个，以此类推。将选中的视频重命名为 `S01.mp4`, `S02.mp4` 等。

**Step 5: Commit 视频**

```bash
git add docs/content/output/outfit-day1-date/
git commit -m "feat: generate Kling videos for outfit-day1-date (8 segments)"
```

---

### Task 5: Stage 4 - 生成 Suno 对唱音频

**Files:**
- Input: `docs/content/config/outfit-day1-date.json` (歌词)
- Output: `docs/content/assets/rap/outfit-day1-date/`

**Step 1: 准备 Suno 歌词**

从 config 的 `lyrics.bars` 转换为 Suno 格式:

```
[Chorus]
初次约会到底怎么穿
太用力反而让人难堪

[Verse]
A套碎花长裙细高跟
精致是精致不像本人
妆浓到走路不敢低头
约会变成走红毯的秀

B套针织衫搭牛仔裤
干净舒服自在不装酷
小白鞋走哪都不紧张
做自己就是最好的装

法则一 场合定基调
约会穿太正式会吓跑
法则二 合身最重要
穿得舒服才敢放开笑

[Outro]
初次约会你站A还是B
评论区投票告诉我你的品味
```

**Step 2: Dry run 预览**

```bash
python3 docs/content/scripts/suno-rap-batch.py \
  --config docs/content/config/outfit-day1-date.json \
  --dry-run
```

**Step 3: 生成对唱音频**

```bash
source docs/content/.env
python3 docs/content/scripts/suno-rap-batch.py \
  --config docs/content/config/outfit-day1-date.json
```

Expected: MP3 文件保存到 `docs/content/assets/rap/outfit-day1-date/`

**Step 4: 听测 3 遍**

- [ ] 男女声对唱清晰可辨
- [ ] 旋律自然，不机械
- [ ] 无 rap/hip hop 元素混入
- [ ] BPM ≈ 130 (±10%)

**Step 5: 提取节拍时间戳**

```bash
python3 -c "
import librosa, json, sys, os
rap_dir = 'docs/content/assets/rap/outfit-day1-date'
mp3_files = [f for f in os.listdir(rap_dir) if f.endswith('.mp3')]
if not mp3_files:
    print('No MP3 files found'); sys.exit(1)
mp3_file = os.path.join(rap_dir, sorted(mp3_files)[-1])
y, sr = librosa.load(mp3_file, sr=44100)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beats, sr=sr).tolist()
output = {'bpm': float(tempo), 'beats': beat_times, 'source': mp3_file}
output_path = os.path.join(rap_dir, 'beats.json')
json.dump(output, open(output_path, 'w'), indent=2)
print(f'BPM: {tempo:.1f}, Beats: {len(beat_times)}, Saved to {output_path}')
"
```

**Step 6: 如果不满意，重新生成**

```bash
python3 docs/content/scripts/suno-rap-batch.py \
  --config docs/content/config/outfit-day1-date.json
```

**Step 7: Commit**

```bash
git add docs/content/assets/rap/outfit-day1-date/
git commit -m "feat: generate Suno duet audio for outfit-day1-date"
```

---

### Task 6: Stage 5 - FFmpeg 视频合成

**Files:**
- Input: `docs/content/output/outfit-day1-date/S0*.mp4` (视频段)
- Input: `docs/content/assets/rap/outfit-day1-date/*.mp3` (对唱音频)
- Output: `docs/content/output/outfit-day1-date-sings.mp4`

**Step 1: Dry run 预览**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/outfit-day1-date.json \
  --dry-run
```

**Step 2: 执行合成**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/outfit-day1-date.json
```

Expected: `outfit-day1-date-sings.mp4` 或 `outfit-day1-date_concat.mp4` 生成

**Step 3: 检查合成结果**

```bash
ffprobe -v quiet -print_format json -show_format -show_streams \
  docs/content/output/outfit-day1-date-sings.mp4 | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Duration: {float(d[\"format\"][\"duration\"]):.1f}s, Size: {int(d[\"format\"][\"size\"])//1024//1024}MB')"
```

Expected: Duration 30-45s

**Step 4: Commit**

```bash
git add docs/content/output/outfit-day1-date/
git commit -m "feat: FFmpeg concat for outfit-day1-date"
```

---

### Task 7: Stage 6 - 剪映后期 (手动)

这一步需要用户在剪映中手动操作。告知用户以下待办:

**剪映后期清单:**

1. **A/B 分屏 (S01)**: 将 S01 的 A套和B套视频做左右分屏并排展示
2. **穿搭标签**: S02 加 "A" 标签，S03 加 "B" 标签
3. **歌词字幕**: 逐行/逐字动态出现，KTV 风格
   - 当前唱到的行放大高亮
   - 已唱行缩小变暗
   - 字幕位置底部居中，留出平台 UI 安全区
4. **投票提示 (S05)**: 底部加 "A / B" 大字
5. **音频裁剪**: Suno 生成 90-130s，裁剪到 30-45s
6. **封面帧**: 杨梦 A/B 穿搭对比 + "初次约会穿搭" 大字
7. **去 AI 4 步法**:
   - Step 1: 胶片颗粒 0-5% (保持干净)
   - Step 2: 柔光 5%
   - Step 3: 饱和度+5~+10, 对比度+5, 色温暖白, 锐度-2~-3
   - Step 4: 手持抖动 3% (如 Kling 未加)
8. **AI 标识**: 开头 "AI 生成内容" 文字贴纸，持续 ≥ 3 秒

---

### Task 8: Stage 7 - 最终审核门控

**Files:**
- Read: `docs/content/output/outfit-day1-date/` (最终视频)

**Step 1: 运行审核脚本**

```bash
# 时长检查
DURATION=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 docs/content/output/outfit-day1-date-sings.mp4)
echo "Duration: ${DURATION}s"

# 技术检查
ffprobe -v quiet -print_format json -show_format -show_streams \
  docs/content/output/outfit-day1-date-sings.mp4 | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
v = [s for s in d['streams'] if s['codec_type']=='video'][0]
print(f'Resolution: {v[\"width\"]}x{v[\"height\"]}')
print(f'FPS: {v[\"r_frame_rate\"]}')
print(f'Codec: {v[\"codec_name\"]}')
print(f'Size: {int(d[\"format\"][\"size\"])//1024//1024}MB')
"
```

**Step 2: 逐项审核**

```
视频编号：outfit-day1-date
日期：2026-04-23

时长：      ___s    [ ] PASS  [ ] FAIL (需 30-45s)
BPM：       ___     [ ] PASS  [ ] FAIL (需 120-140)
节拍同步：          [ ] PASS  [ ] FAIL
A/B对比可见：      [ ] PASS  [ ] FAIL
穿搭法则：  2 条    [ ] PASS  [ ] FAIL
CTA投票：           [ ] PASS  [ ] FAIL
手机预览：          [ ] PASS  [ ] FAIL
去AI检查：          [ ] PASS  [ ] FAIL
AI显性标识：        [ ] PASS  [ ] FAIL
AI隐性标识：        [ ] PASS  [ ] FAIL

最终决定：[ ] 批准上传  [ ] 返回 Stage ___ 原因：__________
```

**Step 3: 全部 PASS 后 commit**

```bash
git add docs/content/config/outfit-day1-date.json
git commit -m "docs: outfit-day1-date config status → review_passed"
```

---

### Task 9: 发布准备

**Step 1: 准备小红书发布内容**

标题候选（从 config `publishing.title_candidates`）:
- "初次约会穿A还是B？碎花裙vs针织牛仔"
- "约会穿搭翻车现场：用力过猛反而输了"
- "约会穿搭法则：场合定调 合身最重要"

标签: `#穿搭对比 #OOTD #约会穿搭 #初次约会 #杨梦穿搭 #场景穿搭 #穿搭法则 #每日穿搭`

**Step 2: 上传前最终确认**

- [ ] 在小红书发布界面勾选 "AI 生成内容" 声明
- [ ] 封面图已制作
- [ ] 发布时间选择 12:00 或 18:00
