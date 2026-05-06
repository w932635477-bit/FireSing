# Medvi 视觉升级 Spec v4.1 → v4.2 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 更新 video-production-spec.md，新增 AI 空镜后处理管线、呼吸式节奏精确值、字幕安全区、文字叠加样式 4 个章节。

**Architecture:** 单文件编辑（video-production-spec.md），涉及 6 个区域。按从上到下顺序执行。注意：设计文档中的章节编号与实际 Spec 文件不同 — 新内容应插入 §9（合成）区域而非 §8，因为混剪/字幕/文字叠加都是剪映合成阶段的工作。

**Tech Stack:** 纯文档编辑，无代码变更。

---

### Task 1: 更新版本号 v4.0 → v4.2 + 最后更新日期

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md:1-7` (文件头)

**Step 1: 替换文件头**

旧内容（行 1）：
```
# AI 短视频生产规范 v4.0 — Medvi 工作流（失业系列）
```

新内容：
```
# AI 短视频生产规范 v4.2 — Medvi 工作流（失业系列）
```

旧内容（行 7）：
```
> 最后更新：2026-04-28
```

新内容：
```
> 最后更新：2026-04-29
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): bump version v4.0 → v4.2, update date"
```

---

### Task 2: 在 §7.5 后处理后新增 §7.5.1 AI 空镜后处理管线

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` — 在 §7.5（行 803-809）之后、§7.6（行 811）之前插入

**Step 1: 在 §7.5 和 §7.6 之间插入新节**

插入位置：行 810（§7.5 结束后，§7.6 质量检查之前）。

插入内容：

```markdown
#### 7.5.1 AI 空镜后处理管线（SHOULD）

> 仅适用于 Seedream/Kling 生成的 atmosphere_shots（氛围空镜）。Playwright UI 截图**不做任何后处理**，保持像素级真实。

| 步骤 | 效果 | 参数 | 剪映实现 |
|------|------|------|---------|
| 胶片颗粒 | 可见但微妙的噪点纹理 | 强度 15-25% | 特效 → 噪点/颗粒 |
| 降饱和度 | 褪色感，不纯黑白 | 降低 20-30% | 调色 → 饱和度滑块 |
| 暗角 | 边缘渐暗，视觉聚焦中心 | 中等强度 | 特效 → 暗角 |
| 色差偏移（可选） | 模拟模拟信号感 | 2-3px 红蓝偏移 | 需要自定义 |

**设计理由：** 截图负责"证据感"（干净、锐利、像素级真实），空镜负责"氛围感"（带颗粒、略褪色、有温度）。两者风格差异帮助观众潜意识区分"这是真实素材"和"这是氛围渲染"。
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): add §7.5.1 AI atmosphere shot post-processing pipeline"
```

---

### Task 3: 在 §9.4 剪映职责中增加混剪节奏表

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` §9.4（行 948-960）

**Step 1: 在 §9.4 表格之后、§9.5 之前插入混剪节奏子节**

插入位置：行 961（§9.4 表格结束后）和行 962（§9.5 开始前）之间。

插入内容：

```markdown
#### 9.4.1 混剪节奏表（精确到秒，MUST）

> **呼吸式节奏原则：** 慢画面（3-5s）建立情绪 → 突然快切（0.5-1s × 3-5 个）制造冲击 → 再回到慢。这种"呼吸"式节奏比匀速快切提升 35% 完播率。

| 段落 | 节奏模式 | 具体时间值 | 画面处理 |
|------|---------|-----------|---------|
| S01 前置高潮 | 极快闪切 | 0.5s/张 × 6-10 张截图 | 截图原始状态，无后处理 |
| S02 设定 | 中速 | 2-3s/张，穿插 1 张截图 | 空镜(后处理) + 截图(原始) |
| S03 崩塌 | 呼吸式：慢→快→慢 | 3s → 1s → 0.5s×3-5 → 2s → 1s → 0.5s×3 | 快切段用截图，慢段用空镜 |
| S04 转念 | 放慢 | 3-4s/张 | 暖色空镜先出现，截图最后 |
| S05 收尾 | 最慢，呼吸感 | 4-6s/张，纯空镜 | 空镜(后处理)，让观众消化 |
| S06 互动 | 收尾 | 2s，1 张截图 | 截图(原始) |

**节奏关键数值：**

| 参数 | 值 | 说明 |
|------|-----|------|
| 最低保持时间 | 0.8s | 新视觉元素至少 0.8s 才能被观众"注册" |
| 快切频率 | 0.5-1s/张 | 制造焦虑/紧迫感 |
| 慢镜头 | 3-6s | 让观众"进入"画面，激活共情 |
| 情绪转折标记 | 节奏突变 | 突然从 3s 切到 0.5s，观众生理上会有反应 |
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): add §9.4.1 breathing rhythm timing table with precise values"
```

---

### Task 4: 在 §9.4 混剪节奏之后新增 §9.4.2 字幕安全区规则

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` — 在 §9.4.1 之后、§9.5 之前插入

