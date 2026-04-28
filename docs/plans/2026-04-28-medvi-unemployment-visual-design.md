# Medvi 失业系列 Corecore 蒙太奇视觉设计

> 设计日期：2026-04-28
> 状态：已批准
> 关联：medvi-unemployment-series-design.md（文案方法论）
> 目标：Spec v4.0 → v4.1

---

## 1. 核心问题

失业话题的核心是**信任和共情**。AI感一出来，观众立刻觉得"你不是我们的人"。以前名人+商业内容，AI画面可以接受；失业话题不行。

**解法：** 素材来源按信任风险分级，AI只做"看不出来"的氛围空镜，信息载体用 Playwright 渲染真实 UI 截图。

---

## 2. 素材三级分类

| 级别 | 来源 | 内容 | 信任风险 |
|------|------|------|---------|
| **A类：信息载体** | Playwright 渲染 HTML/CSS | 招聘界面、聊天记录、邮件、数据面板 | 零风险，UI100%真实 |
| **B类：氛围空镜** | Seedream + Kling | 无人空镜、物件特写、光影 | 低风险，空镜难辨真假 |
| **C类：禁止使用** | 任何来源 | AI生成的截图/手机界面/聊天记录/人脸 | 高风险，一眼假 |

---

## 3. A类：Playwright UI 截图

### 3.1 模板清单

| 模板ID | 模拟对象 | 关键 UI 元素 |
|--------|---------|-------------|
| `tpl-boss-search` | Boss直聘搜索结果 | 职位卡片、薪资、"已读不回"红标、筛选标签 |
| `tpl-dingtalk-leave` | 钉钉系统通知 | "您已被移出群聊"灰色系统消息 |
| `tpl-resume-stats` | 求职数据面板 | 投递总数、已读数、回复数、面试数（进度条） |
| `tpl-wechat-reject` | 微信聊天（HR拒绝） | 绿色气泡、"年龄不太符合"、时间戳 |
| `tpl-wechat-positive` | 微信聊天（正面转折） | 绿色气泡、"我找的是你" |
| `tpl-douyin-comment` | 抖音评论区 | 评论列表、"投了300份了"、点赞数 |

### 3.2 工作流（Stage 1.7，新增）

```
Stage 1: 脚本写作
Stage 1.5: 文案评估（≥90分）
Stage 1.7: UI截图生成（Playwright）  ← 新增
Stage 2: 氛围空镜生成（Seedream）
Stage 3: 空镜转视频（Kling）
Stage 4: 配音（Gemini TTS Aoede）
Stage 5: 剪映混剪
```

### 3.3 模板设计原则

- 每个模板 = 独立 HTML + CSS，存放 `docs/content/templates/`
- 数据通过 JSON 配置注入（对话内容、数字、名字）
- 中文字体用系统默认（PingFang SC），不引入外部字体
- 截图前随机延迟 0.5-1.5s，模拟真实截图的不完美
- 截图尺寸 1080×1920，直接用 PNG 静态图，**不做 Kling 转视频**
- 名字全部打码或用化名（"张*理"、"李*理"），避免隐私问题

---

## 4. B类：AI 氛围空镜

### 4.1 Prompt 风格变更

```python
# 旧（v4.0 电影感）
"shot on Canon 5D Mark IV 35mm f/2.0 Kodak Portra 400, ..."

# 新（Corecore 氛围空镜）
"iPhone 15 snapshot, [场景], ambient [light] lighting,
 no people visible, casual framing, untouched, vertical 9:16"
```

### 4.2 Prompt 六条铁律

1. **不出现人脸** — `no people visible, no faces`
2. **不出现文字/UI** — `no text, no screens, no UI elements`
3. **不用胶片感** — 去掉 `Kodak Portra`、`film grain`
4. **不用精构图** — 加 `casual framing`, `slightly off-center`
5. **只做氛围** — 场景本身传递情绪，不传递信息
6. **有自然瑕疵** — `slight blur`, `overexposed highlight`

### 4.3 常用空镜清单

| 素材 | Prompt 方向 | 为什么安全 |
|------|------------|-----------|
| 凌晨台灯下的简历 | 暖光特写 | 没有人脸没有文字 |
| 空荡办公区 | 荧光灯，空工位 | 只有空间感 |
| 地铁背影人群 | 模糊 | 背影+模糊无法判断 |
| 咖啡杯水珠 | 桌面特写 | 纯物件 |
| 雨天窗外 | 水珠滑落 | 自然现象AI擅长 |
| 深夜手机光照亮半张脸 | 只光线不露五官 | 光影氛围最难辨 |

