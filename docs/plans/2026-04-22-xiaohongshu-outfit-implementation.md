# 小红书穿搭对比 Sings 工作流实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建小红书穿搭对比 Sings 工作流的完整基础设施（模板 + spec + 第一集 config），使用户能开始生产内容。

**Architecture:** 基于现有 Sings 工作流管线（Suno 对唱 + Seedream 生图 + Kling 视频 + FFmpeg），修改色调、歌词主题、视觉风格以适配小红书穿搭对比内容。第一集为"面试穿搭 A vs B"。

**Tech Stack:** JSON config, Seedream 4.5 (Evolink API), Kling 3.0 (Evolink API), Suno v4.5 (Evolink API), FFmpeg, 剪映

**Design doc:** `docs/plans/2026-04-22-xiaohongshu-outfit-sings-design.md`

---

### Task 1: 创建 `sings-outfit-template.json`

**Files:**
- Create: `docs/content/config/sings-outfit-template.json`

**Step 1: 写模板 config**

基于 `sings04-yangmun.json` 的对唱风格 + `sings-template.json` 的模板结构，创建穿搭对比版本。

关键差异：
- `global.style`: `"outfit_compare"` （原 `"warm_textcard"`）
- `global.color_temperature`: `"warm_bright"` （原 `"warm"`）
- `global.accent_color`: `"#e8a87c"` （原 `"#c9a96e"`）
- `global.bg_color`: `"#f5e6d3"` （原 `"#0a0806"`）
- `lyrics.style` / `suno_tags`: 增加 `"fashion"` 关键词
- `lyrics.bars`: 改为穿搭对比歌词模板（5 段式：hook → outfit A → outfit B → 法则 → CTA）
- `segments`: 5 段（S01 hook, S02 outfit A, S03 outfit B, S04 法则, S05 CTA）
- `post_production`: 去 film grain，降 contrast，提 saturation
- `publishing.platforms`: `["xiaohongshu"]`
- `publishing.tags`: 穿搭相关

