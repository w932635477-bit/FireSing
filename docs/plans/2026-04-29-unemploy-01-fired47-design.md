# 失业系列第一条视频设计

> 设计日期：2026-04-29
> 状态：已批准
> 关联：video-production-spec.md v4.2、2026-04-28-medvi-unemployment-visual-design.md
> 目标：制作失业系列第一条完整视频

---

## 1. 基本信息

| 项目 | 值 |
|------|-----|
| video_id | `unemploy-01-fired47` |
| 标题 | 被裁第47天，我赚到第一个5000块 |
| 目标时长 | 75s（甜点区间 70-90s） |
| 最短 | 60s |
| 最长 | 120s |
| 工作流 | Medvi v2 Corecore 蒙太奇（无杨梦） |
| character_anchor | null |
| strategy | unemployment-corecore |
| 故事来源 | Spec §5.8 完整示例 |

---

## 2. 素材清单

### 2.1 UI 截图（Playwright HTML → PNG，6 张）

| ID | 模板 | 数据内容 | 出现段落 |
|----|------|---------|---------|
| SS01 | tpl-boss-search | 搜索"运营总监"，15 个结果，全部已读不回 | S01 前置高潮 |
| SS02 | tpl-dingtalk-leave | "您已被移出群聊" 灰色系统消息 | S02 设定 |
| SS03 | tpl-resume-stats | 投递 200 份，已读 180，回复 3，面试 0 | S03 崩塌 |
| SS04 | tpl-wechat-reject | HR 绿色气泡："年龄不太符合我们的要求" | S03 崩塌 |
| SS05 | tpl-wechat-positive | 老客户绿色气泡："我找的是你，不是你们公司" | S04 转念 |
| SS06 | tpl-douyin-comment | 评论："投了300份了" "第五个月了" 等 | S06 互动 |

### 2.2 氛围空镜（Seedream → Kling，3 张）

| ID | 场景 | 情绪 | 出现段落 | Prompt |
|----|------|------|---------|--------|
| AT01 | 凌晨台灯下的简历 | 代入/共鸣 | S02 | iPhone 15 snapshot, a desk lamp illuminating a printed resume on a wooden desk, 2am ambient warm light, coffee ring stain on paper, no people visible, no text visible, casual framing slightly off-center, untouched, vertical 9:16 |
| AT02 | 空荡办公区 | 共鸣/痛 | S03 | iPhone 15 snapshot, empty open-plan office at night, fluorescent ceiling lights casting harsh shadows on vacant desks, one desk still has a potted plant and a coffee mug, no people visible, no text, untouched, vertical 9:16 |
| AT03 | 暖光通讯录 | 希望/力量 | S04-S05 | iPhone 15 snapshot, warm ambient light from a phone screen illuminating a dark room, the screen shows a contacts list with many entries, cozy atmosphere, no people visible, no text readable, casual framing, untouched, vertical 9:16 |

---

## 3. 段落脚本

### S01 前置高潮 (0-4s)

```
被裁第47天，我赚到了第一个5000块。
不是靠投简历。是靠翻通讯录。
```
- emotion_arc: 好奇
- subtitle_text: "被裁47天 赚了5000"
- 素材：SS01 Boss 搜索快切 × 多张（极快 0.5s/张）

### S02 设定 (4-16s)

```
38岁，外企15年。
一通电话，全没了。
HR说"公司战略调整"，翻译过来就是——你太贵了。
```
- emotion_arc: 代入
- subtitle_text: "38岁 外企15年 一通电话全没了"
- 素材：SS02 钉钉退群 + AT01 台灯简历（中速 2-3s）

### S03 崩塌 (16-40s)

```
第一个星期，投了40份简历。回复0。
第二个星期，降薪30%。回复0。
第三个星期，连降薪都不敢写了。
房贷每月1万2，孩子幼儿园5000，我妈的降压药不能停。
那段时间每天最怕的就是早上醒来——因为醒来就要面对一天。
```
- emotion_arc: 共鸣
- subtitle_text: "40份简历 0回复"
- 素材：SS03 简历数据 + SS04 HR拒绝 + AT02 空办公区
- 节奏：呼吸式 3s → 1s → 0.5s×3-5 → 2s → 1s → 0.5s×3

### S04 转念 (40-55s)

```
有天老客户打电话问我那个项目怎么跟进。
我说我已经不在了。
他说了一句话："我找的是你，不是你们公司。"
那天晚上我翻了翻通讯录，200个客户关系。
原来这些东西，一直都在。只是以前绑在公司身上。
```
- emotion_arc: 希望
- subtitle_text: "我找的是你 不是你们公司"
- 素材：AT03 暖光通讯录 → SS05 微信正面消息（放慢 3-4s）

### S05 收尾 (55-70s)

```
你身上有多少值钱的东西，你自己都没看到？
你的经验，你的人脉，你的行业嗅觉——
这些不会因为一通电话就消失。
```
- emotion_arc: 力量
- subtitle_text: "你身上的东西比你以为的多"
- 素材：AT03 暖光通讯录（延续，最慢 4-6s）

### S06 互动闭环 (70-75s)

```
你投了多少份简历了？评论区说说。
```
- emotion_arc: 参与
- subtitle_text: "你投了多少份了？"
- 素材：SS06 评论区截图（收尾 2s）

---

## 4. 节奏表（按 Spec §9.4.1）

| 段落 | 节奏模式 | 时间值 | 画面处理 |
|------|---------|--------|---------|
| S01 | 极快闪切 | 0.5s/张 × 6-10 | 截图原始，无后处理 |
| S02 | 中速 | 2-3s/张 | 空镜(后处理) + 截图(原始) |
| S03 | 呼吸式 | 3s→1s→0.5s×3-5→2s→1s→0.5s×3 | 快切截图，慢段空镜 |
| S04 | 放慢 | 3-4s/张 | 暖色空镜先出，截图最后 |
| S05 | 最慢 | 4-6s/张 | 空镜(后处理) |
| S06 | 收尾 | 2s | 截图(原始) |

---

## 5. 制作流程

```
Stage 0:   创建 6 个 Playwright HTML 模板（docs/content/templates/）
Stage 0.5: Playwright 渲染 6 张 UI 截图（PNG 1080×1920）
Stage 1:   编写完整 config JSON（unemploy-01-fired47.json）
Stage 1.5: 文案评估（独立 agent 盲评，≥90 分）
Stage 2:   Seedream 生成 3 张空镜（seedream-batch.py 或 seedream-story-images.py）
Stage 3:   Kling 将 3 张空镜转视频（kling-gen-batch.py）
Stage 4:   Gemini TTS Aoede 配音（gemini-tts-batch.py）
Stage 5:   剪映混剪（按节奏表 + 安全区 + 白字硬切）
```

---

## 6. 设计决定记录

| 决定 | 理由 | 日期 |
|------|------|------|
| 用 Spec §5.8 示例故事 | 已验证的完整脚本，直接可用 | 2026-04-29 |
| 6 张 Playwright 截图全部创建 | 一次建完模板库，后续视频复用 | 2026-04-29 |
| 3 张空镜精简方案 | 降低成本，空镜是情绪锚点不是主角 | 2026-04-29 |
| AT03 跨 S04+S05 复用 | 减少素材量，暖光通讯录贯穿希望→力量 | 2026-04-29 |
| 不使用杨梦角色 | 失业系列 Corecore 蒙太奇不需要固定角色 | 2026-04-29 |
