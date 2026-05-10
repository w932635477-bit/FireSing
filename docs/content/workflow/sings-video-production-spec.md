# AI 短视频生产规范 v2.0 — Sings 穿搭对比工作流

> 适用范围：30-45 秒 AI 生成穿搭对比对唱短视频，小红书竖版
> 工具链：Seedream 4.5 + Kling 3.0 + Suno AI + FFmpeg + 剪映
> 工作流类型：**Sings**（穿搭场景对比对唱，音乐节拍驱动）
> 本文档是 Sings 工作流的唯一权威标准
> 最后更新：2026-04-23
> v1.0 说唱科普版本已归档，不再维护

---

## 0. Sings vs Medvi 快速对照

| 维度 | Medvi 工作流 | Sings 工作流 |
|------|-------------|-------------|
| 平台 | 抖音 | 小红书 |
| 内容风格 | 商业名人故事 + 情绪拉动 | 穿搭场景对比 + 美学建议 |
| 驱动方式 | 旁白时长驱动 | BPM + 小节数驱动 |
| 脚本格式 | 旁白文字，≤15字/句 | 对唱歌词，押韵，4/4拍 |
| 音频管线 | Gemini/Doubao TTS | Suno AI (男女对唱曲目) |
| 视觉风格 | 深色暖金纪录片 | 明亮时尚 lookbook |
| 配色 | 暖金 #c9a96e + 纯黑 | 奶油白 #f5e6d3 + 暖橘 #e8a87c |
| 景别节奏 | 每 3-5 秒切换 | 每 2-4 拍切换 |
| 字幕风格 | 白底黑描边，金色高亮 | 动态歌词（KTV/MV 风格） |
| CTA | 评论区聊人生感悟 | 投票 A/B 穿搭选择 |
| 角色定位 | 深度思考的杨梦 | 有品味的杨梦 |

**共用的管线**：Seedream 参考图、Kling 视频生成、FFmpeg 合成、剪映后期、去 AI 化 4 步法。

---

## 1. 视频全局标准

### 1.1 时长

| 规则 | 标记 | 值 |
|------|------|----|
| 最终时长 30-45 秒 | MUST | ffprobe 检查 |
| BPM 甜点区间 120-140 | SHOULD | 130 为默认 |
| 钩子 = 前 2 小节 | MUST | 约 4-6 秒 |
| 穿搭 A = 4 小节 | MUST | 约 6 秒 |
| 穿搭 B = 4 小节 | MUST | 约 6 秒 |
| 法则 = 4 小节 | MUST | 约 6 秒 |
| CTA = 最后 2 小节 | MUST | 约 4-6 秒 |
| 超过 45.0 秒 = 拒绝 | MUST | Stage 7 门控 |

**时长计算公式**：`总时长(秒) = 总拍数 / BPM × 60`
- 130 BPM, 8 小节(32 拍) = 14.8 秒（纯歌词）
- Suno 实际生成 90-130 秒（含前奏/间奏），剪映裁剪到 30-45 秒

### 1.2 分辨率和编码

| 规则 | 标记 | 值 |
|------|------|----|
| 导出分辨率 1080x1920 | MUST | 9:16 竖版 |
| Kling 输出 720x1280 | MUST | 后期升采样 |
| 参考图 1440x2560 | MUST | Seedream API 原生 9:16 2K |
| 帧率 24fps | MUST | |
| 编码 H.264 MP4 | MUST | |
| 码率 ≥ 8Mbps | MUST | |
| FFmpeg 导出参数 | MUST | `-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p` |

### 1.3 镜头数量和类型

| 规则 | 标记 | 值 |
|------|------|----|
| 每条视频 5 个镜头 | MUST | 固定 5 段结构 |
| 单镜头对应 2-4 小节 | MUST | 按节拍对齐 |
| 至少 3 种景别 | MUST | {全身, 中景, 特写, 文字卡片} |

**5 段固定结构：**

| 段落 | 景别 | 用途 |
|------|------|------|
| S01 Hook | 全身 Wide | 穿搭 A/B 并排/切换对比 |
| S02 Outfit A | 中景 Medium | A 套穿搭特写 |
| S03 Outfit B | 中景 Medium | B 套穿搭特写 |
| S04 法则 | 文字卡片 Text | 穿搭法则总结 |
| S05 CTA | 特写 Close-up | 杨梦直视镜头微笑 |

---

## 2. 钩子设计规范（S01）

### 2.1 第一帧

| 规则 | 标记 |
|------|------|
| 第 1 帧必须展示两套穿搭对比 | MUST |
| 场景关键词在前 2 秒内出现 | MUST |
| 明亮色调，抓眼球 | MUST |

### 2.2 钩子歌词

| 规则 | 标记 |
|------|------|
| 钩子歌词 2 行，每行 ≤ 12 字 | MUST |
| 第一行必须是场景提问 | MUST |
| 男声提问 + 女声回应的对唱格式 | MUST |

