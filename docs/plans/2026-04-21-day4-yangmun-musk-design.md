# Day4 Yang Mun + Musk 交替方案设计

> 日期: 2026-04-21
> 状态: APPROVED
> 视频ID: day4-yangmun
> 配置文件: docs/content/config/day4-yangmun.json

## 问题

Day4 使用 Yang Mun 式角色 IP（AI 生成女性人脸）配商业数据文案（"8万→3千"）。
核心矛盾：人脸表达的是情感，商业数据是理性内容，两者不在同一个频道。Yang Mun 的鸡汤内容和人脸天然匹配，但商业数据和人脸之间有隔阂。

## 解决方案：马斯克 + 女性角色交替

文案大量使用"马斯克说"驱动（名人说 + 观点 + 共鸣方法论），用真实的马斯克照片生成视频承担权威层，AI 女性角色承担共情层，两者交替出现。

### 核心逻辑

- 马斯克画面 = 权威层（他说的话、他定的规矩，观众信）
- 女性角色画面 = 共情层（她的表情让观众"感受到"这些话的分量）
- 交替出现，各司其职

### 为什么不用单一画面方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| 纯人脸（原方案） | 情绪冲击强 | 数据和人脸有隔阂 |
| 上下分屏 | 信息情绪分离 | 人脸被压缩到 40%，失去对视感 |
| 人物融入场景 | 成本不变 | 商业信息隐性，不够直接 |
| **马斯克+女性交替** | **权威+共情双叠加** | 多 3 轮 Runway |

## 画面分配

### S01-S03：马斯克开场 + 女性收尾

每段前 2-3 秒显示马斯克（建立权威），后 3-6 秒切换到女性角色（情绪落地）。

| 段 | 配音内容 | 先显示 | 后显示 | 马斯克图片 |
|---|---|---|---|---|
| S01 | "我不需要10个人，我需要1个对的人" | 马斯克（权威） | 女性 shocked | ooGMAyk...webp (2160x2346) |
| S02 | "铁律一，速度就是一切。8万→3千" | 马斯克（讲话） | 女性 determined | o0gAhD3...(1).webp (736x1104) |
| S03 | "铁律二，贵不是问题慢才是。1人=10人" | 马斯克（自信） | 女性 power | a85f12cc...jpeg (751x750) |

### S04-S05：纯女性角色

后两段是反思和号召，需要纯共情，不需要权威。

| 段 | 配音内容 | 画面 |
|---|---|---|
| S04 | "这不是未来，这是现在正在发生的事" | 女性 contemplative（纯人脸） |
| S05 | "改变不需要勇气，只需要一个开始" | 女性 warm（纯人脸） |

## 剪辑节奏

### 过渡方式

马斯克到女性之间用 0.5s 硬切（不是交叉淡入）。硬切有冲击力，交叉淡入会软化权威→共情的转换。

### 示例时间线（S01，配音约 5-6 秒）

```
[0-3s] 马斯克正面照，缓慢推进
       配音: "我不需要十个人"
       字幕: "我不需要10个人"

[3-6s] 女性震惊表情，光影微动
       配音: "我需要一个对的人。AI替代十人设计团队。"
       字幕: "我需要1个对的人"
```

## 角色身份

女性角色是**讲述者**（不是亲历者），表情镜像观众听到数据后的情绪反应。
- "8万→3千" → 观众会震惊 → 她脸上是震惊
- 这是一种共情锚定

## 素材清单

### 马斯克图片（已确认）

| 用途 | 文件 | 分辨率 | 位置 |
|------|------|--------|------|
| S01 权威 | ooGMAyk...webp | 2160x2346 | docs/content/assets/references/musk/ |
| S02 讲话 | o0gAhD3...(1).webp | 736x1104 | docs/content/assets/references/musk/ |
| S03 自信 | a85f12cc...jpeg | 751x750 | docs/content/assets/references/musk/ |

### 女性角色图片（已生成）

| 用途 | 文件 | 位置 |
|------|------|------|
| S01 shock | S01-shock.png | docs/content/assets/references/ |
| S02 determined | S02-determined.png | docs/content/assets/references/ |
| S03 power | S03-power.png | docs/content/assets/references/ |
| S04 contemplative | S04-contemplative.png | docs/content/assets/references/ |
| S05 warm | S05-warm.png | docs/content/assets/references/ |

## 生产管线

```
Stage 1: 马斯克图片裁剪（3 张裁为 9:16 竖版）
Stage 2: Runway 生成 3 段马斯克视频（720x1280, 5s each）
Stage 3: Runway 生成 5 段女性视频（720x1280, 5s each）[复用已有图片]
Stage 4: Edge TTS 配音（zh-CN-YunxiNeural, 7 段）
Stage 5: FFmpeg 拼接（马斯克+女性交替，硬切过渡）
Stage 6: 剪映后期（字幕、去AI滤镜、AI标签水印）
Stage 7: 最终审核
```

### 成本

- 比原计划多 3 轮 Runway（马斯克视频）
- 不需要额外 Seedream（马斯克用真实照片）
- 女性角色图片不需要重新生成（保持纯色背景）

## 配音配置

保持 day4-yangmun.json 中的现有配置：
- 引擎: Edge TTS
- 声音: zh-CN-YunxiNeural
- 语速: -10%
- 风格: 沉稳男声，Yang Mun 式节奏，关键数字加重语气