```json
{
  "video_id": "sings-outfit-template",
  "workflow": "sings",
  "version": "1.0",
  "created": "2026-04-22",
  "status": "template",
  "strategy_notes": "小红书穿搭对比对唱模板。每期一个场景，杨梦展示两套穿搭A/B，男女对唱讲穿搭逻辑",

  "global": {
    "target_duration_sec": 37,
    "max_duration_sec": 45,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": null,
    "style": "outfit_compare",
    "color_temperature": "warm_bright",
    "accent_color": "#e8a87c",
    "bg_color": "#f5e6d3"
  },

  "lyrics": {
    "bpm": 130,
    "time_signature": "4/4",
    "style": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "suno_tags": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": ["[场景提问：如'面试穿A还是B' ≤12字]", "[女声回应：如'不是贵不贵 是对不对位' ≤12字]"],
        "rhyme": "a",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": ["[A套描述：如'A套 深蓝西装白衬衫' ≤12字]", "[A套点评：如'经典不出错' ≤10字]"],
        "rhyme": "e",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B03",
        "beat_count": 4,
        "lines": ["[A套缺点/细节 ≤12字]", "[A套总结 ≤10字 押韵]"],
        "rhyme": "e",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B04",
        "beat_count": 4,
        "lines": ["[B套描述：如'B套 针织衫搭深色裤' ≤12字]", "[B套点评：如'干净有层次' ≤10字]"],
        "rhyme": "i",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B05",
        "beat_count": 4,
        "lines": ["[B套优点/细节 ≤12字]", "[B套总结 ≤10字 押韵]"],
        "rhyme": "i",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B06",
        "beat_count": 4,
        "lines": ["[穿搭法则1 ≤12字]", "[法则1解释 ≤10字 押韵]"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B07",
        "beat_count": 4,
        "lines": ["[穿搭法则2 ≤12字]", "[法则2解释 ≤10字 押韵]"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B08",
        "beat_count": 4,
        "lines": ["[CTA提问：如'面试穿搭你站A还是B' ≤12字]", "[CTA引导：如'评论区告诉我' ≤10字 押韵]"],
        "rhyme": "a",
        "segment_ref": "S05",
        "type": "cta"
      }
    ]
  },

  "script": {
    "topic": "[选题：穿搭场景名称]",
    "source": "原创穿搭对比内容",
    "hook_type": "scenario_question",
    "cta_action": "投票A/B",
    "cta_keyword": "评论区投票",
    "anti_ad_measures": [
      "不提任何品牌或产品推荐",
      "不引导私信、领取、关注",
      "CTA用投票选择，激发评论互动",
      "聚焦穿搭逻辑和审美，不卖任何东西"
    ]
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 6,
      "shot_type": "wide",
      "emotion": "playful",
      "visual_description": "[杨梦全身两套穿搭并排/快速切换对比]",
      "reference_prompt": "[杨梦穿搭对比参考图prompt]",
      "motion_prompt": "gentle sway, fashion lookbook style, bright lighting",
      "lyrics_refs": ["B01"]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "medium",
      "emotion": "confident",
      "visual_description": "[杨梦穿A套特写，展示细节]",
      "reference_prompt": "[A套参考图prompt]",
      "motion_prompt": "slow turn, detail showcase, bright studio lighting",
      "lyrics_refs": ["B02", "B03"]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "medium",
      "emotion": "elegant",
      "visual_description": "[杨梦穿B套特写，展示细节]",
      "reference_prompt": "[B套参考图prompt]",
      "motion_prompt": "slow turn, detail showcase, bright studio lighting",
      "lyrics_refs": ["B04", "B05"]
    },
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
        "lines": ["[穿搭法则1]", "[穿搭法则2]"],
        "font_size": 48,
        "font_color": "#2d2d2d",
        "bg_color": "#f5e6d3",
        "animation": "fade_in"
      },
      "lyrics_refs": ["B06", "B07"]
    },
    {
      "id": "S05",
      "type": "cta",
      "duration_sec": 6,
      "shot_type": "close-up",
      "emotion": "warm",
      "visual_description": "[杨梦直视镜头微笑，CTA画面]",
      "reference_prompt": "[杨梦微笑参考图prompt]",
      "motion_prompt": "warm smile, direct eye contact, gentle movement",
      "lyrics_refs": ["B08"]
    }
  ],

  "audio": {
    "engine": "suno_ai",
    "mode": "custom",
    "style_prompt": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "negative_tags": "rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody",
    "style_weight": 0.9,
    "weirdness_constraint": 0.3,
    "output_format": "mp3",
    "extract_beats": true,
    "beat_tool": "librosa",
    "generation": {
      "model": "suno-v4.5",
      "custom_mode": true,
      "vocal_gender": "m"
    }
  },

  "beat_sync": {
    "enabled": true,
    "align_to": "bar_lines",
    "min_cut_interval_beats": 2,
    "max_cut_interval_beats": 4
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "resolution": "1440x2560",
    "candidates_per_segment": 2,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, cinematic, film grain"
  },

  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "iteration_model": "gen4_turbo",
    "final_model": "gen4",
    "candidates_per_segment": 2,
    "motion_intensity": 4
  },

  "compositing": {
    "engine": "ffmpeg",
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_lyrics",
    "subtitle_style": "ktv_dynamic"
  },

  "ai_labeling": {
    "enabled": true,
    "watermark_text": "AI生成内容",
    "watermark_duration_sec": 3,
    "watermark_position": "top_left",
    "watermark_font_size": 28,
    "watermark_opacity": 0.8,
    "metadata_key": "comment",
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和音乐"
  },

  "post_production": {
    "film_grain_intensity_pct": 0,
    "lens_glow_intensity_pct": 5,
    "saturation_adjust": 10,
    "contrast_adjust": 5,
    "sharpness_adjust": -2,
    "vignette": 0.05
  },

  "publishing": {
    "platforms": ["xiaohongshu"],
    "title_candidates": [
      "[标题1：场景+提问]",
      "[标题2：穿搭对比]",
      "[标题3：法则/结论]"
    ],
    "tags": ["穿搭对比", "OOTD", "杨梦穿搭", "场景穿搭", "穿搭法则"],
    "xiaohongshu_tags": ["穿搭对比", "OOTD", "面试穿搭", "职场穿搭", "杨梦穿搭", "场景穿搭", "穿搭法则", "每日穿搭"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "杨梦A/B穿搭对比 + 场景关键词大字 + 明亮奶油色背景"
  }
}
```

**Step 2: 验证 JSON 合法**

