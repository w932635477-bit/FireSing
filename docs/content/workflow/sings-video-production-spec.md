# AI 短视频生产规范 v1.0 — Sings 工作流

> 适用范围：30-45 秒 AI 生成说唱科普短视频，抖音/小红书竖版
> 工具链：Seedream 4.5 + Runway Gen-4 + Suno AI + FFmpeg + 剪映
> 工作流类型：**Sings**（说唱科普风格 FireSing 推广，音乐节拍驱动）
> 本文档是 Sings 工作流的唯一权威标准
> 最后更新：2026-04-18

---

## 0. Sings vs Medvi 快速对照

| 维度 | Medvi 工作流 | Sings 工作流 |
|------|-------------|-------------|
| 内容风格 | 电影纪录片商业内容 | 说唱科普 FireSing 推广 |
| 驱动方式 | 旁白时长驱动 | BPM + 小节数驱动 |
| 脚本格式 | 旁白文字，≤15字/句 | 说唱歌词，押韵，4/4拍 |
| 音频管线 | Gemini 3.1 Flash TTS | Suno AI (完整说唱曲目) |
| 视觉风格 | 深色暖金纪录片 | 高对比 MV 风格 |
| 配色 | 暖金 #c9a96e + 纯黑 | 品牌紫蓝 + 高对比 |
| 景别节奏 | 每 3-5 秒切换 | 每 2-4 拍切换 |
| 字幕风格 | 白底黑描边，金色高亮 | 动态歌词（KTV/MV 风格） |

**共用的管线**：Seedream 参考图、Runway 视频生成、FFmpeg 合成、剪映后期、去 AI 化 4 步法。

---

## 1. 视频全局标准

### 1.1 时长

| 规则 | 标记 | 值 |
|------|------|----|
| 最终时长 30-45 秒 | MUST | ffprobe 检查 |
| BPM 甜点区间 120-140 | SHOULD | 节奏感好，不太快 |
| 钩子 = 前 2 小节 | MUST | 约 4 秒 |
| 主体 = 中间 12-20 小节 | MUST | |
| CTA = 最后 4 小节 | MUST | 约 8 秒 |
| 超过 45.0 秒 = 拒绝 | MUST | Stage 7 门控 |

**时长计算公式**：`总时长(秒) = 总拍数 / BPM × 60`
- 120 BPM, 16 小节(64 拍) = 32 秒
- 120 BPM, 24 小节(96 拍) = 48 秒 → 需要压缩到 20 小节
- 130 BPM, 16 小节(64 拍) = 29.5 秒
- 130 BPM, 20 小节(80 拍) = 36.9 秒（甜点）

### 1.2 分辨率和编码

| 规则 | 标记 | 值 |
|------|------|----|
| 导出分辨率 1080x1920 | MUST | 9:16 竖版 |
| Runway 输出 720x1280 | MUST | 后期升采样 |
| 参考图 1440x2560 | MUST | Seedream API 原生 9:16 2K |
| 帧率 24fps | MUST | |
| 编码 H.264 MP4 | MUST | |
| 码率 ≥ 8Mbps | MUST | |
| FFmpeg 导出参数 | MUST | `-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p` |

### 1.3 镜头数量和类型

| 规则 | 标记 | 值 |
|------|------|----|
| 每条视频 6-8 个镜头 | MUST | 不超过 8 个 |
| 单镜头对应 2-4 小节 | MUST | 按节拍对齐 |
| 至少 2 种景别 | MUST | {远景, 中景, 特写, 文字卡片} |
| 连续相同景别不超过 2 个镜头 | MUST | |

**景别定义（同 Medvi）：**

| 景别 | 用途 | 占比参考 |
|------|------|---------|
| 远景（Wide） | 开场/转场/结尾 | ~15% |
| 中景（Medium） | 主体展示/概念演示 | ~45% |
| 特写（Close-up） | 情感冲击/细节强调 | ~30% |
| 文字卡片（Text） | 歌词/数据/CTA | ~10% |

