# AI 短视频生产规范 v2.0 — Medvi 工作流

> 适用范围：30-45 秒 AI 生成短视频，抖音/小红书竖版
> 工作流类型：**Medvi**（电影纪录片风格商业内容，旁白驱动）
> 工具链：Seedream 4.5 + Runway Gen-4 + Gemini 3.1 Flash TTS + FFmpeg + 剪映
> 本文档是唯一权威标准，取代所有先前的工作流文档
> 最后更新：2026-04-19

---

## 0. 如何使用本规范

### 规则等级

| 标记 | 含义 | 违反后果 |
|------|------|----------|
| **MUST** | 硬性要求 | 不通过 = 返回对应阶段重做 |
| **SHOULD** | 强烈建议 | 可偏离，但需记录原因 |

### 驱动方式

每条视频由一个 JSON 配置文件驱动全流程。所有工具（Seedream 脚本、Gemini TTS 脚本、FFmpeg 脚本）从配置文件读取参数。

```
config/{video_id}.json  →  驱动全部 7 个阶段
```

### 阶段总览

```
Stage 1: 脚本写作    →  编辑 JSON 配置文件
Stage 2: 参考图生成  →  seedream-batch.py 读配置
Stage 3: 视频生成    →  Runway 手动操作，参数来自配置
Stage 4: 配音生成    →  gemini-tts-batch.py 读配置
Stage 5: 视频合成    →  compose-video.py 读配置
Stage 6: 去AI化后期  →  FFmpeg 滤镜 + 剪映精修
Stage 7: 最终审核    →  人工 + 脚本检查，通过后上传
```

---

## 1. 视频全局标准

### 1.1 时长

| 规则 | 标记 | 值 |
|------|------|----|
| 最终时长 30-45 秒 | MUST | ffprobe 检查 |
| 甜点区间 33-38 秒 | SHOULD | 完播率最高 |
| 钩子 = 前 3 秒 | MUST | |
| 主体 = 22-32 秒 | MUST | |
| CTA = 最后 5 秒 | MUST | |
| 超过 45.0 秒 = 拒绝 | MUST | Stage 7 门控 |

### 1.2 分辨率和编码

| 规则 | 标记 | 值 |
|------|------|----|
| 导出分辨率 1080x1920 | MUST | 9:16 竖版 |
| Runway 输出 720x1280 | MUST | 后期升采样 |
| 参考图 1440x2560 | MUST | Seedream API 原生 9:16 2K |
| 帧率 24fps | MUST | Runway 原生输出，全程一致 |
| 编码 H.264 MP4 | MUST | |
| 码率 ≥ 8Mbps | MUST | |
| FFmpeg 导出参数 | MUST | `-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p` |

### 1.3 镜头数量和类型

| 规则 | 标记 | 值 |
|------|------|----|
| 每条视频 6-8 个镜头 | MUST | 不超过 8 个（Day 1 的 10 个太多） |
| 单镜头不超过 5 秒 | MUST | |
| 平均镜头 4-5 秒 | SHOULD | |
| 至少 2 种景别 | MUST | {远景, 中景, 特写, 文字卡片} |
| 连续相同景别不超过 2 个 | MUST | |
| 景别定义见下表 | MUST | |

**景别定义：**

| 景别 | 用途 | Runway 提示词方向 | 占比参考 |
|------|------|------------------|---------|
| 远景（Wide） | 开场/转场/结尾 | slow pan, wide angle, establishing shot | ~15% |
| 中景（Medium） | 主体展示/工作场景 | medium shot, natural framing | ~45% |
| 特写（Close-up） | 数据放大/情感连接 | extreme close-up, shallow depth of field | ~30% |
| 文字卡片（Text） | 数据展示/对比/CTA | HTML/CSS 渲染 + Playwright 截图 | ~10% |

**文字卡片自动路由：** `shot_type: text_card` 的段落跳过 Stage 2（Seedream）和 Stage 3（Runway），在 Stage 5（FFmpeg 合成）中由 `text-card-renderer.py` 通过 HTML/CSS + Playwright 自动渲染。支持渐变背景、文字发光、逐行动画、微粒子装饰。

**文字卡片配置（`text_card_config`）：**
```json
{
  "lines": ["第一行文字", "第二行文字", "第三行文字"],
  "font_size": 52,
  "font_color": "#c9a96e",
  "bg_color": "#0a0806",
  "animation": "fade_in"
}
```

渲染器自动查找 `assets/references/{video_id}/` 下对应段落的参考图作为背景（带暗化遮罩），无背景图时使用渐变背景。

独立渲染命令：
```bash
python3 scripts/text-card-renderer.py --config config/{video_id}.json --segment S04
python3 scripts/text-card-renderer.py --lines "文字1" "文字2" --style sings --png-only
```

**景别切换节奏模板：**
```
远景(3s) → 中景(4s) → 特写(3s) → 中景(4s) →
特写(3s) → 中景(5s) → 远景(2s) → 文字卡片(3s) → 中景(4s)
```

---

## 2. 钩子设计规范（前 3 秒）

### 2.1 第一帧

| 规则 | 标记 |
|------|------|
| 第 1 帧必须包含可见文字（不是黑色渐入） | MUST |
| 文字占屏幕宽度 ≥ 60% | MUST |
| 核心信息在前 1.5 秒内出现 | MUST |

### 2.2 旁白时序

| 规则 | 标记 |
|------|------|
| 旁白在视频开始后 0.5 秒内出声 | MUST |
| 钩子旁白恰好一句话，≤ 20 个中文字 | MUST |

### 2.3 钩子类型（优先级排序）

| 优先级 | 类型 | 示例 | 3 秒留存率 |
|--------|------|------|-----------|
| 1 | 名人震撼 | "马斯克哪里是给自己公司定规矩，分明是给全行业定规矩" | 70-80% |
| 2 | 反常识数字 | "2个人，103美元月费，4亿营收" | 65-75% |
| 3 | 成本对比 | "10人团队月花5万 vs 1人月花750" | 55-65% |
| 4 | 好奇缺口 | "99%的营销团队不知道的方法" | 50-60% |
| 5 | 身份筛选 | "如果你每个月花超过1万做内容推广" | 55-65% |

