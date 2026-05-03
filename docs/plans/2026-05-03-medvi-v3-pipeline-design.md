# Medvi v3 Pipeline Design — 失业系列生产自动化

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Zhang Wei #1 视频的 ad-hoc 生产方式（Playwright 截图 + Unsplash 空镜 + FFmpeg 完整合成 + BGM + 开场钩子 + 上传文案）集成到 Medvi 工作流，实现 config-driven 一键生产。

**Architecture:** 单脚本 CLI 入口（medvi-produce.py）+ 通用合成脚本（medvi-compose.py），复用现有子脚本（screenshot-renderer, unsplash-downloader, text-card-renderer, gemini-tts-batch）。每条视频只需一个 JSON config 即可驱动全流程。

**Tech Stack:** Python 3, FFmpeg, Playwright, Unsplash API, Gemini TTS API

---

## 1. Medvi v3 工作流架构变更

当前 v4.2 spec：7 阶段（Seedream + Kling + Gemini TTS + 剪映混剪）

v3 变更（失业系列专用，不覆盖名人系列）：

| Stage | v4.2 | v3（失业系列） | 变更原因 |
|-------|------|---------------|---------|
| Stage 2 参考图 | Seedream AI 生图 | **Playwright UI 截图** | 截图像素级真实，免费，秒级完成 |
| Stage 2.5 空镜 | 不存在 | **Unsplash 图库下载** | 免费高质量氛围照，无需 AI 渲染 |
| Stage 3 视频 | Kling 3.0 视频生成 | **跳过** | 静态图 + FFmpeg zoompan 替代，省 $0.33/条 |
| Stage 4 配音 | Gemini TTS Aoede | **Gemini TTS Charon** | 失业系列用男声第一人称自述 |
| Stage 5 合成 | FFmpeg 简单拼接 | **FFmpeg 完整合成**（含开场+BGM+文字卡片） | 剪映只做字幕+后期 |
| Stage 6 后期 | 剪映 4 步去AI | **简化**（截图不需要去AI） | Playwright 截图天然真实 |
| 新增 | 不存在 | **开场钩子**（1.5s 统一片头） | 解决 2 秒跳出率 |
| 新增 | 不存在 | **BGM 混音**（FFmpeg amix） | 视频质感提升 |
| 新增 | 不存在 | **上传文案生成** | 抖音/小红书文案模板 |

关键原则不变：FFmpeg 不做剪映的活。字幕、色彩、去AI滤镜仍由剪映完成。但 v3 的 FFmpeg 做更多"结构合成"（开场+文字卡片+空镜+截图+配音+BGM → 粗剪 MP4）。

---

## 2. Config JSON Schema（v3 失业系列）

```json
{
  "video_id": "unemploy-story-01-zhangwei",
  "version": "3.0",
  "series": "unemploy-story",
  "workflow_mode": "unemploy",

  "global": {
    "target_duration_sec": 80,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon",
    "opening_file": "unemploy-story-opening-v1.mp4"
  },

  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "S01", "emotion": "代入", "text": "38岁，建材行业干了12年..."},
      {"id": "S02", "emotion": "希望", "text": "失业第三个月..."}
    ]
  },

  "screenshots": [
    {"id": "SS01", "template": "tpl-boss-search-zhangwei.html", "output": "SS01-boss-search.png"},
    {"id": "SS02", "template": "tpl-resume-stats-zhangwei.html", "output": "SS02-resume-stats.png"}
  ],

  "atmosphere": [
    {"id": "AT01", "query": "empty warehouse industrial", "output": "AT01-warehouse.jpg"},
    {"id": "AT02", "query": "desk lamp night workspace", "output": "AT02-desk-lamp.jpg"}
  ],

  "text_cards": [
    {"id": "TC01", "lines": ["12年经验", "在HR眼里 就是一张废纸"], "style": "medvi", "bg_image": "AT02-desk-lamp.jpg"},
    {"id": "TC02", "lines": ["你的经验 不是废纸", "是没包装过的产品"], "style": "medvi", "bg_image": "AT05-laptop-desk.jpg"},
    {"id": "TC03", "lines": ["你做什么行业？", "评论区打出来 我帮你拆"], "style": "medvi", "bg_image": "AT06-coffee-shop.jpg"}
  ],

  "storyboard": [
    {"segment": "S01", "clips": [
      {"type": "screenshot", "ref": "SS01", "zoom": false, "pct": 0.55},
      {"type": "screenshot", "ref": "SS02", "zoom": true, "pct": 0.45},
      {"type": "text_card", "ref": "TC01", "duration": 4.0}
    ]},
    {"segment": "S02", "clips": [
      {"type": "atmosphere", "ref": "AT01", "zoom": true, "pct": 0.3},
      {"type": "screenshot", "ref": "SS03", "zoom": false, "pct": 0.4},
      {"type": "atmosphere", "ref": "AT02", "zoom": true, "pct": 0.3}
    ]}
  ],

  "bgm": {
    "file": "synth-pad-placeholder.mp3",
    "volume": 0.08,
    "fade_in": 2.0,
    "fade_out": 3.0
  },

  "upload_copy": {
    "platform": "douyin",
    "title_candidates": [
      "12年经验在HR眼里就是废纸？他失业后靠经验月赚4000",
      "失业后被装修群一个红包点醒：12年经验不该是废纸"
    ],
    "tags": ["#失业", "#经验变现", "#38岁", "#被裁员", "#中年危机"]
  }
}
```

