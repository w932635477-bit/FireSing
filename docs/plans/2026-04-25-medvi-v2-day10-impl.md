# Medvi v2 + Day10 配置 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 更新 Medvi 工作流规范为 v2（跳过主参考图+杨梦视频），并创建 Day10 config JSON 按 v2 格式

**Architecture:** 两个文件变更：(1) video-production-spec.md 添加 v2 模式规则 (2) day10-yangmun.json 用新格式（无主参考图字段，3张故事图，yangmun_clip_hint）。脚本不需要改，v2 只是少运行两个脚本。

**Tech Stack:** JSON config, Markdown spec

**Design docs:** `docs/plans/2026-04-25-medvi-workflow-v2-design.md`, `docs/plans/2026-04-25-day10-renzhengfei-design.md`

---

### Task 1: Create day10-yangmun.json (v2 format)

**Files:**
- Create: `docs/content/config/day10-yangmun.json`

**Context:** v2 格式与 Day9 的区别：每个 segment **没有** `reference_file`、`reference_prompt`、`motion_prompt`。**有** `yangmun_clip_hint`。story_images 每段最多1张（S01/S02/S03各1张，S04无）。

**Step 1: Write the config JSON**

Key structural changes from Day9:
- Remove all `reference_file`, `reference_prompt`, `motion_prompt` from segments
- Remove `kling_seed` from global
- Add `yangmun_clip_hint` to each segment (points to existing Yangmun clips)
- Each segment has exactly 0-1 story_images (not 2)
- Add `workflow_version: "2.0"` to global to distinguish from v1 configs
- Story image prompts come from design doc Section 2/4 (scene images only, no Yangmun character)

Full JSON:

