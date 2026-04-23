# Medvi 工作流故事图增强设计

> **状态：已批准**
> **日期：2026-04-23**

## 问题

1. **TTS 引擎降级**：Day7 用了 Doubao TTS 而非 Medvi 规范要求的 Gemini TTS。需要自动降级机制。
2. **图片数量不足**：当前每个 segment 只有 1 张杨梦情绪图，缺少文案内容对应的故事场景图。导致视频只有 25s 而音频 73.4s，内容单调。

## 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 图片用法 | 穿插模式 | 保留角色情绪锚点图，中间穿插故事场景图 |
| 故事图风格 | Seedream 写实场景 | 统一生成管线，同风格 |
| 每条视频图片数 | 10-15 张 | 每段主图 + 1-2 张故事图 |
| 时间分配 | 段内均匀分配 | 简单可靠 |
| Config 结构 | 分层 Segment（方案 A） | 现有脚本改动最小 |
| TTS 策略 | Gemini 优先 + 自动降级 Doubao | 按额度自动切换 |

## Section 1：JSON Config 结构变更

每个 segment 新增 `story_images` 可选数组：

```json
{
  "id": "S02",
  "type": "body",
  "duration_sec": 15,
  "shot_type": "medium",
  "emotion_arc": "tension",
  "reference_file": "day7-yangmun/S02-tension.png",
  "reference_prompt": "杨梦情绪图 prompt...",
  "motion_prompt": "slow push in, subtle head movement",
  "voiceover_text": "...",
  "voiceover_pause_markers": "...",
  "subtitle_text": "铁律一：忙碌是最隐蔽的偷懒",

  "story_images": [
    {
      "id": "S02-01",
      "trigger_text": "你做100遍的表格",
      "reference_prompt": "35mm documentary film still grainy imperfect focus, exhausted office worker hunched over cluttered desk with scattered papers and coffee cups, Dell monitor showing spreadsheet, fluorescent office light overhead creating harsh shadows, vertical composition 9:16",
      "motion_prompt": "slow zoom out, subtle ambient movement"
    },
    {
      "id": "S02-02",
      "trigger_text": "AI只要3秒",
      "reference_prompt": "shot on Canon 5D Mark IV, close-up of computer screen displaying AI interface generating results, warm glow from screen illuminating keyboard, dark room, vertical composition 9:16",
      "motion_prompt": "slow push in on screen, data subtly moving"
    }
  ]
}
```

**字段说明：**
- `story_images`：可选数组，每段 0-3 张故事图
- `id`：全局唯一，格式 `{segment_id}-{序号}`
- `trigger_text`：该图对应的旁白片段，用于标注对应关系
- `reference_prompt`：遵循 6 层 prompt 结构（spec 6.3 节）
- `motion_prompt`：只写运动，不重复描述画面

**文件命名：**
- 主图：`assets/references/{video_id}/S02.png`
- 故事图：`assets/references/{video_id}/S02-01.png`、`S02-02.png`
- 视频同理：`output/{video_id}/S02.mp4`、`S02-01.mp4`、`S02-02.mp4`

## Section 2：脚本变更

### 2.1 seedream-batch.py

**当前逻辑：** 遍历 segments，每段生成 1 张图。

**改后逻辑：**
1. 遍历 segments
2. 每段先生成主图（reference_prompt）
3. 检查 `story_images` 数组是否存在
4. 如果存在，遍历 story_images，为每张生成图片
5. 所有图片输出到 `assets/references/{video_id}/`

### 2.2 kling-gen4-batch.py

**当前逻辑：** 遍历 segments，每段用主图生成 1 段视频。

**改后逻辑：**
1. 遍历 segments
2. 每段先为主图生成 Kling 视频
3. 检查 `story_images` 数组
4. 如果存在，为每张故事图分别生成 Kling 视频
5. 所有视频输出到 `output/{video_id}/`

### 2.3 compose-video.py (FFmpeg 合成)

**当前逻辑：** 按 segment 顺序硬切拼接视频，配音驱动总时长。

**改后逻辑：**
1. 计算每段配音时长（从各段 mp3 文件获取）
2. 每段内的视频（主图 + 故事图）均匀分配该段配音时长
   - 例：S02 配音 15s，有 3 张图（1 主图 + 2 故事图），每张 5s
3. 用 FFmpeg 的 `-t` 参数裁剪每段视频到指定时长
   - 如果 Kling 视频（5s）短于分配时长，循环播放（`-stream_loop -1`）
   - 如果 Kling 视频长于分配时长，裁剪
4. 所有视频硬切拼接，配音音轨覆盖

## Section 3：TTS 自动降级策略

**优先级：**
1. Gemini TTS (Charon 声音) — Medvi 规范首选
2. Doubao TTS (claire 声音) — 自动降级备选

**降级规则：**
- Gemini API 返回 429（配额）或 403（权限）时自动降级
- 降级时打印提示：`Gemini TTS quota exceeded, falling back to Doubao TTS`
- 降级后在 config 的 voiceover 字段标记 `"engine": "doubao_tts_fallback"`
- 同一条视频不混用两个 TTS 引擎（要么全 Gemini，要么全 Doubao）

**实现位置：** `gemini-tts-batch.py` 的 API 调用异常处理中。

## Section 4：Medvi Spec 变更清单

需要修改 `video-production-spec.md` 的以下部分：

| 章节 | 变更内容 |
|------|---------|
| Stage 1 脚本 | 写作时同步标注 story_images 的 trigger_text 和画面描述 |
| Stage 2 参考图 | 新增"故事图"概念：每段可包含主图 + N 张故事图，总图数 10-15 张 |
| Stage 2 Prompt | 故事图 prompt 遵循 6 层结构，不需要角色锚定 |
| Stage 3 视频 | 所有图片（主图 + 故事图）都生成 Kling 视频 |
| Stage 5 合成 | 段内均匀分配时间，循环短片段，硬切拼接 |
| Stage 4 配音 | TTS 引擎优先级：Gemini → Doubao 自动降级 |

## 影响范围

**修改文件：**
- `docs/content/workflow/video-production-spec.md` — 规范文档
- `docs/content/scripts/seedream-batch.py` — 故事图生成
- `docs/content/scripts/kling-gen4-batch.py` — 故事图视频生成
- `docs/content/scripts/compose-video.py` — 多图拼接合成
- `docs/content/scripts/gemini-tts-batch.py` — TTS 降级逻辑
- `docs/content/config/day7-yangmun.json` — 添加 story_images 示例

**成本影响：**
- Seedream：每条视频从 ~5 张增加到 ~12 张，成本从 $0.15 增加到 ~$0.36
- Kling：每条视频从 ~5 段增加到 ~12 段，Turbo 模式成本可控
- 总成本每条视频增加约 $0.5-1.0
