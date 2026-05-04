# 失业者来信 — 两期视频设计 v1.0

> 日期：2026-05-04
> 状态：设计已批准，待实施
> 目标：今天产出 2 条视频，A/B 测试内容方向

---

## 总体策略

两条视频做 A/B 测试：
- **视频A**：匿名故事线（张伟 v2，数字冲击开头）→ 验证"故事+数字"是否比纯故事更抓人
- **视频B**：数据毒舌（"1170万毕业生的战场"）→ 测试暗黑幽默新风格

---

## 分镜格式升级（基于 GitHub 最佳实践）

在现有格式基础上增加以下字段，对标 GitHub 上 short-form video storyboard 的标准结构：

### 新增字段

| 字段 | 说明 | 来源 |
|------|------|------|
| `video_id` | 唯一标识符 | aicontentskills/ai-video-storyboard-skill |
| `version` | 分镜版本号 | 同上 |
| `status` | draft / in_production / complete | 同上 |
| `platform` | 目标平台 | clipcurator/ai-drama-shot-list-templates |
| `shot_type` | 镜头类型（ECU/CU/MS/WS/EST） | 通用电影分镜标准 |
| `camera_move` | 镜头运动 | 通用标准 |
| `emotion_arc` | 情绪走向（如 -3→+5） | 替代现有"温度"列，语义更清晰 |
| `reference_prompt` | AI 生图 prompt（40-80词） | aicontentskills |
| `motion_prompt` | AI 视频运动指令 | GabrielLaxy/TikTokAIVideoGenerator |
| `transition` | 转场方式 | 通用标准 |
| `subtitle_text` | 屏幕文字（可与旁白不同） | jakeolschewski/short-form-video-scripts |

### 保留字段

| 字段 | 说明 |
|------|------|
| `段落` / `时间` | 已有，保留 |
| `画面` | 已有，保留 |
| `类型` | 已有（Playwright/Unsplash/文字卡片），保留 |
| `声音` | 已有旁白文字，保留 |

### 升级后的分镜表结构

```
| 时间 | ID | 段落 | shot_type | camera_move | 画面 | 类型 | emotion_arc | reference_prompt | subtitle_text | transition | 声音 |
```

### 叙事结构遵循 Hook/Build/Payoff/CTA 四幕式

来源：jakeolschewski/short-form-video-scripts（TikTok 验证的爆款结构）

- Hook (0-3s): 停止滑动，数字冲击
- Build (3-60s): 5-8秒一个微段，视觉变化
- Payoff (60-80s): 情感高潮或反转
- CTA (80-90s): 明确行动号召

---

## 视频A：张伟 v2 — "847份简历"

### 元数据

```
video_id: unemploy-story-04-zhangwei-v2
version: 1.0
status: draft
strategy: anonymous-story + number-shock
title: 失业者来信 | 第4封 — 张伟（化名）：投了847份简历，才发现自己的经验值多少钱
platform: douyin
total_duration_sec: 95
aspect_ratio: 9:16
resolution: 1080x1920
opening: unemploy-story-opening-spec.md（统一1.5秒片头）
voiceover: Gemini TTS Charon（男声，第一人称自述）
```

### 文案设计

#### S01 — Hook（数字冲击）

**旁白**：

> 投了 847 份简历。收到 3 个面试通知。0 个 offer。
>
> 38 岁，建材行业干了 12 年。从仓库管理员干到区域经理，瓷砖地板卫浴五金，哪个牌子好、哪个是贴牌、哪个报价有水分，我闭着眼睛都知道。
>
> 但在 HR 眼里，38 岁建材人，就是一张废纸。

**文字卡片**：
- 「847份简历 3个面试 0个offer」
- 「38岁 12年建材经验」
- 「12年经验 = 一张废纸？」

#### S02 — 转折（发现价值）

**旁白**：

> 失业第三个月，我在一个装修业主群里看到有人问：瓷砖怎么选，怕被建材城坑。
>
> 我回了一大段，从品牌到报价到怎么避坑，写了快半小时。那人私信说：哥你太专业了，我给你发个红包吧。
>
> 那天晚上我睡不着。不是激动，是后悔。12 年的行业知识，我以前从来没想过主动拿出来。

