# Medvi 工作流 v2.0 设计文档

**Date:** 2026-04-25
**Status:** design_approved
**Impact:** 所有未来 Medvi 视频（Day10+）

---

## 1. 变更原因

已有 21 个杨梦表情视频片段（Day5/6/7），覆盖 shock/tension/reversal/warm 等情绪。继续为每个新视频生成4张 Seedream 杨梦人像 + 4个 Kling 杨梦视频是浪费。新流程跳过这些步骤，只生成故事场景图和视频。

**节省：** 每条视频 70% API 成本 + 50% 制作时间。

---

## 2. 新流程对比

### v1 (旧，Day4-9)

```
Seedream 主参考图(4张) → Kling 杨梦视频(4个) ─┐
Seedream 故事图(6张) → Kling 故事视频(6个) ───┤→ FFmpeg 拼接 → 剪映
TTS 配音(4段) ─────────────────────────────────┘
```

### v2 (新，Day10+)

```
[跳过] Seedream 主参考图 + Kling 杨梦视频
Seedream 故事图(3张) → Kling 故事视频(3个) ──→ 剪映混剪
TTS 配音(4段) ─────────────────────────────────→ 剪映合并音频
已有杨梦表情视频(从素材库选取) ──────────────→ 剪映交替混剪
```

---

## 3. Config JSON 结构变更

### 删除的字段（每个 segment）

- `reference_file` — 不再需要杨梦人像参考图
- `reference_prompt` — 不再需要杨梦人像 prompt
- `motion_prompt` — 不再需要杨梦视频运动 prompt

### 保留的字段

- `id`, `type`, `duration_sec`, `shot_type`, `emotion_arc` — 不变
- `story_images` — 改为每段最多1张（S01/S02/S03各1张，S04无）
- `voiceover_text`, `voiceover_pause_markers` — 配音不变
- `subtitle_text` — 字幕不变

### 新增字段

- `yangmun_clip_hint` — 指示应选用哪种杨梦表情视频（shock/tension/reversal/warm），供剪映手动混剪参考

### 示例 segment（v2 格式）

```json
{
  "id": "S01",
  "type": "hook",
  "duration_sec": 10,
  "emotion_arc": "shock",
  "yangmun_clip_hint": "day5-yangmun/S01-shock.mp4",
  "story_images": [
    {
      "id": "S01-01",
      "trigger_text": "美国对华为实施全面制裁",
      "reference_file": "day10-yangmun/S01-01.png",
      "reference_prompt": "...",
      "motion_prompt": "..."
    }
  ],
  "voiceover_text": "...",
  "voiceover_pause_markers": "...",
  "subtitle_text": "..."
}
```

---

## 4. 故事图规则

- **S01/S02/S03：** 各1张故事图，共3张
- **S04 (CTA)：** 无故事图
- 每张故事图配1个 Kling 视频（5秒）
- 故事图 prompt 不包含杨梦角色，只描述故事场景

---

## 5. 剪映混剪模式

交替模式：

```
杨梦(shock) → 故事视频(S01) → 杨梦(tension) → 故事视频(S02) → 杨梦(reversal) → 故事视频(S03) → 杨梦(warm+CTA)
```

杨梦素材来源：
- `docs/content/output/day5-yangmun/` — 6个片段
- `docs/content/output/day6-yangmun/` — 14个片段
- 按 `yangmun_clip_hint` 选择对应情绪片段

---

## 6. 受影响的文件

| 文件 | 变更 |
|------|------|
| `docs/content/workflow/video-production-spec.md` | 更新 Stage 2-5 规则，标记主参考图为可选 |
| `docs/content/config/day10-yangmun.json` | 按 v2 结构创建（无 reference_file/prompt/motion_prompt） |
| `docs/content/scripts/seedream-batch.py` | 不变（不生成主参考图时不运行此脚本） |
| `docs/content/scripts/seedream-story-images.py` | 不变 |
| `docs/content/scripts/kling-gen-batch.py` | 只用 `--include-stories` 生成故事视频 |
| `docs/content/scripts/gemini-tts-batch.py` | 不变 |
| FFmpeg compose | 不再使用（剪映替代） |

---

## 7. 成本对比

| 组件 | v1 | v2 | 节省 |
|------|-----|-----|------|
| Seedream 图 | 10张 ($0.30) | 3张 ($0.09) | $0.21 |
| Kling 视频 | 10个 ($0.80) | 3个 ($0.24) | $0.56 |
| **每条总计** | ~$1.10 | ~$0.33 | **70%** |
| 制作时间 | ~30min | ~15min | **50%** |

---

## 8. 执行规则（永久生效）

从 Day10 开始，所有 Medvi 工作流视频遵循以下规则：

1. **不生成 Seedream 主参考图**（杨梦人像）
2. **不生成 Kling 杨梦视频**
3. **只生成3张故事图**（S01/S02/S03各1张）
4. **只生成3个 Kling 故事视频**
5. **TTS 配音照常生成**（4段）
6. **不使用 FFmpeg 拼接**，所有素材交给剪映混剪
7. **杨梦素材从已有库选取**，按 `yangmun_clip_hint` 匹配
