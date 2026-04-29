# AI 短视频生产规范 v4.2 — Medvi 工作流（失业系列）

> 适用范围：60-120 秒 AI 生成短视频，抖音/小红书竖版
> 工作流类型：**Medvi**（真实故事+情绪共振，旁白驱动）
> 工具链：Seedream 4.5 + Kling 3.0 (Evolink) + Gemini 3.1 Flash TTS + FFmpeg + 剪映
> 本文档是唯一权威标准，取代所有先前的工作流文档
> 最后更新：2026-04-29

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
Stage 1.5: 文案评估  →  独立 agent 盲评，≥90 分通过
Stage 2: 参考图生成  →  seedream-batch.py 读配置
Stage 3: 视频生成    →  Kling 3.0 API 批量生成，参数来自配置
Stage 4: 配音生成    →  gemini-tts-batch.py 读配置
Stage 5: 视频合成    →  compose-video.py 读配置
Stage 6: 去AI化后期  →  FFmpeg 滤镜 + 剪映精修
Stage 7: 最终审核    →  人工 + 脚本检查，通过后上传
```

### Medvi v2 工作流（Day10 起生效）

> v2 核心变更：跳过 Seedream 主参考图 + Kling 杨梦视频，只生成故事图。杨梦表情素材从已有库选取，在剪映混剪。

**v2 适用标记：** JSON config 中 `global.workflow_version` 为 `"2.0"` 时按 v2 规则执行。

| 阶段 | v1 | v2 | 说明 |
|------|-----|-----|------|
| Stage 2 参考图 | Seedream 主图(4) + 故事图(6) | **只生成故事图(3)** | 跳过 seedream-batch.py，只运行 seedream-story-images.py |
| Stage 3 视频 | Kling 杨梦(4) + 故事(6) | **只生成故事视频(3)** | kling-gen-batch.py --include-stories |
| Stage 5 合成 | FFmpeg 拼接 | **跳过，剪映混剪** | 不运行 FFmpeg compose 脚本 |

**v2 Config JSON 结构：** 每个 segment 不含 `reference_file`/`reference_prompt`/`motion_prompt`，新增 `yangmun_clip_hint` 指示选用哪个已有杨梦表情视频。故事图 S01/S02/S03 各 0-1 张（共 3 张），S04 无。

**v2 剪映混剪模式：** 杨梦(shock) → 故事视频(S01) → 杨梦(tension) → 故事视频(S02) → 杨梦(reversal) → 故事视频(S03) → 杨梦(warm+CTA)

**v2 成本：** 每条约 $0.33（3张 Seedream + 3个 Kling），比 v1 节省 70%。

**杨梦素材库：** shock=`day5-yangmun/S01-shock.mp4`, tension=`day5-yangmun/S02-determined.mp4`, power=`day5-yangmun/S03-power.mp4`, contemplative=`day5-yangmun/S04-contemplative.mp4`, warm=`day5-yangmun/S05-warm.mp4`, Day6全套=`day6-yangmun/S01-S05.mp4`

---

## 1. 视频全局标准

### 1.1 时长

| 规则 | 标记 | 值 |
|------|------|----|
| 最终时长 60-120 秒 | MUST | ffprobe 检查 |
| 甜点区间 70-90 秒 | SHOULD | 完播率与信息量平衡 |
| 最短不低于 60 秒 | MUST | 故事需要展开空间 |
| 最长不超过 120 秒 | MUST | 超过则需拆分 |
| 钩子 = 前 3 秒 | MUST | 前置高潮，最强冲击点 |
| 互动闭环 = 最后 5 秒 | MUST | 评论引导 |

### 1.2 分辨率和编码

| 规则 | 标记 | 值 |
|------|------|----|
| 导出分辨率 1080x1920 | MUST | 9:16 竖版 |
| Kling 输出 720x1280 | MUST | 后期升采样 |
| 参考图 1440x2560 | MUST | Seedream API 原生 9:16 2K |
| 帧率 24fps | MUST | Kling 原生输出，全程一致 |
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

| 景别 | 用途 | Kling motion_prompt 方向 | 占比参考 |
|------|------|------------------|---------|
| 远景（Wide） | 开场/转场/结尾 | slow pan, wide angle, establishing shot | ~15% |
| 中景（Medium） | 主体展示/工作场景 | medium shot, natural framing | ~45% |
| 特写（Close-up） | 数据放大/情感连接 | extreme close-up, shallow depth of field | ~30% |
| 文字卡片（Text） | 数据展示/对比/CTA | HTML/CSS 渲染 + Playwright 截图 | ~10% |

**文字卡片自动路由：** `shot_type: text_card` 的段落跳过 Stage 2（Seedream）和 Stage 3（Kling），在 Stage 5（FFmpeg 合成）中由 `text-card-renderer.py` 通过 HTML/CSS + Playwright 自动渲染。支持渐变背景、文字发光、逐行动画、微粒子装饰。

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
| 1 | 前置高潮 | "被裁第47天，我赚到第一个5000块" | 70-80% |
| 2 | 反直觉结果 | "投了200份简历，0回复。但第47天我赚了5000" | 65-75% |
| 3 | 身份共鸣 | "38岁，外企15年，一通电话全没了" | 60-70% |
| 4 | 崩塌数据 | "第一个星期投40份，回复0。第二个星期降薪30%，还是0" | 55-65% |
| 5 | 好奇缺口 | "失业后最蠢的一件事，就是疯狂投简历" | 50-60% |

### 2.4 视觉规则

| 规则 | 标记 |
|------|------|
| 前置高潮型：用反差画面（困境对比成果）或强代入感的生活场景 | MUST |
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
| **共鸣优先** | 完播率、评论互动、精准粉丝聚集 | 前置高潮/身份共鸣 | 开放讨论 | 失业系列，纯共鸣不提产品 |
| **转化优先** | 引导用户行动 | 数字/成本对比 | 私信关键词 | 有成熟产品后（暂不使用） |

### 5.3 MUST 规则

| 规则 | 值 |
|------|----|
| 总旁白字数 | 60 秒 → 200-260 字，75 秒 → 250-320 字，90 秒 → 300-380 字，120 秒 → 400-500 字 |
| 每句旁白 | ≤ 15 个中文字，超过就断句 |
| 套话禁止 | 不用"今天就教大家"、"大家好我是XX" |
| CTA | 只有一个明确的动作 |
| 大声朗读计时 | 60-120 秒，用秒表验证 |
| 每段标注 emotion_arc | 中文情绪标签（好奇/代入/共鸣/希望/力量/参与） |
| 每段有 subtitle_text | ≤ 12 字的浓缩字幕，不是旁白全文 |
| 脚本遵循"真实痛点＋情绪共振"方法论 | 见 5.8 节，所有 Medvi 视频必须遵循 |

### 5.4 共鸣优先策略规则

| 规则 | 值 |
|------|----|
| 真实故事 | 用真实失业者的故事做钩子，不虚构。崩塌段细节必须精准到日常，见 5.8 节 |
| 情绪弧线 | 好奇→代入→共鸣→希望→力量→参与 |
| Anti-ad 措施 | 见下方清单 |
| 不卖东西 | 不提产品、工具、方案、服务 |
| 不引导转化 | 不引导私信、关注、领取 |
| CTA 用开放问题 | 针对崩塌段痛点提问，激发评论互动 |
| 关键细节 | 用在故事里自然带出，不为凑细节而加 |

**Anti-ad 措施清单（配置文件 `script.anti_ad_measures`）：**

```
1. 不提 AI Agent、代运营、智能体等业务关键词
2. 不引导私信、领取、关注
3. CTA 用开放式问题，激发评论互动
4. 聚焦失业者的真实故事和情绪，不卖任何东西
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

