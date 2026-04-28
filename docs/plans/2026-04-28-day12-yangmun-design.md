# Day12 马斯克：被自己公司赶出门 — 设计文档

**Date:** 2026-04-28
**Status:** design_approved
**Workflow:** Medvi v2
**Eval Score:** 90/100

---

## 1. 定位

马斯克被PayPal开除的真实故事，映射2026年AI替代+80后裁员双重焦虑。目标观众：80后职场人，刚被裁或在裁员边缘。

## 2. 情绪弧线

```
shock → tension → reversal → warm(留白)
```

## 3. 脚本 (v3 细化版, 90分)

### S01 Hook (12s, shock)

**配音:**
> 马斯克说过："我每天醒来都觉得今天可能破产。"
> 但2000年，他连醒来的机会都没有。在飞机上度蜜月，落地打开手机——自己已经不是CEO了。他创办的公司，趁他不在，把他踢了出去。

**pause_markers:**
```
马斯克说过<#0.2#>"我每天醒来都觉得今天可能破产。"<#0.8#>但2000年<#0.3#>他连醒来的机会都没有。<#0.5#>在飞机上度蜜月<#0.2#>落地打开手机<#0.8#>自己已经不是CEO了。<#0.5#>他创办的公司<#0.2#>趁他不在<#0.3#>把他踢了出去。
```

**subtitle_text:** "趁他不在 把他踢了出去"
**yangmun_clip_hint:** day5-yangmun/S01-shock.mp4
**名人原话:** "I wake up every morning thinking this could be the day we go bankrupt." (60 Minutes)
**故事图 S01-01:** 飞机蜜月落地被开除
- reference_prompt: `shot on Canon 5D Mark IV 35mm f/2.0 Kodak Portra 400, interior of a commercial airplane cabin window seat, a phone screen glowing with a notification visible but unreadable, uneaten airplane meal on the tray table, warm golden sunset light through the oval window casting long shadows across empty seats, a wedding ring visible on the hand holding the phone, visible film grain, subject lower third, vertical composition 9:16`
- motion_prompt: `slow push toward the glowing phone screen, golden light shifting through window, uneaten food on tray`

### S02 铁律一：你的位子，不是你的 (15s, tension)

**配音:**
> 铁律一：你的位子，不是你的。
> 2026年，AI不是在抢你的饭碗。它已经坐了你的位子。
> 工作12年，通知用了3分钟。钉钉群一退，你就不是这个公司的人了。
> 马斯克说过："失败是一个选项。如果你没有失败过，说明你创新不够。"

**pause_markers:**
```
铁律一<#0.3#>你的位子<#0.2#>不是你的。<#0.8#>2026年<#0.3#>AI不是在抢你的饭碗。<#0.5#>它已经坐了你的位子。<#0.8#>工作12年<#0.2#>通知用了3分钟。<#0.5#>钉钉群一退<#0.2#>你就不是这个公司的人了。<#1.0#>马斯克说过<#0.2#>"失败是一个选项。<#0.3#>如果你没有失败过<#0.2#>说明你创新不够。"
```

**subtitle_text:** "工作12年 通知用了3分钟"
**yangmun_clip_hint:** day5-yangmun/S02-determined.mp4
**名人原话:** "Failure is an option here. If things are not failing, you're not innovating enough." (SpaceX内部文化)
**故事图 S02-01:** AI上线整个部门消失
- reference_prompt: `shot on Canon 5D Mark IV 24mm f/2.8 Kodak Portra 400, split composition left side shows rows of empty office desks with monitors still on but screens black, right side shows cold blue server racks with blinking LED lights, a single coffee mug left on one desk, harsh fluorescent light on office side versus cool blue glow on server side, visible film grain, subject center, vertical composition 9:16`
- motion_prompt: `slow pan from empty desks to glowing server racks, a monitor screen flickers off`

### S03 铁律二：被开除不是终点，是系统的局限 (15s, reversal)