Run: `python3 -c "import json; json.load(open('docs/content/config/sings-outfit-template.json')); print('VALID')"`
Expected: `VALID`

**Step 3: Commit**

```bash
git add docs/content/config/sings-outfit-template.json
git commit -m "feat: add sings-outfit-template.json for Xiaohongshu outfit comparison"
```

---

### Task 2: 创建 Seedream 穿搭 Prompt 模板

**Files:**
- Create: `docs/content/config/outfit-seedream-prompts.md`

**Step 1: 写 Prompt 模板文档**

基于已有的 Seedream v3.0 方法论（`feedback_seedream-prompt-v3.md`），针对穿搭场景调整。

参考 `feedback_seedream-character-anchor.md` 中的杨梦角色锚定结构。

```markdown
# 穿搭对比 Seedream Prompt 模板

## 基础角色锚定（每条 prompt 必须包含）

Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,

## 穿搭 Prompt 结构

[基础角色锚定],
wearing [服装描述],
[场景/背景],
[姿势],
[光影],
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16

## 穿搭 A 套示例（面试 - 深蓝西装）

Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a well-fitted navy blue blazer over a crisp white button-down shirt,
dark tailored trousers, simple leather watch, small stud earrings,
standing in a bright modern office lobby with floor-to-ceiling windows,
confident posture with arms relaxed at sides, slight smile,
soft natural daylight from the left, cream white walls,
bright airy atmosphere,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16

## 穿搭 B 套示例（面试 - 针织衫）

Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a cream knit sweater with subtle ribbed texture,
dark slim-fit chinos, minimalist leather belt, delicate gold necklace,
standing in a bright modern office lobby with floor-to-ceiling windows,
relaxed confident stance, one hand in pocket, genuine smile,
soft natural daylight from the left, cream white walls,
bright airy atmosphere,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16

## CTA 镜头示例

Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
looking directly at camera with warm inviting smile,
wearing [该期推荐的穿搭],
bright cream-colored background, soft diffused lighting,
close-up from chest up,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16

## 负面 Prompt

airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain

## 注意事项

- 每条 prompt 必须包含完整的角色锚定段落，不可省略
- 穿搭描述要具体到面料和版型（如 "ribbed texture", "slim-fit"）
- 背景必须明亮（"bright", "airy", "natural daylight"），不要暗色调
- 姿势要有变化：全身照站姿，特写照表情和手部细节
- 同一集的 A/B 两套 prompt 只改服装和姿势，角色锚定和背景保持一致
```

**Step 2: Commit**

```bash
git add docs/content/config/outfit-seedream-prompts.md
git commit -m "docs: add Seedream prompt templates for outfit comparison content"
```

---

### Task 3: 创建穿搭对比 Spec 附录

**Files:**
- Create: `docs/content/workflow/sings-outfit-production-spec.md`

**Step 1: 写 Spec 文档**

基于 `sings-video-production-spec.md`，写穿搭模式的差异点和新增规则。