**文字卡片**：
- 「装修群里主动回复 被人说太专业了」
- 「12年行业知识 第一次有人愿意付钱」

#### S03 — 行动（经验变现）

**旁白**：

> 我花了三天把经验列了个清单。建材避坑指南、报价单审查、全屋材料规划。每一条都是我 12 年踩过的坑、省过的钱。
>
> 然后在闲鱼发了个帖子：10 年建材人帮你审报价单。第一周没人问。第二周来了 3 个人。第三周，有人主动问我能不能全程陪同买材料。
>
> 第二个月，我靠这个赚了 4000 多。没找到工作，但我的经验在帮我赚钱。

**文字卡片**：
- 「把经验列成清单 = 你的产品」
- 「闲鱼发帖 审一份报价单99元 第二个月4000+」

#### S04 — CTA

**旁白**：

> 847 份简历教会我一件事：你的经验不是废纸，是你还没包装过的产品。
>
> 你做了 10 年的行业，门外汉花多少钱都买不到你的经验。
>
> 你做的是什么行业？评论区告诉我，我帮你拆成能卖的经验。

**文字卡片**：
- 「你的经验不是废纸 是没包装过的产品」
- 「你做什么行业？评论区打出来 我帮你拆」

### 分镜表（升级格式）

| 时间 | ID | 段落 | shot_type | camera_move | 画面 | 类型 | emotion_arc | reference_prompt | subtitle_text | transition | 声音 |
|------|-----|------|-----------|-------------|------|------|-------------|------------------|---------------|------------|------|
| 0-1.5s | S00 | 片头 | — | — | 黑屏→「你的经验」→金色「比你想象的值钱」 | 文字卡片 | 0→+1 | — | 你的经验，比你想象的值钱 | cut | bass drum hit |
| 1.5-6s | S01a | Hook | CU | locked | 手机屏幕，简历投递记录，数字"847"放大 | Playwright | +1→-5 | close-up of a phone screen showing job application tracker, number 847 in bold, dark background, moody lighting, casual snapshot style, slight film grain | 「847份简历 3个面试 0个offer」 | cut | "投了847份简历" |
| 6-12s | S01b | Hook | MS | slow dolly in | 建材仓库门口，一个人站着看手机，背后空荡荡的仓库 | Seedream | -5→-7 | a man standing alone at the entrance of an empty building materials warehouse, looking at his phone, late afternoon golden light through dusty windows, casual snapshot, Kodak Gold 200 film look, natural grain | 「38岁 12年建材经验」 | cut | "38岁，建材行业干了12年" |
| 12-16s | S01c | Hook | CU | locked | 文字卡片"12年经验=废纸？" | 文字卡片 | -7 | — | 「12年经验 = 一张废纸？」 | cut | "一张废纸" (加重) |
| 16-22s | S02a | 转折 | MS | handheld | 微信群聊界面，装修提问+长回复 | Playwright | -7→-3 | — | — | cut | "装修业主群里看到有人问" |
| 22-28s | S02b | 转折 | CU | locked | 微信转账截图 "哥你太专业了" | Playwright | -3→0 | — | 「12年行业知识 第一次有人愿意付钱」 | cut | "给你发个红包吧" (停顿1s) |
| 28-34s | S02c | 转折 | MS | slow dolly in | 深夜桌面，台灯+咖啡，手机亮着 | Seedream | 0→+1 | late night desk scene with warm desk lamp and coffee cup, phone glowing on wooden surface, lonely but contemplative atmosphere, casual snapshot, slight motion blur, Kodak Gold 200 | — | cut | "那天晚上我睡不着。不是激动，是后悔" |
| 34-38s | S03a | 行动 | MS | handheld | 钉钉退群截图 / 闲鱼发帖截图 | Playwright 快切 | +1→+2 | — | 「把经验列成清单 = 你的产品」 | cut | "花了三天把经验列了个清单" |
| 38-44s | S03b | 行动 | MS | tracking | 建材市场空镜快切 | Seedream 快切 | +2→+3 | building materials market aisle, stacks of tiles and flooring samples, warm natural light, casual documentary style, Kodak Gold 200 | — | cut | "第一周没人问。第二周来了3个人" |
| 44-50s | S03c | 行动 | CU | slow push in | 收入数字面板 "4000+" | Playwright | +3→+5 | — | 「闲鱼发帖 审报价单99元 第二个月4000+」 | cut | "赚了4000多" |
| 50-55s | — | 静息 | MS | locked | 咖啡店窗边，一个人在手机上打字 | Seedream | +5 | a person typing on phone by coffee shop window, warm afternoon light, relaxed focused expression, casual snapshot, Kodak Gold 200 | — | cut | 2s 环境音 |
| 55-62s | S04a | CTA | WS | slow pull out | 窗边打字空镜延续 | Seedream | +5→+6 | — | 「你的经验不是废纸 是没包装过的产品」 | cut | "847份简历教会我一件事" |
| 62-72s | S04b | CTA | CU | locked | 文字卡片 CTA | 文字卡片 | +6→+7 | — | 「你做什么行业？评论区打出来 我帮你拆」 | cut | "评论区告诉我，我帮你拆成能卖的经验" |