**配音:**
> 铁律二：被开除不是终点，是系统的局限。
> 马斯克被踢出PayPal那年，瘦了30斤，在路边吃冰淇淋，没人搭理他。
> 后来PayPal市值涨了10倍，但把他赶走的那些人，没有一个名字被记住。
> 马斯克说："我不放弃，除非我死了。"

**pause_markers:**
```
铁律二<#0.3#>被开除不是终点<#0.2#>是系统的局限。<#0.8#>马斯克被踢出PayPal那年<#0.2#>瘦了30斤<#0.2#>在路边吃冰淇淋<#0.2#>没人搭理他。<#1.0#>后来PayPal市值涨了10倍<#0.3#>但把他赶走的那些人<#0.2#>没有一个名字被记住。<#0.8#>马斯克说<#0.2#>"我不放弃<#0.2#>除非我死了。"
```

**subtitle_text:** "把他赶走的人 没有一个被记住"
**yangmun_clip_hint:** day6-yangmun/S03.mp4
**名人原话:** "I don't ever give up. I'd have to be dead or completely incapacitated." (多次采访)
**故事图 S03-01:** 马斯克路边吃冰淇淋
- reference_prompt: `shot on Canon 5D Mark IV 50mm f/1.4 Kodak Portra 400, documentary style street scene, a single melting ice cream cone sitting on a concrete bench in harsh afternoon sunlight, no people visible, just the abandoned cone casting a small shadow, cracked pavement, a blurred city street behind, warm harsh light with deep shadows, visible film grain, subject lower center, vertical composition 9:16`
- motion_prompt: `slow zoom on melting ice cream, afternoon light shifting, a drop slowly falls`

### S04 情感收尾 (10s, warm)

**配音:**
> 马斯克说的不是PayPal。说的是你。
> 你被裁掉不是因为你不行。是因为那个系统，看不到你的价值。
> 你还没有死。评论区聊聊。

**pause_markers:**
```
马斯克说的不是PayPal。<#0.5#>说的是你。<#0.8#>你被裁掉不是因为你不行。<#0.5#>是因为那个系统<#0.2#>看不到你的价值。<#0.8#>你还没有死。<#0.3#>评论区聊聊。
```

**subtitle_text:** "你还没有死"
**yangmun_clip_hint:** day5-yangmun/S05-warm.mp4
**故事图:** 无

## 4. 评估 (90/100)

| 维度 | 分数 | 说明 |
|------|------|------|
| Hook名人原话开场 | 9 | S01原话与场景略有时间差 |
| 至少2处原话 | 10 | 3处，超标 |
| 原话可溯源 | 7 | 第三句翻译略夸大 |
| 无数字开头 | 10 | |
| 收尾名人→观众 | 9 | "系统看不到价值"偏安慰剂 |
| CTA开放问题 | 9 | "聊聊"不是发问式 |
| 数字自然带出 | 10 | |
| 画面感/共鸣力 | 8 | 缺"你"直接代入场景 |
| 时长合规 | 9 | ~50s，在45-55s目标内 |
| 情绪弧线 | 9 | S02转折略快 |

## 5. 素材清单

| 类型 | 数量 | 来源 |
|------|------|------|
| 故事图 (Seedream) | 3张 | S01-01, S02-01, S03-01 |
| 故事视频 (Kling) | 3个 | 从故事图生成，5s/个 |
| TTS配音 (Aoede) | 4段 | S01-S04 |
| 杨梦表情视频 | 4段 | day5/day6 素材库选取 |

## 6. 剪映混剪顺序

```
杨梦(shock/S01) → 故事视频(S01-01) → 杨梦(tension/S02) → 故事视频(S02-01) → 杨梦(reversal/S03) → 故事视频(S03-01) → 杨梦(warm/S04+CTA)
```

## 7. 成本估算

| 组件 | 单价 | 数量 | 小计 |
|------|------|------|------|
| Seedream 图 | $0.03 | 3 | $0.09 |
| Kling 视频 | $0.079/s × 5s | 3 | $1.19 |
| TTS (Gemini) | ~$0.01 | 4段 | $0.04 |
| **总计** | | | **~$1.32** |