- [ ] 大声朗读计时：___ 秒（MUST：60-120s）
- [ ] 字数：___ 字（MUST：200-500 字）
- [ ] CTA 动作数量：___ 个（MUST：= 1）
- [ ] 最长单句：___ 字（MUST：≤ 15）
- [ ] 每段有 emotion_arc 标签（MUST）
- [ ] 每段有 subtitle_text（MUST）
- [ ] 共鸣优先视频：anti_ad_measures 全部通过（MUST）
- [ ] 共鸣优先视频：无营销词汇、无转化引导（MUST）
- [ ] 转化优先视频：数字数量 ≥ 3（MUST）
- [ ] "真实痛点＋情绪共振"方法论全项通过（MUST，见 5.8）
- [ ] Stage 1.5 文案评估分数 ≥ 90（MUST，见 5.9）

### 5.8 "真实痛点＋情绪共振"写作方法论（MUST）

> 所有 Medvi 视频脚本必须遵循此方法论。真实失业者故事驱动情绪，具体生活细节建立共鸣。

#### 核心原则

**1. 故事必须来自真实生活细节，不是概念。**
"凌晨三点还在改简历"比"就业形势严峻"有穿透力。每段至少一个让观众觉得"这就是我生活"的具体画面。

**2. 崩塌段要精准到失业者的日常，不是笼统的"很难"。**
简历投了多少份、读了多少遍、等了多久、改了几版——这些数字不用来炫，用来让观众对号入座。