---

## 5. SPR-L 素材映射

### 5.1 段落-素材对应表

| 段落 | A类截图 | B类空镜 | 切换节奏 |
|------|--------|--------|---------|
| S01 前置高潮 | Boss搜索结果 × 多张闪切 | 无 | 极快 0.5s/张 |
| S02 设定 | 钉钉退群 × 1张 | 办公桌/工牌 | 中速 2-3s/张 |
| S03 崩塌 | 简历数据面板 + HR拒绝聊天 | 凌晨台灯 | 加速→减速→加速 |
| S04 转念 | 正面微信消息 × 1张 | 暖光场景 | 放慢 3-4s/张 |
| S05 收尾 | 无 | 纯空镜 3-5s/张 | 最慢，呼吸感 |
| S06 互动 | 评论区截图 × 1张 | 无 | 2s 收尾 |

### 5.2 剪映混剪节奏

- S01：截图快速闪切，信息轰炸，建立冲击
- S02：空镜为主，穿插一张截图锚定"被移除"的真实感
- S03：截图+空镜交替，节奏越来越快模拟焦虑升级
- S04：放慢，暖色空镜先出现，截图作为"证据"最后亮出
- S05：纯空镜，让观众消化情绪
- S06：评论区截图收尾，引导参与

---

## 6. 杨梦角色退出

失业系列**不再使用杨梦角色锚点**。原因：

- Corecore 蒙太奇是"素材拼贴"风格，不需要固定角色
- AI 人脸在失业话题中信任风险高
- 纯素材拼贴更贴近真实 Corecore 风格

Config JSON 中 `character_anchor` 设为 `null`。

---

## 7. Config JSON 变更

```json
{
  "strategy": "unemployment-corecore",
  "character_anchor": null,
  "screenshots": [
    {
      "id": "SS01",
      "template": "tpl-boss-search",
      "data": {
        "job_title": "运营总监",
        "results_count": 15,
        "all_read_no_reply": true
      },
      "output_file": "day13-unemploy/SS01-boss-search.png"
    }
  ],
  "atmosphere_shots": [
    {
      "id": "AT01",
      "scene": "凌晨台灯下的简历",
      "prompt": "iPhone 15 snapshot, a desk lamp illuminating a printed resume on a wooden desk, 2am ambient light, coffee ring stain on paper, no people visible, untouched, vertical 9:16",
      "output_file": "day13-unemploy/AT01-lamp-resume.png",
      "video_file": "day13-unemploy/AT01-lamp-resume.mp4"
    }
  ]
}
```

---

## 8. Spec v4.0 → v4.1 更新范围

| 章节 | 变更 |
|------|------|
| §0 总览 | 增加 Stage 1.7 UI截图 |
| §2.4 视觉规则 | `character_anchor` 改为可选，失业系列=null |
| §6.3 Prompt 方法论 | 新增 B类空镜 6 条规则；`Canon 5D` → `iPhone snapshot` |
| §6.4 故事图规划 | `story_images` 拆分为 `screenshots` + `atmosphere_shots` |
| **新增 §6.5** | **Playwright UI截图：模板库、数据注入、截图工作流** |
| §7 视频生成 | 明确 Kling 只处理 atmosphere_shots |
| §8 合成 | 混剪节奏表（SPR-L 对应素材节奏） |
| §12 JSON Schema | 新增 `screenshots[]`、`atmosphere_shots[]` 字段 |

---

## 9. 设计决定记录

| 决定 | 理由 | 日期 |
|------|------|------|
| AI感是失业视频的致命问题 | 信任和共情是核心，AI感破坏信任 | 2026-04-28 |
| Playwright 渲染 UI 替代 AI 生成截图 | UI 元素100%真实，只有数据是编的 | 2026-04-28 |
| UI 截图不做 Kling 转视频 | 截图就是截图，不该动，动=假 | 2026-04-28 |
| 杨梦角色退出失业系列 | Corecore不需要固定角色，AI人脸信任风险高 | 2026-04-28 |
| Prompt 从 Canon 5D 转 iPhone snapshot | 电影感=AI感，手机随手拍更贴近Corecore | 2026-04-28 |
| 空镜不出现人脸和文字 | 只做氛围不做信息传递，降低AI暴露风险 | 2026-04-28 |