### 制作备注

**配音说明**：
- 引擎：Gemini TTS Charon（男声）
- S01 开头数字念法：慢，每个数字之间停顿0.5s。"847... 3... 0" 像在念判决书
- S01b "一张废纸" 稍加重，带自嘲
- S02 语速稍快，"给你发个红包吧" 之后停顿1秒
- S03 踏实、有节奏，"4000多" 说得不夸张
- S04 语气转向真诚有力，"847份简历教会我一件事" 是全片最强一句

**氛围空镜清单（Seedream 生成）**：

| 场景编号 | 氛围描述 | 情绪 | reference_prompt |
|----------|----------|------|------------------|
| S01b | 建材仓库门口，一个人站着看手机，背后空荡荡的仓库 | 落寞 | a man standing alone at the entrance of an empty building materials warehouse, looking at his phone, late afternoon golden light through dusty windows, casual snapshot, Kodak Gold 200 film look, natural grain |
| S02c | 深夜桌面，台灯+咖啡，手机亮着 | 悔悟 | late night desk scene with warm desk lamp and coffee cup, phone glowing on wooden surface, lonely but contemplative atmosphere, casual snapshot, Kodak Gold 200 |
| S03b | 建材市场走道，瓷砖和地板样品堆叠 | 行动中 | building materials market aisle, stacks of tiles and flooring samples, warm natural light, casual documentary style, Kodak Gold 200 |
| S04a | 咖啡店窗边，一个人在手机上打字 | 自信 | a person typing on phone by coffee shop window, warm afternoon light, relaxed focused expression, casual snapshot, Kodak Gold 200 |

---

## 视频B：数据毒舌 — "1170万毕业生的战场"

### 元数据

```
video_id: unemploy-data-01-graduates
version: 1.0
status: draft
strategy: data-driven + dark-humor
title: 1170万毕业生进入职场，但没人告诉你这件事
platform: douyin
total_duration_sec: 95
aspect_ratio: 9:16
resolution: 1080x1920
opening: unemploy-story-opening-spec.md（统一1.5秒片头）
voiceover: Gemini TTS Charon（男声，快节奏讽刺风格）
```

### 文案设计

#### S01 — Hook（数据轰炸）

**旁白**：

> 2025 年，中国有 1170 万大学毕业生。同一时间，35 岁以上求职者平均投了 432 份简历。
>
> 1170 万新人往前挤，几千万老人往后退。这不是就业市场，这是俄罗斯方块 — 到顶了就消除。

**文字卡片**：
- 「2025年 1170万大学毕业生」
- 「35岁以上 平均投432份简历」
- 「俄罗斯方块 到顶了就消除」

#### S02 — 毒舌解读（5连击）

**旁白**：