**3. 转念必须来自外部触发，不能是自我鸡汤。**
"我告诉自己要坚强"没人信。"老客户说'我找的是你不是你们公司'"——这种来自别人的认可，才是真正能打动失业者的转折点。

#### 脚本结构模板（SPR-L：前置高潮→设定→崩塌→转念→收尾→互动）

```
S01  前置高潮 (0-3s)
     最强冲击点前置——重建后的成果瞬间
     例："被裁第47天，我赚到第一个5000块"

S02  设定 (3-20s)
     人物画像：年龄、行业、工龄、怎么丢的工作
     例："38岁，外企15年，一通电话，全没了"

S03  崩塌 (20-45s) + 钩子1
     疯狂投简历 → 石沉大海 → 面试被拒 → 开始怀疑自己
     例："第一个星期投了40份简历，回复0。第二个星期降薪30%，回复0。
          第三个星期连降薪都不敢写了。这15年到底算什么？"
     钩子：每15-20秒一个更深的情绪戳点

S04  转念 (45-65s) + 钩子2
     一个具体的触发事件
     例："有天老客户打电话问我那个项目怎么跟进。
          他说'我找的是你，不是你们公司'。"

S05  收尾 (65-85s)
     把故事拉回观众自身
     例："你身上有多少你自己没看到的东西？"

S06  互动闭环 (85-95s)
     针对崩塌段的痛点提问
     例："你投了多少份简历了？评论区聊聊"
```

**段数要求：** 4-7 段（前置高潮 + 设定 + 1-3 个困境/反转弧 + 收尾 + 互动闭环），总段数 ≤ 8。

#### 每段写作结构

| 段落 | 写作重点 | 技法 |
|------|---------|------|
| S01 前置高潮 | 一句话+一个反直觉结果 | 先给答案再讲过程 |
| S02 设定 | 3个具体身份标签（年龄/行业/工龄） | 数字即代入感 |
| S03 崩塌 | 简历投递数据+情绪下坠细节 | 递进式绝望：第一周→第二周→第三周 |
| S04 转念 | 一句别人的话或一个意外事件 | 外部视角打碎自我否定 |
| S05 收尾 | 把故事拉回观众自身 | "你身上有多少你自己没看到的东西" |
| S06 互动 | 针对崩塌段的痛点提问 | 引发评论而不是点赞 |

#### 情绪弧线

```
好奇(前置高潮) → 代入(设定) → 共鸣(崩塌) → 希望(转念) → 力量(收尾) → 参与(互动)
```

| 段落 | 情绪 | 观众内心反应 | 关键技法 |
|------|------|------------|---------|
| 前置高潮 | 震惊+好奇 | "怎么做到的？" | 反直觉结果 |
| 设定 | 代入 | "这不就是我吗？" | 具体数字（年龄、工龄） |
| 崩塌 | 共鸣+痛 | "对，就是这样" | 简历黑洞的精准细节 |
| 转念 | 希望 | "还有这种角度？" | 外部视角的意外认可 |
| 收尾 | 力量感 | "我也可以" | 把故事拉回观众自身 |
| 互动 | 参与 | "我要说说" | 针对痛点的开放问题 |

#### 核心写作铁律

> **崩塌段必须真实到让失业者觉得"这人是不是在偷看我生活"。** 转念段必须来自外部触发（别人的话、一个事件），不能是"我告诉自己要坚强"——没人信。

#### 禁止写法

- 鸡汤式收尾（"相信自己，一切都会好的"）
- 自我激励式转折（"我告诉自己不能放弃"）
- 笼统描述（"那段日子很难熬"）
- 陌生人视角的总结（"失业不可怕"——你没失过业你当然这么说）
- 数字开头（"8万降到3千"）→ 改为画面开头（"凌晨三点还在改简历"）
- 冷冰冰的结论 → 改为情绪化结论

