# Day 1 视频制作执行清单

> 视频ID: day1-medvi-story | 7段情感弧线 | 9:16 竖版
> 预计总耗时：30-45 分钟（自动化脚本驱动）
> 工具链：Seedream 4.5 → Kling 3.0 → Gemini 3.1 Flash TTS → FFmpeg
> **起飞前必读**：`pre-flight-checklist.md`

---

## Phase 1: 参考图生成（自动化）

已完成 7/7，状态：reference_images_approved

- [x] S01 共情 — 穷小子坐在地上（S01-empathy-poor-kid.png）
- [x] S02 向往 — 深夜苦干背影（S02-desire-late-night.png）
- [x] S03 希望 — 抓住AI机会（S03-hope-ai-opportunity.png）
- [x] S04 震撼 — 数据爆发增长（S04-shock-explosive-growth.png）
- [x] S05 对比 — 一人 vs 空旷办公室（S05-contrast-one-vs-many.png）
- [x] S06 喜悦 — 赚到钱的反应（S06-joy-massive-profit.png）
- [x] S07 邀请 — CTA 信任邀请（S07-invitation-cta.png）

```bash
source docs/content/.env
python3 docs/content/scripts/seedream-batch.py --config config/day1-medvi-story.json --dry-run
python3 docs/content/scripts/seedream-batch.py --config config/day1-medvi-story.json
```

---

## Phase 2: 配音生成（自动化）

- [ ] 配置 voiceover.voice（Gemini 声音名，如 Charon）
- [ ] 运行 TTS 脚本生成 7 段配音 + SRT 字幕
- [ ] 检查总时长 30-45s

```bash
source docs/content/.env
python3 docs/content/scripts/gemini-tts-batch.py --config config/day1-medvi-story.json --dry-run
python3 docs/content/scripts/gemini-tts-batch.py --config config/day1-medvi-story.json
```

---

## Phase 3: Kling 3.0 视频生成（自动化）

- [ ] S01: 共情 → slow push in, subtle ambient light shift
- [ ] S02: 向往 → slow push in, screen glow flickers slightly
- [ ] S03: 希望 → slow zoom in, screen glow subtly intensifies
- [ ] S04: 震撼 → slow zoom in on screen, numbers appear to shift
- [ ] S05: 对比 → slow wide pan from empty desks to the single lit desk
- [ ] S06: 喜悦 → subtle celebratory movement, warm light shift
- [ ] S07: 邀请 → gentle nod, warm light steady

```bash
source docs/content/.env
python3 docs/content/scripts/kling-gen4-batch.py --config config/day1-medvi-story.json --dry-run
python3 docs/content/scripts/kling-gen4-batch.py --config config/day1-medvi-story.json --turbo
python3 docs/content/scripts/kling-gen4-batch.py --config config/day1-medvi-story.json  # Gen-4 final
```

### 后处理（Kling UI 手动）

- [ ] 每个片段：Trim 裁掉不稳定帧
- [ ] 每个片段：Handheld Shake 10-15%
- [ ] 最终片段：4K Upscale

---

## Phase 4: FFmpeg 合成（自动化）

- [ ] 运行合成脚本：配音驱动时长 + 视频片段拼接 + 去AI后期
- [ ] 检查输出文件

```bash
python3 docs/content/scripts/ffmpeg-compose-day1.py --config config/day1-medvi-story.json
```

去AI后期参数（已内置于脚本）：
- 胶片颗粒 noise=c0s=12
- 对比度 +8%, 饱和度 -8%
- 暗角 vignette=0.3
- 锐度 -3

---

## Phase 5: 导出 & 发布

- [ ] 导出 MP4（1080x1920，24fps）
- [ ] 确认 AI 标识已嵌入（显性水印 + 元数据）
- [ ] 写标题（3 选 1）：
  - 2万启动，14个月4亿营收，AI获客全拆解
  - 2个人用AI做到4亿美元年营收，工具链全公开
  - 在拖车公园长大的人，用AI做出了4亿营收的公司
- [ ] 添加标签：#AI获客 #AI营销 #人工智能 #创业 #一人公司
- [ ] 发布时勾选 "AI生成内容" 声明
- [ ] 发布时间：12:00 或 18:00
- [ ] 记录发布数据到 tracking 表

---

## 完成标志

- [ ] 视频已发布到抖音/小红书
- [ ] 工作流优化点记录到 video-production-spec.md