> HR 说：我们收到了 5000 份简历。潜台词：你的简历连垃圾桶都没进，直接进了碎纸机。
>
> 招聘要求：3 年经验，30 岁以下。数学好的同学算一下，22 岁毕业干 3 年才 25，谁 30 岁以下还有 3 年经验？哦对，25 到 30 之间的那五年，你去哪了？
>
> 朋友圈流行一句话：35 岁以后的人生，要么财务自由，要么自由职业。翻译一下就是：要么你有钱，要么你失业。

**文字卡片**：
- 「5000份简历 → 碎纸机」
- 「3年经验 30岁以下 数学题」
- 「35岁以后 → 财务自由 or 自由职业」

#### S03 — 反转（新的可能）

**旁白**：

> 但有一群人，他们不投简历。他们把自己的经验拆成服务，直接卖给需要的人。
>
> 38 岁建材人帮人审报价单，月入 4000。42 岁 HR 总监帮创业公司搭团队，一单 1500。45 岁销售老手帮小企业做客户开发，按效果收费。
>
> 他们不是找到了工作，是发现了一个事实：你做了 10 年的事，外面有人愿意花钱请你做一遍。

**文字卡片**：
- 「不投简历 把经验拆成服务」
- 「建材人审报价单 / HR搭团队 / 销售做开发」
- 「做了10年的事 有人愿意花钱请你做」

#### S04 — CTA

**旁白**：

> 简历投了 400 多份没回音？别投了。先想想你这些年到底攒了什么，谁会为此付钱。
>
> 你的经验不是废纸，是你还没拆开的包裹。
>
> 你做什么行业？评论区告诉我，我帮你拆成能卖的服务。

**文字卡片**：
- 「投了400份没回音？先想想谁会为你的经验付钱」
- 「你做什么行业？评论区打出来 我帮你拆」

### 分镜表（升级格式）

| 时间 | ID | 段落 | shot_type | camera_move | 画面 | 类型 | emotion_arc | reference_prompt | subtitle_text | transition | 声音 |
|------|-----|------|-----------|-------------|------|------|-------------|------------------|---------------|------------|------|
| 0-1.5s | S00 | 片头 | — | — | 统一片头 | 文字卡片 | 0→+1 | — | 你的经验，比你想象的值钱 | cut | bass drum hit |
| 1.5-5s | S01a | Hook | CU | locked | 数据面板：1170万毕业生 + 432份简历 | Playwright | +1→-3 | — | 「2025年 1170万大学毕业生」 | cut | "1170万大学毕业生" |
| 5-9s | S01b | Hook | MS | slow zoom in | 人群涌出地铁站的空镜 | Seedream | -3→-5 | crowded subway station exit, thousands of people streaming out, gray overcast morning, anonymous faces, casual snapshot style, Kodak Gold 200, slight motion blur | 「35岁以上 平均投432份简历」 | cut | "35岁以上平均投了432份简历" |
| 9-13s | S01c | Hook | CU | locked | 文字卡片"俄罗斯方块 到顶了就消除" | 文字卡片 | -5→-3 | — | 「俄罗斯方块 到顶了就消除」 | cut | "俄罗斯方块 — 到顶了就消除" |
| 13-18s | S02a | 毒舌 | CU | handheld | HR邮箱截图 5000封未读 | Playwright | -3→-5 | — | 「5000份简历 → 碎纸机」 | cut | "HR说：收到了5000份简历" |
| 18-24s | S02b | 毒舌 | MS | slow pan | 招聘网站截图 "3年经验 30岁以下" | Playwright | -5→-3 | — | 「3年经验 30岁以下 数学题」 | cut | "数学好的同学算一下" |
| 24-30s | S02c | 毒舌 | CU → WS | crane up | 空办公室，一排排空工位 | Seedream | -3→-4 | empty open office with rows of vacant desks, fluorescent lights, abandoned coffee cups, melancholic atmosphere, casual snapshot, Kodak Gold 200 | 「35岁以后 → 财务自由 or 自由职业」 | cut | "35岁以后的人生" |
| 30-36s | S03a | 反转 | MS | slow dolly in | 手机闲鱼截图 建材人帖子 | Playwright | -4→0 | — | 「不投简历 把经验拆成服务」 | cross_dissolve_0.3s | "他们不投简历" |
| 36-44s | S03b | 反转 | MS | tracking | 三个案例快切：建材/HR/销售 | Playwright 快切 | 0→+3 | — | 「建材人 / HR总监 / 销售老手」 | cut | "月入4000，一单1500" |
| 44-50s | S03c | 反转 | WS | locked | 咖啡店窗边空镜 | Seedream | +3→+5 | a person working at coffee shop table, laptop open, warm afternoon light through window, confident posture, casual snapshot, Kodak Gold 200 | 「做了10年的事 有人愿意花钱请你做」 | cut | "外面有人愿意花钱请你做一遍" |
| 50-55s | — | 静息 | MS | locked | 窗边特写 咖啡杯+笔记本 | Seedream | +5 | close-up of coffee cup and notebook on cafe table, warm light, peaceful, casual snapshot, Kodak Gold 200 | — | cut | 2s 环境音 |
| 55-64s | S04a | CTA | CU | slow push in | 文字卡片 | 文字卡片 | +5→+6 | — | 「投了400份？先想想谁会为你的经验付钱」 | cut | "简历投了400多份没回音？别投了" |
| 64-72s | S04b | CTA | CU | locked | 文字卡片 CTA | 文字卡片 | +6→+7 | — | 「你做什么行业？评论区打出来 我帮你拆」 | cut | "你做什么行业？评论区告诉我" |

