# Yang Mun 式情绪 IP：从纪录片信息流到固定角色美学

> 日期：2026-04-20
> 状态：分析完成，待验证
> 关联：video-production-spec.md（当前 v3.0 Prompt 方法论）

---

## 一、为什么研究 Yang Mun

Yang Mun 是一个 AI 生成的"东方老僧"角色 IP，由以色列创作者 Shalev Hani 制作。

**数据：**
- Instagram 粉丝：250 万+
- 总播放量：20.7 亿次
- 付费会员：2,300 人 x $50/月 = **月收入 115K 美元**
- 变现产品："30-Day Healing Journey" 疗愈课程

**他的视频极简到什么程度：**
- 每条视频只有 1-2 张 AI 生成的老僧图片
- 用 KlingAI 2.6 做缓慢推拉动画
- 沉稳旁白 + 环境音（风声、水声）
- 少量金色文字叠加
- 没有"故事"，只有"情绪"

**核心启示：内容质量 > 视觉复杂度。固定角色 IP + 极简美学 = 强记忆点。**

---

## 二、Yang Mun 的工具链

| 步骤 | 工具 | 用途 |
|------|------|------|
| 角色设计 | OpenArt | 生成固定老僧形象 |
| 图生视频 | KlingAI 2.6 | 缓慢推拉/平移动画 |
| 配音 | HeyGen AI | 沉稳旁白声 |
| 文字叠加 | 后期工具 | 金色 fade in/out 文字 |
| 音乐 | 环境音素材 | 风声、水声、自然音 |

---

## 三、我们的 Day4 vs Yang Mun 对比

| 维度 | 我们 Day4（v4-stock-musk） | Yang Mun |
|------|--------------------------|----------|
| 角色 | 马斯克照片 PiP，非固定 | 固定 AI 老僧，每条视频同一张脸 |
| 场景 | Pexels 真实素材（办公室、设计团队等） | 极简冥想背景（树林、寺庙） |
| 动态 | FFmpeg 拼接真实视频片段 | KlingAI 缓慢推拉 |
| 声音 | Edge TTS YunxiNeural，快节奏 | 沉稳旁白 + 环境音，慢节奏 |
| 文字 | ASS 字幕叠加 | 少量金色文字 |
| 美学 | 科技纪录片风格 | 东方禅意，暖色调，治愈感 |
| 内容 | 数据驱动（"8万→3千"） | 情绪驱动（鸡汤/哲理） |
| 节奏 | 3-5 秒换一个刺激 | 一个画面 8-15 秒 |

---

## 四、Yang Mun 的弱点（我们的超越机会）

1. **内容同质化严重**：全都是鸡汤，没有干货。看 10 条和看 1 条没区别。
2. **没有数据支撑**：纯情绪输出，缺乏可信度。
3. **无法建立专业权威**：老僧形象适合心灵疗愈，不适合科技/商业内容。
4. **变现在天花板**：疗愈赛道客单价有上限。

**我们的差异化武器：Yang Mun 的视觉美学 + 我们的数据内容深度。**

Yang Mun 做不出来的东西（"月成本 8 万降到 3 千"这种反差数字），正是我们的杀手锏。

---

## 五、打法变更清单

### 需要改变

| # | 维度 | 当前做法 | 改为 | 变更幅度 |
|---|------|---------|------|---------|
| 1 | 角色 | 每条视频换人物/无人物 | 固定一个 AI 角色 IP，每条视频重复使用 | 核心变更 |
| 2 | 场景 | 复杂环境（ThinkPad、IKEA 桌、咖啡渍） | 极简背景（纯色、几何、光效） | 大改 |
| 3 | 情感弧线 | 6 步情绪剧（震撼→紧张→反转...） | 单一情绪贯穿（宁静/坚定/温暖） | 大改 |
| 4 | Prompt 方法论 | v3.0 六层结构（摄影声明 → 不完美细节） | v4.0 角色锚定结构（固定角色 → 表情变化） | 核心变更 |
| 5 | 构图 | 多种角度 | 统一构图（正面/3/4 侧脸） | 中改 |
| 6 | 节奏 | 快节奏，3-5 秒换刺激 | 慢节奏，一个画面 8-15 秒 | 中改 |

### 不需要改变