#### 完整示例

```
标题：被裁第47天，我赚到第一个5000块

S01 (前置高潮):
被裁第47天，我赚到了第一个5000块。
不是靠投简历。是靠翻通讯录。

S02 (设定):
38岁，外企15年。
一通电话，全没了。
HR说"公司战略调整"，翻译过来就是——你太贵了。

S03 (崩塌):
第一个星期，投了40份简历。回复0。
第二个星期，降薪30%。回复0。
第三个星期，连降薪都不敢写了。
房贷每月1万2，孩子幼儿园5000，我妈的降压药不能停。
那段时间每天最怕的就是早上醒来——因为醒来就要面对一天。

S04 (转念):
有天老客户打电话问我那个项目怎么跟进。
我说我已经不在了。
他说了一句话："我找的是你，不是你们公司。"
那天晚上我翻了翻通讯录，200个客户关系。
原来这些东西，一直都在。只是以前绑在公司身上。

S05 (收尾):
你身上有多少值钱的东西，你自己都没看到？
你的经验，你的人脉，你的行业嗅觉——这些不会因为一通电话就消失。

S06 (互动):
你投了多少份简历了？评论区说说。
```

#### 5.8 质量检查

- [ ] 前置高潮有具体数字+具体时间（MUST）
- [ ] 设定段有3个身份标签（年龄/行业/工龄）（MUST）
- [ ] 崩塌段有递进式绝望细节（不是笼统的"很难"）（MUST）
- [ ] 转念段来自外部触发（不是自我鸡汤）（MUST）
- [ ] 收尾段把故事拉回观众自身（MUST）
- [ ] 互动段针对崩塌段的痛点提问（MUST）
- [ ] 没有以数字开头的段落（SHOULD）
- [ ] CTA 是开放问题，不推销（MUST）

### 5.9 文案质量门控（Stage 1.5）

> 每条视频脚本写完后，必须经过独立评估。未达 90 分不得进入 Stage 2。

#### 流程

```
Stage 1: 脚本写作 → Stage 1.5: 文案评估 → 通过(≥90分) → Stage 2: 参考图生成
                                       → 不通过(<90分) → 重写脚本
```

#### 评估方式

由独立 agent 担任评审，不带写作时的上下文，只看成品打分。

#### 评估维度（100分制）

| 维度 | 分值 | 评估标准 |
|------|------|---------|
| 情绪真实度 | 25分 | 崩塌段细节是否精准到失业者日常，不笼统 |
| 代入感 | 20分 | 设定段是否有让观众"这就是我"的元素 |
| 转念可信度 | 20分 | 转折是否来自外部触发，不是自我鸡汤 |
| 钩子密度 | 15分 | 每15-20秒是否有新的情绪刺激点 |
| 结构完整性 | 10分 | 是否完整走完 前置高潮→设定→崩塌→转念→收尾→互动 |
| 禁止项检查 | 10分 | 是否避免了所有禁止写法 |

#### 评分规则

| 分数 | 结果 |
|------|------|
| ≥ 90 | 通过，进入 Stage 2 |
| 80-89 | 修改：标注薄弱维度，针对性改进后重新评估 |
| < 80 | 重写：换角度重写整个脚本 |

#### 执行方式

脚本写完后，启动独立 agent 盲评。评分结果写入 config JSON 的 `script.review` 字段，包含 `score`、`dimensions`（各维度得分）、`suggestions`（具体修改建议）。

#### Config JSON 示例

```json
"review": {
  "score": 92,
  "dimensions": {
    "emotion_authenticity": 24,
    "immersion": 18,
    "turning_point_credibility": 19,
    "hook_density": 13,
    "structure_completeness": 10,
    "prohibition_check": 8
  },
  "suggestions": ["崩塌段可以加入具体的面试被拒场景增加真实感"],
  "status": "pass"
}
```

### 5.10 故事图规划（story_images）

每段在写脚本时同步规划 1-2 张故事场景图。故事图不包含角色肖像，而是展现文案提到的具体画面，让观众产生代入感。