### 2.3 钩子类型

| 类型 | 示例 | 适用场景 |
|------|------|---------|
| 场景提问 | "面试穿西装还是休闲" | 职场系列 |
| 选择困难 | "约会穿裙子还是裤子" | 约会系列 |
| 季节困惑 | "下雨天怎么穿才不狼狈" | 季节系列 |
| 特殊场合 | "见家长穿什么不出错" | 特殊场景 |

---

## 3. 歌词规范

### 3.1 格式

| 规则 | 标记 |
|------|------|
| 100% 歌词有对应字幕 | MUST |
| 男女对唱交替 | MUST |
| 押韵格式 AABB 或 ABAB | SHOULD |
| 关键穿搭词汇用强调色高亮 | MUST |

### 3.2 歌词字幕样式

| 规则 | 标记 |
|------|------|
| 动态逐字/逐行出现（KTV 风格） | MUST |
| 当前唱到的行放大高亮，已唱行缩小变暗 | MUST |
| 字幕位置底部居中，留出平台 UI 安全区 | SHOULD |

### 3.3 歌词写作规则

| 规则 | 值 | 标记 |
|------|----|------|
| 每行字数 | ≤ 12 个中文字 | MUST |
| 总行数 | 16 行（8 bars × 2 lines） | MUST |
| 押韵密度 | 每 4 行至少 2 行押韵 | SHOULD |
| 穿搭信息密度 | 每 2 行至少 1 个穿搭知识点或点评 | MUST |
| 套话禁止 | 不用"今天给大家带来"、"大家好" | MUST |

### 3.4 歌词段落结构

```
[Chorus]                    ← Hook (男声提问 + 女声回应)
场景提问 + 穿搭核心观点

[Verse 1]                   ← Outfit A (男声点评)
A套描述 + 优点 + 缺点/细节

[Verse 2]                   ← Outfit B (女声回应)
B套描述 + 优点 + 总结

[Verse 3]                   ← 穿搭法则 (男女交替)
法则1 + 法则2

[Outro]                     ← CTA (合唱)
投票引导 + 品味互动
```

---

## 4. CTA 规范

### 4.1 位置

| 规则 | 标记 |
|------|------|
| CTA 占据最后 2 小节（约 4-6 秒） | MUST |
| CTA 同时出现在歌词和画面上 | MUST |

### 4.2 内容

| 规则 | 标记 |
|------|------|
| 只要求一个动作：投票 A/B | MUST |
| 使用投票模板 | MUST |
| 关键词 ≤ 6 个中文字 | MUST |

**批准的 CTA 模板：**
```
"[场景]穿搭你站A还是B"
"评论区投票 告诉我你的品味"
"[场景]穿A还是穿B 评论区见"
```

---

## 5. Stage 1：歌词脚本写作

### 5.0 核心原则：原创穿搭对比内容

> Sings 歌词独立创作，不依赖 Medvi 脚本。每期围绕一个穿搭场景，设计两套对比穿搭，
> 通过男女对唱形式讲解穿搭逻辑和法则。

**工作流程：**
1. 确定场景（面试/约会/通勤/聚会等）
2. 设计 A/B 两套穿搭方案（风格对立，各有道理）
3. 提炼 2 条穿搭法则
4. 按段落结构写歌词
5. 填入 config JSON

### 5.1 歌词创作模板

```
[Chorus]
男：[场景提问 ≤12字]
女：[核心观点/回应 ≤12字]

[Verse 1]
男：A套 [服装描述] ≤12字
男：[A套点评] ≤10字
男：[A套细节/缺点] ≤12字
男：[A套总结 押韵] ≤10字

[Verse 2]
女：B套 [服装描述] ≤12字
女：[B套点评] ≤10字
女：[B套优点] ≤12字
女：[B套总结 押韵] ≤10字

[Verse 3]
男：法则一 [法则内容] ≤12字
女：[法则解释 押韵] ≤10字
男：法则二 [法则内容] ≤12字
女：[法则解释 押韵] ≤10字

[Outro]
合唱：[场景]穿搭你站A还是B
合唱：评论区投票 告诉我你的品味
```

### 5.2 质量检查

- [ ] 场景明确，观众能代入？（MUST）
- [ ] A/B 两套风格有对比？（MUST）
- [ ] 至少 2 条穿搭法则？（MUST）
- [ ] 大声唱一遍：节奏是否自然？（MUST）
- [ ] 总行数：16 行（MUST）
- [ ] 押韵对数：___ 对（SHOULD：≥ 4）
- [ ] 最长单行：___ 字（MUST：≤ 12）

---

## 6. Stage 2：参考图生成（Seedream 4.5）

### 6.1 输入/输出