---

## 2. 钩子设计规范（前 2 小节）

### 2.1 第一帧

| 规则 | 标记 |
|------|------|
| 第 1 帧必须包含可见文字或视觉冲击元素 | MUST |
| 歌词第一句在前 2 秒内出现 | MUST |
| 画面色彩高对比、抓眼球 | MUST |

### 2.2 钩子歌词

| 规则 | 标记 |
|------|------|
| 钩子歌词 2-4 行，每行 ≤ 10 字 | MUST |
| 第一句必须包含好奇心缺口或反常识 | MUST |
| 押韵但不刻意 | SHOULD |

### 2.3 钩子类型（优先级排序）

| 优先级 | 类型 | 示例 | 3 秒留存率 |
|--------|------|------|-----------|
| 1 | 好奇缺口 | "你知道歌曲能换个嗓子唱吗" | 60-70% |
| 2 | 反常识 | "AI翻唱比原唱还像本人" | 55-65% |
| 3 | 数字冲击 | "10秒把周杰伦变成林俊杰" | 55-65% |
| 4 | 身份筛选 | "如果你也想用自己的声音翻唱" | 50-60% |

---

## 3. 歌词规范

### 3.1 格式

| 规则 | 标记 |
|------|------|
| 100% 旁白有对应歌词字幕 | MUST |
| 押韵格式 AABB 或 ABAB | SHOULD |
| 关键词用品牌色高亮 | MUST |

### 3.2 歌词字幕样式

| 规则 | 标记 |
|------|------|
| 动态逐字/逐行出现（KTV 风格） | MUST |
| 当前唱到的行放大高亮，已唱行缩小变暗 | MUST |
| 字幕位置底部居中，留出平台 UI 安全区 | SHOULD |

### 3.3 歌词写作规则

| 规则 | 值 | 标记 |
|------|----|------|
| 每行字数 | ≤ 10 个中文字 | MUST |
| 总行数 | 16-24 行（对应小节数） | MUST |
| 押韵密度 | 每 4 行至少 2 行押韵 | SHOULD |
| 信息密度 | 每 2 行至少 1 个知识点或产品功能点 | MUST |
| 套话禁止 | 不用"今天给大家带来"、"大家好" | MUST |

---

## 4. CTA 规范

### 4.1 位置

| 规则 | 标记 |
|------|------|
| CTA 占据最后 4 小节（约 8 秒） | MUST |
| CTA 同时出现在歌词和画面文字卡片上 | MUST |

### 4.2 内容

| 规则 | 标记 |
|------|------|
| 只要求一个动作 | MUST |
| 使用批准的模板之一 | MUST |
| 关键词 ≤ 6 个中文字 | MUST |

**批准的 CTA 模板：**
```
模板 A："关注我，[下期预告]"
模板 B："私信'[关键词]'，我发你[交付物]"
模板 C："评论区扣1，免费体验[功能]"
```

---

## 5. Stage 1：歌词脚本写作

### 5.0 核心原则：歌词必须从 Medvi 台词转化

> Sings 歌词不是独立创作的。每条 Sings 歌词必须对应一条 Medvi 旁白脚本，逐段转化。

**工作流程：**
1. 先按 Medvi 工作流写好完整旁白脚本（`segments[].voiceover`）
2. 将每段旁白台词转化为对应的歌词小节（`lyrics.bars`）
3. 歌词必须保留原旁白的所有核心信息和数据点
4. 画面描述（`segments[].reference_prompt`）与 Medvi 共用，只改风格参数

**转化规则：**

| Medvi 旁白 | Sings 歌词 |
|------------|-----------|
| 每句 ≤15 字 | 每行 ≤10 字（拆分或压缩） |
| 无押韵要求 | 必须押韵 |
| 叙述语气 | 说唱节奏感 |
| 保留所有数字和数据 | 保留所有数字和数据（MUST） |
| 保留 CTA 动作 | CTA 相同，用说唱表达 |