```json
{
  "video_id": "day10-yangmun",
  "version": "2.0",
  "created": "2026-04-25",
  "status": "script_approved",
  "strategy": "yangmun-emotion-ip",
  "strategy_notes": "Day10 任正非备胎转正。自由叙事结构。shock→tension→reversal→warm。Medvi v2工作流：无主参考图，3张故事图，杨梦素材从已有库选取混剪。",
  "eval_score": 90,
  "global": {
    "target_duration_sec": 43,
    "max_duration_sec": 60,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "workflow_version": "2.0",
    "style": "yangmun_minimalist_portrait",
    "color_temperature": "cool_warm_shift",
    "accent_color": "#8b7355"
  },
  "script": {
    "topic": "备胎转正",
    "hook_type": "scene_immersion",
    "cta_action": "评论",
    "cta_keyword": "备胎准备了几年",
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
      "duration_sec": 10,
      "shot_type": "close-up",
      "emotion_arc": "shock",
      "yangmun_clip_hint": "day5-yangmun/S01-shock.mp4",
      "story_images": [
        {
          "id": "S01-01",
          "trigger_text": "美国对华为实施全面制裁",
          "reference_file": "day10-yangmun/S01-01.png",
          "reference_prompt": "iPhone 15 Pro photo natural lighting slightly underexposed, close-up of a phone screen at night showing a breaking news push notification in Chinese about US sanctions on a major tech company, the phone held in a dark room illuminated only by the blue-white screen light casting harsh shadows on the holder's hand, visible film grain especially in shadow areas, subject center, vertical composition 9:16",
          "motion_prompt": "slow zoom in on phone screen, notification banner sliding in, screen glow pulsing"
        }
      ],
      "voiceover_text": "半夜里手机突然亮了。一条推送：美国对华为实施全面制裁。芯片，断了。操作系统，锁了。供应商，撤了。三天之内，华为从全球第二，变成了一个不知道还能不能活下去的公司。",
      "voiceover_pause_markers": "半夜里手机突然亮了。<#0.3#>一条推送<#0.5#>美国对华为实施全面制裁。<#0.5#>芯片<#0.3#>断了。<#0.2#>操作系统<#0.3#>锁了。<#0.2#>供应商<#0.3#>撤了。<#0.6#>三天之内<#0.2#>华为从全球第二<#0.2#>变成了一个不知道还能不能活下去的公司。",
      "subtitle_text": "三天之内 从全球第二变成不知道能不能活"
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 11,
      "shot_type": "medium",
      "emotion_arc": "tension",
      "yangmun_clip_hint": "day5-yangmun/S02-determined.mp4",
      "story_images": [
        {
          "id": "S02-01",
          "trigger_text": "从来没有被真正依赖过",
          "reference_file": "day10-yangmun/S02-01.png",
          "reference_prompt": "35mm documentary film still grainy imperfect focus, interior of a high-tech chip fabrication laboratory late at night, rows of silicon wafers and testing equipment, a single researcher sitting alone at a workstation in the background barely visible through blue-tinted clean room lighting, cold sterile fluorescent light mixing with warm amber from a desk lamp, visible film grain, subject lower third, vertical composition 9:16",
          "motion_prompt": "slow pan across lab equipment, dust particles drifting in light beam, subtle machine hum"
        }
      ],
      "voiceover_text": "十年前，华为成立了一家叫海思的公司。投了上百亿，造芯片。造出来的芯片，从来没有被真正依赖过。有人说浪费。有人说疯了。但任正非什么也没说。",
      "voiceover_pause_markers": "十年前<#0.3#>华为成立了一家叫海思的公司。<#0.5#>投了上百亿<#0.2#>造芯片。<#0.5#>造出来的芯片<#0.2#>从来没有被真正依赖过。<#0.5#>有人说浪费。<#0.3#>有人说疯了。<#0.8#>但任正非<#0.3#>什么也没说。",
      "subtitle_text": "上百亿造芯片 从来没有被真正依赖过"
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 12,
      "shot_type": "medium",
      "emotion_arc": "reversal",
      "yangmun_clip_hint": "day6-yangmun/S03.mp4",
      "story_images": [
        {
          "id": "S03-01",
          "trigger_text": "一夜之间全部转正",
          "reference_file": "day10-yangmun/S03-01.png",
          "reference_prompt": "shot on Canon 5D Mark IV 85mm f/1.4 Kodak Portra 400, extreme close-up of a single silicon chip glowing with warm amber light from within, held between two fingers in a completely dark room, the golden light from the chip illuminating only the fingertips and casting dramatic shadows, warm amber core with cool blue edges, visible film grain, subject center, vertical composition 9:16",
          "motion_prompt": "slow push in on glowing chip, warm light intensifying, darkness receding"
        }
      ],
      "voiceover_text": "制裁第二天，海思总裁何庭波发了一封内部信。信里只有一句话让人记住：所有我们曾经打造的备胎，一夜之间全部转正。十年。没有人鼓掌，没有人看见。但它一直在那里。",
      "voiceover_pause_markers": "制裁第二天<#0.3#>海思总裁何庭波发了一封内部信。<#0.5#>信里只有一句话让人记住<#0.5#>所有我们曾经打造的备胎<#0.3#>一夜之间全部转正。<#1.0#>十年。<#0.8#>没有人鼓掌<#0.3#>没有人看见。<#0.5#>但它一直在那里。",
      "subtitle_text": "所有备胎 一夜之间全部转正"
    },
    {
      "id": "S04",
      "type": "cta",
      "duration_sec": 10,
      "shot_type": "close-up",
      "emotion_arc": "warm",
      "yangmun_clip_hint": "day5-yangmun/S05-warm.mp4",
      "story_images": [],
      "voiceover_text": "任正非后来说过一句话：没有伤痕累累，哪来皮糙肉厚。备胎不只是芯片。那些年不被看见的准备，那些年没人理解的坚持，都是你的海思。评论区聊聊，你的备胎准备了几年？",
      "voiceover_pause_markers": "任正非后来说过一句话<#0.3#>没有伤痕累累<#0.2#>哪来皮糙肉厚。<#0.8#>备胎不只是芯片。<#0.5#>那些年不被看见的准备<#0.2#>那些年没人理解的坚持<#0.2#>都是你的海思。<#0.5#>评论区聊聊<#0.2#>你的备胎准备了几年？",
      "subtitle_text": "没有伤痕累累 哪来皮糙肉厚"
    }
  ],
  "voiceover": {
    "engine": "gemini-3.1-flash-tts-preview",
    "voice": "Aoede",
    "sample_rate": 24000,
    "format": "mp3",
    "normalize": true,
    "director_notes": "女声，全部使用Aoede声音保持一致性。S01开头'半夜里手机突然亮了'用低沉近乎耳语，'断了/锁了/撤了'三个词逐个加重，'全球第二'上扬，'不知道能不能活'压低带颤抖。S02'十年前'缓慢，'上百亿'稍加重量，'从来没有被真正依赖过'带一丝心疼，'有人说浪费有人说疯了'稍快带讽刺，'但任正非什么也没说'完全停顿后用极轻声音说出。S03'制裁第二天'中速清晰，何庭波信原文要读得庄重有力仿佛在宣读宣言，'十年'单字读完后长停顿(1秒)，'没有人鼓掌没有人看见'放慢每个短句后都有呼吸，'但它一直在那里'轻而坚定。S04'没有伤痕累累哪来皮糙肉厚'温暖有力像长辈对晚辈说话，'备胎不只是芯片'转换语气像在跟朋友聊天，'都是你的海思'温暖停顿，CTA自然友好带微笑感"
  },
  "reference_images": {
    "engine": "seedream_4.5",
    "api": "evolink",
    "resolution": "1440x2560",
    "candidates_per_segment": 1,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, perfect facial symmetry, symmetric face, centered perfectly symmetrical features, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, oil painting, watermark, text, logo, oversaturated, hyperrealistic, mannequin, doll-like, flawless, magazine cover, retouched, even skin tone, poreless skin, multiple people, group shot, changing face, different person, inconsistent features, aged, child, cartoon character, hands, hand visible"
  },
  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true
  },
  "compositing": {
    "engine": "剪映",
    "note": "v2工作流：不使用FFmpeg拼接。所有素材在剪映手动混剪。杨梦表情视频+故事视频+TTS配音在剪映中交替剪辑。",
    "subtitle_source": "auto_from_script",
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
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和配音"
  },
  "post_production": {
    "film_grain_intensity_pct": 8,
    "lens_glow_intensity_pct": 8,
    "saturation_adjust": 5,
    "contrast_adjust": 5,
    "sharpness_adjust": -3,
    "vignette": 0.3,
    "note": "在剪映完成。v2工作流：杨梦(shock)→故事视频(S01)→杨梦(tension)→故事视频(S02)→杨梦(reversal)→故事视频(S03)→杨梦(warm+CTA)"
  },
  "publishing": {
    "platforms": ["douyin"],
    "title_candidates": [
      "备胎转正那天 全世界都安静了",
      "十年没有名字 但它一直在那里",
      "被制裁那天 任正非什么也没说"
    ],
    "tags": ["任正非", "华为", "备胎", "芯片", "海思", "逆袭", "自强"],
    "xiaohongshu_tags": ["任正非", "华为", "备胎转正", "逆袭", "自强", "自我提升"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "杨梦冷暖交替光影，文字'备胎转正'"
  }
}
```