- 输入：JSON 配置文件中的 `segments[].reference_prompt`
- 输出：PNG 文件，1440x2560，存入 `assets/references/{video_id}/`

### 6.2 MUST 规则

| 规则 | 值 |
|------|----|
| 所有图片 9:16 比例 | 1440x2560 |
| 提示词后缀 | 每张图末尾加 `vertical composition 9:16` |
| 风格统一 | 明亮时尚 lookbook 风格 |
| 主体位置 | 居中偏下，上方留空间给运动和歌词字幕 |
| 画面中无文字 | AI 生成的文字一定是乱码 |
| 避免手部特写 | Seedream 手部生成有缺陷 |
| 边缘干净 | 无重要元素靠近画框边缘 |

### 6.3 穿搭模式视觉风格

**Medvi**: 深色调 + 暖金色 + 电影纪录片感
**Sings 穿搭**: 明亮 + 奶油白背景 + 时尚 lookbook 感

| 参数 | Sings 穿搭值 |
|------|---------|
| 色温 | 暖白，约 5500K |
| 饱和度 | 略增（明亮活力感） |
| 对比度 | 中等偏低（柔和自然） |
| 风格关键词 | `bright studio, fashion lookbook, natural daylight, cream background` |

**角色锚定（杨梦 v4.0）：**

每张穿搭图必须包含完整的角色锚定段落：

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
```

**穿搭 Prompt 结构（7 层，基于行业最佳实践 v2.1）：**

> AI 模型对 prompt 前 5-8 个词权重最高，因此顺序很重要。
> Prompt 长度控制在 30-100 词，太长会让模型迷失。
> 用 3-5 个强有力的描述词，不用 20 个弱词。
> 服装用具体面料名（"哑光精梳棉" 而非 "棉"，"真丝 Charmeuse" 而非 "闪亮面料"）。

1. **整体美学/mood**（前 5-8 词决定基调，MUST）
   - 全身: `Bright fashion lookbook editorial`
   - 中景: `Fashion lookbook detail shot`
   - 特写: `Warm intimate fashion portrait`
2. 角色锚定（上面段落，MUST，逐字不变）
3. 服装描述（具体面料名+颜色名+版型+配饰，MUST）
4. 场景背景（明亮的现代空间，MUST）
5. 姿势（站立/转身/微笑等，MUST）
6. 光影（自然日光，柔和明亮，明确光源方向和色温，MUST）
7. **相机/技术**（镜头焦段+景别+构图，MUST）
   - 全身: `50mm lens, model centered with negative space above`
   - 中景: `85mm portrait lens, shallow depth of field`
   - 特写: `85mm portrait lens, shallow depth of field`
   - 所有图末尾: `vertical composition 9:16`

完整 prompt 模板见 `docs/content/config/outfit-seedream-prompts.md`。

**Negative Prompt（每张图必须配置）：**

```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain,
wrinkled clothes, fabric distortion, texture error, stiff pose,
cropped, cut off, out of frame, tilted, cluttered
```

### 6.4 每集参考图需求

| 段落 | 参考图数 | 内容 |
|------|---------|------|
| S01 Hook | 2 候选 | 穿搭对比（可用 S02+S03 在剪映拼分屏） |
| S02 Outfit A | 2 候选 | 杨梦穿 A 套全身/半身 |
| S03 Outfit B | 2 候选 | 杨梦穿 B 套全身/半身 |
| S04 法则 | 无 | 文字卡，FFmpeg/剪映直接生成 |
| S05 CTA | 2 候选 | 杨梦微笑特写 |
| **合计** | **8 张** | |

### 6.5 Seedream 4.5 参数

| 参数 | 值 |
|------|----|
| API | EvoLink，$0.030/张 |
| 分辨率 | 1440x2560 |
| 模型 | doubao-seedream-4.5 |
| 批量命令 | `python docs/content/scripts/seedream-batch.py --config config/{video_id}.json` |

---

## 7. Stage 3：视频生成（Kling 3.0）

### 7.1 MUST 规则

| 规则 | 值 |
|------|----|
| 只使用 Image-to-Video | 绝不用纯文生视频 |
| 提示词只写运动 | 不重复描述画面中已有的内容 |
| Fixed Seed 开启 | 全片用同一个 seed 值 |
| 分辨率 | 720x1280 (9:16) |
| 每段时长 | 5 秒 |
| 每段候选数 | ≥ 2 个，选最佳 |

### 7.2 穿搭模式运动参数

| 参数 | 值 | 原因 |
|------|----|------|
| 运动强度 | 4/10 | 穿搭需要稳定画面展示细节 |
| Camera 运动 | 缓慢转身/微动 | lookbook 风格不需要 MV 的剧烈运动 |

**景别对应 Camera 参数：**

| 景别 | Camera 运动 | 提示词模板 |
|------|------------|-----------|
| 全身 (S01) | gentle sway | `gentle sway, fashion lookbook style, bright lighting` |
| 中景 (S02/S03) | slow turn | `slow turn, detail showcase, bright studio lighting` |
| 特写 (S05) | gentle movement | `warm smile, direct eye contact, gentle movement` |

### 7.3 Kling 后处理

| 操作 | 标记 | 参数 |
|------|------|------|
| Retime → Trim | MUST | 裁掉首尾不稳定帧 |
| Handheld Shake | MUST | 强度 5%（穿搭模式比旧 Sings 更轻） |
| 4K Upscale | SHOULD | 最终选中的片段 |

---

## 8. Stage 4：对唱音频生成（Suno AI via Evolink）

### 8.1 输入/输出

- 输入：JSON 配置中的 `lyrics` 字段
- 输出：MP3 对唱音频 + 节拍时间戳 JSON

### 8.2 MUST 规则

| 规则 | 值 |
|------|----|
| API | Evolink Suno API (`https://api.evolink.ai`) |
| API Key | `SUNO_API_KEY` in `.env` |
| 模型 | `suno-v4.5` |
| 模式 | custom_mode=true（自定义歌词） |
| 风格提示 | `catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm` |
| 负面标签 | `rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody` |
| 输出格式 | MP3（音频链接 72 小时有效） |
| 3 遍听测 | 连听 3 遍觉得旋律自然、对唱和谐 |
| 节拍提取 | 生成后用 librosa 提取 beats.json |