**示例对照：**

| Medvi 旁白台词 | Sings 歌词 |
|----------------|-----------|
| 一个人，2万美元启动资金，14个月做到4亿美元营收。 | 两万块钱你敢创业吗 / 他14个月干了四个亿啊 |
| 创始人Matthew Gallagher，在拖车公园长大，用叔叔的电脑自学编程。 | 拖车公园长大的穷小子 / 用叔叔电脑自学写代码 |
| 他用2个人，跑了同行3倍的利润率。代码AI写，广告AI生成。 | 二四零零人干不过俩人 / AI效率就是这么蛮 |
| 私信AI获客，我发你完整工具清单。 | 私信回复AI获客 / 工具清单免费发你 |

### 5.1 输入/输出

- 输入：**已完成的 Medvi 旁白脚本**（同选题的 Medvi 配置文件）
- 输出：JSON 配置文件（含 lyrics 字段，segments 共用 Medvi 画面描述）

### 5.2 歌词 JSON 格式

```json
{
  "lyrics": {
    "bpm": 130,
    "time_signature": "4/4",
    "style": "chinese rap, energetic, educational",
    "source_config": "day1-medvi-story.json",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": ["两万块钱你敢创业吗", "他14个月干了四个亿啊"],
        "rhyme": "a",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": ["拖车公园长大的穷小子", "用叔叔电脑自学写代码"],
        "rhyme": "i",
        "segment_ref": "S02",
        "type": "body"
      }
    ]
  }
}
```

### 5.3 歌词写作 MUST 规则

| 规则 | 值 |
|------|----|
| 内容来源 | 必须从同选题 Medvi 旁白台词逐段转化 |
| 数据完整性 | Medvi 旁白中的所有数字必须出现在歌词中 |
| 总行数 | 16-24 行（或根据 Medvi 段落数调整） |
| 每行字数 | ≤ 10 个中文字 |
| 押韵 | 每 4 行至少 2 行押韵 |
| CTA | 与 Medvi 脚本相同的 CTA 动作和关键词 |
| 知识点 | 至少 3 个具体知识点（与 Medvi 相同） |

### 5.4 SHOULD 规则

| 规则 | 值 |
|------|----|
| 情绪曲线 | 与 Medvi 相同：炸(钩子) → 低(背景) → 高(数据) → 高(对比) → 暖(CTA) |
| 唱起来顺口 | 大声朗读时有自然节奏感 |
| 避免书面语 | 用口语，不说"此外"、"然而" |
| 信息零损失 | 转化后的歌词不丢失任何 Medvi 旁白中的关键信息 |

### 5.5 质量检查

- [ ] 歌词 vs Medvi 旁白：所有数据点已覆盖？（MUST）
- [ ] 大声唱一遍：节奏是否自然？（MUST）
- [ ] 总行数：___ 行（MUST：16-24 行）
- [ ] 押韵对数：___ 对（MUST：≥ 每 4 行 2 行押韵）
- [ ] 数字数量：___ 个（MUST：≥ 3，与 Medvi 一致）
- [ ] CTA 动作：与 Medvi 相同？（MUST）
- [ ] 最长单行：___ 字（MUST：≤ 10）

---

## 6. Stage 2：参考图生成（Seedream 4.5）

> 和 Medvi 工作流共用管线。区别仅在风格参数。

### 6.1 输入/输出

- 输入：JSON 配置文件中的 `segments[].reference_prompt`
- 输出：PNG 文件，1440x2560，存入 `assets/references/{video_id}/`

### 6.2 MUST 规则

| 规则 | 值 |
|------|----|
| 所有图片 9:16 比例 | 1440x2560 |
| 提示词后缀 | 每张图末尾加 `vertical composition 9:16` |
| 风格统一 | 高对比度 + 鲜艳色彩 + MV 视觉感 |
| 主体位置 | 居中偏下，上方留空间给运动和歌词字幕 |
| 画面中无文字 | AI 生成的文字一定是乱码 |
| 画面中无手部 | Seedream 手部生成有缺陷 |
| 边缘干净 | 无重要元素靠近画框边缘 |