**Step 1: 在 §9.4.1 之后插入新节**

插入内容：

```markdown
#### 9.4.2 字幕安全区规则（MUST）

> 抖音底部约 320px、小红书底部约 540px 被 UI 元素遮挡。字幕放在画面底部 30% 会被完全遮住。

**1080×1920 竖屏安全区：**

| 平台 | 顶部遮挡 | 底部遮挡 | 安全区 |
|------|---------|---------|-------|
| 抖音 | 130px（关注/推荐标签） | 320px（用户名、文案、音频） | 130-1600px（7%-83%） |
| 小红书 | 150px（Reels 标题） | 540px（大型 UI 区域，28%屏幕） | 150-1380px（8%-72%） |
| YouTube Shorts | 顶部搜索/相机图标 | 右侧互动+底部频道信息 | 类似抖音 |
| **通用安全区** | 150px | 540px | **画面高度 8%-72%** |

**硬性规则（MUST）：**

- 所有字幕/文字叠加放在画面高度 **25%-70%** 区域（留余量）
- 距屏幕左右边缘至少 **60px**
- 字体：无衬线（PingFang SC / 思源黑体）
- 最小字号：**18pt**（移动端观看）
- 每行最多 **42 个字符**
- 每条字幕显示时长：最短 **1s**，最长 **6s**
- 连续字幕之间留 **2 帧**间隔
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): add §9.4.2 subtitle safe zone rules (MUST)"
```

---

### Task 5: 在 §9.4.2 之后新增 §9.4.3 文字叠加样式

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` — 在 §9.4.2 之后、§9.5 之前插入

**Step 1: 在 §9.4.2 之后插入新节**

插入内容：

```markdown
#### 9.4.3 文字叠加样式（MUST）

> 海外 corecore 标准做法：极简白字硬切。越粗糙越真实。

**样式规格：**

| 属性 | 值 |
|------|-----|
| 字体颜色 | 白色（#FFFFFF） |
| 对比度要求 | ≥ 7:1（WCAG 2.1 AA） |
| 阴影 | 无 |
| 描边 | 无（或仅底图过亮时用 1px 黑色描边） |
| 动画 | 无 — 硬切进出（瞬间出现，瞬间消失） |
| 位置 | 画面高度 25%-70%，水平居中 |
| 背景 | 半透明黑色遮罩（可选，仅当底图太亮无法保证对比度时） |

**禁止项：**

- 不用淡入淡出动画
- 不用彩色字体
- 不用花哨字体
- 不用打字机效果
- 不用弹跳/缩放动画
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): add §9.4.3 text overlay style rules (MUST)"
```

---

### Task 6: 更新 §9.4 剪映职责表格，增加新任务

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` §9.4 表格（行 950-960）

**Step 1: 在剪映职责表格中增加新行**

在现有表格（行 950-960）的"封面帧"行之后增加：

```
| AI空镜后处理 | 降饱和度20-30% + 胶片颗粒15-25% + 暗角（仅 atmosphere_shots） |
| 字幕位置 | 放在画面高度 25%-70%，避开底部 UI（见 9.4.2） |
| 文字叠加 | 白字无阴影无动画硬切（见 9.4.3） |
```

**Step 2: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): update §9.4 editing tasks table with post-processing, safe zone, text style"
```

---

### Task 7: 更新修订记录 + 全文验证

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md` 修订记录（文件末尾）

**Step 1: 添加修订记录**

在修订记录表末尾添加：

```
| 2026-04-29 | 4.2 | 视觉升级（海外技术研究）：新增§7.5.1 AI空镜后处理管线（颗粒+降饱和+暗角，仅atmosphere_shots）、§9.4.1混剪呼吸式节奏表（精确到秒）、§9.4.2字幕安全区规则（MUST，抖音/小红书平台安全区）、§9.4.3文字叠加样式（MUST，极简白字硬切）、§9.4剪映职责表新增3项 |
```

**Step 2: 全文验证**

搜索残留问题：
```bash
grep -n "v4\.0" docs/content/workflow/video-production-spec.md
grep -n "2026-04-28" docs/content/workflow/video-production-spec.md
```

只有修订记录中应出现 v4.0 和 2026-04-28。文件头应显示 v4.2 和 2026-04-29。

**Step 3: 最终 Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs(spec): v4.2 — visual upgrade based on overseas research (post-processing, rhythm, safe zones, text style)"