核心设计决策：
- `storyboard` 数组替代旧的 `segments[].reference_prompt/motion_prompt`
- `screenshots` / `atmosphere` / `text_cards` 三个资产清单独立声明，storyboard 通过 ref 引用
- `voiceover.segments` 独立于 storyboard——配音按段划分，分镜按 clip 划分
- `bgm` 和 `upload_copy` 是新增的顶层配置

---

## 3. CLI 入口 + 通用合成脚本

### 3.1 medvi-produce.py

```bash
# 全流程
python3 scripts/medvi-produce.py --config config/unemploy-story-01-zhangwei.json

# 单阶段
python3 scripts/medvi-produce.py --config config/xxx.json --stage screenshots
python3 scripts/medvi-produce.py --config config/xxx.json --stage atmosphere
python3 scripts/medvi-produce.py --config config/xxx.json --stage voiceover
python3 scripts/medvi-produce.py --config config/xxx.json --stage textcards
python3 scripts/medvi-produce.py --config config/xxx.json --stage compose
python3 scripts/medvi-produce.py --config config/xxx.json --stage upload_copy

# 跳过某些阶段
python3 scripts/medvi-produce.py --config config/xxx.json --skip screenshots,voiceover
```

### 3.2 阶段映射

| Stage | 调用的脚本 | 输入 | 输出 |
|-------|-----------|------|------|
| screenshots | screenshot-renderer.py | config 中 screenshots[].template | assets/screenshots/{video_id}/ PNG |
| atmosphere | unsplash-downloader.py | config 中 atmosphere[].query | assets/unsplash/{video_id}/ JPG |
| voiceover | gemini-tts-batch.py | config 中 voiceover.segments | assets/voiceover/{video_id}/ MP3 |
| textcards | text-card-renderer.py | config 中 text_cards[] | assets/textcards/{video_id}/ MP4 |
| compose | medvi-compose.py（新） | storyboard + 所有资产 | output/{video_id}/ MP4 |
| upload_copy | 内置模板渲染 | config 中 upload_copy | assets/upload-copy/ MD |

### 3.3 medvi-compose.py 核心逻辑

1. 读取 config JSON
2. 检测配音文件，获取每段时长
3. Prepend 开场钩子（opening_file re-encode 到 24fps）
4. 遍历 storyboard，对每个 clip：
   - screenshot → image_to_video()（无 zoom 或 zoompan）
   - atmosphere → image_to_video()（无 zoom 或 zoompan）
   - text_card → re-encode 到 24fps 1080x1920
   - pct 决定该 clip 占 segment 时长比例（扣除 text_card 固定时长后）
5. 逐 segment concat → merge voiceover → 收集所有 segment clips
6. Final concat all segments
7. BGM 混音（amix）
8. 输出粗剪 MP4

关键函数（从 compose-unemploy-story-01.py 提取）：
- image_to_video(image, duration, output, zoom=False)
- concat_video_audio(video, audio, output)
- get_duration(path)
- build_segment_clips(segment_id, clips_config, voiceover_dur) — 新增

---

## 4. video-production-spec.md 更新内容

在现有 v4.2 spec 基础上新增"失业系列 v3 模式"章节，不覆盖原有内容。

### 新增章节

- §0.2 工作流模式路由（workflow_mode 字段决定走哪套规则）
- §2.5 开场钩子规范（1.5s 统一片头，从 unemploy-story-opening-spec.md 精简合并）
- §6.5 Playwright UI 截图（模板目录、渲染工具、模板类型）
- §6.6 Unsplash 氛围空镜（下载工具、搜索关键词、自动选图）
- §9.3 v3 FFmpeg 合成管线（完整结构合成：开场+clips+配音+BGM）
- §9.5 上传文案模板（标题+正文+标签通用模板）

### 修改的现有章节

- §8.4 配音：新增 Charon 男声选项，失业系列 override Aoede 规则
- §9.0 FFmpeg 分工原则：补充 v3 模式下 FFmpeg 做结构合成+BGM混音
- §12 Config Schema：新增 v3 字段

---

## 5. 文件清单

### 新建文件

| 文件 | 说明 |
|------|------|
| scripts/medvi-produce.py | CLI 入口，解析 config，按 stage 调度子脚本 |
| scripts/medvi-compose.py | 通用合成脚本，从 compose-unemploy-story-01.py 重构 |

### 修改文件

| 文件 | 改动 |
|------|------|
| workflow/video-production-spec.md | 新增 v3 章节 + schema 更新 |

### 不动的文件（复用）

| 文件 | 角色 |
|------|------|
| scripts/screenshot-renderer.py | Stage screenshots |
| scripts/unsplash-downloader.py | Stage atmosphere |
| scripts/text-card-renderer.py | Stage textcards |
| scripts/gemini-tts-batch.py | Stage voiceover |

### 不做的事

- 不改 v2 杨梦系列的任何逻辑
- 不加 GUI / Web 界面
- 不做 config schema 校验库
- 不合并多个 TTS 脚本

---

## 6. 设计决策记录

1. **方案 A 单脚本 CLI** 而非 Pipeline class 或 Makefile — YAGNI，改动最小
2. **storyboard 配置驱动** 而非硬编码分镜 — 新视频只写 JSON config
3. **v3 作为失业系列专用** 而非替换 v2 — 名人系列和杨梦系列不受影响
4. **FFmpeg 做结构合成但不做视觉处理** — 保持与剪映的分工边界