### 6.3 Sings 视觉风格（区别于 Medvi）

**Medvi**: 深色调 + 暖金色 + 电影纪录片感
**Sings**: 高对比 + 鲜艳色彩 + MV/音乐视频感

| 参数 | Sings 值 |
|------|---------|
| 色温 | 中性偏冷，约 5500K 等效 |
| 饱和度 | 保持或略增（AI 默认已偏饱和） |
| 对比度 | 高对比，暗部更暗亮部更亮 |
| 风格关键词 | `vibrant, high contrast, music video aesthetic, dynamic lighting` |

**去AI质感指令（v3.0 摄影先行 + 面部不对称，经验证有效）**

> v3.0 经 3 轮实测验证（v1→v2→v3），生图必须严格遵循。完整方法论见 Medvi 工作流原则 3。
> 这里只列出 Sings 特有差异。

**Sings 摄影声明（区别于 Medvi，偏向 MV/音乐录影带风格）：**
- `music video behind the scenes, shot on RED Komodo 6K, anamorphic lens flare` — MV 幕后质感
- `concert documentary still, shot on Canon C300, stage lighting` — 演唱会纪录片
- `hip hop music video freeze frame, shot on Arri Alexa, neon lighting` — 说唱 MV 质感

**其余 5 层严格同 Medvi v3.0：**
1. 摄影声明（上面 3 个选项）
2. 主体 + 具体不完美 + 面部不对称（MUST，有人脸画面至少 1 处不对称）
3. 环境 + 真实物件名（MUST）
4. 光影 + 方向（MUST）
5. 构图 + `vertical composition 9:16`
6. Negative Prompt（MUST）

**Negative Prompt（每张图必须配置，v3.0 完整版）：**

```
airbrushed, smooth plastic skin, perfect symmetry, perfect facial symmetry,
symmetric face, centered perfectly symmetrical features, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
oil painting, watermark, text, logo, oversaturated, hyperrealistic,
mannequin, doll-like, flawless, magazine cover, retouched,
even skin tone, poreless skin
```

配置文件中通过 `reference_images.negative_prompt` 字段设置，`seedream-batch.py` 自动读取。

### 6.4 Seedream 4.5 参数

| 参数 | 值 |
|------|----|
| API | EvoLink，$0.030/张 |
| 分辨率 | 1440x2560 |
| 模型 | doubao-seedream-4.5 |
| 批量命令 | `python docs/content/scripts/seedream-batch.py --config config/{video_id}.json` |

---

## 7. Stage 3：视频生成（Runway Gen-4）

> 和 Medvi 工作流共用管线。区别仅在运动幅度。

### 7.1 MUST 规则

| 规则 | 值 |
|------|----|
| 只使用 Image-to-Video | 绝不用纯文生视频 |
| 提示词只写运动 | 不重复描述画面中已有的内容 |
| Fixed Seed 开启 | 全片用同一个 seed 值 |
| 分辨率 | 720x1280 (9:16) |
| 每段时长 | 5 秒 |
| 每段候选数 | ≥ 3 个，选最佳 |

### 7.2 Sings 运动参数（区别于 Medvi）

| 参数 | Medvi | Sings |
|------|-------|-------|
| 运动强度 | 3-5/10 | 5-7/10（更有活力） |
| Camera 运动 | 缓慢推进 | 更有节奏感的推拉摇移 |

**景别对应 Camera 参数（同 Medvi）：**

| 景别 | Camera 运动 | 提示词模板 |
|------|------------|-----------|
| 远景 | slow pan 或 slow zoom out | `slow dynamic pan, music video aesthetic, cinematic motion` |
| 中景 | medium push in | `dynamic head movement, rhythm, vibrant lighting shift` |
| 特写 | punch zoom in | `punch zoom in, high contrast lighting, energetic motion` |
| 文字卡片 | gentle fade + 轻微视差 | `gentle fade in, slight parallax on text elements` |