### 8.3 SHOULD 规则

| 规则 | 值 |
|------|----|
| BPM | 130（默认） |
| 歌词分段 | [Chorus] / [Verse] / [Outro] 标记 |
| 候选数 | ≥ 2 个版本，选最佳 |

### 8.4 Suno 歌词格式转换

从 config 的 `lyrics.bars` 生成 Suno 格式：

```
[Chorus]
面试穿西装还是休闲
评委看第一眼 定你行不行

[Verse]
A套 深蓝西装白衬衫
经典不出错 但太正式
这条领带像去银行
科技公司穿成这样太紧张

B套 针织衫搭深色裤
干净有层次 不装成熟
做你自己就够自信
不用西装也能赢

法则一 看行业定基调
金融正式 互联网太拘谨反而不妙
法则二 合身比品牌重要
肩膀对不上号 大牌也像借来的搞笑

[Outro]
面试穿搭你站A还是B
评论区投票 告诉我你的品味
```

### 8.5 节拍提取

```bash
python -c "
import librosa, json
y, sr = librosa.load('output.mp3', sr=44100)
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beats, sr=sr).tolist()
json.dump({'bpm': float(tempo), 'beats': beat_times}, open('beats.json', 'w'))
"
```

### 8.6 批量命令

```bash
source docs/content/.env
python docs/content/scripts/suno-rap-batch.py --config config/{video_id}.json
```

### 8.7 质量检查

- [ ] 男女声对唱清晰可辨
- [ ] 旋律自然，不机械
- [ ] 无 rap/hip hop 元素混入
- [ ] BPM 与 config 指定值匹配（±10%）
- [ ] 节拍时间戳已提取

---

## 9. Stage 5：视频合成

> 核心原则同 Medvi：FFmpeg 只做拼接+音频合并，所有视觉处理用剪映。

### 9.1 节拍同步

```
beats.json 中的 bar_lines → 定义镜头切换时间点
segments[].duration_sec → 被 bar_lines 覆盖（节拍优先于固定时长）
```

### 9.2 FFmpeg 命令

```bash
# Step 1: 拼接视频片段
ffmpeg -f concat -safe 0 -i segments.txt \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 24 \
  -an concat_video.mp4

# Step 2: 合并对唱音频
ffmpeg -i concat_video.mp4 -i duet_audio.mp3 \
  -c:v copy -c:a aac -b:a 192k \
  -shortest output/{video_id}_concat.mp4
```

### 9.3 剪映职责（所有视觉工作）

| 任务 | 操作 |
|------|------|
| A/B 分屏 | S01 段左右分屏，A/B 穿搭并排 |
| 穿搭标签 | S02/S03 加 "A" / "B" 文字标签 |
| 歌词字幕 | 逐行/逐字动态出现（KTV 风格） |
| 投票提示 | S05 底部加 "A / B" 大字 |
| 去 AI 4 步 | 见 Stage 6 |
| AI 标识水印 | 开头添加 "AI 生成内容" 文字贴纸，持续 ≥ 3 秒 |
| 文字卡片 | 明亮时尚风格 |
| 音频裁剪 | Suno 生成 90-130s，裁剪到 30-45s |
| 封面帧 | 选取或 Canva 制作 |

---

## 10. Stage 6：去 AI 化后期

### 10.1 四步去 AI 法（穿搭模式参数）

**Step 1：胶片颗粒**