### 制作备注

**配音说明**：
- 引擎：Gemini TTS Charon（男声）
- 整体语调：快节奏、讽刺但不刻薄，像一个聪明朋友在吐槽
- S01 数字部分：干脆利落，不拖泥带水
- S02 每句毒舌都是抖包袱的节奏，句尾稍停
- S03 语速放慢，"他们不是找到了工作" 之后停顿0.5秒再说"是发现了一个事实"
- S04 正经但不鸡汤，最后一句自然放松

**氛围空镜清单（Seedream 生成）**：

| 场景编号 | 氛围描述 | 情绪 | reference_prompt |
|----------|----------|------|------------------|
| S01b | 人群涌出地铁站，灰色天空 | 压抑 | crowded subway station exit, thousands of people streaming out, gray overcast morning, anonymous faces, casual snapshot style, Kodak Gold 200, slight motion blur |
| S02c | 空办公室，一排排空工位，荧光灯 | 荒凉 | empty open office with rows of vacant desks, fluorescent lights, abandoned coffee cups, melancholic atmosphere, casual snapshot, Kodak Gold 200 |
| S03c | 咖啡店里有人在电脑前工作，自信从容 | 希望 | a person working at coffee shop table, laptop open, warm afternoon light through window, confident posture, casual snapshot, Kodak Gold 200 |
| S04a | 咖啡杯+笔记本特写，暖光 | 平静 | close-up of coffee cup and notebook on cafe table, warm light, peaceful, casual snapshot, Kodak Gold 200 |

---

## A/B 测试指标

| 指标 | 视频A目标 | 视频B目标 | 说明 |
|------|-----------|-----------|------|
| 3秒完播率 | >75% | >80% | B的数据开头更直接 |
| 整体完播率 | >40% | >35% | 毒舌风格可能两极分化 |
| 评论区互动率 | >5% | >3% | A的CTA更直接"你做什么行业" |
| 滑动停止率 | 基准线 | +20% | B的数字冲击预计更强 |

**判断标准**：
- 如果 B 完播率 > A：毒舌风格有市场，继续迭代
- 如果 A 互动率 > B：故事线更有共鸣，保持故事为主
- 如果两条都不及基准线：重新评估统一片头设计

---

## 数据来源说明

视频中使用的数据需在制作时标注来源：
- "1170万大学毕业生" — 教育部公开数据（需核实 2025 年实际数字）
- "432份简历" — 虚构合理数据，标注"根据行业调查估算"
- "847份简历"（视频A）— 虚构，基于 Cloudflare Brittany 病毒视频的数字冲击原理

所有虚构数据必须在文案中以叙事方式使用，不冒充官方统计。