```markdown
# Sings 穿搭对比模式 Spec

> 适用范围：小红书穿搭场景对比短视频，Sings 工作流穿搭变体
> 工具链：Seedream 4.5 + Kling 3.0 + Suno AI + FFmpeg + 剪映
> 基于：sings-video-production-spec.md v1.0
> 最后更新：2026-04-22

---

## 与标准 Sings 工作流的差异

| 维度 | 标准 Sings | 穿搭对比模式 |
|------|-----------|-------------|
| 平台 | 抖音 + 小红书 | 仅小红书 |
| 内容主题 | 商业/科普 | 穿搭场景对比 |
| 色调 | 暗金 / 品牌紫蓝 | 明亮时尚（奶油白 + 暖橘） |
| 歌词 | 知识/故事 | 穿搭逻辑/点评 |
| 视觉 | 电影感/MV | 时尚 lookbook |
| CTA | 评论区聊聊 | 投票 A/B |
| 段落结构 | 6段（hook+4body+cta） | 5段（hook+A套+B套+法则+cta） |

## 色彩规范

| 元素 | 色值 | 用途 |
|------|------|------|
| 主背景 | #f5e6d3 | 奶油白，文字卡背景 |
| 主文字 | #2d2d2d | 深灰，文字卡文字 |
| 强调色 | #e8a87c | 暖橘，高亮/标题 |
| 次强调 | #8b7355 | 暖棕，辅助文字 |

## 段落结构（5 段，30-45s）

1. **Hook（S01, 6s）**: 场景提问 + 杨梦两套穿搭对比
2. **Outfit A（S02, 6s）**: A 套穿搭特写 + 点评歌词
3. **Outfit B（S03, 6s）**: B 套穿搭特写 + 点评歌词
4. **法则（S04, 6s）**: 穿搭法则文字卡 + 总结歌词
5. **CTA（S05, 6s）**: 杨梦直视镜头 + 投票引导

## 剪映后期新增步骤

### A/B 穿搭对比编辑

标准 Sings 后期流程基础上，新增：

1. **左右分屏**（推荐）：S01 hook 段落，左 A 右 B 并排展示
   - 剪映：画中画，50% 缩放，左右各一轨
   - 中间加 2px 白色分割线
2. **快速切换**（备选）：S01 段落，A/B 交替闪现，每 0.5s 切一次
3. **文字叠加**：每套穿搭上方加 "A" / "B" 标签，字体用强调色
4. **投票引导**：S05 段落底部加 "A / B" 大字投票提示

### 去 AI 化注意

穿搭模式去 AI 化 4 步法额外注意：
- 面料质感：AI 生成的服装纹理可能不自然，需要在剪映中适当锐化
- 手部细节：AI 手部常见问题，穿搭镜头尽量避开手部特写
- 服装版型：AI 可能改变服装版型，分屏对比时确保视觉平衡

## 小红书发布规范

### 标题格式

- `[场景]穿A还是B？` （提问式）
- `[场景]穿搭避雷指南` （干货式）
- `[人物]教你[场景]怎么穿` （教学式）

### 标签

必选：#穿搭对比 #OOTD #杨梦穿搭
场景标签：#面试穿搭 #约会穿搭 #通勤穿搭 （每期选 1-2 个）
流量标签：#每日穿搭 #穿搭灵感 （每期带 1 个）

### 封面

杨梦 A/B 穿搭对比 + 场景关键词（如"面试"）大字 + 奶油白背景

## 内容选题日历（第 1 周）

| 集数 | 场景 | A 套 | B 套 | 法则 |
|------|------|------|------|------|
| Day1 | 面试穿搭 | 深蓝西装白衬衫 | 针织衫深色裤 | 看行业定基调 + 合身比品牌重要 |
| Day2 | 入职第一天 | 休闲西装内搭T恤 | 衬衫裙+小白鞋 | 不超过三个颜色 + 鞋子定风格 |
| Day3 | 述职报告 | 黑色西装+丝巾 | 深色连衣裙+腰带 | 场合决定正式度 + 一个亮点就够 |
| Day4 | 商务晚宴 | 深色礼服裙+耳环 | 西装套装+胸针 | 面料比款式重要 + 饰品要克制 |
| Day5 | 周五便装 | 卫衣+阔腿裤 | 针织开衫+牛仔裤 | 休闲不随便 + 一件单品撑场面 |
```

**Step 2: Commit**

```bash
git add docs/content/workflow/sings-outfit-production-spec.md
git commit -m "docs: add sings-outfit-production-spec.md for Xiaohongshu outfit mode"
```

---

### Task 4: 创建第一集 Config: `outfit-day1-interview.json`

**Files:**
- Create: `docs/content/config/outfit-day1-interview.json`
- Create: `docs/content/output/outfit-day1/` (output directory)

**Step 1: 写第一集 config**

基于 `sings-outfit-template.json` 填入面试穿搭的具体内容。