### 7.3 Runway 后处理

| 操作 | 标记 | 参数 |
|------|------|------|
| Retime → Trim | MUST | 裁掉首尾不稳定帧 |
| Retime → Handheld Shake | MUST | 强度 8-12%（Sings 比 Medvi 轻一些，因为有节奏剪辑） |
| 4K Upscale | SHOULD | 最终选中的片段 |

---

## 8. Stage 4：说唱音频生成（Suno AI via Evolink）

### 8.1 输入/输出

- 输入：JSON 配置中的 `lyrics` 字段
- 输出：MP3 说唱音频 + 节拍时间戳 JSON

### 8.2 MUST 规则

| 规则 | 值 |
|------|----|
| API | Evolink Suno API (`https://api.evolink.ai`) |
| API Key | `SUNO_API_KEY` in `.env` |
| 模型 | `suno-v4.5` 或 `suno-v5` |
| 模式 | custom_mode=true（自定义歌词） |
| 风格提示 | `chinese rap, energetic, educational, 130bpm` |
| 输出格式 | MP3（音频链接 72 小时有效） |
| 3 遍听测 | 连听 3 遍觉得节奏自然、不机械 |
| 节拍提取 | 生成后用 librosa 提取 beats.json |

### 8.3 SHOULD 规则

| 规则 | 值 |
|------|----|
| BPM | 120-140（甜点 130） |
| 歌词分段 | [Verse] / [Chorus] / [Outro] 标记 |
| 候选数 | ≥ 2 个版本，选最佳 |

### 8.4 Suno 歌词格式转换

从 config 的 `lyrics.bars` 生成 Suno 格式：

```
[Verse]
你知道歌曲能换个嗓子唱吗
AI翻唱比你想象更炸

RVC技术把声音特征提取
换个模型就是新的歌曲
...
[Chorus]
FireSing让翻唱变得简单
十秒钟就能换个嗓音来唱
...
[Outro]
私信"FireSing"免费体验
让AI帮你实现翻唱梦想
```

### 8.5 节拍提取

Suno 生成音频后，用 aubio 或 librosa 提取节拍时间戳：

```bash
python -c "
import librosa, json
y, sr = librosa.load('output.mp3', sr=44100)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beats, sr=sr).tolist()
json.dump({'bpm': float(tempo), 'beats': beat_times}, open('beats.json', 'w'))
"
```

输出 `beats.json`：
```json
{
  "bpm": 130.0,
  "beats": [0.46, 0.92, 1.38, 1.85, ...],
  "bar_lines": [0.46, 2.31, 4.15, ...]
}
```

### 8.6 批量命令

```bash
source docs/content/.env
python docs/content/scripts/suno-rap-batch.py --config config/{video_id}.json
```

### 8.7 质量检查

- [ ] 节奏感强，不拖沓
- [ ] 歌词清晰可辨识（不含糊）
- [ ] 无机械/电子感（3 遍听测通过）
- [ ] BPM 与 config 指定值匹配（±5%）
- [ ] 节拍时间戳已提取
- [ ] 总时长：___ 秒（MUST：30-45s）

---

## 9. Stage 5：视频合成

> 核心原则同 Medvi：FFmpeg 只做拼接+音频合并，所有视觉处理用剪映。

### 9.1 节拍同步

Sings 工作流独有的关键步骤：**视觉切换对齐到节拍**。

```
beats.json 中的 bar_lines → 定义镜头切换时间点
segments[].duration_sec → 被 bar_lines 覆盖（节拍优先于固定时长）
```

每个 segment 的实际时长 = 对应小节线之间的间隔。

### 9.2 FFmpeg 命令

```bash
# Step 1: 按节拍时间点分割并拼接视频片段
# 使用 concat demuxer + 精确时间点
ffmpeg -f concat -safe 0 -i segments.txt \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 24 \
  -an concat_video.mp4

# Step 2: 合并说唱音频
ffmpeg -i concat_video.mp4 -i rap_audio.mp3 \
  -c:v copy -c:a aac -b:a 192k \
  -shortest output/{video_id}_concat.mp4
```