| 维度 | 保持 | 原因 |
|------|------|------|
| Runway Gen-4 | 缓慢推拉/平移 | Yang Mun 也是慢动画 |
| 去AI化后期 4 步法 | 保留 | 固定角色更需要去 AI 感 |
| Negative prompt v3.0 | 保留 + 微调 | 基础有效 |
| Edge TTS | 保留但降语速 | 声音已验证 |
| 字幕/叠加 | 保留 | Yang Mun 也有文字叠加 |
| FFmpeg 管线 | 完全不变 | 工具链就绪 |
| 数据钩子内容 | 保留 | 差异化武器 |

---

## 六、Prompt 方法论：v3.0 → v4.0

### v3.0 结构（当前，纪录片风格）

```
[摄影声明], [主体+具体不完美+面部不对称], [环境+真实物件名], [光影+方向], [构图], vertical composition 9:16
```

设计目标：每张图追求真实感、不完美感。适合纪录片叙事。

### v4.0 结构（Yang Mun 式，角色锚定）

```
[角色锚定], [摄影声明], [表情/姿态], [极简背景], [光影+方向], vertical composition 9:16
```

设计目标：跨图片角色一致性。只有表情/背景变化，角色描述固定。

---

### 第 1 层：角色锚定（新增，权重最高，MUST）

每条 prompt 开头必须包含角色的固定描述，确保跨图片一致性。

**固定描述（每条 prompt 完全相同，一字不改）：**

```
a young Chinese woman in her late 20s, round face, short black bob haircut
with straight bangs just above eyebrows, wearing a simple cream-colored
linen shirt with a small collar
```

这和 Yang Mun 的做法完全一致：他每条视频的 monk 描述（orange robe, elderly, bald, serene）是固定不变的。Seedream 没有 "character lock" 功能，文字描述的一致性是唯一手段。

**角色设计（经验证确定）：**

| 属性 | 最终值 | 原因 |
|------|--------|------|
| 性别 | 女性 | 抖音/小红书女性受众更多，信任感更强 |
| 年龄 | 25-30 | 有阅历但不老，能讲科技也能讲人生 |
| 发型 | 黑色齐刘海短发（bob cut） | 辨识度高，Seedream 一致性好 |
| 穿搭 | 米白亚麻衫+小翻领 | 极简美学，和 Yang Mun 的橙色僧袍同理 |
| 面部特征 | 圆脸，无痣 | 痣不可控（左右脸随机），去掉 |

**重要教训：** Seedream 无法控制痣/雀斑等面部小细节的精确位置。v1 用 "beauty mark on left cheek" 太模糊；v2 精确到解剖学位置仍然左右脸随机。一致性只能靠发型和穿搭，不能靠面部小细节。

---

### 第 2 层：摄影声明（保留，调整风格）

从"纪录片真实感"转向"电影级肖像感"：

| 当前选项 | 处理 |
|---------|------|
| `shot on Canon 5D Mark IV 50mm f/1.4 Kodak Portra 400` | 保留 |
| `iPhone 15 Pro photo, slightly underexposed` | 删掉，太随意 |
| `35mm documentary film still, grainy` | 改为 `cinematic portrait, shallow depth of field, soft bokeh` |
| `shot on Sony A7III 85mm f/1.8` | 保留，适合肖像 |

**新增选项：**
- `medium format portrait, Hasselblad X2D, natural skin rendering` -- 高端肖像感
- `editorial portrait photography, soft window light, film color science` -- 编辑肖像
- `cinematic portrait, 85mm f/1.4, shallow depth of field, soft warm bokeh` -- 电影肖像

---

### 第 3 层：表情/姿态（取代原来的"具体不完美"）

v3.0 重点是不完美细节。v4.0 重点变成表情/姿态的微变化：

**表情词库（按情绪选一个）：**

| 情绪 | 表情描述 |
|------|---------|
| 坚定/激励 | `confident gaze, slight knowing smile, chin slightly raised` |
| 温暖/治愈 | `gentle smile, eyes soft, relaxed shoulders` |
| 沉思 | `looking slightly downward, thoughtful expression, hand near chin` |
| 震撼/数据 | `eyes wide with quiet amazement, lips slightly parted` |
| 对比/力量 | `strong direct eye contact, jaw set with determination` |
| 邀请/CTA | `warm smile, leaning slightly forward, open body language` |

---

### 第 4 层：极简背景（取代原来的"复杂真实环境"）

v3.0 追求环境细节（ThinkPad、IKEA 桌、咖啡渍）。v4.0 追求情绪氛围和空间感。

**背景选项（每次只选一个）：**