```json
{
  "video_id": "outfit-day1-interview",
  "workflow": "sings",
  "version": "1.0",
  "created": "2026-04-22",
  "status": "draft",
  "strategy_notes": "小红书穿搭对比第1集：面试穿搭A vs B。杨梦穿深蓝西装 vs 针织衫，讲面试穿搭法则",

  "global": {
    "target_duration_sec": 37,
    "max_duration_sec": 45,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": 10001,
    "style": "outfit_compare",
    "color_temperature": "warm_bright",
    "accent_color": "#e8a87c",
    "bg_color": "#f5e6d3"
  },

  "lyrics": {
    "bpm": 130,
    "time_signature": "4/4",
    "style": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "suno_tags": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": ["面试穿西装还是休闲", "评委看第一眼 定你行不行"],
        "rhyme": "an",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": ["A套 深蓝西装白衬衫", "经典不出错 但太正式"],
        "rhyme": "an",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B03",
        "beat_count": 4,
        "lines": ["这条领带像去银行", "科技公司穿成这样太紧张"],
        "rhyme": "ang",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B04",
        "beat_count": 4,
        "lines": ["B套 针织衫搭深色裤", "干净有层次 不装成熟"],
        "rhyme": "u",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B05",
        "beat_count": 4,
        "lines": ["做你自己就够自信", "不用西装也能赢"],
        "rhyme": "in",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B06",
        "beat_count": 4,
        "lines": ["法则一 看行业定基调", "金融正式 互联网太拘谨反而不妙"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B07",
        "beat_count": 4,
        "lines": ["法则二 合身比品牌重要", "肩膀对不上号 大牌也像借来的搞笑"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B08",
        "beat_count": 4,
        "lines": ["面试穿搭你站A还是B", "评论区投票 告诉我你的品味"],
        "rhyme": "i",
        "segment_ref": "S05",
        "type": "cta"
      }
    ]
  },

  "script": {
    "topic": "面试穿搭：西装正式 vs 针织干练",
    "source": "原创穿搭对比",
    "hook_type": "scenario_question",
    "cta_action": "投票A/B",
    "cta_keyword": "评论区投票",
    "outfit_a": {
      "name": "深蓝西装白衬衫",
      "description": "经典正式，适合金融/传统行业面试",
      "keywords": ["正式", "经典", "专业"]
    },
    "outfit_b": {
      "name": "针织衫深色裤",
      "description": "干练有层次，适合科技/创意行业面试",
      "keywords": ["干练", "层次", "自信"]
    },
    "fashion_rules": [
      "看行业定基调：金融正式，互联网太拘谨反而不好",
      "合身比品牌重要：肩膀对不上号，大牌也像借来的"
    ],
    "anti_ad_measures": [
      "不提任何品牌或产品推荐",
      "不引导私信、领取、关注",
      "CTA用投票选择，激发评论互动",
      "聚焦穿搭逻辑和审美，不卖任何东西"
    ]
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 6,
      "shot_type": "wide",
      "emotion": "playful",
      "visual_description": "杨梦两套面试穿搭并排对比",
      "reference_prompt": "Candid photograph of a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, standing in a bright modern office lobby, split view showing two outfit options side by side, soft natural daylight, cream white walls, bright airy atmosphere, natural skin texture, visible noise, fashion lookbook style, vertical composition 9:16",
      "motion_prompt": "gentle sway between two poses, fashion lookbook style, bright lighting",
      "lyrics_refs": ["B01"]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "medium",
      "emotion": "confident",
      "visual_description": "杨梦穿A套：深蓝西装白衬衫，办公室背景",
      "reference_prompt": "Candid photograph of a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a well-fitted navy blue blazer over a crisp white button-down shirt, dark tailored trousers, simple leather watch, small stud earrings, standing in a bright modern office lobby with floor-to-ceiling windows, confident posture with arms relaxed at sides, slight smile, soft natural daylight from the left, cream white walls, bright airy atmosphere, natural skin texture, visible noise, fashion lookbook style, vertical composition 9:16",
      "motion_prompt": "slow turn, detail showcase, bright studio lighting",
      "lyrics_refs": ["B02", "B03"]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "medium",
      "emotion": "elegant",
      "visual_description": "杨梦穿B套：针织衫深色裤，办公室背景",
      "reference_prompt": "Candid photograph of a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream knit sweater with subtle ribbed texture, dark slim-fit chinos, minimalist leather belt, delicate gold necklace, standing in a bright modern office lobby with floor-to-ceiling windows, relaxed confident stance, one hand in pocket, genuine smile, soft natural daylight from the left, cream white walls, bright airy atmosphere, natural skin texture, visible noise, fashion lookbook style, vertical composition 9:16",
      "motion_prompt": "slow turn, detail showcase, bright studio lighting",
      "lyrics_refs": ["B04", "B05"]
    },
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
        "lines": ["面试穿搭法则", "① 看行业定基调", "② 合身比品牌重要"],
        "font_size": 48,
        "font_color": "#2d2d2d",
        "bg_color": "#f5e6d3",
        "animation": "fade_in"
      },
      "lyrics_refs": ["B06", "B07"]
    },
    {
      "id": "S05",
      "type": "cta",
      "duration_sec": 6,
      "shot_type": "close-up",
      "emotion": "warm",
      "visual_description": "杨梦直视镜头微笑，CTA投票引导",
      "reference_prompt": "Candid photograph of a young Chinese woman, mid-twenties, warm complexion, subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, looking directly at camera with warm inviting smile, wearing a cream knit sweater, bright cream-colored background, soft diffused lighting, close-up from chest up, natural skin texture, visible noise, fashion lookbook style, vertical composition 9:16",
      "motion_prompt": "warm smile, direct eye contact, gentle movement",
      "lyrics_refs": ["B08"]
    }
  ],

  "audio": {
    "engine": "suno_ai",
    "mode": "custom",
    "style_prompt": "catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm",
    "negative_tags": "rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody",
    "style_weight": 0.9,
    "weirdness_constraint": 0.3,
    "output_format": "mp3",
    "extract_beats": true,
    "beat_tool": "librosa",
    "generation": {
      "model": "suno-v4.5",
      "custom_mode": true,
      "vocal_gender": "m"
    }
  },

  "beat_sync": {
    "enabled": true,
    "align_to": "bar_lines",
    "min_cut_interval_beats": 2,
    "max_cut_interval_beats": 4
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "resolution": "1440x2560",
    "candidates_per_segment": 2,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, cinematic, film grain"
  },

  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "iteration_model": "gen4_turbo",
    "final_model": "gen4",
    "candidates_per_segment": 2,
    "motion_intensity": 4
  },

  "compositing": {
    "engine": "ffmpeg",
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_lyrics",
    "subtitle_style": "ktv_dynamic"
  },

  "ai_labeling": {
    "enabled": true,
    "watermark_text": "AI生成内容",
    "watermark_duration_sec": 3,
    "watermark_position": "top_left",
    "watermark_font_size": 28,
    "watermark_opacity": 0.8,
    "metadata_key": "comment",
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和音乐"
  },

  "post_production": {
    "film_grain_intensity_pct": 0,
    "lens_glow_intensity_pct": 5,
    "saturation_adjust": 10,
    "contrast_adjust": 5,
    "sharpness_adjust": -2,
    "vignette": 0.05
  },

  "publishing": {
    "platforms": ["xiaohongshu"],
    "title_candidates": [
      "面试穿A还是B 一秒定胜负",
      "面试穿搭两套对比 你站哪边",
      "面试穿搭法则 看行业定基调"
    ],
    "tags": ["穿搭对比", "OOTD", "面试穿搭", "职场穿搭", "杨梦穿搭"],
    "xiaohongshu_tags": ["穿搭对比", "OOTD", "面试穿搭", "职场穿搭", "杨梦穿搭", "场景穿搭", "穿搭法则", "每日穿搭"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "杨梦面试A/B穿搭对比 + '面试穿搭' 大字 + 奶油白背景"
  }
}
```