### 2.4 视觉规则

| 规则 | 标记 |
|------|------|
| 名人震撼型：用真实名人照片或强代入感的人物画面 | MUST |
| 数字钩子用暗色背景 + 冷蓝/暖金点缀（按视频色系） | MUST |
| 不要慢速渐入，直接切入画面 | MUST |
| 钩子镜头使用特写或极特写（不用远景） | SHOULD |

---

## 3. 字幕规范

### 3.1 覆盖率

| 规则 | 标记 |
|------|------|
| 100% 旁白文字有对应字幕 | MUST |
| 旁白中所有数字在字幕中用相同数值出现 | MUST |

### 3.2 样式

| 规则 | 标记 |
|------|------|
| 白色文字 (#FFFFFF)，黑色描边 (2-3px)，字号 ≥ 36pt (1080p) | MUST |
| 关键数字用金色 (#c9a96e) 加粗，1.5 倍常规字号 | MUST |
| 字幕位置底部居中，留出平台 UI 安全区 | SHOULD |

### 3.3 自动化

| 规则 | 标记 |
|------|------|
| 字幕从脚本配置文件自动生成 SRT，不手动输入 | MUST |
| SRT 文件在合成阶段自动烧入视频 | MUST |

### 3.4 时序

| 规则 | 标记 |
|------|------|
| 字幕在旁白前 ≤ 0.2 秒出现 | MUST |
| 字幕在旁白后 ≤ 0.3 秒消失 | MUST |

---

## 4. CTA 规范

### 4.1 位置

| 规则 | 标记 |
|------|------|
| CTA 占据视频最后 5 秒 | MUST |
| CTA 文字同时出现在字幕和画面文字卡片上 | MUST |

### 4.2 内容

| 规则 | 标记 |
|------|------|
| 只要求一个动作（不是两个） | MUST |
| 使用批准的模板之一 | MUST |
| 关键词 ≤ 6 个中文字（好记好打） | MUST（转化型 CTA） |
| 给出具体明确的交付物（"完整工具清单"不是"更多内容"） | MUST（转化型 CTA） |
| 流量优先视频不引导私信、关注、领取 | MUST（流量型 CTA） |

**批准的 CTA 模板：**

**流量优先型（推荐，追求完播率和评论互动）：**
```
模板 D："你觉得你的[岗位/行业]，AI多久能替代？评论区聊聊。"
模板 E："如果是你，你会怎么做？评论区说说你的看法。"
模板 F："你觉得这件事对不对？评论区聊聊。"
```

**转化型（用于需要引导用户行动的场景）：**
```
模板 A："关注我，[下一条内容预告]"
模板 B："私信'[关键词]'，我发你[交付物]"
模板 C："评论区扣1，我发你[交付物]"
```

### 4.3 视觉

| 规则 | 标记 |
|------|------|
| 暗色背景 (#000000)，文字颜色按视频色系（冷蓝 #4a90d9 或暖金 #c9a96e） | MUST |
| 包含平台图标（抖音/小红书） | SHOULD |

---

## 5. Stage 1：脚本写作

### 5.1 输入/输出

- 输入：选题想法（来自内容日历）
- 输出：JSON 配置文件

### 5.2 策略选择

每条视频在配置文件中通过 `strategy_notes` 声明策略：

| 策略 | 目标 | 钩子 | CTA | 适用场景 |
|------|------|------|-----|---------|
| **流量优先** | 完播率、评论互动 | 名人震撼/反常识 | 开放讨论 | 早期涨粉，不卖东西 |
| **转化优先** | 引导用户行动 | 数字/成本对比 | 私信关键词 | 有成熟产品后 |

### 5.3 MUST 规则

| 规则 | 值 |
|------|----|
| 总旁白字数 | 30 秒 → 100-130 字，45 秒 → 150-200 字 |
| 每句旁白 | ≤ 15 个中文字，超过就断句 |
| 套话禁止 | 不用"今天就教大家"、"大家好我是XX" |
| CTA | 只有一个明确的动作 |
| 大声朗读计时 | 30-45 秒，用秒表验证 |
| 每段标注 emotion_arc | 中文情绪标签（震撼/紧张/反转/好奇/恐惧/参与） |
| 每段有 subtitle_text | ≤ 12 字的浓缩字幕，不是旁白全文 |

### 5.4 流量优先策略规则

| 规则 | 值 |
|------|----|
| 名人叙事 | 用真实名人/大公司的故事做钩子，不虚构 |
| 情绪弧线 | 震撼→紧张→反转→好奇→恐惧→参与（6 段压缩版） |
| Anti-ad 措施 | 见下方清单 |
| 不卖东西 | 不提产品、工具、方案、服务 |
| 不引导转化 | 不引导私信、关注、领取 |
| CTA 用开放问题 | 激发评论互动，不是推销 |
| 关键数字 | 用在故事里自然带出，不为凑数字而加 |

**Anti-ad 措施清单（配置文件 `script.anti_ad_measures`）：**

```
1. 不提 AI Agent、代运营、智能体等业务关键词
2. 不引导私信、领取、关注
3. CTA 用开放式问题，激发评论互动
4. 聚焦名人的故事和情绪，不卖任何东西
5. 避免出现"工具""方案""服务"等营销词汇
```

### 5.5 转化优先策略规则

| 规则 | 值 |
|------|----|
| 关键数字 | 全文至少 3 个具体数字 |
| 主体数据点 | 4-6 个，每个映射到独立镜头 |
| 情绪弧线 | 高(钩子) → 低(背景) → 高(数据) → 高(对比) → 暖(CTA) |
| CTA | 有明确关键词和交付物 |

### 5.6 SHOULD 规则

| 规则 | 值 |
|------|----|
| 信息密度 | 不超过 2 秒无新信息的段落 |
| 节奏 | 整体偏快，不拖沓 |
| 数字强调 | 说到关键数字时放慢加重（通过 voiceover_pause_markers 控制） |

### 5.7 质量检查

- [ ] 大声朗读计时：___ 秒（MUST：30-45s）
- [ ] 字数：___ 字（MUST：100-200 字）
- [ ] CTA 动作数量：___ 个（MUST：= 1）
- [ ] 最长单句：___ 字（MUST：≤ 15）
- [ ] 每段有 emotion_arc 标签（MUST）
- [ ] 每段有 subtitle_text（MUST）
- [ ] 流量优先视频：anti_ad_measures 全部通过（MUST）
- [ ] 流量优先视频：无营销词汇、无转化引导（MUST）
- [ ] 转化优先视频：数字数量 ≥ 3（MUST）

---

## 6. Stage 2：参考图生成（Seedream 4.5）

### 6.1 输入/输出

- 输入：JSON 配置文件中的 `segments[].reference_prompt`
- 输出：PNG 文件，1440x2560，存入 `assets/references/{video_id}/`

### 6.2 MUST 规则

| 规则 | 值 |
|------|----|
| 所有图片 9:16 比例 | 1440x2560（Seedream API） |
| 提示词后缀 | 每张图末尾加 `vertical composition 9:16` |
| 风格统一 | 深色调 + 冷蓝/暖金点缀 + 电影纪录片感（按视频色系） |
| 主体位置 | 居中偏下，上方留空间给运动和字幕 |
| 画面中无文字 | AI 生成的文字一定是乱码，文字在后期加 |
| 画面中无手部 | Seedream/Midjourney 手部生成有缺陷 |
| 边缘干净 | 无重要元素靠近画框边缘（Runway 会扭曲边缘） |

### 6.3 Prompt 生成逻辑（MUST 阅读）

> 经 4 轮迭代验证的最终方法论。违反这些原则 = 图片无法引起观众情绪共鸣。

**核心框架：情感弧线 + 辨识度元素**

每条视频的图片序列必须构成一条完整的情感弧线。按策略选择对应弧线：

**流量优先弧线（名人叙事型）：**

```
震撼 → 紧张 → 反转 → 好奇 → 恐惧 → 参与
```

| 步骤 | 情绪 | 观众内心反应 | 视觉要素 |
|------|------|------------|---------|
| 1 震撼 | 震惊/好奇 | "真的假的？" | 权威人物/大场面，低角度仰拍，强光影 |
| 2 紧张 | 焦虑/不安 | "然后呢？" | 空旷/荒凉的办公室场景，冷光 |
| 3 反转 | 意外/惊叹 | "怎么可能？" | 人离开/行走的背影，暖光尽头 |
| 4 好奇 | 想知道秘密 | "到底是什么？" | 半脸/暗处人物，屏幕光 |
| 5 恐惧 | 危机感 | "这会不会轮到我？" | 一个人 vs 大量屏幕/数据，压迫感 |
| 6 参与 | 被问到 | "让我想想" | 人物正面看向镜头，诚恳表情 |

**转化优先弧线（数据冲击型）：**

```
共情 → 向往 → 希望 → 震撼 → 对比 → 信任
```

| 步骤 | 情绪 | 观众内心反应 | 视觉要素 |
|------|------|------------|---------|
| 1 共情 | 同情/代入 | "我也是普通人" | 朴素环境中的人，简陋但有温度 |
| 2 向往 | 渴望逆袭 | "我也想翻盘" | 深夜苦干的身影，微光中的坚持 |
| 3 希望 | 抓住机会 | "这可能就是出路" | 人面对屏幕/数据，专注投入 |
| 4 震撼 | 数字冲击 | "这不可能" | 爆发式增长的视觉化（有辨识度的增长曲线/柱体） |
| 5 对比 | 不服/惊叹 | "比大公司还猛？" | 一人 vs 空间（以小胜大的视觉张力） |
| 6 信任 | 温暖邀请 | "告诉我怎么做的" | 分享的姿态，温暖光线 |

**原则 1：图片要有辨识度元素，不是纯抽象**

| 维度 | 正确做法 | 错误做法 |
|------|---------|---------|
| 画面内容 | 有辨识度的元素（人、电脑、办公桌、数据图） | 纯抽象几何图形（光点、色块） |
| 情绪来源 | 观众从画面中的"人/物"产生共情 | 观众看到抽象图形，无从产生情绪 |
| 辨识速度 | 0.3 秒内识别画面内容并产生情绪 | 需要思考"这是什么"，情绪中断 |

关键区别：图片不能抽象到让观众看不懂。画面中必须有人能识别的元素，才能触发情绪。

**原则 2：图片是旁白的情绪伴奏，不是旁白的复述**

| 维度 | 正确做法 | 错误做法 |
|------|---------|---------|
| 图片功能 | 为旁白提供情绪氛围 | 把旁白内容"画出来" |
| 信息传递 | 100% 旁白 + 字幕传递信息 | 图片试图承载信息 |
| 叙事 | 图片只传达一个情绪，不讲故事 | 图片试图讲述完整故事线 |

观众不需要从图片里看出"这是拖车公园"，但需要看到"一个在简陋环境中坚持的人"才能产生共情。

**原则 3：摄影先行的 Prompt 方法论（v3.0 去AI感，经验证有效）**

> v3.0 经 3 轮实测验证（v1→v2→v3），每轮迭代有明确改善。生图必须严格遵循此方法论。

核心思路：摄影术语不会让 Seedream 精确模拟物理相机，但会强烈引导模型走向「真实摄影」的分布，远离「精修插画/AI渲染」分布。

**Prompt 结构（6 层，严格按顺序）：**

```
[摄影声明], [主体+具体不完美+面部不对称], [环境+真实物件名], [光影+方向], [构图], vertical composition 9:16
```

**第 1 层：摄影声明（prompt 最前面，权重最高，MUST）**

每条 prompt 开头必须包含摄影参数声明，从以下选项中选一个：
- `shot on Canon 5D Mark IV, 50mm f/1.4, Kodak Portra 400 film` — 纪录片质感
- `iPhone 15 Pro photo, slightly underexposed, natural lighting` — 随手拍质感
- `35mm documentary film still, grainy, imperfect focus` — 胶片纪录片质感
- `shot on Sony A7III, 85mm f/1.8, available light, Fuji 400H` — 日系纪实

**第 2 层：主体 + 具体不完美 + 面部不对称（MUST）**

不能用笼统的 "natural skin texture"。必须写具体的、可见的不完美。**凡是有人脸的画面，必须包含至少 1 处明确的面部不对称描述。**

具体不完美：
- ✅ `slight forehead acne and uneven stubble` — 具体可见
- ✅ `wearing a faded oversized hoodie with a small stain on sleeve` — 具体磨损
- ❌ `natural skin texture with visible pores` — 太笼统，AI 模型倾向忽略

面部不对称（至少选 1 条）：
- `one eyebrow slightly raised/furrowed higher than the other`
- `lips pressed together with one corner slightly higher`
- `one eye slightly more squinted than the other`
- `uneven stubble with a small patch missed while shaving`
- `one front tooth slightly overlapping`
- `jaw slightly clenched with visible tension in the cheek muscle`
- `smile lines deeper on one side than the other`

**第 3 层：环境 + 真实物件名（MUST）**

用真实品牌/型号代替笼统描述：
- ✅ `old ThinkPad laptop on a wobbly IKEA table with coffee ring stains`
- ✅ `water-stained ceiling, peeling wallpaper edges, power strip under desk`
- ❌ `small room with old laptop on a table`

**第 4 层：光影 + 方向（MUST）**

必须有光源方向和质感，不能只写 "warm light"：
- ✅ `late afternoon directional light through a dirty window casting hard warm shadows`
- ✅ `cool white screen glow as only light source casting hard shadow edges on face`
- ❌ `warm golden evening light` — 没有方向，AI 会生成平面柔光

**第 5 层：构图**
- 主体在下 2/3，上方留空间
- 每张图末尾加 `vertical composition 9:16`

**第 6 层：Negative Prompt（每张图 MUST 配置）**

```
airbrushed, smooth plastic skin, perfect symmetry, perfect facial symmetry,
symmetric face, centered perfectly symmetrical features, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
oil painting, watermark, text, logo, oversaturated, hyperrealistic,
mannequin, doll-like, flawless, magazine cover, retouched,
even skin tone, poreless skin
```

配置文件中通过 `reference_images.negative_prompt` 字段设置，`seedream-batch.py` 自动读取。

**完整示例：**

`shot on Canon 5D Mark IV 50mm f/1.4 Kodak Portra 400, young man early twenties with lips pressed together tightly showing quiet struggle, one eyebrow slightly furrowed higher than the other, jaw slightly clenched with visible tension in the cheek muscle, uneven stubble on jaw with a small patch missed while shaving, sitting on floor in a cramped rented room with water-stained ceiling and peeling wallpaper edges, a single old ThinkPad laptop on the floor in front of him, late afternoon directional light through a dirty window casting hard warm shadows with one shadow crossing his face diagonally, visible film grain especially in shadow areas, subject in lower two-thirds, vertical composition 9:16`

**原则 4：画面中禁止的元素**

- 无手部（AI 生成有缺陷）
- 无文字（AI 生成的文字一定是乱码，文字在后期加）
- 无过于具体的场景细节（不需要画出"拖车公园"这种具体场景）
- 无笼统的去AI后缀（如 "natural skin texture with visible pores" 单独贴在末尾无效）

**原则 5：手机视角检验**

每个 prompt 想象在 200px 宽的屏幕上看到的效果。如果画面细节在 200px 下丢失了，那个细节就不值得生成。辨识度元素必须在 200px 下仍然可识别。

### 6.4 SHOULD 规则

| 规则 | 值 |
|------|----|
| 每个镜头生成候选 | 2-3 张，选最佳 |
| 统一色温 | 暖金色约 4500K（转化优先）或冷钢蓝约 6500K（流量优先） |
| 提示词结构 | 严格遵循原则 3 v3.0 六层结构 |

### 6.5 Seedream 4.5 参数

| 参数 | 值 |
|------|----|
| API | EvoLink，$0.030/张 |
| 分辨率 | 1440x2560 |
| 模型 | doubao-seedream-4.5 |
| 批量命令 | `python docs/content/scripts/seedream-batch.py --config config/{video_id}.json` |

### 6.6 质量检查

- [ ] 所有图片色温一致
- [ ] 无手部可见
- [ ] 无 AI 生成文字
- [ ] 主体在下 2/3，上方留空
- [ ] 边缘元素最少
- [ ] 分辨率 ≥ 1440px 高
- [ ] 每张图有辨识度元素（不是纯抽象），观众 0.3 秒能识别（原则 1）
- [ ] 每张图只传达一个情绪，不承载叙事信息（原则 2）
- [ ] 6 张图构成完整情感弧线（流量优先：震撼→紧张→反转→好奇→恐惧→参与；转化优先：共情→向往→希望→震撼→对比→信任）
- [ ] Prompt 开头有摄影声明（原则 3 v3.0）
- [ ] Prompt 中有具体的、可见的不完美描述（不是笼统后缀）
- [ ] 有人脸的画面包含至少 1 处面部不对称描述（原则 3 v3.0）
- [ ] Negative prompt 已配置，包含 v3.0 完整列表（原则 3 v3.0）
- [ ] 200px 宽度下辨识度元素仍可识别（原则 5）

---

## 7. Stage 3：视频生成（Runway Gen-4）

### 7.1 输入/输出

- 输入：参考图 + JSON 配置中的 `segments[].motion_prompt`
- 输出：MP4 文件，720x1280，24fps，5 秒/段

### 7.2 MUST 规则

| 规则 | 值 |
|------|----|
| 只使用 Image-to-Video | 绝不用纯文生视频 |
| 提示词只写运动 | 不重复描述画面中已有的内容，最多 2 句 |
| Fixed Seed 开启 | 全片用同一个 seed 值 |
| 分辨率 | 720x1280 (9:16) |
| 每段时长 | 5 秒 |
| 拒收标准 | 任何片段出现变形、闪烁、物体扭曲、面部异常 = 重新生成 |
| 每段候选数 | ≥ 3 个，选最佳 |

### 7.3 SHOULD 规则

| 规则 | 值 |
|------|----|
| 迭代用 Gen-4 Turbo | 5 credits/s，速度快 |
| 最终用 Gen-4 | 12 credits/s，质量最高 |
| 运动强度 | 3-5/10，宁低勿高 |
| 景别匹配运动 | 见下表 |

**景别对应 Camera 参数：**

| 景别 | Camera 运动 | 提示词模板 |
|------|------------|-----------|
| 远景 | slow pan 或 slow zoom out | `slow pan left, ambient atmosphere, cinematic motion` |
| 中景 | slow push in 或微幅运动 | `subtle head movement, natural breathing, ambient light shift` |
| 特写 | very slow zoom in | `slow zoom in, numbers glowing subtly, cinematic motion` |
| 文字卡片 | gentle fade + 轻微视差 | `gentle fade in, slight parallax on text elements` |

### 7.4 Runway 后处理（导出前）

| 操作 | 标记 | 参数 |
|------|------|------|
| Retime → Trim | MUST | 裁掉首尾不稳定帧 |
| Retime → Handheld Shake | MUST | 强度 10-15% |
| 4K Upscale | SHOULD | 最终选中的片段 |

### 7.5 质量检查

- [ ] 5 秒内无变形/闪烁
- [ ] 运动自然不卡顿
- [ ] 色调与参考图一致
- [ ] 无 AI 水印
- [ ] 首帧和末帧干净可用

---

## 8. Stage 4：配音生成

### 8.1 输入/输出

- 输入：JSON 配置中的 `segments[].voiceover_text`
- 输出：每段 MP3 + 完整旁白 MP3 + SRT 字幕文件

### 8.2 TTS 引擎优先级

| 优先级 | 引擎 | 费用 | 质量 | 脚本 |
|--------|------|------|------|------|
| 1 | **Gemini 3.1 Flash TTS** | 免费（有额度限制） | 最高 | `gemini-tts-batch.py` |
| 2 | **Edge TTS** (YunxiNeural) | 完全免费，无限制 | 高 | `edge-tts-batch.py` |
| 3 | Fish Audio S2 Pro | 按量付费 | 高 | `fish-audio-tts-batch.py` |
| 4 | CosyVoice (DashScope) | 免费额度 | 中高 | `cosyvoice-tts-batch.py` |

**选择规则：** Gemini 额度可用时用 Gemini。额度用尽后用 Edge TTS。质量优先于时长限制。

### 8.3 MUST 规则

| 规则 | 值 |
|------|----|
| 音频格式 | MP3 |
| 音量标准化 | 开启 |
| 3 遍听测 | 连听 3 遍不觉得机械感，否则重新生成 |
| 叙述者一致性 | 全片使用同一声音，只改情绪参数 |

### 8.4 Gemini 3.1 Flash TTS 参数

| 参数 | 值 |
|------|----|
| 模型 | gemini-3.1-flash-tts-preview |
| 声音 | Charon（深沉男声）或 Orus（温暖男声） |
| 批量命令 | `python3 gemini-tts-batch.py --config config/{video_id}.json` |
| 需要环境变量 | `GEMINI_API_KEY` |

**特点：** 支持 Director's Notes 精细控制情绪，音频标签（[amazed], [warmly]），质量最接近真人。

### 8.5 Edge TTS 参数（免费备选）

| 参数 | 值 |
|------|----|
| 声音 | `zh-CN-YunxiNeural`（推荐，年轻温暖男声） |
| 声音备选 | `zh-CN-YunjianNeural`（沉稳新闻风格） |
| 批量命令 | `python3 edge-tts-batch.py --config config/{video_id}.json` |
| 需要环境变量 | 无 |

**情绪控制：** 通过 rate/pitch/volume 参数按 emotion_arc 自动调整：

| emotion_arc | rate | pitch | volume | 效果 |
|------------|------|-------|--------|------|
| 震撼 (shock) | -5% | +2Hz | +10% | 沉重有力 |
| 紧张 (tension) | +5% | -2Hz | +5% | 紧凑压迫 |
| 反转 (reversal) | -10% | +0Hz | +5% | 减速强调 |
| 好奇 (curiosity) | +0% | +3Hz | +0% | 微妙好奇 |
| 恐惧 (fear) | +3% | -3Hz | -5% | 低沉威胁 |
| 参与 (engagement) | +5% | +2Hz | +5% | 真诚互动 |

### 8.6 SHOULD 规则

| 规则 | 值 |
|------|----|
| 生成方式 | 同时生成分段文件（用于合成）+ 完整文件（用于参考） |
| 时长超 45s | 优先保证质量，可通过剪映调速 |

### 8.7 质量检查

- [ ] 每个字可辨识（无含糊不清）
- [ ] 无金属/电子感（3 遍听测通过）
- [ ] 关键数字有自然强调
- [ ] 音质干净无噪音
- [ ] 全片叙述者声音一致

---

## 9. Stage 5：视频合成

### 9.0 核心原则：FFmpeg 只做拼接+音频合并

> FFmpeg 不做剪映的活。拼接 + 音频合并用 FFmpeg（秒级完成），所有视觉处理用剪映（实时预览）。违反这个分工 = 无法批量生产。

### 9.1 输入/输出

- 输入：视频片段 + 配音 MP3
- 输出：`output/{video_id}/{video_id}_concat.mp4`，仅拼接+配音

### 9.2 FFmpeg 职责（只做这些）

| 规则 | 值 |
|------|----|
| 视频片段按脚本顺序拼接，硬切 | concat demuxer |
| 配音音轨合并 | 不做任何音频处理 |
| 不做滤镜、不做字幕、不做叠加 | MUST |
| 不做色彩校正、不做去AI | MUST |

### 9.3 FFmpeg 命令（简单版）

```bash
# Step 1: 拼接视频片段
ffmpeg -f concat -safe 0 -i segments.txt \
  -c:v libx264 -preset fast -crf 18 -pix_fmt yuv420p -r 24 \
  -an concat_video.mp4

# Step 2: 合并配音
ffmpeg -i concat_video.mp4 -i voiceover_full.mp3 \
  -c:v copy -c:a aac -b:a 192k \
  -shortest output/{video_id}_concat.mp4
```

### 9.4 剪映职责（所有视觉工作）

在剪映里完成以下所有操作：

| 任务 | 操作 |
|------|------|
| 字幕 | 自动生成 + 手动校对数字，金色高亮 |
| BGM | 拖拽音频轨，音量 8-12% |
| 去AI 4 步 | 胶片颗粒 + 光晕 + 色彩校正 + 抖动（见 Stage 6） |
| AI标识水印 | 开头添加 "AI生成内容" 文字贴纸，持续 ≥ 3 秒 |
| 文字卡片 | 黑底金字画面 |
| 照片叠加 | 人物照片等 |
| 封面帧 | 选取或 Canva 制作 |

### 9.5 导出后的元数据标注

剪映导出后，用 FFmpeg 一条命令写入 AI 声明（不重编码，秒级完成）：

```bash
ffmpeg -i output.mp4 -metadata comment="本视频由AI生成合成，包含AI生成的图像和配音" -c copy output_labeled.mp4
```

### 9.6 质量检查

- [ ] ffprobe 时长 ≤ 45.0s 且 ≥ 30.0s
- [ ] 音画同步（抽查 3 个时间点）
- [ ] 片段间无黑帧

---

## 10. Stage 6：去AI化后期

### 10.1 四步去AI法

> 这 10% 的工作决定 90% 的真实感。

**Step 1：胶片颗粒**

| 参数 | 值 | 标记 |
|------|----|----|
| FFmpeg | `noise=c0s=12:c0f=t+u` | MUST |
| 剪映等效 | 滤镜 → 质感 → 胶片，强度 15-20% | MUST |
| 目的 | 打破 AI 的"过于干净"质感 | |

**Step 2：光晕/辉光**

| 参数 | 值 | 标记 |
|------|----|----|
| 剪映 | 特效 → 光效 → 柔光，强度 10-15% | MUST |
| 目的 | 模拟真实镜头光线散射 | |

**Step 3：色彩校正**

| 参数 | 值 | 标记 |
|------|----|----|
| 饱和度 | -5 到 -10 | MUST |
| 对比度 | +5 到 +10 | MUST |
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
| 包含大数字或关键短语 + 品牌色 (#c9a96e) | MUST |
| 9:16 比例，1080x1920 或 1440x2560 | MUST |
| 文字在缩略图尺寸下可读（抖音网格约 200px 宽） | MUST |

### 10.3 质量检查

- [ ] 关掉声音看一遍：画面是否自然？
- [ ] 截取任意一帧：能否看出是 AI 生成？
- [ ] 颗粒感可见但不过度
- [ ] 光晕"看得到但说不出"
- [ ] 所有镜头色温统一
- [ ] 封面帧在缩略图尺寸可读

### 10.4 FFmpeg vs 剪映分工

> **核心原则**：FFmpeg 只做拼接+音频合并。所有视觉处理在剪映里完成。违反 = 无法批量生产。

| 任务 | FFmpeg | 剪映 | 推荐 |
|------|--------|------|------|
| 片段拼接 | concat demuxer | 拖拽 | FFmpeg |
| 配音合并 | -i audio | 拖拽 | FFmpeg |
| AI 元数据标注 | -metadata -c copy | — | FFmpeg（导出后一条命令） |
| 字幕 | — | 自动+手动 | 剪映 |
| 去AI 4 步滤镜 | — | GUI 实时预览 | 剪映 |
| 色彩校正 | — | GUI | 剪映 |
| BGM 混合 | — | 拖拽 | 剪映 |
| AI标识水印 | — | 文字贴纸 | 剪映 |
| 文字卡片 | — | 文字模板 | 剪映 |
| 照片叠加 | — | 画中画 | 剪映 |
| 封面帧制作 | — | — | Canva |
| 最终视觉 QA | — | 预览+手机 | 剪映 + 手机 |

---

## 11. Stage 7：最终审核门控

> 这道门控决定视频能否上传。任何 MUST 检查不通过 = 返回对应阶段。

### 11.1 时长门控

- [ ] ffprobe 报告时长 ≤ 45.0s 且 ≥ 30.0s（MUST）
- 不通过 → 返回 Stage 1（脚本）或 Stage 5（合成）

### 11.2 内容完整性门控

- [ ] 旁白中所有数字与字幕中的数字一致（MUST）
- [ ] 所有数字经过来源核实（MUST）
- [ ] 无矛盾陈述（MUST）

### 11.3 技术质量门控

- [ ] 分辨率 1080x1920，24fps，H.264（MUST）
- [ ] 文件大小 ≥ 15MB（MUST，过小说明质量损失）
- [ ] 音频峰值 ≤ -1dB（MUST，无削波）
- [ ] 旁白信噪比 ≥ 20dB（MUST，清晰于 BGM）

### 11.4 去AI验证门控

- [ ] 手机预览通过"我会知道这是 AI 吗？"测试（MUST）
- [ ] 无手部伪影、文字乱码、面部异常（MUST）
- [ ] 无 AI 水印（MUST）

### 11.5 AI 内容标识门控（法规强制）

> 依据：《人工智能生成合成内容标识办法》，2025年9月1日生效

**显性标识（MUST）：**

- [ ] 视频开头有 "AI生成内容" 文字标识，持续 ≥ 3 秒
- [ ] 或全程半透明水印标注 "AI生成"
- [ ] 标识清晰可见、不可轻易去除
- [ ] FFmpeg 脚本自动添加（见 Stage 5 配置）

**隐性标识（MUST）：**

- [ ] 视频文件元数据包含 AI 生成声明
- [ ] FFmpeg 脚本自动写入 metadata（见 Stage 5 配置）

**发布时（MUST）：**

- [ ] 在平台发布界面勾选 "AI生成内容" 声明

**不合规后果**：平台有权下架、限流、封号。2025年9月1日后执行力度加强。

### 11.6 平台内容合规门控

**抖音规则（2025）：**

- [ ] 如涉及健康/医疗/减肥话题，发布者须为认证医疗专业人员（MUST）
- [ ] 无具体疗效承诺（"瘦了XX斤" 须有真实案例支撑）（MUST）
- [ ] 无暗示医疗建议的内容（MUST）
- [ ] 如涉及健康话题，添加 "仅供参考，不构成医疗建议" 免责声明（SHOULD）
- [ ] 无夸大/虚假广告用语（MUST）
- [ ] CTA 使用批准的模板（MUST）

**小红书规则：**

- [ ] 禁止虚假 Before/After 对比图（MUST）
- [ ] 禁止夸大效果宣传（MUST）
- [ ] 标注 "AI生成内容"（MUST）
- [ ] 无违反社区准则的内容（MUST）

**如内容不涉及健康/医疗话题：** 跳过健康相关检查项，其余项仍须通过。

### 11.8 元数据门控

- [ ] 标题从配置文件的 3 个候选中选取（MUST）
- [ ] 标签至少 3 个来自批准标签列表（MUST）
- [ ] 计划发布时间 12:00 或 18:00（SHOULD）

### 11.9 最终审批

```
视频编号：__________
日期：__________

时长：      ___s    [ ] PASS  [ ] FAIL
镜头数：    ___     [ ] PASS  [ ] FAIL
景别种类：  ___     [ ] PASS  [ ] FAIL
数字核实：  ___/___ [ ] PASS  [ ] FAIL
字幕覆盖：  ___%    [ ] PASS  [ ] FAIL
CTA 动作：  ___     [ ] PASS  [ ] FAIL
手机预览：          [ ] PASS  [ ] FAIL
去AI检查：          [ ] PASS  [ ] FAIL
AI显性标识：        [ ] PASS  [ ] FAIL  ← 法规强制
AI隐性标识：        [ ] PASS  [ ] FAIL  ← 法规强制
平台合规：          [ ] PASS  [ ] FAIL
封面帧：            [ ] PASS  [ ] FAIL

最终决定：[ ] 批准上传  [ ] 返回 Stage ___ 原因：__________
```

---

## 12. 视频配置文件格式

每条视频一个 JSON 文件，存放在 `docs/content/config/{video_id}.json`。

### Schema

```json
{
  "video_id": "day2-medvi-tools",
  "version": "2.0",
  "created": "2026-04-19",
  "status": "draft",
  "strategy_notes": "流量优先策略：不考虑转化，只追求完播率。名人叙事+情绪冲击，不提Agent/代运营/任何业务",

  "global": {
    "target_duration_sec": 33,
    "max_duration_sec": 45,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "runway_seed": 67890,
    "style": "cinematic_documentary",
    "color_temperature": "cool_steel",
    "accent_color": "#4a90d9",
    "bg_color": "#000000"
  },

  "script": {
    "topic": "马斯克裁了6000人用AI替代，公司效率反升",
    "source": "Yahoo Finance 2025, InfoQ 2025",
    "hook_type": "celebrity_shock",
    "cta_action": "讨论",
    "cta_keyword": "",
    "cta_deliverable": "",
    "anti_ad_measures": [
      "不提AI Agent、代运营、智能体等业务关键词",
      "不引导私信、领取、关注",
      "CTA用开放式问题，激发评论互动",
      "聚焦名人的故事和情绪，不卖任何东西",
      "避免出现'工具''方案''服务'等营销词汇"
    ]
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 5,
      "shot_type": "close-up",
      "emotion": "shock",
      "emotion_arc": "震撼",
      "visual_description": "权威人物低角度仰拍，强光影，绝对权威感",
      "motion_prompt": "slow push in from low angle...",
      "voiceover_text": "马斯克哪里是给自己公司定规矩。分明是给全行业定规矩。六千人，说裁就裁了。",
      "voiceover_pause_markers": "马斯克哪里是给自己公司定规矩。<#0.3#>分明是给全行业定规矩。<#0.3#>六千人<#0.2#>说裁就裁了。",
      "subtitle_text": "给全行业定规矩 说裁就裁",
      "reference_prompt": "..."
    }
  ],

  "voiceover": {
    "engine": "gemini_3.1_flash_tts",
    "model": "gemini-3.1-flash",
    "voice": "Charon",
    "sample_rate": 44100,
    "format": "mp3",
    "normalize": true,
    "director_notes": "像在讲一个震撼的故事，不是在念稿。说到数字时放慢加重，'六千人'、'九成'要掷地有声"
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "api": "evolink",
    "resolution": "1440x2560",
    "candidates_per_segment": 2,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry..."
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
    "post_processing": {
      "trim_unstable_frames": true,
      "handheld_shake_pct": 12,
      "upscale_4k": true
    }
  },

  "compositing": {
    "engine": "ffmpeg",
    "bgm_file": "assets/bgm/cinematic_dark_01.mp3",
    "bgm_volume_pct": 10,
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_script"
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
    "film_grain_intensity_pct": 18,
    "lens_glow_intensity_pct": 12,
    "saturation_adjust": -8,
    "contrast_adjust": 8,
    "sharpness_adjust": -3,
    "vignette": 0.3
  },

  "publishing": {
    "platforms": ["douyin", "xiaohongshu"],
    "title_candidates": [
      "马斯克裁了6000人，公司效率反而更高",
      "裁员80%效率反升，马斯克的秘密只有三个字",
      "未来公司的最小单元不是人，马斯克正在证明这件事"
    ],
    "tags": ["AI", "马斯克", "人工智能", "裁员", "自动化", "职场"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "暗色调背景，蓝色数据光，剪影+裁员数字对比"
  }
}
```

### 配置文件如何驱动全流程

| 阶段 | 读取的字段 |
|------|-----------|
| Stage 1 脚本 | 编辑 `segments` 数组和 `script` 字段 |
| Stage 2 参考图 | `segments[].reference_prompt` + `reference_images` 配置 |
| Stage 3 视频 | `segments[].motion_prompt` + `video_generation` 配置 |
| Stage 4 配音 | `segments[].voiceover_pause_markers` + `voiceover` 配置 |
| Stage 5 合成 | 镜头顺序 + `compositing` 配置 |
| Stage 6 后期 | `post_production` 配置 |
| Stage 7 审核 | 校验所有 MUST 规则 |

---

## 13. 文件组织

```
docs/content/
├── config/                # 视频配置文件（每条视频一个 JSON）
│   ├── day1-medvi-story.json
│   ├── day2-medvi-tools.json
│   └── ...
├── scripts/               # 脚本文档（Markdown）
│   └── day1-拆解40亿公司AI获客.md
├── workflow/              # 工作流文档
│   └── video-production-spec.md  ← 本文档（唯一权威标准）
├── assets/
│   ├── references/{video_id}/    # 参考图
│   ├── voiceover/{video_id}/     # 配音文件
│   ├── subtitles/{video_id}/     # SRT 字幕文件
│   ├── bgm/                      # BGM 库
│   └── covers/{video_id}/        # 封面帧
├── output/{video_id}/             # 最终输出 + 审核清单
└── tracking/
    ├── content-tracker.csv
    ├── weekly-summary.csv
    └── private-users.csv
```

---

## 14. 批量生产模式

### Day A：准备（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| 写 5 份配置文件 | 75 分钟 | 手动编辑 JSON |
| 批量生成参考图 | 50 分钟 | `seedream-batch.py` |
| Runway 批量生成视频 | 75 分钟 | 手动操作 Runway |
| 批量生成配音 | 25 分钟 | `gemini-tts-batch.py` |
| **总计** | **225 分钟** | |

### Day B：制作（5 条视频）

| 步骤 | 耗时 | 工具 |
|------|------|------|
| FFmpeg 合成 × 5 | 25 分钟 | `compose-video.py` |
| 剪映精修 × 5 | 50 分钟 | 剪映 |
| 最终审核 × 5 | 25 分钟 | Stage 7 清单 |
| **总计** | **100 分钟** | |

**产能：5 条/2 天，平均 65 分钟/条。周产能 15-20 条。**

---

## 15. 常见失败模式和修复

| 失败 | 根因 | 修复 |
|------|------|------|
| 视频 > 45s | 脚本太长或镜头 > 5s | 砍掉最弱数据点，强制 5s/镜头上限 |
| 景别单一 | 分镜表无景别字段 | 配置文件有 shot_type，Stage 7 检查 ≥ 2 种 |
| 字幕缺失 | 手动流程被遗忘 | 从配置自动生成 SRT |
| AI 痕迹明显 | 未做帧级检查 | Stage 7 强制逐帧检查 |
| 工具名不一致 | 多份文档互相矛盾 | 本文档是唯一标准 |
| 配音太长 | 语速太慢或文字太多 | 字数 ≤ 200 字，语速 ≥ 1.0 |

---

## 附录 A：批准标签列表

```
#AI获客 #AI营销 #AI视频 #人工智能 #内容营销 #创业 #一人公司 #AI工具 #AI代运营
```

## 附录 B：可复用 BGM 清单

| 文件名 | 风格 | BPM | 适用场景 |
|--------|------|-----|---------|
| tech_ambient_01.mp3 | 科技氛围 | 90 | 数据震撼型 |
| cinematic_dark_01.mp3 | 电影暗调 | 80 | 对比冲击型 |
| warm_documentary_01.mp3 | 温暖纪录片 | 100 | 方法论型 |
| upbeat_tutorial_01.mp3 | 轻快教学 | 110 | 实操演示型 |

## 附录 C：配色系统

### 色系 A：冷钢蓝（流量优先 / 名人叙事型）

| 用途 | 色值 | 使用场景 |
|------|------|---------|
| 冷蓝点缀 | #4a90d9 | 数据高亮、CTA 文字、封面 |
| 纯黑 | #000000 | 背景、文字卡片底色 |
| 深灰 | #0a0a0a | 替代纯黑的背景变体 |
| 白色 | #FFFFFF | 正文文字 |
| 冷白 | #e8edf5 | 次要文字 |

### 色系 B：暖金色（转化优先 / 数据冲击型）

| 用途 | 色值 | 使用场景 |
|------|------|---------|
| 品牌金 | #c9a96e | 数字高亮、CTA 文字、封面 |
| 纯黑 | #000000 | 背景、文字卡片底色 |
| 深灰 | #0a0a0a | 替代纯黑的背景变体 |
| 白色 | #FFFFFF | 正文文字 |
| 暖白 | #f5f0e8 | 次要文字 |

---

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-17 | 1.0 | 初始版本，取代所有先前工作流文档 |
| 2026-04-17 | 1.1 | 配音引擎从 MiniMax Speech-02 替换为 Fish Audio S2 Pro |
| 2026-04-18 | 1.2 | 配音引擎替换为 Gemini 3.1 Flash TTS，新增 AI 内容标识规范、平台合规门控 |
| 2026-04-18 | 1.3 | 添加 Medvi 工作流标识，新增 Sings 工作流 |
| 2026-04-18 | 1.2 | 新增 AI 内容标识规范（显性+隐性）、平台合规门控强化（抖音健康内容规则、小红书规则）、最终审批增加 AI 标识字段 |
| 2026-04-19 | 2.0 | 集成流量优先脚本写作方案：名人叙事钩子(celebrity_shock)、开放讨论CTA、anti-ad措施、新情绪弧线(震撼→紧张→反转→好奇→恐惧→参与)、冷钢蓝色系、每段emotion_arc+subtitle_text字段 |
| 2026-04-19 | 2.1 | TTS 引擎分层：Gemini(首选) → Edge TTS(免费备选) → Fish Audio → CosyVoice；新增 edge-tts-batch.py 脚本，支持 emotion_arc 自动调 rate/pitch/volume |
