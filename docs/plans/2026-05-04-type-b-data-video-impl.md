# Type B 数据冲击视频 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a 45-55s data shock video "2026裁员最狠行业TOP5" using v3 workflow (Playwright data cards + Unsplash atmosphere + FFmpeg compose), zero cost.

**Architecture:** Config-driven v3 Medvi pipeline. A single JSON config (`unemploy-data-02-top5.json`) drives all stages: Playwright renders HTML data cards to PNG, Unsplash downloader fetches atmosphere photos, Gemini TTS generates Charon male voiceover, FFmpeg composes rough-cut with opening + clips + voiceover + BGM. Final polish in JianYing.

**Tech Stack:** Python 3, Playwright, Unsplash API, Gemini 3.1 Flash TTS, FFmpeg, JSON config

---

### Task 1: Create JSON config file

**Files:**
- Create: `docs/content/config/unemploy-data-02-top5.json`

**Step 1: Write config JSON**

```json
{
  "video_id": "unemploy-data-02-top5",
  "version": "3.0",
  "series": "unemploy-data",
  "workflow_mode": "unemploy",

  "global": {
    "target_duration_sec": 55,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon",
    "opening_file": "unemploy-story-opening-v1.mp4"
  },

  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "S01", "emotion": "shock", "text": "2026裁员最狠的5个行业，看到最后你会庆幸自己不在里面"},
      {"id": "S02", "emotion": "tension", "text": "第5名，教育培训。双减之后60万人失业，机构倒闭率超过70%。新东方一口气裁了6万人。"},
      {"id": "S03", "emotion": "tension", "text": "第4名，制造业。产业转移加自动化，沿海工厂一波接一波裁员，打工人的退路越来越窄。"},
      {"id": "S04", "emotion": "tension", "text": "第3名，新能源车。看着风光，产能已经严重过剩。头部车企裁员10%起步，供应商更惨。"},
      {"id": "S05", "emotion": "fear", "text": "第2名，房地产。三年寒冬没见底，百强房企裁员超过一半，上下游产业链全遭殃。"},
      {"id": "S06", "emotion": "shock", "text": "第1名，互联网。阿里一年砍了34%的人，百度裁了7%，而且现在流行静默裁员——不公开裁，逼你自己走，连赔偿金都省了。"},
      {"id": "S07", "emotion": "engagement", "text": "你在哪个行业？评论区说说，看看谁最难。关注我，下期告诉你被裁后怎么办。"}
    ]
  },

  "screenshots": [
    {"id": "SS01", "template": "tpl-top5-ranking", "output": "SS01-top5-ranking.png"},
    {"id": "SS02", "template": "tpl-layoff-data-edu", "output": "SS02-edu-60w.png"},
    {"id": "SS03", "template": "tpl-layoff-data-mfg", "output": "SS03-mfg.png"},
    {"id": "SS04", "template": "tpl-layoff-data-ev", "output": "SS04-ev-10pct.png"},
    {"id": "SS05", "template": "tpl-layoff-data-realestate", "output": "SS05-realestate.png"},
    {"id": "SS06", "template": "tpl-layoff-data-tech", "output": "SS06-tech-34pct.png"}
  ],

  "atmosphere": [
    {"id": "AT01", "query": "empty classroom school desks abandoned", "output": "AT01-empty-classroom.jpg"},
    {"id": "AT02", "query": "abandoned factory production line idle", "output": "AT02-idle-factory.jpg"},
    {"id": "AT03", "query": "car dealership showroom empty vehicles", "output": "AT03-empty-showroom.jpg"},
    {"id": "AT04", "query": "abandoned construction site unfinished buildings", "output": "AT04-unfinished-buildings.jpg"},
    {"id": "AT05", "query": "empty office desks night city lights", "output": "AT05-empty-office-night.jpg"},
    {"id": "AT06", "query": "late night office building windows illuminated", "output": "AT06-night-office.jpg"}
  ],

  "text_cards": [
    {"id": "TC01", "lines": ["2026裁员最狠", "5个行业"], "style": "medvi", "bg_image": "AT05-empty-office-night.jpg", "duration": 3.0},
    {"id": "TC02", "lines": ["第5名", "教育培训", "60万人失业"], "style": "medvi", "bg_image": "AT01-empty-classroom.jpg", "duration": 3.5},
    {"id": "TC03", "lines": ["第4名", "制造业", "沿海工厂裁员潮"], "style": "medvi", "bg_image": "AT02-idle-factory.jpg", "duration": 3.5},
    {"id": "TC04", "lines": ["第3名", "新能源车", "头部裁员10%+"], "style": "medvi", "bg_image": "AT03-empty-showroom.jpg", "duration": 3.5},
    {"id": "TC05", "lines": ["第2名", "房地产", "百强裁员超50%"], "style": "medvi", "bg_image": "AT04-unfinished-buildings.jpg", "duration": 3.5},
    {"id": "TC06", "lines": ["第1名", "互联网科技", "阿里裁员34%"], "style": "medvi", "bg_image": "AT06-night-office.jpg", "duration": 3.5},
    {"id": "TC07", "lines": ["你在哪个行业？", "评论区说说"], "style": "medvi", "bg_image": "AT05-empty-office-night.jpg", "duration": 4.0}
  ],

  "storyboard": [
    {
      "segment": "S01",
      "clips": [
        {"type": "text_card", "ref": "TC01", "duration": 3.0}
      ]
    },
    {
      "segment": "S02",
      "clips": [
        {"type": "screenshot", "ref": "SS02", "zoom": true, "pct": 0.5},
        {"type": "atmosphere", "ref": "AT01", "zoom": true, "pct": 0.5}
      ]
    },
    {
      "segment": "S03",
      "clips": [
        {"type": "screenshot", "ref": "SS03", "zoom": true, "pct": 0.5},
        {"type": "atmosphere", "ref": "AT02", "zoom": true, "pct": 0.5}
      ]
    },
    {
      "segment": "S04",
      "clips": [
        {"type": "screenshot", "ref": "SS04", "zoom": true, "pct": 0.5},
        {"type": "atmosphere", "ref": "AT03", "zoom": true, "pct": 0.5}
      ]
    },
    {
      "segment": "S05",
      "clips": [
        {"type": "screenshot", "ref": "SS05", "zoom": true, "pct": 0.5},
        {"type": "atmosphere", "ref": "AT04", "zoom": true, "pct": 0.5}
      ]
    },
    {
      "segment": "S06",
      "clips": [
        {"type": "screenshot", "ref": "SS06", "zoom": true, "pct": 0.5},
        {"type": "atmosphere", "ref": "AT06", "zoom": true, "pct": 0.5}
      ]
    },
    {
      "segment": "S07",
      "clips": [
        {"type": "atmosphere", "ref": "AT05", "zoom": true, "pct": 0.5},
        {"type": "text_card", "ref": "TC07", "duration": 4.0}
      ]
    }
  ],

  "bgm": {
    "file": "synth-pad-placeholder.mp3",
    "volume": 0.08,
    "fade_in": 2.0,
    "fade_out": 3.0
  },

  "upload_copy": {
    "platform": "douyin",
    "title_candidates": [
      "2026裁员最狠的5个行业，第1名裁掉了三分之一",
      "这5个行业正在疯狂裁员，你在里面吗",
      "2026裁员排行榜：第5名就开始心慌了"
    ],
    "tags": ["#裁员", "#失业", "#2026", "#行业分析", "#互联网", "#房地产", "#制造业", "#中年危机", "#求职", "#职场"],
    "comment_trigger": "互联网人集合了，你们公司今年裁了多少人？"
  }
}
```

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-data-02-top5.json
git commit -m "feat: add Type B data video config (2026 layoff TOP5)"
```

---

### Task 2: Create HTML data card templates

**Files:**
- Create: `docs/content/templates/tpl-top5-ranking.html` — TOP5 overview card
- Create: `docs/content/templates/tpl-layoff-data-edu.html` — Education data card
- Create: `docs/content/templates/tpl-layoff-data-mfg.html` — Manufacturing data card
- Create: `docs/content/templates/tpl-layoff-data-ev.html` — EV data card
- Create: `docs/content/templates/tpl-layoff-data-realestate.html` — Real estate data card
- Create: `docs/content/templates/tpl-layoff-data-tech.html` — Tech data card

**Step 1: Create tpl-top5-ranking.html**

Full 1080x1920 overview card. Dark background (#1a1a2e), countdown list 5→1, red highlight (#ff4444) on #1. Style matches existing `tpl-data-panel-1170w.html`.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 40px; }
.page-title { font-size: 56px; font-weight: 700; color: #ffffff; letter-spacing: 2px; }
.page-subtitle { font-size: 28px; color: #8888aa; margin-top: 16px; }
.ranking { padding: 20px 60px; }
.rank-row { display: flex; align-items: center; padding: 32px 40px; margin-bottom: 16px; background: #16213e; border-radius: 20px; border: 1px solid #1a2d50; }
.rank-row.top { background: #2a1020; border-color: #4a1530; }
.rank-num { font-size: 60px; font-weight: 800; width: 100px; flex-shrink: 0; color: #8888cc; }
.rank-row.top .rank-num { color: #ff4444; }
.rank-info { flex: 1; }
.rank-industry { font-size: 36px; font-weight: 600; color: #ffffff; }
.rank-data { font-size: 24px; color: #8888aa; margin-top: 6px; }
.rank-row.top .rank-data { color: #ff8888; }
</style>
</head>
<body>
<div class="header">
  <div class="page-title">2026 裁员最狠行业 TOP5</div>
  <div class="page-subtitle">数据来源：Rest of World / Metaintro</div>
</div>
<div class="ranking">
  <div class="rank-row">
    <div class="rank-num">5</div>
    <div class="rank-info">
      <div class="rank-industry">教育培训</div>
      <div class="rank-data">60万人失业 · 机构倒闭率超70%</div>
    </div>
  </div>
  <div class="rank-row">
    <div class="rank-num">4</div>
    <div class="rank-info">
      <div class="rank-industry">制造业</div>
      <div class="rank-data">产业转移+自动化 · 沿海裁员潮</div>
    </div>
  </div>
  <div class="rank-row">
    <div class="rank-num">3</div>
    <div class="rank-info">
      <div class="rank-industry">新能源汽车</div>
      <div class="rank-data">产能过剩 · 头部裁员10%+</div>
    </div>
  </div>
  <div class="rank-row">
    <div class="rank-num">2</div>
    <div class="rank-info">
      <div class="rank-industry">房地产</div>
      <div class="rank-data">三年寒冬 · 百强房企裁员超50%</div>
    </div>
  </div>
  <div class="rank-row top">
    <div class="rank-num">1</div>
    <div class="rank-info">
      <div class="rank-industry">互联网科技</div>
      <div class="rank-data">阿里裁员34% · 静默裁员成常态</div>
    </div>
  </div>
</div>
</body>
</html>
```