```
warm cream wall with a single soft window light casting long shadows
dark charcoal background with a warm amber accent light from the side
soft gradient from warm gold to deep burgundy, no objects
minimalist concrete wall, one warm-toned desk lamp creating a pool of light
out-of-focus bookshelf with warm-toned spines, shallow depth of field
```

**原则：背景只有颜色和光影，没有具体物件。**

---

### 第 5 层：光影 + 方向（保留）

基本不变，确保统一为暖色调：

```
warm directional light from upper left casting soft shadows
golden hour window light from the side with gentle falloff
warm amber backlight creating a soft rim light on hair and shoulders
```

---

### 第 6 层：Negative Prompt（保留 + 微调）

v3.0 的 negative prompt 基本保留，新增确保角色一致性的条目：

```
新增：
multiple people, group shot, changing face, different person,
inconsistent features, aged, child, cartoon character
```

---

### 完整示例（Day4 用 Yang Mun 风格重写）

**S01 Hook（震撼情绪）：**
```
a young Chinese woman in her late 20s, round face, short black bob haircut
with straight bangs just above eyebrows, wearing a simple cream-colored
linen shirt with a small collar, shot on Canon 5D Mark IV 85mm f/1.4 Kodak Portra 400,
eyes wide with quiet amazement lips slightly parted, dark charcoal background
with a warm amber accent light from the side, warm directional light from
upper left casting soft shadows on her face, visible film grain especially in
shadow areas, subject in lower two-thirds, vertical composition 9:16
```

**S03 反转（坚定情绪）：**
```
a young Chinese woman in her late 20s, round face, short black bob haircut
with straight bangs just above eyebrows, wearing a simple cream-colored
linen shirt with a small collar, shot on Canon 5D Mark IV 85mm f/1.4 Kodak Portra 400,
confident direct gaze slight knowing smile chin slightly raised, minimal
warm cream wall with a single soft window light, warm directional light
from the right creating gentle falloff into shadow, visible film grain
especially in shadow areas, subject in lower two-thirds, vertical composition 9:16
```

**S05 CTA（温暖邀请）：**
```
a young Chinese woman in her late 20s, round face, short black bob haircut
with straight bangs just above eyebrows, wearing a simple cream-colored
linen shirt with a small collar, shot on Canon 5D Mark IV 85mm f/1.4 Kodak Portra 400,
gentle warm smile eyes soft relaxed shoulders leaning slightly forward,
out-of-focus bookshelf with warm-toned spines shallow depth of field,
golden hour window light from the side with gentle falloff, visible film grain
especially in shadow areas, subject in lower two-thirds, vertical composition 9:16
```

---

## 七、执行优先级

| # | 步骤 | 工具 | 预计时间 | 产出 |
|---|------|------|---------|------|
| 1 | 设计角色锚定描述 | Seedream | 30 分钟 | 5-10 张测试图，验证跨图一致性 |
| 2 | 重写 Day4 Prompt 模板 | 手动 | 15 分钟 | v4.0 角色锚定版 Day4 配置 |
| 3 | 跑 Day4 Demo 对比 | Seedream + Runway + FFmpeg | 1 小时 | 同一脚本两种视觉风格的 A/B 视频 |
| 4 | 决定方向 | 人工判断 | - | 走 Yang Mun 路线 or 保持纪录片路线 |

---

## 八、风险和不确定性

1. **Seedream 角色一致性不确定**：Seedream 没有 "character lock" 功能，纯靠文字描述可能无法实现 Yang Mun（用 OpenArt）那种跨图一致性。需要先测试。
2. **中国受众对"固定角色"的反应不确定**：Yang Mun 面向欧美市场，中国抖音/小红书用户可能更偏好快节奏信息流。
3. **数据钩子 + 慢节奏可能冲突**："8万→3千"需要快节奏输出才能制造冲击力，Yang Mun 式慢节奏可能削弱数字冲击感。
4. **角色设计需要迭代**：当前建议的女性角色可能需要 2-3 轮测试才能找到辨识度和一致性的平衡点。

---

## 九、结论

Yang Mun 证明了一件事：**固定角色 IP + 极简美学 > 复杂视觉**。

我们的超越路线是：用 Yang Mun 的视觉框架（固定角色 + 慢动画 + 暖色调），装进我们的内容优势（数据反差 + 名人叙事 + 实操干货）。

如果 Seedream 的角色一致性测试通过，这是低成本高回报的方向切换：工具链不变，只变 Prompt 写法。
