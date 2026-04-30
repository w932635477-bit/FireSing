# 批量制作4条视频 — 2026-04-30

> 2条 Medvi 失业名人堂 + 2条 Sings 城市吵架段位表
> 全流程今天完成，明天出差

## 内容矩阵

| # | 工作流 | video_id | 标题方向 | 平台 | 目标时长 |
|---|--------|----------|----------|------|----------|
| 1 | Medvi | unemploy-celebrity-02 | 俞敏洪：6万裁员到百亿东方甄选 | 抖音 | ≤180s |
| 2 | Medvi | unemploy-celebrity-03 | 马云：被KFC拒到阿里万亿 | 抖音 | ≤180s |
| 3 | Sings | sings-qingdao-argue | 青岛吵架段位表（好汉歌风） | 小红书 | 30-45s |
| 4 | Sings | sings-shenyang-argue | 沈阳吵架段位表（好汉歌风） | 小红书 | 30-45s |

## 核心原则

**评论区炸了，流量就来了**
- Medvi：名人真实失败 + AI失业 = 两派对立
- Sings：城市段位表 = 本地人觉得对 + 外地人觉得好笑

## Medvi 脚本结构

沿用 unemploy-celebrity-01 倒叙炸弹结构，6段：

| 段 | 类型 | 时长 | 内容 |
|----|------|------|------|
| S01 | 倒叙炸弹 hook | 10-15s | 巅峰成就 → 反转"但在X岁..." |
| S02 | 至暗时刻 | 20-30s | 具体失败细节（数字+画面感） |
| S03 | 转折 | 15-20s | 最低谷的关键决定 |
| S04 | 逆袭 | 15-20s | 从0到1关键数字 |
| S05 | AI映射 | 15-20s | 9200万岗位 + 两派观点 |
| S06 | CTA | 5-10s | 开放式站队问题 |

### 俞敏洪 #02

- Hook：新东方市值蒸发2000亿，裁员6万人——他60岁从0开始直播
- 至暗：双减政策，教学点全关，桌椅捐乡村小学
- 转折：董宇辉爆火，东方甄选从亏损到百亿
- AI映射：行业一夜被政策摧毁 = 岗位一夜被AI替代

### 马云 #03

- Hook：阿里万亿——但被KFC拒绝，24人唯一落选
- 至暗：高考3次，月薪89块英语老师，被说是骗子
- 转折：湖畔花园18人创业，孙正义6分钟投2000万
- AI映射：他说"AI不是威胁" vs "他说这话因为他不用打工"

### 视觉

- Corecore 蒙太奇，atmosphere_shots 空镜
- 无杨梦角色，character_anchor=null
- Charon 男声旁白（覆盖 Aoede 女声规则）
- Prompt: iPhone snapshot 风格

## Sings 脚本结构

沿用上海吵架段位表 argue_duet 格式，歌曲换好汉歌风。

### 好汉歌风特点

- Suno tags: `Duet (Alternating). Male lead sings in bold, powerful folk style like 好汉歌. Female lead counters with playful, sharp comebacks. Strong rhythmic drive, Chinese folk pop fusion, marching beat, 100-120 bpm`
- 男声豪迈（刘欢式），女声利落反击
- 比上海吵架更有气势

### 青岛 sings-qingdao-argue

10级段位表：哈啤酒不算→你瞅啥→海鲜市场砍价→蛤蜊不新鲜→栈桥抢位→青岛是东北的？→青岛话骂人→袋装啤酒踩到→青岛大虾38一只→青岛不如大连？

### 沈阳 sings-shenyang-argue

10级段位表：你瞅啥/瞅你咋地→别整那没用的→烧烤摊抢串→你说东北冷？→洗浴中心抢搓澡→东北菜太咸→沈阳不是省会？→东北人都是社会人→东北没文化？→沈阳不如大连/哈尔滨？

### 争议引爆

- 共通："你说X不如大连？"——大连是假想敌
- 本地人觉得对 + 外地人觉得好笑 = 评论吵起来

## 制作流程

```
Phase 1: 并行写4条脚本
Phase 2: 并行盲评（≥90分通过）
Phase 3: 并行素材生成
  Medvi: Seedream空镜 + Kling视频 + Gemini TTS
  Sings: Suno好汉歌 + Seedream参考图 + Kling视频
Phase 4: FFmpeg拼接 + 上传文案
```

## 红线

- 不提 AI Agent / 代运营 / 智能体
- 不引导私信/领取/关注
- CTA 永远是开放式站队问题
- 绝不说"名人能行你也能"

## 质量门控

- Medvi 盲评：叙事力(25) + 情绪共振(25) + 争议设计(20) + AI关联(15) + 文案质量(15)，≥90通过
- Sings 盲评：歌词韵律(25) + 争议引爆(25) + 城市特色(20) + 对唱互动(15) + 段位递进(15)，≥90通过