| 参数 | 值 | 标记 |
|------|----|------|
| 剪映 | 滤镜 → 质感 → 胶片，强度 0-5% | SHOULD |
| 说明 | 穿搭模式不需要颗粒感，保持干净明亮 | |

**Step 2：光晕/辉光**

| 参数 | 值 | 标记 |
|------|----|------|
| 剪映 | 特效 → 光效 → 柔光，强度 5% | MUST |

**Step 3：色彩校正**

| 参数 | 值 | 标记 |
|------|----|------|
| 饱和度 | +5 到 +10（明亮活力感） | MUST |
| 对比度 | +5（柔和自然） | MUST |
| 色温 | 统一所有片段，偏暖白 | MUST |
| 锐度 | -2 到 -3 | SHOULD |

**Step 4：手持抖动**

| 条件 | 操作 |
|------|------|
| 已在 Kling Retime 加过 | 跳过 |
| 未在 Kling 加 | 剪映 → 特效 → 抖动，强度 3% |

### 10.2 面料质感注意

- AI 生成的服装纹理可能不自然，适当锐化改善
- 避免手部特写镜头（AI 手部常见问题）
- 分屏对比时确保两套穿搭视觉平衡

### 10.3 封面帧

| 规则 | 标记 |
|------|------|
| 杨梦 A/B 穿搭对比画面 | MUST |
| 包含场景关键词大字（如"面试穿搭"） | MUST |
| 9:16 比例 | MUST |
| 奶油白/暖橘色调 | MUST |
| 缩略图尺寸下可读 | MUST |

---

## 11. Stage 7：最终审核门控

### 11.1 时长门控

- [ ] ffprobe 报告时长 ≤ 45.0s 且 ≥ 30.0s（MUST）

### 11.2 节奏门控

- [ ] 镜头切换全部对齐到节拍（MUST）
- [ ] 无镜头内卡顿或不自然跳切（MUST）
- [ ] 歌词字幕与音频同步（MUST）
- [ ] A/B 穿搭对比清晰可见（MUST）

### 11.3 技术质量门控

- [ ] 分辨率 1080x1920，24fps，H.264（MUST）
- [ ] 文件大小 ≥ 15MB（MUST）
- [ ] 音频峰值 ≤ -1dB（MUST）
- [ ] 人声信噪比 ≥ 20dB（MUST）

### 11.4 去 AI 验证门控

- [ ] 手机预览通过"我会知道这是 AI 吗？"测试（MUST）
- [ ] 无手部伪影、文字乱码、面部异常（MUST）
- [ ] 无 AI 水印（MUST）
- [ ] 穿搭细节自然，无 AI 瑕疵（MUST）

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
A/B对比可见：      [ ] PASS  [ ] FAIL
穿搭法则：  ___条   [ ] PASS  [ ] FAIL
CTA投票：           [ ] PASS  [ ] FAIL
手机预览：          [ ] PASS  [ ] FAIL
去AI检查：          [ ] PASS  [ ] FAIL
AI显性标识：        [ ] PASS  [ ] FAIL
AI隐性标识：        [ ] PASS  [ ] FAIL