### 9.3 剪映职责（所有视觉工作）

| 任务 | 操作 |
|------|------|
| 歌词字幕 | 逐行/逐字动态出现（KTV 风格） |
| BGM | 说唱音频是主体（非 BGM），不需要额外 BGM |
| 去 AI 4 步 | 胶片颗粒 + 光晕 + 色彩校正 + 抖动 |
| AI 标识水印 | 开头添加 "AI 生成内容" 文字贴纸，持续 ≥ 3 秒 |
| 文字卡片 | 高对比风格 |
| 封面帧 | 选取或 Canva 制作 |

---

## 10. Stage 6：去 AI 化后期

### 10.1 四步去 AI 法（Sings 参数）

**Step 1：胶片颗粒**

| 参数 | 值 | 标记 |
|------|----|------|
| 剪映 | 滤镜 → 质感 → 胶片，强度 8-12% | MUST |
| 说明 | Sings 颗粒比 Medvi 轻（15-20%），因为 MV 风格本身偏干净 | |

**Step 2：光晕/辉光**

| 参数 | 值 | 标记 |
|------|----|------|
| 剪映 | 特效 → 光效 → 柔光，强度 8-12% | MUST |

**Step 3：色彩校正**

| 参数 | 值 | 标记 |
|------|----|------|
| 饱和度 | 0 到 -5（Sings 本身高饱和） | MUST |
| 对比度 | +10 到 +15 | MUST |
| 色温 | 统一所有片段 | MUST |
| 锐度 | -3 到 -5 | SHOULD |

**Step 4：手持抖动**

| 条件 | 操作 |
|------|------|
| 已在 Runway Retime 加过 | 跳过 |
| 未在 Runway 加 | 剪映 → 特效 → 抖动，强度 3-5% |

### 10.2 封面帧

| 规则 | 标记 |
|------|------|
| 从视频选取或用 Canva 制作 | MUST |
| 包含关键短语 + 品牌色 | MUST |
| 9:16 比例 | MUST |
| 缩略图尺寸下可读 | MUST |

---

## 11. Stage 7：最终审核门控

### 11.1 时长门控

- [ ] ffprobe 报告时长 ≤ 45.0s 且 ≥ 30.0s（MUST）

### 11.2 节奏门控

- [ ] 镜头切换全部对齐到节拍（MUST）
- [ ] 无镜头内卡顿或不自然跳切（MUST）
- [ ] 歌词字幕与音频同步（MUST）

### 11.3 技术质量门控

- [ ] 分辨率 1080x1920，24fps，H.264（MUST）
- [ ] 文件大小 ≥ 15MB（MUST）
- [ ] 音频峰值 ≤ -1dB（MUST）
- [ ] 人声信噪比 ≥ 20dB（MUST）

### 11.4 去 AI 验证门控

- [ ] 手机预览通过"我会知道这是 AI 吗？"测试（MUST）
- [ ] 无手部伪影、文字乱码、面部异常（MUST）
- [ ] 无 AI 水印（MUST）

### 11.5 AI 内容标识门控（法规强制）

**显性标识（MUST）：**
- [ ] 视频开头有 "AI 生成内容" 文字标识，持续 ≥ 3 秒

**隐性标识（MUST）：**
- [ ] 视频文件元数据包含 AI 生成声明

**发布时（MUST）：**
- [ ] 在平台发布界面勾选 "AI 生成内容" 声明

### 11.6 最终审批