| 段落 | 故事图数量 | 内容来源 |
|------|-----------|---------|
| 前置高潮 | 1-2 | 反差画面（困境 vs 成果暗示） |
| 设定/崩塌/转念 | 2 | 故事中的具体生活画面（简历、通讯录、空房间） |
| 收尾/互动 | 0 | 角色特写已足够 |

故事图写入 JSON config 的 `segments[].story_images` 数组，每条包含 `id`、`trigger_text`、`reference_prompt`、`motion_prompt`。故事图 prompt 遵循 6 层结构，但不包含 character_anchor。

---

## 6. Stage 2：参考图生成（Seedream 4.5）

> **v2 模式：** 当 `workflow_version: "2.0"` 时，跳过主参考图生成（seedream-batch.py），只运行 seedream-story-images.py 生成故事场景图（3张）。每个 segment 的 reference_prompt 字段不存在。

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
| 边缘干净 | 无重要元素靠近画框边缘（Kling 可能扭曲边缘） |

### 6.4 故事图（Story Images）

每段可有 0-3 张故事场景图，与主图（角色情绪锚点）穿插使用。

| 规则 | 值 |
|------|-----|
| 每段可有 0-3 张故事图 | JSON config 中 `story_images` 数组 |
| 故事图不包含角色锚定 | 不需要 character_anchor |
| 故事图遵循 6 层 prompt 结构 | 摄影声明 + 场景主体 + 环境 + 光影 + 构图 |
| 总图数 10-15 张/条视频 | 主图 5 张 + 故事图 5-10 张 |
| 生成工具 | `python3 seedream-story-images.py --config {video_id}.json` |
| 文件命名 | `S02-01.png`、`S02-02.png`（主图为 `S02.png`） |

### 6.3 Prompt 生成逻辑（MUST 阅读）

> 经 4 轮迭代验证的最终方法论。违反这些原则 = 图片无法引起观众情绪共鸣。

**核心框架：情感弧线 + 辨识度元素**

每条视频的图片序列必须构成一条完整的情感弧线。按策略选择对应弧线：

**共鸣优先弧线（失业系列型）：**

```
好奇 → 代入 → 共鸣 → 希望 → 力量 → 参与
```

| 步骤 | 情绪 | 观众内心反应 | 视觉要素 |
|------|------|------------|---------|
| 1 好奇 | 震惊+好奇 | "怎么做到的？" | 反差画面：困境中的人 vs 成果暗示 |
| 2 代入 | 自我投射 | "这不就是我吗？" | 办公室/求职场景，具体生活物件 |
| 3 共鸣 | 痛/被理解 | "对，就是这样" | 空荡房间、手机上的已读不回、简历截图 |
| 4 希望 | 意外认可 | "还有这种角度？" | 暖光、通讯录、老客户来电 |
| 5 力量 | 行动力 | "我也可以" | 人物正面看向镜头，坚定表情 |
| 6 参与 | 被问到 | "我要说说" | 诚恳表情+开放问题 |

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
- [ ] 6 张图构成完整情感弧线（共鸣优先：好奇→代入→共鸣→希望→力量→参与；转化优先：共情→向往→希望→震撼→对比→信任）
- [ ] Prompt 开头有摄影声明（原则 3 v3.0）
- [ ] Prompt 中有具体的、可见的不完美描述（不是笼统后缀）
- [ ] 有人脸的画面包含至少 1 处面部不对称描述（原则 3 v3.0）
- [ ] Negative prompt 已配置，包含 v3.0 完整列表（原则 3 v3.0）
- [ ] 200px 宽度下辨识度元素仍可识别（原则 5）

---

## 7. Stage 3：视频生成（Kling 3.0 via Evolink API）

> **v2 模式：** 当 `workflow_version: "2.0"` 时，跳过主视频生成，只生成故事图视频（--include-stories，3个）。脚本会自动发现无主参考图可生成。

### 7.1 输入/输出

- 输入：参考图 + JSON 配置中的 `segments[].motion_prompt`
- 输出：MP4 文件，720x1280，24fps，5 秒/段
- 脚本：`kling-gen-batch.py --config <config> --include-stories`

### 7.2 MUST 规则