最终决定：[ ] 批准上传  [ ] 返回 Stage ___ 原因：__________
```

---

## 12. 视频配置文件格式

每条视频一个 JSON 文件，存放在 `docs/content/config/{video_id}.json`。

模板文件：`sings-template.json`（穿搭对比对唱模板 v2.0）

---

## 13. 文件组织

```
docs/content/
├── config/                         # 视频配置文件
│   ├── sings-template.json         # Sings 穿搭对比模板
│   ├── outfit-seedream-prompts.md  # 穿搭参考图 Prompt 模板
│   └── outfit-day1-interview.json  # 穿搭系列视频
├── scripts/                        # 批量生成脚本
│   ├── seedream-batch.py           # 共用：参考图
│   ├── kling-gen4-batch.py        # 共用：视频生成
│   ├── suno-rap-batch.py          # Sings：对唱音频
│   └── ffmpeg-compose-day1.py     # 共用：合成
├── workflow/                       # 工作流文档
│   ├── video-production-spec.md    # Medvi 规范
│   ├── sings-video-production-spec.md  # Sings 规范（本文档）
│   └── README.md                   # 工作流索引
├── assets/
│   ├── references/{video_id}/      # Seedream 参考图
│   ├── rap/{video_id}/             # Suno 对唱音频 + beats.json
│   └── covers/{video_id}/          # 封面图
└── output/{video_id}/              # FFmpeg 输出 + 剪映最终版
```

---

## 14. 批量生产模式

### Day A：准备（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| 写 5 份穿搭歌词脚本 | 45 分钟 | 手动编辑 JSON |
| 批量生成参考图（40 张） | 50 分钟 | `seedream-batch.py` |
| Kling 批量生成视频（20 个） | 60 分钟 | 手动操作 Kling |
| Suno 批量生成对唱音频（10 个） | 15 分钟 | `suno-rap-batch.py` |
| **总计** | **170 分钟** | |

### Day B：制作（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| FFmpeg 合成 × 5 | 20 分钟 | `ffmpeg-compose` |
| 剪映精修 × 5（分屏+字幕+去AI） | 75 分钟 | 剪映 |
| 最终审核 × 5 | 25 分钟 | Stage 7 清单 |
| **总计** | **120 分钟** | |

**产能：5 条/2 天，平均 58 分钟/条。周产能 15-20 条。**

---

## 15. 穿搭选题库

### 职场系列

| 编号 | 场景 | A 套 | B 套 | 法则 |
|------|------|------|------|------|
| D01 | 面试穿搭 | 深蓝西装白衬衫 | 针织衫深色裤 | 看行业定基调 + 合身比品牌重要 |
| D02 | 入职第一天 | 休闲西装+T恤 | 衬衫裙+小白鞋 | 不超过三个颜色 + 鞋子定风格 |
| D03 | 述职报告 | 黑色西装+丝巾 | 深色连衣裙+腰带 | 场合决定正式度 + 一个亮点就够 |
| D04 | 商务晚宴 | 深色礼服裙+耳环 | 西装套装+胸针 | 面料比款式重要 + 饰品要克制 |
| D05 | 周五便装 | 卫衣+阔腿裤 | 针织开衫+牛仔裤 | 休闲不随便 + 一件单品撑场面 |

### 约会系列

| 编号 | 场景 | A 套 | B 套 | 法则 |
|------|------|------|------|------|
| D06 | 第一次约会 | 碎花连衣裙 | 高腰裤+修身针织 | 舒适优先 + 一个焦点单品 |
| D07 | 看电影 | 卫衣+短裙 | 风衣+直筒裤 | 层次感 + 脱外套也好看 |
| D08 | 闺蜜下午茶 | 西装外套+短靴 | 毛衣+百褶裙 | 拍照上镜 + 对比色显白 |

### 季节系列

| 编号 | 场景 | A 套 | B 套 | 法则 |
|------|------|------|------|------|
| D09 | 春游 | 薄风衣+帆布鞋 | 卫衣+运动裤 | 防风+拍照好看 |
| D10 | 雨天通勤 | 防水外套+雨靴 | 长款雨衣+短靴 | 防水材质 + 不怕湿的鞋 |

---

## 附录 A：配色系统

| 用途 | 色值 | 使用场景 |
|------|------|---------|
| 奶油白 | #f5e6d3 | 背景色、文字卡底色 |
| 深灰 | #2d2d2d | 文字卡文字、正文 |
| 暖橘 | #e8a87c | 强调色、标题高亮、标签 |
| 暖棕 | #8b7355 | 辅助文字、次要强调 |

## 附录 B：批准标签列表

```
#穿搭对比 #OOTD #杨梦穿搭 #场景穿搭 #穿搭法则
#面试穿搭 #约会穿搭 #通勤穿搭 #每日穿搭 #穿搭灵感
```

---

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-18 | 1.0 | Sings 工作流初始版本（说唱科普） |
| 2026-04-22 | 2.0 | 全面改为穿搭对比对唱模式，小红书专发 |
| 2026-05-09 | 3.0 | 新增方言说唱模式（Section 16），固定BGM+冲突对立歌词+摇拖拉机视觉 |

---

## 16. 方言说唱模式（v3.0 新增）

> 适用范围：90-100 秒东北方言半说半唱短视频，抖音竖版
> 工具链：Suno Add Vocals API + Seedream 4.5 + Kling 3.0 + FFmpeg + 剪映
> BGM：**固定使用 Fraelis by Frankie T（用户剪辑版 95s, 128 BPM Tech House）**
> 本节是方言说唱模式的唯一权威标准

### 16.0 核心理念

**固定公式：固定BGM + 固定视觉(杨梦摇拖拉机) + 旋转歌词(冲突对立主题)**

每集只换歌词和文案，BGM和视觉风格完全复用。高效率批量生产。

### 16.1 BGM 结构分析

Fraelis (128 BPM Tech House, 95s) 能量分布：

```
0s──────15s──────30s──37s──45s─47s──────60s──────75s──────90s─95s
│ A段(主拍)  │ A段续    │ 过渡段  │DROP│ B段(主拍)  │ B段续    │ B段续    │尾│
│ HIGH ENERGY │ HIGH    │ BREAK   │ !! │ HIGH ENERGY│ HIGH     │ HIGH     │FADE│
└─────────────┴─────────┴─────────┴────┴────────────┴──────────┴──────────┴───┘
```

| 区段 | 时间 | 小节数 | 能量 | 用途 |
|------|------|--------|------|------|
| A段 | 0-30s | 16 bars | HIGH | 主说唱段 |
| 过渡段 | 30-45s | 8 bars | LOW→BUILD | 铺垫悬念 |
| DROP | 45-47s | 1-2 bars | SILENCE→EXPLOSION | 金句爆发点 |
| B段 | 47-90s | 23 bars | HIGH | 高潮说唱 |
| 尾声 | 90-95s | 2 bars | FADE | 收尾反转 |

### 16.2 歌词+BGM 融合规则（MANDATORY）

歌词的 `[Section]` 标记必须对齐 BGM 能量变化：

```
[Intro]       → 0-4s    短感叹，1-2句
[Verse 1]     → 4-30s   主说唱，半说半唱，紧跟鼓点
[Break]       → 30-45s  放慢，留白，铺垫悬念
[Chorus]      → 47-65s  DROP后爆发，全曲最密集最扎心
[Verse 2]     → 65-85s  延续高潮
[Outro]       → 85-95s  金句收尾+反转
```

#### 音节密度规则（128 BPM）

| Section | 每小节音节 | 每段总音节 | 说明 |
|---------|-----------|-----------|------|
| Intro | 2-4 | 4-8 | 短促东北口语 |
| Verse | 6-8 | 80-110 | 节奏紧凑，句尾上扬 |
| Break | 3-5 | 24-40 | 放慢留白，戏剧性 |
| Chorus | 8-10 | 80-100 | 最密集，能量最高 |
| Outro | 4-6 | 10-15 | 简洁反转收尾 |

#### 歌词写作原则

1. **每句必须有一个"刺"** — 听众觉得"说到我心里了"
2. **Break段必须有悬念** — 让人期待接下来是什么
3. **Chorus必须对齐DROP后的高能量区** — 这是完播率决定性段落
4. **Outro必须反转** — 让人想听第二遍
5. **东北方言点缀** — 哎呀妈呀、咋整、嘎哈呢、整挺好、寻思，不过度

#### 歌词模板（MANDATORY 格式）

```
[Intro]
{1-2句开场感叹，东北口语}