**Step 2: 创建输出目录**

```bash
mkdir -p docs/content/output/outfit-day1
```

**Step 3: 验证 JSON 合法**

Run: `python3 -c "import json; json.load(open('docs/content/config/outfit-day1-interview.json')); print('VALID')"`
Expected: `VALID`

**Step 4: Commit**

```bash
git add docs/content/config/outfit-day1-interview.json
git commit -m "feat: add outfit-day1-interview.json config for Xiaohongshu outfit series"
```

---

### Task 5: Suno 音频生成

**依赖:** Task 4 完成（config 就绪）

**Step 1: 运行 Suno 生成脚本**

```bash
source docs/content/.env
cd docs/content/scripts
python suno-rap-batch.py --config ../config/outfit-day1-interview.json
```

Expected: 生成 2 个版本的 MP3 音频到 `docs/content/assets/rap/outfit-day1-interview/`

**Step 2: 验证音频**

```bash
ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 docs/content/assets/rap/outfit-day1-interview/*.mp3
```

Expected: 每个 90-130 秒（Suno v4.5 的正常范围）。用户会在剪映中裁剪到 30-45s。

**Step 3: Commit**

```bash
git add docs/content/assets/rap/outfit-day1-interview/
git commit -m "feat: add Suno duet audio for outfit-day1-interview"
```

---