| 规则 | 值 |
|------|----|
| 只使用 Image-to-Video | 绝不用纯文生视频 |
| 提示词只写运动 | 不重复描述画面中已有的内容，最多 2 句 |
| model | `kling-v3-image-to-video` |
| image_start 参数 | base64 data URI 直接传入，无需上传到公网 |
| 分辨率 | 720x1280 (9:16) |
| 每段时长 | 5 秒 |
| API 轮询 | POST 创建任务 → GET `/v1/tasks/{id}` 轮询，约 30-50s/段 |
| 拒收标准 | 任何片段出现变形、闪烁、物体扭曲、面部异常 = 重新生成 |

**故事图视频：** 加 `--include-stories` 参数，脚本自动为 `story_images` 中的每张图生成 Kling 视频。文件命名为 `S02-01.mp4`、`S02-02.mp4`。

### 7.3 SHOULD 规则

| 规则 | 值 |
|------|----|
| 质量 720p | $0.079/s，性价比最高 |
| 可选 1080p | $0.106/s，质量优先时 |
| 运动强度 | prompt 控制在 subtle/slow 级别，宁低勿高 |
| 景别匹配运动 | 见下表 |

**景别对应 motion_prompt 模板：**

| 景别 | motion_prompt 模板 |
|------|------------|
| 远景 | `slow pan left, ambient atmosphere, cinematic motion` |
| 中景 | `slow push in, subtle head movement, natural light shift` |
| 特写 | `slow zoom in, gentle ambient light pulse, cinematic` |
| 故事场景 | `slow subtle camera movement, {description}` |
| 文字卡片 | 跳过（由 text-card-renderer.py 处理） |

### 7.4 批量生成命令

```bash
source docs/content/.env
python3 docs/content/scripts/kling-gen-batch.py --config config/day6-yangmun.json --include-stories
python3 docs/content/scripts/kling-gen-batch.py --config config/day6-yangmun.json --shot S01  # 单段测试
python3 docs/content/scripts/kling-gen-batch.py --config config/day6-yangmun.json --dry-run     # 预览
```

### 7.5 后处理（剪映中完成）

| 操作 | 标记 | 参数 |
|------|------|------|
| 裁剪首尾 | MUST | 去掉首尾不稳定帧 |
| 手持抖动 | MUST | 剪映 → 特效 → 抖动，强度 10-15% |
| 胶片颗粒 | SHOULD | 剪映 → 特效，增加质感 |

#### 7.5.1 AI 空镜后处理管线（SHOULD）

> 仅适用于 Seedream/Kling 生成的 atmosphere_shots（氛围空镜）。Playwright UI 截图**不做任何后处理**，保持像素级真实。

| 步骤 | 效果 | 参数 | 剪映实现 |
|------|------|------|---------|
| 胶片颗粒 | 可见但微妙的噪点纹理 | 强度 15-25% | 特效 → 噪点/颗粒 |
| 降饱和度 | 褪色感，不纯黑白 | 降低 20-30% | 调色 → 饱和度滑块 |
| 暗角 | 边缘渐暗，视觉聚焦中心 | 中等强度 | 特效 → 暗角 |
| 色差偏移（可选） | 模拟模拟信号感 | 2-3px 红蓝偏移 | 需要自定义 |

**设计理由：** 截图负责"证据感"（干净、锐利、像素级真实），空镜负责"氛围感"（带颗粒、略褪色、有温度）。两者风格差异帮助观众潜意识区分"这是真实素材"和"这是氛围渲染"。

### 7.6 质量检查

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
| 2 | **Doubao TTS 2.0** (自动降级) | 按量付费 | 高 | `gemini-tts-batch.py` 内置降级 |
| 3 | **Edge TTS** (YunxiNeural) | 完全免费，无限制 | 高 | `edge-tts-batch.py` |
| 4 | Fish Audio S2 Pro | 按量付费 | 高 | `fish-audio-tts-batch.py` |

**选择规则：** Gemini 额度可用时用 Gemini。Gemini 返回 429/403 时自动降级到 Doubao TTS（claire 声音克隆）。同一条视频不混用两个 TTS 引擎。

**自动降级机制：** `gemini-tts-batch.py` 在 Gemini API 返回配额错误时自动切换到 Doubao TTS，无需手动干预。

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
| 声音 | **Aoede（女声）** — 强制要求，禁止使用男声 |
| 批量命令 | `python3 gemini-tts-batch.py --config config/{video_id}.json` |
| 需要环境变量 | `GEMINI_API_KEY` |