[Verse 1]
{4-6句，每句7-10字，押韵}
{内容：冲突对立主题的前半段}

[Break]
{2-3句，放慢节奏}
{内容：转折/铺垫/悬念}
{语气：自言自语或反问}

[Chorus]
{4-6句，最密集最有力}
{内容：核心冲突/最大包袱}
{节奏：加速，句尾下压}

[Verse 2]
{3-5句，延续高潮}
{内容：反转或补充}

[Outro]
{1-2句，金句收尾}
{节奏：拖长最后一个字}
```

### 16.3 冲突对立选题库

每集选一个对立主题：

| 对立维度 | 示例主题 | Chorus 包袱方向 |
|---------|---------|----------------|
| 职场 | 老板画饼 vs 打工人真相 | "你太优秀了，项目交给小李" |
| 爱情 | 相亲期望 vs 现实 | "条件挺好，就是差点感觉" |
| 金钱 | 月光族 vs 所谓理财 | "基金定投三年，赚了八十块" |
| 社交 | 朋友圈 vs 真实生活 | "滤镜一关，自己都认不出" |
| 消费 | 双11剁手 vs 退货 | "买的时候是投资，退的时候是断舍离" |
| 年龄 | 90后vs00后 | "领导比我还小三岁" |
| 婚姻 | 婆媳相处 vs 理论 | "妈只有一个，媳妇可以再找（婆婆原话）" |
| 学历 | 文凭 vs 能力 | "硕士毕业，月薪五千，还嫌我眼高手低" |

### 16.4 音频管线：Suno Add Vocals API

**与旧模式的核心区别：不上传歌词让 Suno 生成歌曲，而是上传固定 BGM 让 Suno 在上面加人声。**

#### API 流程

1. 上传 BGM → `POST https://sunoapiorg.redpandaai.co/api/file-stream-upload`
2. 创建任务 → `POST https://api.sunoapi.org/api/v1/generate/add-vocals`
3. 轮询状态 → `GET https://api.sunoapi.org/api/v1/generate/record-info?taskId=`
4. 下载结果 → `response.sunoData[].audioUrl`

#### API 参数

| 参数 | 值 | 说明 |
|------|----|------|
| uploadUrl | BGM 上传后的 URL | 必须用用户剪辑版 |
| prompt | 见下方模板 | 包含歌词+演唱指令 |
| model | V4_5PLUS | chirp-bluejay |
| vocalGender | f | 女声 |
| styleWeight | 0.70 | |
| weirdnessConstraint | 0.60 | |
| audioWeight | 0.65 | BGM 和人声的混合比例 |

#### Prompt 模板（MANDATORY）