**Step 2: Validate JSON**

```bash
python3 -c "
import json
c = json.load(open('docs/content/config/day10-yangmun.json'))
assert c['video_id'] == 'day10-yangmun'
assert c['global']['workflow_version'] == '2.0'
assert len(c['segments']) == 4

# v2: no reference_file/reference_prompt/motion_prompt in segments
for seg in c['segments']:
    assert 'reference_file' not in seg, f'{seg[\"id\"]} still has reference_file'
    assert 'reference_prompt' not in seg, f'{seg[\"id\"]} still has reference_prompt'
    assert 'motion_prompt' not in seg, f'{seg[\"id\"]} still has motion_prompt'
    assert 'yangmun_clip_hint' in seg, f'{seg[\"id\"]} missing yangmun_clip_hint'

# v2: story images count = 3 (S01:1, S02:1, S03:1, S04:0)
story_count = sum(len(s.get('story_images', [])) for s in c['segments'])
assert story_count == 3, f'Expected 3 story images, got {story_count}'

print(f'OK: v2 format, {len(c[\"segments\"])} segments, {story_count} story images, no main reference images')
"
```

Expected: `OK: v2 format, 4 segments, 3 story images, no main reference images`

**Step 3: Validate story images script can read it**

```bash
cd docs/content/scripts
python3 -c "
from pathlib import Path
from seedream_story_images import load_story_images
shots = load_story_images(Path('../../config/day10-yangmun.json'))
print(f'Story images: {len(shots)}')
for s in shots:
    print(f'  {s[\"id\"]}: {s[\"output_file\"]}')
"
```

Expected: 3 story image shots (S01-01, S02-01, S03-01).

Note: `seedream-batch.py` will find 0 main shots (no reference_prompt in any segment), which is correct for v2. `kling-gen-batch.py --include-stories` will find 3 story video shots.

**Step 4: Commit**

```bash
git add docs/content/config/day10-yangmun.json
git commit -m "feat: Day10 config v2 format (no main refs, 3 story images, yangmun_clip_hint)"
```

---

### Task 2: Update video-production-spec.md with v2 workflow rules

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md`

**Step 1: Add v2 mode section after the stage overview (around line 38)**

Insert after the Stage 7 line (line 37), before `## 1. 视频全局标准`:

```markdown

---

## 0.1 Medvi v2 工作流（从 Day10 起生效）

> v2 核心变更：跳过 Seedream 主参考图 + Kling 杨梦视频，只生成故事图。杨梦表情素材从已有库选取，在剪映混剪。

### v2 适用标记

当 JSON config 中 `global.workflow_version` 为 `"2.0"` 时，按 v2 规则执行。

### v2 阶段变更

| 阶段 | v1 | v2 | 说明 |
|------|-----|-----|------|
| Stage 2 参考图 | Seedream 主图(4) + 故事图(6) | **只生成故事图(3)** | 跳过 `seedream-batch.py`，只运行 `seedream-story-images.py` |
| Stage 3 视频 | Kling 杨梦(4) + 故事(6) | **只生成故事视频(3)** | `kling-gen-batch.py --include-stories`（无主视频） |
| Stage 5 合成 | FFmpeg 拼接 | **跳过，剪映混剪** | 不运行 FFmpeg compose 脚本 |
| 混剪 | 自动拼接 | **剪映手动** | 杨梦+故事图交替 |

### v2 Config JSON 结构

每个 segment **不含**以下字段：
- `reference_file` — 无杨梦主参考图
- `reference_prompt` — 无杨梦人像 prompt
- `motion_prompt` — 无杨梦视频运动 prompt

每个 segment **新增**：
- `yangmun_clip_hint` — 指示选用哪个已有杨梦表情视频（如 `"day5-yangmun/S01-shock.mp4"`）

故事图规则：
- S01/S02/S03 各 0-1 张（共 3 张）
- S04 (CTA) 无故事图
- 故事图 prompt 不包含角色锚定

### v2 剪映混剪模式

```
杨梦(shock) → 故事视频(S01) → 杨梦(tension) → 故事视频(S02) → 杨梦(reversal) → 故事视频(S03) → 杨梦(warm+CTA)
```

### v2 成本

每条视频约 $0.33（3张 Seedream + 3个 Kling），比 v1 节省 70%。

### v2 杨梦素材库

已有片段按情绪分类：
- **shock**: `day5-yangmun/S01-shock.mp4`
- **tension/determined**: `day5-yangmun/S02-determined.mp4`
- **power**: `day5-yangmun/S03-power.mp4`
- **contemplative**: `day5-yangmun/S04-contemplative.mp4`
- **warm**: `day5-yangmun/S05-warm.mp4`
- **Day6 全套**: `day6-yangmun/S01-S05.mp4` (含 story 视频)
```

**Step 2: Update Stage 2 header (line 483) to note v2 bypass**

After the existing Stage 2 header, add a note:

Find: `## 6. Stage 2：参考图生成（Seedream 4.5）`

After line 483, insert:

```markdown

> **v2 模式：** 当 `workflow_version: "2.0"` 时，跳过主参考图生成（seedream-batch.py），只运行 `seedream-story-images.py` 生成故事场景图。每个 segment 的 `reference_prompt` 字段不存在。
```

**Step 3: Update Stage 3 header (line 693) to note v2 bypass**

After line 693, insert:

```markdown

> **v2 模式：** 当 `workflow_version: "2.0"` 时，跳过主视频生成，只生成故事图视频（`--include-stories`）。脚本会自动发现无主参考图可生成。
```

**Step 4: Update Stage 5 header (line 839) to note v2 bypass**

After line 839, insert:

```markdown

> **v2 模式：** 当 `workflow_version: "2.0"` 时，完全跳过 FFmpeg 合成。所有素材（杨梦表情视频 + 故事视频 + TTS 配音）在剪映中手动混剪。
```

**Step 5: Update the spec version header (line 1)**

Change: `# AI 短视频生产规范 v2.0 — Medvi 工作流`
To: `# AI 短视频生产规范 v3.0 — Medvi 工作流`

Change: `> 最后更新：2026-04-23`
To: `> 最后更新：2026-04-25`

**Step 6: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs: update production spec to v3.0 with Medvi v2 workflow rules"
```

---

### Task 3: Update Day10 implementation plan to match v2

**Files:**
- Modify: `docs/plans/2026-04-25-day10-renzhengfei-impl.md`

**Step 1: Update the plan**

The existing plan (Tasks 2-6) was written for v1 workflow. Replace with v2 workflow tasks:

- Task 2 (Seedream main refs): DELETE — not needed in v2
- Task 3 (Seedream story images): KEEP — change from 6 to 3 images
- Task 4 (Kling videos): CHANGE — only 3 story videos, no main videos, no `--include-stories` needed (just stories)
- Task 5 (TTS): KEEP — unchanged
- Task 6 (FFmpeg compose): DELETE — replaced by 剪映 manual editing
- Task 7 (剪映): UPDATE — now the primary assembly step, not just post-production

New task list:

| # | Task | Description |
|---|------|-------------|
| 1 | Config | day10-yangmun.json v2 format (DONE in Task 1 above) |
| 2 | Story images | 3 Seedream story images only |
| 3 | Story videos | 3 Kling story videos only |
| 4 | TTS | 4 Gemini voiceover segments |
| 5 | 剪映 | Manual mix: Yangmun clips + story videos + TTS + subtitles |

**Step 2: Commit**

```bash
git add docs/plans/2026-04-25-day10-renzhengfei-impl.md
git commit -m "docs: update Day10 impl plan for Medvi v2 workflow (3 images, 3 videos, no FFmpeg)"
```

---

### Task Summary

| Task | Description | Type | Est. Time |
|------|-------------|------|-----------|
| 1 | Create day10-yangmun.json (v2 format) | config | 5 min |
| 2 | Update video-production-spec.md to v3.0 | docs | 5 min |
| 3 | Update Day10 impl plan for v2 | docs | 3 min |