```
视频编号：__________
日期：__________

时长：      ___s    [ ] PASS  [ ] FAIL
BPM：       ___     [ ] PASS  [ ] FAIL
节拍同步：          [ ] PASS  [ ] FAIL
歌词覆盖：  ___%    [ ] PASS  [ ] FAIL
CTA 动作：  ___     [ ] PASS  [ ] FAIL
手机预览：          [ ] PASS  [ ] FAIL
去AI检查：          [ ] PASS  [ ] FAIL
AI显性标识：        [ ] PASS  [ ] FAIL
AI隐性标识：        [ ] PASS  [ ] FAIL

最终决定：[ ] 批准上传  [ ] 返回 Stage ___ 原因：__________
```

---

## 12. 视频配置文件格式

每条视频一个 JSON 文件，存放在 `docs/content/config/{video_id}.json`。

### Schema

```json
{
  "video_id": "sings01-rvc-intro",
  "workflow": "sings",
  "version": "1.0",
  "created": "2026-04-18",
  "status": "draft",

  "global": {
    "target_duration_sec": 37,
    "max_duration_sec": 45,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "runway_seed": 12345,
    "style": "mv_rap",
    "color_temperature": "neutral_cool",
    "accent_color": "#7b68ee",
    "bg_color": "#0a0a1a"
  },

  "lyrics": {
    "bpm": 130,
    "time_signature": "4/4",
    "style": "chinese rap, energetic, educational, 130bpm",
    "suno_tags": "chinese hip hop, rap, energetic, educational, bouncy, 130 bpm",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": ["你知道歌曲能换个嗓子唱吗", "AI翻唱比你想象更炸"],
        "rhyme": "a",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": ["RVC技术把声音特征提取", "换个模型就是新的歌曲"],
        "rhyme": "i",
        "segment_ref": "S02",
        "type": "body"
      }
    ]
  },

  "script": {
    "topic": "RVC 声音变换科普",
    "source": "FireSing 项目技术文档",
    "hook_type": "curiosity_gap",
    "cta_action": "私信",
    "cta_keyword": "FireSing",
    "cta_deliverable": "免费体验名额"
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 4,
      "shot_type": "close-up",
      "emotion": "explosive",
      "visual_description": "microphone exploding into colorful sound waves",
      "motion_prompt": "dynamic zoom in, vibrant color burst, music video energy",
      "reference_prompt": "explosive sound waves bursting from microphone, vibrant purple and blue neon, high contrast, energetic, dynamic lighting, music video aesthetic, vertical composition 9:16",
      "lyrics_refs": ["B01"]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "medium",
      "emotion": "educational",
      "visual_description": "person recording in home studio",
      "motion_prompt": "subtle head bob, natural movement, warm studio lighting",
      "reference_prompt": "young person in home studio recording vocals, headphones, microphone, warm ambient light from monitor, purple and blue accent lighting, high contrast, music video aesthetic, vertical composition 9:16",
      "lyrics_refs": ["B02", "B03"]
    }
  ],

  "audio": {
    "engine": "suno_ai",
    "mode": "custom",
    "style_prompt": "chinese rap, energetic, educational, 130bpm",
    "output_format": "mp3",
    "extract_beats": true,
    "beat_tool": "librosa"
  },

  "beat_sync": {
    "enabled": true,
    "align_to": "bar_lines",
    "min_cut_interval_beats": 2,
    "max_cut_interval_beats": 4
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "api": "evolink",
    "resolution": "1440x2560",
    "candidates_per_segment": 2,
    "style_suffix": "vertical composition 9:16"
  },

  "video_generation": {
    "engine": "runway_gen4",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "iteration_model": "gen4_turbo",
    "final_model": "gen4",
    "candidates_per_segment": 3,
    "motion_intensity": 6,
    "post_processing": {
      "trim_unstable_frames": true,
      "handheld_shake_pct": 10,
      "upscale_4k": true
    }
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
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像、配音和音乐"
  },

  "post_production": {
    "film_grain_intensity_pct": 10,
    "lens_glow_intensity_pct": 10,
    "saturation_adjust": -3,
    "contrast_adjust": 12,
    "sharpness_adjust": -3,
    "vignette": 0.2
  },

  "publishing": {
    "platforms": ["douyin", "xiaohongshu"],
    "title_candidates": [
      "AI翻唱比你想象更炸！RVC技术到底多强",
      "10秒把周杰伦变成林俊杰，AI翻唱是怎么做到的",
      "你知道歌曲能换个嗓子唱吗？AI音乐科普说唱"
    ],
    "tags": ["AI翻唱", "AI音乐", "RVC", "FireSing", "说唱科普"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "高对比 麦克风+声波 + 'AI翻唱比你想象更炸'"
  }
}
```