```
东北方言半说半唱喜剧说唱，配合128BPM Tech House节拍。歌词如下：
{lyrics}

演唱要求：
- [Intro]和[Break]段：放慢节奏，像日常聊天，留白给音乐
- [Verse]段：紧跟鼓点，每句落在拍子上，半说半唱
- [Chorus]段：全曲最高能量，加快语速，收尾冲击力强
- [Outro]：拖腔收尾，最后一句反转
整体风格：东北方言韵律，句尾上扬，像朋友之间吐槽不是表演。
节奏停顿明显，语气变化丰富。
```

#### API Key

`SUNOAPI_ORG_KEY` in `docs/content/.env`

#### 批量脚本

```bash
source docs/content/.env
python docs/content/scripts/suno-add-vocals-test.py
```

### 16.5 视觉风格：杨梦摇拖拉机

#### 参考视频

抖音 鸿燊 摇拖拉机卡点（202.2万赞）— 有节奏的身体抖动，双臂像发动拖拉机的动作，与节拍同步的夸张动作。

#### 角色锚定

每张图必须使用完全相同的角色描述：

```
a young Chinese woman in her late 20s, round face, short black bob haircut
with straight bangs just above eyebrows, wearing a simple cream-colored
linen shirt with a small collar
```

#### 摇拖拉机视觉要素

| 要素 | 描述 |
|------|------|
| 主体动作 | 有节奏的身体前后抖动，双臂像手摇拖拉机 |
| 表情 | 夸张的开心/搞笑表情，嘴巴张开 |
| 景别 | 全身或膝上，展示身体动作 |
| 背景 | 简洁明亮的室内/户外，不抢主体 |
| 运动感 | 画面要有动感模糊，不是静态摆拍 |

#### Seedream Prompt 结构（v4.0）

```
{角色锚定},
{摄影声明: Canon 5D Mark IV / Sony A7III},
{动作: doing rhythmic body-shaking dance move, arms cranking like starting a tractor, energetic and exaggerated movement, wide smile, laughing},
{背景: simple bright background},
{光影: natural daylight from left side, hard warm shadows},
vertical composition 9:16
```

#### Negative Prompt

```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain,
static pose, stiff, frozen, blur face
```

### 16.6 方言说唱配置文件格式

```json
{
  "video_id": "sings-dialect-rap-ep{NN}",
  "workflow": "sings-dialect-rap",
  "version": "3.0",
  "series": "sings-dialect-rap",
  "episode": NN,
  "episode_title": "{冲突对立主题}",

  "bgm": {
    "file": "docs/content/assets/bgm/杨梦.bgm_副本.mp3",
    "title": "Fraelis (trimmed)",
    "artist": "Frankie T",
    "bpm": 128,
    "duration_s": 95,
    "structure": {
      "intro": {"start": 0, "end": 4},
      "verse1": {"start": 4, "end": 30},
      "break": {"start": 30, "end": 45},
      "drop": {"start": 45, "end": 47},
      "chorus": {"start": 47, "end": 65},
      "verse2": {"start": 65, "end": 85},
      "outro": {"start": 85, "end": 95}
    }
  },

  "suno": {
    "model": "V4_5PLUS",
    "vocal_gender": "f",
    "style_tags": "comedic spoken-word rap, Chinese Northeast dialect, half-spoken half-sung, 128 bpm, tech house beat, tongue-in-cheek, comedic timing",
    "negative_tags": "slow ballad, sad, dramatic, rock, heavy metal, autotune, R&B, jazz, country"
  },

  "lyrics": {
    "suno_format": "[Intro]\n...\n[Verse 1]\n...\n[Break]\n...\n[Chorus]\n...\n[Verse 2]\n...\n[Outro]\n..."
  },

  "publishing": {
    "title_candidates": ["..."],
    "tags": ["东北话", "搞笑", "方言说唱", "..."],
    "collection": "杨梦东北话说唱"
  }
}
```

### 16.7 生产流程

```
1. 选冲突对立主题 → 写歌词（按 Section 16.2 模板）
2. 填入 config JSON
3. 上传 BGM → 调用 Suno Add Vocals → 下载合成音频
4. 用 Seedream 生成 5-6 张杨梦摇拖拉机参考图
5. 用 Kling 将参考图生成 5 秒视频片段
6. FFmpeg 拼接视频 + 合并音频
7. 剪映加字幕+特效+去AI化
8. Stage 7 审核门控
```

### 16.8 质量检查（方言说唱专用）

- [ ] 歌词 Section 标记对齐 BGM 能量变化（MUST）
- [ ] Break 段在 30-45s 低能量区（MUST）
- [ ] Chorus 段在 47s DROP 后爆发（MUST）
- [ ] 东北方言自然不生硬（MUST）
- [ ] 半说半唱风格，不是纯说唱也不是纯唱歌（MUST）
- [ ] BGM 和人声融合自然，不互相打架（MUST）
- [ ] 每句有"刺"，能引起共鸣（SHOULD）
- [ ] Outro 有反转/意外（SHOULD）