**强制规则：** 所有 Medvi 视频统一使用 Aoede 女声配音，禁止使用男声（Charon、Orus 等）。声音一致性是品牌标识的一部分。

**特点：** 支持 Director's Notes 精细控制情绪，音频标签（[amazed], [warmly]），质量最接近真人。

### 8.5 Edge TTS 参数（免费备选）

| 参数 | 值 |
|------|----|
| 声音 | `zh-CN-XiaoxiaoNeural`（推荐，温暖女声） |
| 声音备选 | `zh-CN-XiaoyiNeural`（活力女声） |
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
| 时长超 90s | 优先保证质量，可通过剪映调速 |

### 8.7 质量检查

- [ ] 每个字可辨识（无含糊不清）
- [ ] 无金属/电子感（3 遍听测通过）
- [ ] 关键数字有自然强调
- [ ] 音质干净无噪音
- [ ] 全片叙述者声音一致

---

## 9. Stage 5：视频合成

> **v2 模式：** 当 `workflow_version: "2.0"` 时，完全跳过 FFmpeg 合成。所有素材（杨梦表情视频 + 故事视频 + TTS 配音）在剪映中手动混剪。

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

### 9.2.1 多图段合成（story_images）

当一段有多张图（主图 + 故事图）时：

| 规则 | 值 |
|------|-----|
| 每张图均匀分配该段的配音时长 | audio_duration / num_clips |
| 主图在前，故事图按 config 顺序排列 | MUST |
| Kling 视频（5s）短于分配时长时循环播放（正播+倒播交替） | 自动处理 |
| 所有图硬切拼接 | 无转场 |
| 脚本 | `ffmpeg-compose-day1.py` 自动识别 `video_clips` |

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

- [ ] ffprobe 时长 ≤ 120.0s 且 ≥ 60.0s
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
| 已在 Kling 生成时处理 | 跳过 |
| 未在 Kling 加 | 剪映 → 特效 → 抖动，强度 3-5% |

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

- [ ] ffprobe 报告时长 ≤ 120.0s 且 ≥ 60.0s（MUST）
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
  "strategy_notes": "共鸣优先策略：纯情绪共鸣不提产品。真实失业者故事+SPR-L结构+多钩子设计，不提Agent/代运营/任何业务",

  "global": {
    "target_duration_sec": 75,
    "max_duration_sec": 120,
    "min_duration_sec": 60,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": 67890,
    "style": "cinematic_documentary",
    "color_temperature": "cool_steel",
    "accent_color": "#4a90d9",
    "bg_color": "#000000"
  },

  "script": {
    "topic": "马斯克裁了6000人用AI替代，公司效率反升",
    "source": "Yahoo Finance 2025, InfoQ 2025",
    "hook_type": "preemptive_highlight",
    "cta_action": "讨论",
    "cta_keyword": "",
    "cta_deliverable": "",
    "anti_ad_measures": [
      "不提AI Agent、代运营、智能体等业务关键词",
      "不引导私信、领取、关注",
      "CTA用开放式问题，激发评论互动",
      "聚焦失业者的真实故事和情绪，不卖任何东西",
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
    "engine": "kling_v3",
    "mode": "image_to_video",
    "model": "kling-v3-image-to-video",
    "api_base": "https://api.evolink.ai/v1",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "quality": "720p",
    "aspect_ratio": "9:16",
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
| Kling 批量生成视频 | 15 分钟 | `kling-gen-batch.py` 自动化 |
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
| 视频 > 120s | 脚本太长 | 拆分为两条视频 |
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

### 色系 A：冷钢蓝（共鸣优先 / 失业系列型）

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
| 2026-04-20 | 3.0 | 新增 5.8 "名人说＋情绪拉动"写作方法论：名人原话驱动情绪、铁律结构模板、画面故事替代数字堆砌、情感收尾从名人转观众。所有 Medvi 视频必须遵循。 |
| 2026-04-28 | 4.0 | 失业系列方法论更新：时长60-120s（甜点70-90s）、SPR-L叙事结构替代三大铁律、"真实痛点＋情绪共振"替代"名人说＋情绪拉动"、纯共鸣不提产品、共鸣优先策略、新增Stage 1.5文案质量门控（≥90分通过）、钩子类型+情绪弧线+质量检查全面适配 |
