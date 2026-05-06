# Day 3 AI头像视频 — Prompt Reveals 全自动生产管线

## 概述

用 GPT-4o（云雾API）+ DALL-E 3 + Gemini TTS + HTML截图 + FFmpeg 全自动生产 Day 3 "AI画头像"视频。目标是账号破圈（114粉丝，当前500-900播放量）。

## 生产流程

```
GPT-4o优化脚本 → Gemini TTS配音 → DALL-E 3生图 → HTML截图+数据卡 → FFmpeg拼接 → 剪映后期
```

## Step 1: GPT-4o 优化脚本

- API: 云雾AI (yunwu.ai) 提供的 GPT-4o
- 输入: Day3 v2 config JSON
- 输出: 优化后的 config JSON（更精准的文案、visual_note、capcut_search）
- 模型: `gpt-4o` via yunwu.ai OpenAI-compatible endpoint
- 成本: ~¥0.2

## Step 2: Gemini TTS 配音

- 脚本: `gemini-tts-batch.py`（已有）
- 声音: Charon 男声
- 情绪: bitter/shock/pivot_attempt/hopeful/warm_unemploy
- 降级链: Google直接 → yunwuAI Gemini代理
- 成本: ¥0（免费额度）

## Step 3: DALL-E 3 生图

- 需要生成的图片:
  1. 橘猫宇航员（S04 Prompt Reveal核心图）
  2. 真实猫咪参考照风格图（S06 Before/After 对比用）
  3. AI头像示例图（S03 对比用）
  4. 投票卡片背景图（可选）
- API: OpenAI DALL-E 3 via yunwu.ai
- 分辨率: 1024×1024（竖版视频需要裁切）
- 成本: ~¥1.0（4张 × $0.04）

## Step 4: HTML 模板截图

已有脚本: `screenshot-renderer.py`, `text-card-renderer.py`

需要新增的模板:
1. `tpl-wechat-moments.html` — 模拟朋友圈截图（3条消息，0评论0点赞）
2. `tpl-wechat-chat.html` — 模拟微信聊天截图（猫画头像对话）
3. `tpl-vote-card.html` — 投票卡片（AI头像¥10 值/不值）
4. `tpl-prompt-reveal.html` — Prompt文字展示卡片（逐字打出效果截图）

已有可复用的模板:
- `tpl-income-4000.html` — 收入数据卡（参考改造为Day3收入¥30）
- `tpl-douyin-comment.html` — 评论区截图
- `tpl-xianyu-post.html` — 闲鱼帖子截图

## Step 5: FFmpeg 拼接

新建脚本: `compose-day3-prompt-reveal.py`

流程:
1. 每个 segment 独立渲染（图片/截图 + 配音音频）
2. 叠加 BGM（heartbeat-60bpm.m4a，音量8%）
3. 最终 concat 所有 segment
4. 输出: `output/unemploy-day3-ai-portrait/unemploy-day3-ai-portrait-rough-cut.mp4`

参考: `compose-unemploy-story-01.py` 的模式

Segment 映射:
- S01 (hook): 黑底文字卡 → AI界面截图
- S02 (fail): 朋友圈截图 + 倒计时
- S03 (pivot): 左右对比分屏截图
- S04 (prompt reveal): Prompt文字卡 → DALL-E猫咪图
- S05 (chat): 微信聊天截图
- S06 (comparison): Before/After对比截图
- S07 (data): 收入数据卡
- S08 (debate): 投票卡片

## Step 6: 剪映后期（手动）

- 添加字幕（剪映自动识别）
- Pattern interrupt 动画（缩放/闪烁/文字弹出）
- 滤镜调色
- AI生成内容标注水印

## 预估成本

| 环节 | API | 成本 |
|------|-----|------|
| GPT-4o 优化脚本 | 云雾AI | ¥0.2 |
| Gemini TTS 配音 | Google/云雾 | ¥0 |
| DALL-E 3 生图 ×4 | 云雾AI | ¥1.0 |
| HTML截图 + 数据卡 | 本地 | ¥0 |
| FFmpeg拼接 | 本地 | ¥0 |
| **总计** | | **~¥1.2** |

## 需要新建的文件

1. `scripts/dalle-gen-batch.py` — DALL-E 3 批量生图（via yunwu.ai）
2. `scripts/compose-day3-prompt-reveal.py` — Day3 FFmpeg拼接
3. `scripts/gpt-script-optimizer.py` — GPT-4o 脚本优化（via yunwu.ai）
4. `templates/tpl-wechat-moments.html` — 朋友圈截图模板
5. `templates/tpl-wechat-chat.html` — 微信聊天截图模板
6. `templates/tpl-vote-card.html` — 投票卡片模板
7. `templates/tpl-prompt-reveal.html` — Prompt展示卡片模板

## 需要更新的文件

1. `config/unemploy-day3-ai-portrait.json` — 增加 screenshots、text_cards、images 字段
2. `scripts/medvi-produce.py` — 增加 dalle 和 gpt-optimize stage（可选）

## 成功标准

- 粗剪 mp4 输出（35秒，1080×1920）
- 配音清晰自然，情绪到位
- Prompt Reveal 画面有视觉冲击力
- Before/After 对比清晰可辨
- 剪映后期后发布，观察24小时数据

## 风险

- 云雾AI DALL-E 3 可能不支持图片生成（需验证）
- 备选: Seedream 4.5 (Evolink) 已有管线，可作为图片生成降级方案
- 微信截图模板可能需要多轮调参