---

## 13. 文件组织

```
docs/content/
├── config/                    # 视频配置文件
│   ├── day1-medvi-story.json  # Medvi 工作流
│   ├── sings-template.json    # Sings 工作流模板
│   └── sings01-*.json         # Sings 工作流视频
├── scripts/                   # 批量生成脚本
│   ├── seedream-batch.py      # 共用：参考图
│   ├── runway-gen4-batch.py   # 共用：视频生成
│   ├── gemini-tts-batch.py     # Medvi：配音
│   ├── suno-rap-batch.py      # Sings：说唱音频
│   └── ffmpeg-compose-day1.py # 共用：合成
├── workflow/                  # 工作流文档
│   ├── video-production-spec.md      # Medvi 规范
│   ├── sings-video-production-spec.md # Sings 规范（本文档）
│   └── README.md                      # 工作流索引
├── assets/
│   ├── references/{video_id}/
│   ├── voiceover/{video_id}/
│   ├── rap/{video_id}/        # Suno 生成的说唱音频 + beats.json
│   ├── bgm/
│   └── covers/{video_id}/
└── output/{video_id}/
```

---

## 14. 批量生产模式

### Day A：准备（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| 写 5 份歌词脚本 | 60 分钟 | 手动编辑 JSON |
| 批量生成参考图 | 50 分钟 | `seedream-batch.py` |
| Runway 批量生成视频 | 75 分钟 | 手动操作 Runway |
| Suno 批量生成说唱音频 | 15 分钟 | `suno-rap-batch.py` |
| **总计** | **200 分钟** | |

### Day B：制作（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| FFmpeg 合成 × 5 | 25 分钟 | `compose-video.py` |
| 剪映精修 × 5 | 50 分钟 | 剪映（歌词字幕+去AI） |
| 最终审核 × 5 | 25 分钟 | Stage 7 清单 |
| **总计** | **100 分钟** | |

**产能：5 条/2 天，平均 60 分钟/条。周产能 15-20 条。**

---

## 15. 歌词选题库

### FireSing 功能说唱选题

| 编号 | 主题 | 知识点 | 产品关联 |
|------|------|--------|---------|
| S01 | RVC 声音变换原理 | 声音特征提取 + 模型训练 | FireSing 核心功能 |
| S02 | 音频源分离 | Demucs/MDX 原理 | FireSing 第一步 |
| S03 | LRC 歌词解析 | 时间标签 + 分段 | FireSing 精确控制 |
| S04 | f0 提取与音高匹配 | harvest vs rmvpe | FireSing 音高对齐 |
| S05 | 一人合唱原理 | 多轨叠加 + 声音模型 | FireSing 高级玩法 |
| S06 | AI 音乐伦理 | 版权 + 原创保护 | FireSing 合规使用 |

---

## 附录 A：批准标签列表

```
#AI翻唱 #AI音乐 #RVC #FireSing #说唱科普 #AI工具 #声音变换 #知识以卑鄙的手段进入了脑海里
```

## 附录 B：配色系统

| 用途 | 色值 | 使用场景 |
|------|------|---------|
| 品牌紫蓝 | #7b68ee | 歌词高亮、CTA 文字、封面 |
| 深空黑 | #0a0a1a | 背景、文字卡片底色 |
| 纯白 | #FFFFFF | 正文歌词字幕 |
| 霓虹粉 | #ff1493 | 强调、钩子元素 |
| 电光蓝 | #00bfff | 次要强调 |

---

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-18 | 1.0 | Sings 工作流初始版本 |