**Step 2: Create tpl-layoff-data-edu.html**

Education sector data card. Same dark theme. Large "60万" number, supporting details.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 30px; display: flex; align-items: center; gap: 20px; }
.rank-badge { font-size: 72px; font-weight: 800; color: #8888cc; }
.industry-name { font-size: 52px; font-weight: 700; color: #ffffff; }
.hero-stat { text-align: center; padding: 60px 60px 40px; }
.big-number { font-size: 180px; font-weight: 800; color: #ff4444; line-height: 1; }
.big-unit { font-size: 60px; color: #ff8888; margin-top: 10px; }
.detail-cards { padding: 20px 60px; display: flex; gap: 24px; }
.detail-card { flex: 1; background: #16213e; border-radius: 20px; padding: 40px 30px; text-align: center; border: 1px solid #1a2d50; }
.detail-label { font-size: 28px; color: #8888aa; margin-bottom: 16px; }
.detail-value { font-size: 56px; font-weight: 700; color: #ffffff; }
.detail-sub { font-size: 22px; color: #666688; margin-top: 10px; }
.footer-strip { position: absolute; bottom: 0; left: 0; right: 0; background: #16213e; padding: 40px 60px; border-top: 1px solid #1a2d50; }
.footer-text { font-size: 30px; color: #8888aa; line-height: 1.6; }
</style>
</head>
<body>
<div class="header">
  <div class="rank-badge">NO.5</div>
  <div class="industry-name">教育培训</div>
</div>
<div class="hero-stat">
  <div class="big-number">60万</div>
  <div class="big-unit">双减后失业人数</div>
</div>
<div class="detail-cards">
  <div class="detail-card">
    <div class="detail-label">机构倒闭率</div>
    <div class="detail-value">>70%</div>
    <div class="detail-sub">中小机构大面积关门</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">新东方裁员</div>
    <div class="detail-value">6万人</div>
    <div class="detail-sub">一刀切清退</div>
  </div>
</div>
<div class="footer-strip">
  <div class="footer-text">双减政策后，教培行业从巅峰跌入谷底</div>
</div>
</body>
</html>
```

**Step 3: Create tpl-layoff-data-mfg.html**

Manufacturing data card. Same layout structure.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 30px; display: flex; align-items: center; gap: 20px; }
.rank-badge { font-size: 72px; font-weight: 800; color: #8888cc; }
.industry-name { font-size: 52px; font-weight: 700; color: #ffffff; }
.hero-stat { text-align: center; padding: 80px 60px 40px; }
.big-text { font-size: 64px; font-weight: 700; color: #ff4444; line-height: 1.4; }
.detail-cards { padding: 20px 60px; display: flex; gap: 24px; }
.detail-card { flex: 1; background: #16213e; border-radius: 20px; padding: 40px 30px; text-align: center; border: 1px solid #1a2d50; }
.detail-label { font-size: 28px; color: #8888aa; margin-bottom: 16px; }
.detail-value { font-size: 48px; font-weight: 700; color: #ffffff; }
.detail-sub { font-size: 22px; color: #666688; margin-top: 10px; }
.footer-strip { position: absolute; bottom: 0; left: 0; right: 0; background: #16213e; padding: 40px 60px; border-top: 1px solid #1a2d50; }
.footer-text { font-size: 30px; color: #8888aa; line-height: 1.6; }
</style>
</head>
<body>
<div class="header">
  <div class="rank-badge">NO.4</div>
  <div class="industry-name">制造业</div>
</div>
<div class="hero-stat">
  <div class="big-text">产业转移 + 自动化<br/>沿海工厂裁员潮</div>
</div>
<div class="detail-cards">
  <div class="detail-card">
    <div class="detail-label">产业外迁</div>
    <div class="detail-value">东南亚</div>
    <div class="detail-sub">订单持续转移</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">自动化替代</div>
    <div class="detail-value">加速</div>
    <div class="detail-sub">机器人替代流水线</div>
  </div>
</div>
<div class="footer-strip">
  <div class="footer-text">打工人的退路，越来越窄了</div>
</div>
</body>
</html>
```

**Step 4: Create tpl-layoff-data-ev.html**

EV data card.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 30px; display: flex; align-items: center; gap: 20px; }
.rank-badge { font-size: 72px; font-weight: 800; color: #8888cc; }
.industry-name { font-size: 52px; font-weight: 700; color: #ffffff; }
.hero-stat { text-align: center; padding: 60px 60px 40px; }
.big-number { font-size: 180px; font-weight: 800; color: #ff4444; line-height: 1; }
.big-unit { font-size: 60px; color: #ff8888; margin-top: 10px; }
.detail-cards { padding: 20px 60px; display: flex; gap: 24px; }
.detail-card { flex: 1; background: #16213e; border-radius: 20px; padding: 40px 30px; text-align: center; border: 1px solid #1a2d50; }
.detail-label { font-size: 28px; color: #8888aa; margin-bottom: 16px; }
.detail-value { font-size: 56px; font-weight: 700; color: #ffffff; }
.detail-sub { font-size: 22px; color: #666688; margin-top: 10px; }
.footer-strip { position: absolute; bottom: 0; left: 0; right: 0; background: #16213e; padding: 40px 60px; border-top: 1px solid #1a2d50; }
.footer-text { font-size: 30px; color: #8888aa; line-height: 1.6; }
</style>
</head>
<body>
<div class="header">
  <div class="rank-badge">NO.3</div>
  <div class="industry-name">新能源汽车</div>
</div>
<div class="hero-stat">
  <div class="big-number">10%+</div>
  <div class="big-unit">头部车企裁员比例</div>
</div>
<div class="detail-cards">
  <div class="detail-card">
    <div class="detail-label">产能过剩</div>
    <div class="detail-value">严重</div>
    <div class="detail-sub">价格战越打越烈</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">供应商</div>
    <div class="detail-value">更惨</div>
    <div class="detail-sub">上下游全遭殃</div>
  </div>
</div>
<div class="footer-strip">
  <div class="footer-text">看着风光，实则危机四伏</div>
</div>
</body>
</html>
```

**Step 5: Create tpl-layoff-data-realestate.html**

Real estate data card.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 30px; display: flex; align-items: center; gap: 20px; }
.rank-badge { font-size: 72px; font-weight: 800; color: #8888cc; }
.industry-name { font-size: 52px; font-weight: 700; color: #ffffff; }
.hero-stat { text-align: center; padding: 60px 60px 40px; }
.big-number { font-size: 180px; font-weight: 800; color: #ff4444; line-height: 1; }
.big-unit { font-size: 60px; color: #ff8888; margin-top: 10px; }
.detail-cards { padding: 20px 60px; display: flex; gap: 24px; }
.detail-card { flex: 1; background: #16213e; border-radius: 20px; padding: 40px 30px; text-align: center; border: 1px solid #1a2d50; }
.detail-label { font-size: 28px; color: #8888aa; margin-bottom: 16px; }
.detail-value { font-size: 56px; font-weight: 700; color: #ffffff; }
.detail-sub { font-size: 22px; color: #666688; margin-top: 10px; }
.footer-strip { position: absolute; bottom: 0; left: 0; right: 0; background: #16213e; padding: 40px 60px; border-top: 1px solid #1a2d50; }
.footer-text { font-size: 30px; color: #8888aa; line-height: 1.6; }
</style>
</head>
<body>
<div class="header">
  <div class="rank-badge">NO.2</div>
  <div class="industry-name">房地产</div>
</div>
<div class="hero-stat">
  <div class="big-number">50%+</div>
  <div class="big-unit">百强房企裁员比例</div>
</div>
<div class="detail-cards">
  <div class="detail-card">
    <div class="detail-label">寒冬持续</div>
    <div class="detail-value">3年</div>
    <div class="detail-sub">仍未触底</div>
  </div>
  <div class="detail-card">
    <div class="detail-label">产业链</div>
    <div class="detail-value">全遭殃</div>
    <div class="detail-sub">建材/装修/中介</div>
  </div>
</div>
<div class="footer-strip">
  <div class="footer-text">三年寒冬没见底，上下游全遭殃</div>
</div>
</body>
</html>
```

**Step 6: Create tpl-layoff-data-tech.html**

Tech/Internet data card — #1 ranking, highest visual impact.

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1080">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", sans-serif; background: #1a1a2e; width: 1080px; height: 1920px; overflow: hidden; color: #e0e0e0; }
.header { padding: 80px 60px 30px; display: flex; align-items: center; gap: 20px; }
.rank-badge { font-size: 72px; font-weight: 800; color: #ff4444; }
.industry-name { font-size: 52px; font-weight: 700; color: #ffffff; }
.split-panel { display: flex; gap: 24px; padding: 40px 60px; }
.panel-card { flex: 1; background: #2a1020; border-radius: 20px; padding: 50px 40px; text-align: center; border: 1px solid #4a1530; }
.panel-label { font-size: 30px; color: #ff8888; margin-bottom: 20px; }
.panel-number { font-size: 96px; font-weight: 700; color: #ff4444; line-height: 1.1; }
.panel-unit { font-size: 36px; font-weight: 400; margin-left: 4px; }
.panel-sub { font-size: 22px; color: #aa6666; margin-top: 12px; }
.alert-section { padding: 30px 60px; }
.alert-box { background: #2a1020; border: 2px solid #ff4444; border-radius: 20px; padding: 40px; text-align: center; }
.alert-title { font-size: 36px; color: #ff4444; font-weight: 700; margin-bottom: 16px; }
.alert-text { font-size: 28px; color: #e0e0e0; line-height: 1.6; }
.footer-strip { position: absolute; bottom: 0; left: 0; right: 0; background: #ff4444; padding: 40px 60px; }
.footer-text { font-size: 32px; color: #ffffff; font-weight: 600; line-height: 1.6; }
</style>
</head>
<body>
<div class="header">
  <div class="rank-badge">NO.1</div>
  <div class="industry-name">互联网科技</div>
</div>
<div class="split-panel">
  <div class="panel-card">
    <div class="panel-label">阿里巴巴</div>
    <div class="panel-number">34<span class="panel-unit">%</span></div>
    <div class="panel-sub">一年裁员比例</div>
  </div>
  <div class="panel-card">
    <div class="panel-label">百度</div>
    <div class="panel-number">7<span class="panel-unit">%</span></div>
    <div class="panel-sub">裁员比例</div>
  </div>
</div>
<div class="alert-section">
  <div class="alert-box">
    <div class="alert-title">静默裁员</div>
    <div class="alert-text">不公开裁，逼你自己走<br/>连赔偿金都省了</div>
  </div>
</div>
<div class="footer-strip">
  <div class="footer-text">互联网寒冬，静默裁员成常态</div>
</div>
</body>
</html>
```

**Step 7: Commit**

```bash
git add docs/content/templates/tpl-top5-ranking.html \
        docs/content/templates/tpl-layoff-data-edu.html \
        docs/content/templates/tpl-layoff-data-mfg.html \
        docs/content/templates/tpl-layoff-data-ev.html \
        docs/content/templates/tpl-layoff-data-realestate.html \
        docs/content/templates/tpl-layoff-data-tech.html
git commit -m "feat: add 6 HTML data card templates for TOP5 layoff video"
```

---

### Task 3: Generate screenshots via Playwright

**Step 1: Source environment and run screenshot renderer for each template**

```bash
cd /Users/weilei/FireSing/docs/content
source .env
python3 scripts/screenshot-renderer.py --template tpl-top5-ranking --output assets/screenshots/unemploy-data-02-top5/SS01-top5-ranking.png
python3 scripts/screenshot-renderer.py --template tpl-layoff-data-edu --output assets/screenshots/unemploy-data-02-top5/SS02-edu-60w.png
python3 scripts/screenshot-renderer.py --template tpl-layoff-data-mfg --output assets/screenshots/unemploy-data-02-top5/SS03-mfg.png
python3 scripts/screenshot-renderer.py --template tpl-layoff-data-ev --output assets/screenshots/unemploy-data-02-top5/SS04-ev-10pct.png
python3 scripts/screenshot-renderer.py --template tpl-layoff-data-realestate --output assets/screenshots/unemploy-data-02-top5/SS05-realestate.png
python3 scripts/screenshot-renderer.py --template tpl-layoff-data-tech --output assets/screenshots/unemploy-data-02-top5/SS06-tech-34pct.png
```

Expected: 6 PNG files at 1080x1920 in `assets/screenshots/unemploy-data-02-top5/`

**Step 2: Verify screenshots exist and look correct**

```bash
ls -la assets/screenshots/unemploy-data-02-top5/
open assets/screenshots/unemploy-data-02-top5/  # visual check
```

---

### Task 4: Download Unsplash atmosphere photos

**Step 1: Run unsplash-downloader for each atmosphere query**

```bash
source .env
python3 scripts/unsplash-downloader.py --query "empty classroom school desks abandoned" --output assets/unsplash/unemploy-data-02-top5/AT01-empty-classroom.jpg
python3 scripts/unsplash-downloader.py --query "abandoned factory production line idle" --output assets/unsplash/unemploy-data-02-top5/AT02-idle-factory.jpg
python3 scripts/unsplash-downloader.py --query "car dealership showroom empty vehicles" --output assets/unsplash/unemploy-data-02-top5/AT03-empty-showroom.jpg
python3 scripts/unsplash-downloader.py --query "abandoned construction site unfinished buildings" --output assets/unsplash/unemploy-data-02-top5/AT04-unfinished-buildings.jpg
python3 scripts/unsplash-downloader.py --query "empty office desks night city lights" --output assets/unsplash/unemploy-data-02-top5/AT05-empty-office-night.jpg
python3 scripts/unsplash-downloader.py --query "late night office building windows illuminated" --output assets/unsplash/unemploy-data-02-top5/AT06-night-office.jpg
```

Expected: 6 JPG files in `assets/unsplash/unemploy-data-02-top5/`

**Step 2: Verify downloads**

```bash
ls -la assets/unsplash/unemploy-data-02-top5/
open assets/unsplash/unemploy-data-02-top5/  # visual check
```

---

### Task 5: Generate TTS voiceover

**Step 1: Run Gemini TTS batch with Charon voice**

```bash
source .env
python3 scripts/medvi-produce.py --config config/unemploy-data-02-top5.json --stage voiceover
```

This uses `medvi-produce.py` which internally creates a temp TTS config and calls `gemini-tts-batch.py` with Charon voice.

Expected: 7 MP3 files (S01-S07) in `assets/voiceover/unemploy-data-02-top5/`

**Step 2: Listen to each segment for quality**

```bash
ls -la assets/voiceover/unemploy-data-02-top5/
# Play segments to verify
for f in assets/voiceover/unemploy-data-02-top5/S0*.mp3; do echo "--- $f ---"; ffprobe -v error -show_entries format=duration -of csv=p=0 "$f"; done
```

Expected total voiceover: ~45-55s. If any segment sounds robotic, regenerate with adjusted emotion tags.

---

### Task 6: Render text cards

**Step 1: Run text card renderer**

```bash
source .env
python3 scripts/medvi-produce.py --config config/unemploy-data-02-top5.json --stage textcards
```

Expected: 7 MP4 text card files (TC01-TC07) in `assets/textcards/unemploy-data-02-top5/`

**Step 2: Verify text cards**

```bash
ls -la assets/textcards/unemploy-data-02-top5/
open assets/textcards/unemploy-data-02-top5/TC01.mp4
```

---

### Task 7: Compose rough-cut video

**Step 1: Run medvi-compose**

```bash
python3 scripts/medvi-compose.py --config config/unemploy-data-02-top5.json
```

This reads the config, builds clips per storyboard segment, merges voiceover, adds BGM, outputs rough-cut MP4.

Expected: `output/unemploy-data-02-top5/unemploy-data-02-top5-rough-cut.mp4`

**Step 2: Verify output**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 output/unemploy-data-02-top5/unemploy-data-02-top5-rough-cut.mp4
open output/unemploy-data-02-top5/
```

Expected: Duration ~55-60s (including 1.5s opening), file size ~15-30MB.

**Step 3: Commit output metadata**

```bash
git add docs/content/assets/screenshots/unemploy-data-02-top5/
git add docs/content/assets/unsplash/unemploy-data-02-top5/
git add docs/content/assets/voiceover/unemploy-data-02-top5/
git add docs/content/assets/textcards/unemploy-data-02-top5/
git commit -m "feat: generate all assets for Type B data video (TOP5 layoff)"
```

---

### Task 8: Generate Douyin upload copy

**Step 1: Run upload copy generation**

```bash
python3 scripts/medvi-produce.py --config config/unemploy-data-02-top5.json --stage upload_copy
```

Expected: `assets/upload-copy/unemploy-data-02-top5-douyin.md`

**Step 2: Review and enhance upload copy**

Read the generated file and add the comment trigger line from the design:
- Comment trigger: "互联网人集合了，你们公司今年裁了多少人？"

**Step 3: Commit**

```bash
git add docs/content/assets/upload-copy/unemploy-data-02-top5-douyin.md
git commit -m "docs: add Douyin upload copy for Type B data video"
```

---

### Task 9: JianYing post-production checklist

This is manual work by the user. No code to write.

**Steps for user:**

1. **Import rough-cut** into JianYing (剪映)
2. **Add subtitles** — auto-generate from audio, manually verify all numbers match script
3. **Key number highlights** — gold (#c9a96e) + bold + 1.5x size for: 60万, 70%, 6万, 10%, 50%, 34%, 7%
4. **AI content label** — add "AI生成内容" text sticker at beginning, ≥3 seconds
5. **Color grade** — saturation -5 to -10, contrast +5 to +10, consistent color temperature
6. **Film grain** — filter → texture → film, 15-20% intensity
7. **AI atmosphere post-processing** — desaturation 20-30% + grain 15-25% + vignette on Unsplash atmosphere shots only (NOT on Playwright screenshots)
8. **Cover frame** — select frame with "2026裁员最狠" text visible, or create in Canva
9. **Export** — 1080x1920, H.264, ≥8Mbps
10. **AI metadata** — after export, run:
    ```bash
    ffmpeg -i output.mp4 -metadata comment="本视频由AI生成合成，包含AI生成的图像和配音" -c copy output_labeled.mp4
    ```

---

### Task 10: Final review gate (Stage 7)

Manual checklist for user:

- [ ] Duration 60-120s (ffprobe check)
- [ ] 7 segments (HOOK + 5 industries + CTA)
- [ ] ≥2 shot types (data cards, atmosphere photos, text cards)
- [ ] All numbers verified against sources (Rest of World, Metaintro)
- [ ] 100% subtitle coverage
- [ ] CTA = 1 action ("评论区说说")
- [ ] Mobile preview passes "would I know this is AI?" test
- [ ] AI label visible ≥3s at beginning
- [ ] Metadata contains AI declaration
- [ ] Title from 3 candidates selected
- [ ] ≤10 tags, ≥3 from approved list
- [ ] Cover frame readable at 200px width

**Publish time:** 12:00 or 18:00 (lunch/evening active hours)