### Task 6: Seedream 参考图生成

**依赖:** Task 4 完成（config 就绪）

**Step 1: 用 Evolink API 生成参考图**

每段需要 2 张候选参考图：
- S01: 穿搭对比（需要特殊处理，可能用 S02 + S03 的图在剪映中拼分屏）
- S02: A 套穿搭（深蓝西装）
- S03: B 套穿搭（针织衫）
- S04: 文字卡（不需要参考图）
- S05: CTA 微笑特写

实际需要生成 4 段 × 2 候选 = 8 张图片。

用 Evolink Seedream API 发送 prompt（从 config 的 `reference_prompt` 字段读取）。

**Step 2: 验证图片**

检查生成图片的分辨率（应为 1440×2560）和视觉效果（明亮、穿搭清晰可见）。

**Step 3: Commit**

```bash
git add docs/content/assets/references/outfit-day1/
git commit -m "feat: add Seedream reference images for outfit-day1-interview"
```

---

### Task 7: Kling 视频生成

**依赖:** Task 6 完成（参考图就绪）

**Step 1: 用 Evolink API 生成视频**

每段用参考图生成 5 秒视频，每段 2 个候选：
- S01: 2 个候选
- S02: 2 个候选
- S03: 2 个候选
- S04: 文字卡（FFmpeg 直接生成）
- S05: 2 个候选

实际需要 4 段 × 2 候选 = 8 个视频。

motion_intensity 设为 4（比标准 Sings 的 6 更低，穿搭需要稳定画面）。

**Step 2: 验证视频**

```bash
ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 docs/content/output/outfit-day1/*.mp4
```

Expected: 每个约 5 秒。

**Step 3: Commit**

```bash
git add docs/content/output/outfit-day1/
git commit -m "feat: add Kling videos for outfit-day1-interview"
```

---

### Task 8: FFmpeg 拼接

**依赖:** Task 7 + Task 5 完成

**Step 1: 选择最佳视频片段**

从每段 2 个候选中选 1 个最佳，加上文字卡（S04），写入 concat list。

```bash
cd docs/content/output/outfit-day1

cat > concat.txt << 'EOF'
file 'S01-best.mp4'
file 'S02-best.mp4'
file 'S03-best.mp4'
file 'S04-textcard.mp4'
file 'S05-best.mp4'
EOF
```

**Step 2: FFmpeg 拼接视频**

```bash
ffmpeg -f concat -safe 0 -i concat.txt -c copy outfit-day1-video-only.mp4
```

**Step 3: 合并 Suno 音频**

```bash
ffmpeg -i outfit-day1-video-only.mp4 -i ../../assets/rap/outfit-day1-interview/outfit-day1-interview_v1.mp3 -c:v copy -c:a aac -shortest outfit-day1-concat.mp4
```

**Step 4: 验证输出**

```bash
ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 outfit-day1-concat.mp4
```

Expected: 约 25-30 秒（5 段 × 5-6 秒，受 `-shortest` 限制）。

**Step 5: Commit**

```bash
git add docs/content/output/outfit-day1/
git commit -m "feat: add FFmpeg concat output for outfit-day1-interview"
```

---

### Task 9: 剪映后期（用户手动）

**依赖:** Task 8 完成

这一步由用户在剪映中手动完成：

1. 导入 `outfit-day1-concat.mp4`
2. 裁剪 Suno 音频到 30-45s，选取最好的片段
3. S01 hook 段做左右分屏（A/B 穿搭对比）
4. S02/S03 加 "A" / "B" 文字标签
5. S04 法则文字卡调整样式
6. S05 底部加 "A / B" 投票提示
7. KTV 歌词字幕
8. 去 AI 化 4 步处理
9. 导出最终版到 `docs/content/output/outfit-day1/outfit-day1-final.mp4`

---

## 执行顺序

```
Task 1 (模板) → Task 2 (Prompt) → Task 3 (Spec) → Task 4 (第一集 Config)
                                                            ↓
                                                    Task 5 (Suno) ──→ Task 8 (FFmpeg)
                                                    Task 6 (Seedream) → Task 7 (Kling) ─↑
                                                                                         ↓
                                                                                    Task 9 (剪映)
```

Task 1-4 必须按顺序。Task 5/6/7 可以并行。Task 8 依赖 5+7。Task 9 由用户手动完成。
