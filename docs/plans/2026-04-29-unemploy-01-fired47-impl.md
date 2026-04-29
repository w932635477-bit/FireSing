# 失业系列第一条视频实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 制作失业系列第一条完整视频 `unemploy-01-fired47`，从 Playwright HTML 模板到最终剪映素材包。

**Architecture:** 7 个 Stage 按顺序执行。Stage 0 创建 6 个 Playwright HTML 模板，Stage 0.5 渲染截图，Stage 1 编写 config JSON，Stage 1.5 文案评估，Stage 2-4 生成素材（空镜+视频+配音）。剪映混剪由用户手动完成。

**Tech Stack:** Playwright (Python) + Seedream 4.5 API + Kling 3.0 API + Gemini TTS + JSON config

---

### Task 1: 创建 tpl-boss-search.html（Boss直聘搜索结果）

**Files:**
- Create: `docs/content/templates/tpl-boss-search.html`

**Step 1: 创建 HTML 模板**

模拟 Boss 直聘搜索结果页面。黑色顶部导航栏 + 搜索栏 + 多个职位卡片，每张卡片显示职位名、公司名、薪资、"已读"红色标签。数据通过 JS 变量注入，截图时替换。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #f5f5f5; width: 1080px; height: 1920px; overflow: hidden; }
.header { background: #202020; padding: 40px 30px 20px; }
.search-bar { background: #333; border-radius: 20px; padding: 16px 24px; color: #fff; font-size: 28px; display: flex; align-items: center; gap: 12px; }
.search-icon { color: #999; font-size: 24px; }
.search-text { color: #fff; }
.filter-tags { display: flex; gap: 12px; padding: 16px 30px; background: #fff; }
.tag { background: #f0f0f0; color: #666; padding: 8px 20px; border-radius: 16px; font-size: 22px; }
.tag.active { background: #e8f5e9; color: #00b38a; }
.results-info { padding: 16px 30px; color: #999; font-size: 22px; background: #fff; border-bottom: 1px solid #eee; }
.job-list { padding: 0 30px; }
.job-card { background: #fff; border-radius: 16px; padding: 24px; margin-bottom: 12px; border: 1px solid #f0f0f0; }
.job-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.job-title { font-size: 28px; font-weight: 600; color: #222; }
.salary { font-size: 26px; color: #ff6633; font-weight: 600; }
.company-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.company-name { font-size: 24px; color: #666; }
.company-tag { font-size: 20px; color: #999; background: #f5f5f5; padding: 4px 10px; border-radius: 8px; }
.tags-row { display: flex; gap: 8px; flex-wrap: wrap; }
.job-tag { font-size: 20px; color: #00b38a; background: #e8f5e9; padding: 4px 12px; border-radius: 8px; }
.status-row { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.read-status { font-size: 22px; color: #ff4444; font-weight: 500; }
.time-ago { font-size: 20px; color: #ccc; }
</style>
</head>
<body>
<div class="header">
  <div class="search-bar">
    <span class="search-icon">&#128269;</span>
    <span class="search-text" id="search-keyword">运营总监</span>
  </div>
</div>
<div class="filter-tags">
  <span class="tag active">不限经验</span>
  <span class="tag">本科</span>
  <span class="tag">15-25K</span>
  <span class="tag">上市公司</span>
</div>
<div class="results-info" id="results-info">为你推荐 15 个职位</div>
<div class="job-list" id="job-list"></div>
<script>
const jobs = [
  {title:"运营总监",company:"某互联网大厂",tag:"已上市",salary:"25-40K",status:"已读",time:"3天前"},
  {title:"运营总监",company:"某跨境电商",tag:"C轮",salary:"20-35K",status:"已读",time:"5天前"},
  {title:"高级运营经理",company:"某教育科技",tag:"B轮",salary:"18-30K",status:"已读",time:"1周前"},
  {title:"运营总监",company:"某新能源",tag:"A轮",salary:"22-38K",status:"已读",time:"2周前"},
  {title:"运营负责人",company:"某消费品牌",tag:"已上市",salary:"30-50K",status:"已读",time:"3周前"},
  {title:"运营总监",company:"某医疗健康",tag:"B轮",salary:"20-35K",status:"已读",time:"1月前"},
];
const list = document.getElementById("job-list");
jobs.forEach(j => {
  list.innerHTML += `<div class="job-card"><div class="job-title-row"><span class="job-title">${j.title}</span><span class="salary">${j.salary}</span></div><div class="company-row"><span class="company-name">${j.company}</span><span class="company-tag">${j.tag}</span></div><div class="tags-row"><span class="job-tag">Boss活跃</span></div><div class="status-row"><span class="read-status">${j.status}不回</span><span class="time-ago">${j.time}</span></div></div>`;
});
</script>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-boss-search.html
git commit -m "feat(templates): add Boss zhipin search result template"
```

---

### Task 2: 创建 tpl-dingtalk-leave.html（钉钉退群通知）

**Files:**
- Create: `docs/content/templates/tpl-dingtalk-leave.html`

**Step 1: 创建 HTML 模板**

模拟钉钉系统通知。灰色系统消息，显示"您已被管理员移出群聊"。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #ededed; width: 1080px; height: 1920px; overflow: hidden; }
.header { background: #2f88ff; padding: 40px 30px 20px; display: flex; align-items: center; color: #fff; }
.back { font-size: 32px; margin-right: 16px; }
.title { font-size: 32px; font-weight: 600; }
.chat-area { padding: 30px; display: flex; flex-direction: column; gap: 16px; min-height: 800px; }
.system-msg { text-align: center; color: #999; font-size: 24px; padding: 12px 0; }
.system-msg-box { background: #fff; border-radius: 16px; padding: 20px 24px; display: inline-block; margin: 0 auto; color: #999; font-size: 24px; }
.gray-system { background: rgba(0,0,0,0.05); border-radius: 12px; padding: 16px 20px; text-align: center; color: #999; font-size: 26px; }
.time-divider { text-align: center; color: #bbb; font-size: 22px; padding: 20px 0; }
</style>
</head>
<body>
<div class="header">
  <span class="back">&lt;</span>
  <span class="title">公司全员群 (386)</span>
</div>
<div class="chat-area">
  <div class="time-divider">昨天 14:32</div>
  <div class="gray-system">张*理 修改了群名称</div>
  <div class="time-divider">昨天 16:15</div>
  <div class="gray-system">王*华 退出了群聊</div>
  <div class="time-divider">今天 09:23</div>
  <div class="system-msg"><div class="system-msg-box">您已被管理员移出群聊<br><span style="font-size:20px;color:#bbb">群主已将你移除，你无法查看群内消息</span></div></div>
  <div class="time-divider">今天 09:23</div>
  <div class="gray-system">你已退出群聊</div>
</div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-dingtalk-leave.html
git commit -m "feat(templates): add DingTalk group removal notification template"
```

---

### Task 3: 创建 tpl-resume-stats.html（简历数据面板）

**Files:**
- Create: `docs/content/templates/tpl-resume-stats.html`

**Step 1: 创建 HTML 模板**

模拟求职数据统计面板。大数字 + 进度条，显示投递/已读/回复/面试。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" width="1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #fafafa; width: 1080px; height: 1920px; overflow: hidden; }
.header { background: #fff; padding: 40px 30px 20px; border-bottom: 1px solid #eee; }
.page-title { font-size: 32px; font-weight: 600; color: #222; }
.page-subtitle { font-size: 24px; color: #999; margin-top: 8px; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 30px; }
.stat-card { background: #fff; border-radius: 16px; padding: 30px; text-align: center; }
.stat-number { font-size: 72px; font-weight: 700; }
.stat-label { font-size: 24px; color: #999; margin-top: 8px; }
.stat-card.total .stat-number { color: #222; }
.stat-card.read .stat-number { color: #2f88ff; }
.stat-card.reply .stat-number { color: #ff9800; }
.stat-card.interview .stat-number { color: #ff4444; }
.progress-section { background: #fff; border-radius: 16px; padding: 30px; margin: 0 30px 20px; }
.progress-title { font-size: 28px; font-weight: 600; color: #222; margin-bottom: 20px; }
.progress-item { margin-bottom: 20px; }
.progress-label { display: flex; justify-content: space-between; font-size: 24px; color: #666; margin-bottom: 8px; }
.progress-bar { height: 16px; background: #f0f0f0; border-radius: 8px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 8px; }
.fill-blue { background: #2f88ff; }
.fill-orange { background: #ff9800; }
.fill-red { background: #ff4444; }
.summary { padding: 30px; text-align: center; }
.summary-text { font-size: 26px; color: #999; line-height: 1.6; }
.summary-highlight { color: #ff4444; font-weight: 600; }
</style>
</head>
<body>
<div class="header">
  <div class="page-title">求职数据</div>
  <div class="page-subtitle">2024.03 - 2024.06</div>
</div>
<div class="stats-grid">
  <div class="stat-card total"><div class="stat-number">200</div><div class="stat-label">投递总数</div></div>
  <div class="stat-card read"><div class="stat-number">180</div><div class="stat-label">已读</div></div>
  <div class="stat-card reply"><div class="stat-number">3</div><div class="stat-label">回复</div></div>
  <div class="stat-card interview"><div class="stat-number">0</div><div class="stat-label">面试</div></div>
</div>
<div class="progress-section">
  <div class="progress-title">转化漏斗</div>
  <div class="progress-item">
    <div class="progress-label"><span>已读率</span><span>90%</span></div>
    <div class="progress-bar"><div class="progress-fill fill-blue" style="width:90%"></div></div>
  </div>
  <div class="progress-item">
    <div class="progress-label"><span>回复率</span><span>1.5%</span></div>
    <div class="progress-bar"><div class="progress-fill fill-orange" style="width:1.5%"></div></div>
  </div>
  <div class="progress-item">
    <div class="progress-label"><span>面试率</span><span>0%</span></div>
    <div class="progress-bar"><div class="progress-fill fill-red" style="width:0.5%"></div></div>
  </div>
</div>
<div class="summary">
  <div class="summary-text">投了 <span class="summary-highlight">200</span> 份简历<br>面试次数 <span class="summary-highlight">0</span></div>
</div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-resume-stats.html
git commit -m "feat(templates): add resume stats dashboard template"
```

---

### Task 4: 创建 tpl-wechat-reject.html（微信HR拒绝聊天）

**Files:**
- Create: `docs/content/templates/tpl-wechat-reject.html`

**Step 1: 创建 HTML 模板**

模拟微信聊天界面，HR 发来拒绝消息。绿色气泡（对方）+ 白色气泡（我方）。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #ededed; width: 1080px; height: 1920px; overflow: hidden; }
.header { background: #ededed; padding: 40px 30px 16px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #d9d9d9; }
.header-title { font-size: 32px; font-weight: 600; color: #222; }
.chat-area { padding: 30px; display: flex; flex-direction: column; gap: 24px; }
.time-divider { text-align: center; color: #999; font-size: 22px; padding: 16px 0; }
.msg-row { display: flex; align-items: flex-start; gap: 12px; }
.msg-row.other { flex-direction: row; }
.msg-row.me { flex-direction: row-reverse; }
.avatar { width: 64px; height: 64px; border-radius: 8px; background: #ccc; flex-shrink: 0; }
.bubble { max-width: 680px; padding: 20px 24px; border-radius: 12px; font-size: 28px; line-height: 1.6; position: relative; }
.bubble.other { background: #fff; color: #222; }
.bubble.me { background: #95ec69; color: #222; }
</style>
</head>
<body>
<div class="header">
  <span class="header-title">HR-Lisa</span>
</div>
<div class="chat-area">
  <div class="time-divider">昨天 10:23</div>
  <div class="msg-row me">
    <div class="avatar" style="background:#b0c4de"></div>
    <div class="bubble me">您好，上周面试的结果出来了吗？</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#ffb6c1"></div>
    <div class="bubble other">不好意思让你久等了</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#ffb6c1"></div>
    <div class="bubble other">面试官反馈挺好的</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#ffb6c1"></div>
    <div class="bubble other">但是这个岗位要求35岁以下</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#ffb6c1"></div>
    <div class="bubble other">年龄不太符合我们的要求</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#ffb6c1"></div>
    <div class="bubble other">建议关注我们其他岗位 祝好</div>
  </div>
  <div class="time-divider">昨天 10:25</div>
</div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-wechat-reject.html
git commit -m "feat(templates): add WeChat HR rejection chat template"
```

---

### Task 5: 创建 tpl-wechat-positive.html（微信正面消息）

**Files:**
- Create: `docs/content/templates/tpl-wechat-positive.html`

**Step 1: 创建 HTML 模板**

模拟微信聊天界面，老客户发来正面认可消息。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #ededed; width: 1080px; height: 1920px; overflow: hidden; }
.header { background: #ededed; padding: 40px 30px 16px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #d9d9d9; }
.header-title { font-size: 32px; font-weight: 600; color: #222; }
.chat-area { padding: 30px; display: flex; flex-direction: column; gap: 24px; }
.time-divider { text-align: center; color: #999; font-size: 22px; padding: 16px 0; }
.msg-row { display: flex; align-items: flex-start; gap: 12px; }
.msg-row.other { flex-direction: row; }
.msg-row.me { flex-direction: row-reverse; }
.avatar { width: 64px; height: 64px; border-radius: 8px; background: #ccc; flex-shrink: 0; }
.bubble { max-width: 680px; padding: 20px 24px; border-radius: 12px; font-size: 28px; line-height: 1.6; }
.bubble.other { background: #fff; color: #222; }
.bubble.me { background: #95ec69; color: #222; }
</style>
</head>
<body>
<div class="header">
  <span class="header-title">王总-XX集团</span>
</div>
<div class="chat-area">
  <div class="time-divider">今天 19:42</div>
  <div class="msg-row other">
    <div class="avatar" style="background:#deb887"></div>
    <div class="bubble other">老陈，上次那个项目二期怎么跟进？</div>
  </div>
  <div class="msg-row me">
    <div class="avatar" style="background:#b0c4de"></div>
    <div class="bubble me">王总，我已经不在公司了</div>
  </div>
  <div class="msg-row me">
    <div class="avatar" style="background:#b0c4de"></div>
    <div class="bubble me">上个月走的</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#deb887"></div>
    <div class="bubble other">？？？</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#deb887"></div>
    <div class="bubble other">那项目还得有人跟啊</div>
  </div>
  <div class="msg-row other">
    <div class="avatar" style="background:#deb887"></div>
    <div class="bubble other">我找的是你，不是你们公司</div>
  </div>
</div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-wechat-positive.html
git commit -m "feat(templates): add WeChat positive client message template"
```

---

### Task 6: 创建 tpl-douyin-comment.html（抖音评论区）

**Files:**
- Create: `docs/content/templates/tpl-douyin-comment.html`

**Step 1: 创建 HTML 模板**

模拟抖音评论区。半透明背景 + 评论列表 + 点赞数。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: rgba(0,0,0,0.85); width: 1080px; height: 1920px; overflow: hidden; }
.comment-panel { position: absolute; bottom: 0; left: 0; right: 0; background: #1a1a1a; border-radius: 24px 24px 0 0; padding: 30px; max-height: 1200px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.panel-title { font-size: 28px; color: #fff; font-weight: 600; }
.panel-count { font-size: 24px; color: #999; }
.comment-list { display: flex; flex-direction: column; gap: 28px; }
.comment-item { display: flex; gap: 16px; }
.comment-avatar { width: 56px; height: 56px; border-radius: 50%; flex-shrink: 0; }
.comment-body { flex: 1; }
.comment-user { font-size: 22px; color: #999; margin-bottom: 6px; }
.comment-text { font-size: 28px; color: #fff; line-height: 1.5; }
.comment-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.comment-time { font-size: 20px; color: #666; }
.comment-like { display: flex; align-items: center; gap: 6px; color: #666; font-size: 22px; }
.comment-like-icon { font-size: 20px; }
</style>
</head>
<body>
<div class="comment-panel">
  <div class="panel-header">
    <span class="panel-title">评论</span>
    <span class="panel-count">128条评论</span>
  </div>
  <div class="comment-list">
    <div class="comment-item">
      <div class="comment-avatar" style="background:#e9967a"></div>
      <div class="comment-body">
        <div class="comment-user">加油的小李</div>
        <div class="comment-text">投了300份了，已读不回290份</div>
        <div class="comment-meta"><span class="comment-time">2小时前</span><span class="comment-like">&#9825; 2.3w</span></div>
      </div>
    </div>
    <div class="comment-item">
      <div class="comment-avatar" style="background:#87ceeb"></div>
      <div class="comment-body">
        <div class="comment-user">第五个月了</div>
        <div class="comment-text">第五个月了，已经开始怀疑人生</div>
        <div class="comment-meta"><span class="comment-time">3小时前</span><span class="comment-like">&#9825; 1.8w</span></div>
      </div>
    </div>
    <div class="comment-item">
      <div class="comment-avatar" style="background:#dda0dd"></div>
      <div class="comment-body">
        <div class="comment-user">38岁的老王</div>
        <div class="comment-text">38岁被裁，投了两个月一个面试都没有</div>
        <div class="comment-meta"><span class="comment-time">5小时前</span><span class="comment-like">&#9825; 9876</span></div>
      </div>
    </div>
    <div class="comment-item">
      <div class="comment-avatar" style="background:#90ee90"></div>
      <div class="comment-body">
        <div class="comment-user">前外企人</div>
        <div class="comment-text">外企15年出来发现什么都不值钱了</div>
        <div class="comment-meta"><span class="comment-time">6小时前</span><span class="comment-like">&#9825; 5621</span></div>
      </div>
    </div>
    <div class="comment-item">
      <div class="comment-avatar" style="background:#f0e68c"></div>
      <div class="comment-body">
        <div class="comment-user">新的一天</div>
        <div class="comment-text">每天醒来最怕的就是打开Boss直聘</div>
        <div class="comment-meta"><span class="comment-time">8小时前</span><span class="comment-like">&#9825; 3421</span></div>
      </div>
    </div>
  </div>
</div>
</body>
</html>
```

**Step 2: Commit**

```bash
git add docs/content/templates/tpl-douyin-comment.html
git commit -m "feat(templates): add Douyin comment section template"
```

---

### Task 7: 创建截图渲染脚本 screenshot-renderer.py

**Files:**
- Create: `docs/content/scripts/screenshot-renderer.py`

**Step 1: 创建 Playwright 截图渲染脚本**

读取 templates 目录下的 HTML 文件，用 Playwright 渲染为 1080x1920 PNG。

```python
#!/usr/bin/env python3
"""
Render HTML templates to 1080x1920 PNG screenshots using Playwright.

Usage:
  python3 screenshot-renderer.py --template tpl-boss-search --output ../output/unemploy-01-fired47/SS01-boss-search.png
  python3 screenshot-renderer.py --all --output-dir ../output/unemploy-01-fired47
"""

import argparse
import sys
import time
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def render_template(template_name: str, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    html_path = TEMPLATE_DIR / f"{template_name}.html"
    if not html_path.exists():
        print(f"ERROR: template not found: {html_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(html_path.as_uri())
        time.sleep(0.5)
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()

    print(f"OK: {output_path} ({output_path.stat().st_size // 1024}KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render HTML templates to PNG")
    parser.add_argument("--template", type=str, help="Template name (without .html)")
    parser.add_argument("--output", type=str, help="Output PNG path")
    parser.add_argument("--all", action="store_true", help="Render all templates")
    parser.add_argument("--output-dir", type=str, help="Output directory for --all")
    args = parser.parse_args()

    if args.all:
        out_dir = Path(args.output_dir) if args.output_dir else Path(".")
        out_dir.mkdir(parents=True, exist_ok=True)
        for html_file in sorted(TEMPLATE_DIR.glob("*.html")):
            name = html_file.stem
            render_template(name, out_dir / f"{name}.png")
    elif args.template and args.output:
        render_template(args.template, Path(args.output))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add docs/content/scripts/screenshot-renderer.py
git commit -m "feat(scripts): add Playwright screenshot renderer for HTML templates"
```

---

### Task 8: 渲染 6 张 UI 截图

**Files:**
- Create: `docs/content/output/unemploy-01-fired47/SS01-boss-search.png`
- Create: `docs/content/output/unemploy-01-fired47/SS02-dingtalk-leave.png`
- Create: `docs/content/output/unemploy-01-fired47/SS03-resume-stats.png`
- Create: `docs/content/output/unemploy-01-fired47/SS04-wechat-reject.png`
- Create: `docs/content/output/unemploy-01-fired47/SS05-wechat-positive.png`
- Create: `docs/content/output/unemploy-01-fired47/SS06-douyin-comment.png`

**Step 1: 运行截图渲染**

```bash
cd docs/content/scripts
python3 screenshot-renderer.py --all --output-dir ../output/unemploy-01-fired47
```

Expected: 6 个 PNG 文件，每个 1080x1920。

**Step 2: 验证截图**

```bash
ls -la ../output/unemploy-01-fired47/SS*.png
```

Expected: 6 个文件，每个 50-200KB。

**Step 3: Commit**

```bash
git add docs/content/output/unemploy-01-fired47/
git commit -m "feat: render 6 UI screenshots for unemploy-01-fired47"
```

---

### Task 9: 编写完整 config JSON

**Files:**
- Create: `docs/content/config/unemploy-01-fired47.json`

**Step 1: 创建 config JSON**

包含 6 个 segments + 3 个 atmosphere_shots + screenshots 引用。无 character_anchor。

```json
{
  "video_id": "unemploy-01-fired47",
  "version": "2.0",
  "created": "2026-04-29",
  "status": "script_approved",
  "strategy": "unemployment-corecore",
  "strategy_notes": "失业系列第1条：被裁第47天赚5000。SPR-L结构，纯共鸣不提产品。Corecore蒙太奇：Playwright截图+Seedream空镜，无杨梦角色。",
  "global": {
    "target_duration_sec": 75,
    "max_duration_sec": 120,
    "min_duration_sec": 60,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "workflow_version": "2.0",
    "style": "corecore_montage",
    "color_temperature": "cool_to_warm_shift",
    "accent_color": "#ffffff"
  },
  "script": {
    "topic": "38岁外企人被裁47天后靠翻通讯录赚到第一个5000块",
    "hook_type": "preemptive_highlight",
    "cta_action": "评论",
    "cta_keyword": "你投了多少份",
    "anti_ad_measures": [
      "不提AI Agent、代运营、智能体等业务关键词",
      "不引导私信、领取、关注",
      "CTA用开放式问题，激发评论互动",
      "聚焦失业者的真实故事和情绪，不卖任何东西",
      "避免出现'工具''方案''服务'等营销词汇"
    ]
  },
  "character_anchor": null,
  "screenshots": [
    {
      "id": "SS01",
      "template": "tpl-boss-search",
      "output_file": "unemploy-01-fired47/SS01-boss-search.png",
      "segment": "S01"
    },
    {
      "id": "SS02",
      "template": "tpl-dingtalk-leave",
      "output_file": "unemploy-01-fired47/SS02-dingtalk-leave.png",
      "segment": "S02"
    },
    {
      "id": "SS03",
      "template": "tpl-resume-stats",
      "output_file": "unemploy-01-fired47/SS03-resume-stats.png",
      "segment": "S03"
    },
    {
      "id": "SS04",
      "template": "tpl-wechat-reject",
      "output_file": "unemploy-01-fired47/SS04-wechat-reject.png",
      "segment": "S03"
    },
    {
      "id": "SS05",
      "template": "tpl-wechat-positive",
      "output_file": "unemploy-01-fired47/SS05-wechat-positive.png",
      "segment": "S04"
    },
    {
      "id": "SS06",
      "template": "tpl-douyin-comment",
      "output_file": "unemploy-01-fired47/SS06-douyin-comment.png",
      "segment": "S06"
    }
  ],
  "atmosphere_shots": [
    {
      "id": "AT01",
      "scene": "凌晨台灯下的简历",
      "reference_prompt": "iPhone 15 snapshot, a desk lamp illuminating a printed resume on a wooden desk, 2am ambient warm light, coffee ring stain on paper, no people visible, no text visible, casual framing slightly off-center, untouched, vertical 9:16",
      "motion_prompt": "slow subtle flicker of desk lamp light, slight camera drift",
      "output_file": "unemploy-01-fired47/AT01-lamp-resume.png",
      "video_file": "unemploy-01-fired47/AT01-lamp-resume.mp4",
      "segment": "S02"
    },
    {
      "id": "AT02",
      "scene": "空荡办公区",
      "reference_prompt": "iPhone 15 snapshot, empty open-plan office at night, fluorescent ceiling lights casting harsh shadows on vacant desks, one desk still has a potted plant and a coffee mug, no people visible, no text, untouched, vertical 9:16",
      "motion_prompt": "slow pan across empty desks, fluorescent light buzzes slightly",
      "output_file": "unemploy-01-fired47/AT02-empty-office.png",
      "video_file": "unemploy-01-fired47/AT02-empty-office.mp4",
      "segment": "S03"
    },
    {
      "id": "AT03",
      "scene": "暖光通讯录",
      "reference_prompt": "iPhone 15 snapshot, warm ambient light from a phone screen illuminating a dark room, the screen shows a contacts list with many entries, cozy atmosphere, no people visible, no text readable, casual framing, untouched, vertical 9:16",
      "motion_prompt": "phone screen gently glows brighter then settles, subtle warmth shift",
      "output_file": "unemploy-01-fired47/AT03-contacts-glow.png",
      "video_file": "unemploy-01-fired47/AT03-contacts-glow.mp4",
      "segment": "S04"
    }
  ],
  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 4,
      "emotion_arc": "好奇",
      "subtitle_text": "被裁47天 赚了5000",
      "voiceover_text": "被裁第47天，我赚到了第一个5000块。不是靠投简历。是靠翻通讯录。",
      "voiceover_pause_markers": "被裁第47天<#0.3#>我赚到了第一个5000块。<#0.5#>不是靠投简历。<#0.3#>是靠翻通讯录。"
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 12,
      "emotion_arc": "代入",
      "subtitle_text": "38岁 外企15年 一通电话全没了",
      "voiceover_text": "38岁，外企15年。一通电话，全没了。HR说\"公司战略调整\"，翻译过来就是——你太贵了。",
      "voiceover_pause_markers": "38岁<#0.2#>外企15年。<#0.5#>一通电话<#0.3#>全没了。<#0.8#>HR说\"公司战略调整\"<#0.3#>翻译过来就是——<#0.5#>你太贵了。",
      "story_images": [
        {
          "id": "S02-01",
          "trigger_text": "凌晨台灯下的简历",
          "reference_file": "unemploy-01-fired47/AT01-lamp-resume.png",
          "reference_prompt": "iPhone 15 snapshot, a desk lamp illuminating a printed resume on a wooden desk, 2am ambient warm light, coffee ring stain on paper, no people visible, no text visible, casual framing slightly off-center, untouched, vertical 9:16",
          "motion_prompt": "slow subtle flicker of desk lamp light, slight camera drift"
        }
      ]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 24,
      "emotion_arc": "共鸣",
      "subtitle_text": "40份简历 0回复",
      "voiceover_text": "第一个星期，投了40份简历。回复0。第二个星期，降薪30%。回复0。第三个星期，连降薪都不敢写了。房贷每月1万2，孩子幼儿园5000，我妈的降压药不能停。那段时间每天最怕的就是早上醒来——因为醒来就要面对一天。",
      "voiceover_pause_markers": "第一个星期<#0.2#>投了40份简历。<#0.3#>回复0。<#0.8#>第二个星期<#0.2#>降薪30%。<#0.3#>回复0。<#0.8#>第三个星期<#0.2#>连降薪都不敢写了。<#0.5#>房贷每月1万2<#0.2#>孩子幼儿园5000<#0.2#>我妈的降压药不能停。<#1.0#>那段时间每天最怕的就是早上醒来——<#0.5#>因为醒来就要面对一天。",
      "story_images": [
        {
          "id": "S03-01",
          "trigger_text": "空荡办公区",
          "reference_file": "unemploy-01-fired47/AT02-empty-office.png",
          "reference_prompt": "iPhone 15 snapshot, empty open-plan office at night, fluorescent ceiling lights casting harsh shadows on vacant desks, one desk still has a potted plant and a coffee mug, no people visible, no text, untouched, vertical 9:16",
          "motion_prompt": "slow pan across empty desks, fluorescent light buzzes slightly"
        }
      ]
    },
    {
      "id": "S04",
      "type": "body",
      "duration_sec": 15,
      "emotion_arc": "希望",
      "subtitle_text": "我找的是你 不是你们公司",
      "voiceover_text": "有天老客户打电话问我那个项目怎么跟进。我说我已经不在了。他说了一句话：\"我找的是你，不是你们公司。\"那天晚上我翻了翻通讯录，200个客户关系。原来这些东西，一直都在。只是以前绑在公司身上。",
      "voiceover_pause_markers": "有天老客户打电话问我那个项目怎么跟进。<#0.5#>我说我已经不在了。<#0.8#>他说了一句话：<#0.3#>\"我找的是你，不是你们公司。\"<#1.0#>那天晚上我翻了翻通讯录<#0.3#>200个客户关系。<#0.5#>原来这些东西<#0.2#>一直都在。<#0.3#>只是以前绑在公司身上。",
      "story_images": [
        {
          "id": "S04-01",
          "trigger_text": "暖光通讯录",
          "reference_file": "unemploy-01-fired47/AT03-contacts-glow.png",
          "reference_prompt": "iPhone 15 snapshot, warm ambient light from a phone screen illuminating a dark room, the screen shows a contacts list with many entries, cozy atmosphere, no people visible, no text readable, casual framing, untouched, vertical 9:16",
          "motion_prompt": "phone screen gently glows brighter then settles, subtle warmth shift"
        }
      ]
    },
    {
      "id": "S05",
      "type": "body",
      "duration_sec": 15,
      "emotion_arc": "力量",
      "subtitle_text": "你身上的东西比你以为的多",
      "voiceover_text": "你身上有多少值钱的东西，你自己都没看到？你的经验，你的人脉，你的行业嗅觉——这些不会因为一通电话就消失。"
    },
    {
      "id": "S06",
      "type": "cta",
      "duration_sec": 5,
      "emotion_arc": "参与",
      "subtitle_text": "你投了多少份了？",
      "voiceover_text": "你投了多少份简历了？评论区说说。"
    }
  ]
}
```

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-01-fired47.json
git commit -m "feat(config): add unemploy-01-fired47 video config (SPR-L, 6 segments, 3 atmosphere shots)"
```

---

### Task 10: 文案评估（Stage 1.5）

**Step 1: 运行独立评估**

读取 config JSON 中的 segments 脚本，按 Spec §5.9 评估维度打分。用独立 agent 盲评。

评估维度（100分制）：
- 情绪真实度 (25分)
- 代入感 (20分)
- 转念可信度 (20分)
- 钩子密度 (15分)
- 结构完整性 (10分)
- 禁止项检查 (10分)

≥90 分通过。不通过则修改脚本后重新评估。

**Step 2: 通过后将评估结果写入 config JSON 的 `review` 字段并 commit**

```bash
git add docs/content/config/unemploy-01-fired47.json
git commit -m "docs(config): add Stage 1.5 script review score for unemploy-01-fired47"
```

---

### Task 11: Seedream 生成 3 张空镜（Stage 2）

**Step 1: 运行 Seedream 批量生成**

```bash
source docs/content/.env
cd docs/content/scripts
python3 seedream-story-images.py --config config/unemploy-01-fired47.json
```

Expected: 3 张 PNG 文件输出到 `docs/content/assets/references/unemploy-01-fired47/`。

**Step 2: 验证输出**

```bash
ls -la docs/content/assets/references/unemploy-01-fired47/
```

Expected: AT01-lamp-resume.png, AT02-empty-office.png, AT03-contacts-glow.png。

**Step 3: Commit**

```bash
git add docs/content/assets/references/unemploy-01-fired47/
git commit -m "feat: generate 3 Seedream atmosphere shots for unemploy-01-fired47"
```

---

### Task 12: Kling 空镜转视频（Stage 3）

**Step 1: 运行 Kling 批量生成**

```bash
source docs/content/.env
cd docs/content/scripts
python3 kling-gen-batch.py --config config/unemploy-01-fired47.json --include-stories
```

Expected: 3 个 MP4 文件输出到 `docs/content/output/unemploy-01-fired47/`。

**Step 2: 验证输出**

```bash
ls -la docs/content/output/unemploy-01-fired47/AT*.mp4
```

Expected: 3 个 MP4 文件，每个约 5 秒。

**Step 3: Commit**

```bash
git add docs/content/output/unemploy-01-fired47/
git commit -m "feat: generate 3 Kling atmosphere videos for unemploy-01-fired47"
```

---

### Task 13: Gemini TTS 配音（Stage 4）

**Step 1: 运行 Gemini TTS 生成**

```bash
source docs/content/.env
cd docs/content/scripts
python3 gemini-tts-batch.py --config config/unemploy-01-fired47.json --voice Aoede
```

Expected: 每段 MP3 + 完整旁白 MP3 + SRT 字幕文件输出到 `docs/content/assets/voiceover/unemploy-01-fired47/`。

**Step 2: 验证输出**

```bash
ls -la docs/content/assets/voiceover/unemploy-01-fired47/
```

Expected: S01.mp3 ~ S06.mp3 + full.mp3 + subtitles.srt。

**Step 3: 检查时长**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 docs/content/assets/voiceover/unemploy-01-fired47/full.mp3
```

Expected: 60-90 秒之间。

**Step 4: Commit**

```bash
git add docs/content/assets/voiceover/unemploy-01-fired47/
git commit -m "feat: generate Gemini TTS Aoede voiceover for unemploy-01-fired47"
```

---

### Task 14: 素材打包 + 交付清单

**Step 1: 创建素材目录清单**

列出所有生成的素材文件，供剪映混剪使用：

```bash
echo "=== UI截图 ===" && ls docs/content/output/unemploy-01-fired47/SS*.png
echo "=== 空镜视频 ===" && ls docs/content/output/unemploy-01-fired47/AT*.mp4
echo "=== 配音 ===" && ls docs/content/assets/voiceover/unemploy-01-fired47/*.mp3
echo "=== 字幕 ===" && ls docs/content/assets/voiceover/unemploy-01-fired47/*.srt
```

**Step 2: 交付给剪映**

用户在剪映中按 §9.4.1 节奏表混剪：
- S01: SS01 快切 0.5s/张
- S02: SS02 + AT01 交替 2-3s
- S03: SS03 + SS04 + AT02 呼吸式节奏
- S04: AT03 → SS05 放慢 3-4s
- S05: AT03 延续 4-6s
- S06: SS06 收尾 2s

字幕按 §9.4.2 安全区（25%-70%），白字硬切按 §9.4.3。

**Step 3: 更新 config status**

```json
"status": "materials_ready_for_editing"
```

```bash
git add docs/content/config/unemploy-01-fired47.json
git commit -m "docs(config): update unemploy-01-fired47 status to materials_ready"
```
