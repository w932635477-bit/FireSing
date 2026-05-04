# Unemploy Videos 04 & Data-01 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce 2 Medvi unemployment series videos — unemploy-story-04 (Zhang Wei v2, number-shock hook) and unemploy-data-01 (data-driven dark humor) — using the existing `medvi-produce.py` pipeline.

**Architecture:** Each video is a v3 config JSON that drives `medvi-produce.py` through 6 stages: screenshots → atmosphere → voiceover → textcards → compose → upload_copy. The config follows the format established by `unemploy-story-01-zhangwei-v3.json`.

**Tech Stack:** Python 3, FFmpeg, Gemini 3.1 Flash TTS (Charon voice), Playwright (screenshots), Seedream 4.5 via Evolink (reference images — optional, handled manually), `medvi-produce.py` CLI.

---

## Pipeline Overview

```
For each video (A then B):
  1. Write config JSON (based on design doc)
  2. Create HTML screenshot templates
  3. Run pipeline: medvi-produce.py --config config/<video>.json
  4. Verify output: rough-cut MP4 + voiceover MP3s
  5. Generate upload copy for Douyin
  6. Commit all assets
```

---

### Task 1: Create config JSON for Video A (unemploy-story-04-zhangwei-v2)

**Files:**
- Create: `docs/content/config/unemploy-story-04-zhangwei-v2.json`

**Step 1: Write the config JSON**

Create `unemploy-story-04-zhangwei-v2.json` following the exact structure of `unemploy-story-01-zhangwei-v3.json` but with the updated voiceover segments from the design doc. Key changes from v1:

- `video_id`: `unemploy-story-04-zhangwei-v2`
- Voiceover S01 now opens with "847份简历" number shock
- New screenshots needed: tpl-resume-stats-847.html (847/3/0), tpl-wechat-redpacket.html
- Atmosphere images: 4 Seedream reference prompts from design doc (but config uses Unsplash queries as fallback)
- Text cards updated with new copy

```json
{
  "video_id": "unemploy-story-04-zhangwei-v2",
  "version": "2.0",
  "series": "unemploy-story",
  "workflow_mode": "unemploy",

  "global": {
    "target_duration_sec": 95,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon",
    "opening_file": "unemploy-story-opening-v1.mp4"
  },

  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "S01", "emotion": "代入", "text": "投了847份简历。收到3个面试通知。0个offer。38岁，建材行业干了12年。从仓库管理员干到区域经理，瓷砖地板卫浴五金，哪个牌子好哪个是贴牌哪个报价有水分，我闭着眼睛都知道。但在HR眼里，38岁建材人，就是一张废纸。"},
      {"id": "S02", "emotion": "希望", "text": "失业第三个月，我在一个装修业主群里看到有人问：瓷砖怎么选，怕被建材城坑。我回了一大段，从品牌到报价到怎么避坑，写了快半小时。那人私信说：哥你太专业了，我给你发个红包吧。那天晚上我睡不着。不是激动，是后悔。12年的行业知识，我以前从来没想过主动拿出来。"},
      {"id": "S03", "emotion": "力量", "text": "我花了三天把经验列了个清单。建材避坑指南、报价单审查、全屋材料规划。每一条都是我12年踩过的坑、省过的钱。然后在闲鱼发了个帖子：10年建材人帮你审报价单。第一周没人问。第二周来了3个人。第三周，有人主动问我能不能全程陪同买材料。第二个月，我靠这个赚了4000多。没找到工作，但我的经验在帮我赚钱。"},
      {"id": "S04", "emotion": "力量", "text": "847份简历教会我一件事：你的经验不是废纸，是你还没包装过的产品。你做了10年的行业，门外汉花多少钱都买不到你的经验。"},
      {"id": "S05", "emotion": "参与", "text": "你做的是什么行业？评论区告诉我，我帮你拆成能卖的经验。"}
    ]
  },

  "screenshots": [
    {"id": "SS01", "template": "tpl-resume-stats-847", "output": "SS01-resume-847.png"},
    {"id": "SS02", "template": "tpl-boss-search-zhangwei", "output": "SS02-boss-search.png"},
    {"id": "SS03", "template": "tpl-wechat-redpacket", "output": "SS03-wechat-redpacket.png"},
    {"id": "SS04", "template": "tpl-xianyu-post", "output": "SS04-xianyu-post.png"},
    {"id": "SS05", "template": "tpl-income-4000", "output": "SS05-income-4000.png"}
  ],

  "atmosphere": [
    {"id": "AT01", "query": "empty warehouse industrial golden light", "output": "AT01-warehouse.jpg"},
    {"id": "AT02", "query": "desk lamp night workspace coffee phone", "output": "AT02-desk-night.jpg"},
    {"id": "AT03", "query": "building materials market tiles samples", "output": "AT03-market.jpg"},
    {"id": "AT04", "query": "coffee shop window phone typing natural light", "output": "AT04-coffee-shop.jpg"}
  ],

  "text_cards": [
    {"id": "TC01", "lines": ["847份简历 3个面试 0个offer"], "style": "medvi", "bg_image": "AT02-desk-night.jpg", "duration": 4.0},
    {"id": "TC02", "lines": ["12年经验", "在HR眼里 就是一张废纸"], "style": "medvi", "bg_image": "AT01-warehouse.jpg", "duration": 4.0},
    {"id": "TC03", "lines": ["把经验列成清单 = 你的产品", "闲鱼发帖 审报价单99元 第二个月4000+"], "style": "medvi", "bg_image": "AT03-market.jpg", "duration": 4.0},
    {"id": "TC04", "lines": ["你的经验不是废纸", "是没包装过的产品"], "style": "medvi", "bg_image": "AT04-coffee-shop.jpg", "duration": 4.0},
    {"id": "TC05", "lines": ["你做什么行业？", "评论区打出来 我帮你拆"], "style": "medvi", "bg_image": "AT04-coffee-shop.jpg", "duration": 4.0}
  ],

  "storyboard": [
    {
      "segment": "S01",
      "clips": [
        {"type": "screenshot", "ref": "SS01", "zoom": true, "pct": 0.35},
        {"type": "atmosphere", "ref": "AT01", "zoom": true, "pct": 0.35},
        {"type": "text_card", "ref": "TC02", "duration": 4.0}
      ]
    },
    {
      "segment": "S02",
      "clips": [
        {"type": "screenshot", "ref": "SS03", "zoom": false, "pct": 0.4},
        {"type": "atmosphere", "ref": "AT02", "zoom": true, "pct": 0.35},
        {"type": "text_card", "ref": "TC01", "duration": 4.0}
      ]
    },
    {
      "segment": "S03",
      "clips": [
        {"type": "screenshot", "ref": "SS04", "zoom": false, "pct": 0.2},
        {"type": "atmosphere", "ref": "AT03", "zoom": true, "pct": 0.2},
        {"type": "screenshot", "ref": "SS05", "zoom": false, "pct": 0.2},
        {"type": "text_card", "ref": "TC03", "duration": 4.0}
      ]
    },
    {
      "segment": "S04",
      "clips": [
        {"type": "atmosphere", "ref": "AT04", "zoom": true, "pct": 0.5},
        {"type": "text_card", "ref": "TC04", "duration": 4.0}
      ]
    },
    {
      "segment": "S05",
      "clips": [
        {"type": "atmosphere", "ref": "AT04", "zoom": false, "pct": 0.5},
        {"type": "text_card", "ref": "TC05", "duration": 4.0}
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
      "投了847份简历0个offer，38岁建材人靠经验月赚4000",
      "847份简历教会我：你的经验不是废纸，是没包装过的产品",
      "38岁失业投847份简历没人要，反靠经验月入4000，怎么做到的"
    ],
    "tags": ["#失业", "#经验变现", "#38岁", "#被裁员", "#中年危机", "#闲鱼赚钱", "#行业经验", "#失业逆袭", "#职场", "#建材"]
  }
}
```

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-story-04-zhangwei-v2.json
git commit -m "feat: v3 config for unemploy-story-04 zhangwei v2 (number-shock hook)"
```

---

### Task 2: Create screenshot templates for Video A

**Files:**
- Create: `docs/content/templates/tpl-resume-stats-847.html`
- Create: `docs/content/templates/tpl-wechat-redpacket.html`
- Create: `docs/content/templates/tpl-xianyu-post.html`
- Create: `docs/content/templates/tpl-income-4000.html`

**Step 1: Create tpl-resume-stats-847.html**

Copy `tpl-resume-stats-zhangwei.html` and update numbers: 847投递 / 3回复 / 0面试. Update date range to "2024.08 - 2025.01" (6 months of searching). Update summary to show "847" prominently.

**Step 2: Create tpl-wechat-redpacket.html**

WeChat chat screenshot: a user says "哥你太专业了，我给你发个红包吧" with a red packet (红包) visible. Follow the existing `tpl-wechat-positive-zhangwei.html` pattern for layout/style.

**Step 3: Create tpl-xianyu-post.html**

闲鱼 post screenshot: "10年建材人帮你审报价单 ¥99" with a service listing style. Dark header, product image area, price tag. Use the same 1080x1920 / PingFang SC font setup as other templates.

**Step 4: Create tpl-income-4000.html**

Simple income dashboard: "第二个月收入 ¥4,000+" with a progress bar or simple stats card. Use the same stat-card CSS from tpl-resume-stats-zhangwei.html.

**Step 5: Commit**

```bash
git add docs/content/templates/tpl-resume-stats-847.html docs/content/templates/tpl-wechat-redpacket.html docs/content/templates/tpl-xianyu-post.html docs/content/templates/tpl-income-4000.html
git commit -m "feat: screenshot templates for unemploy-story-04 zhangwei v2"
```

---

### Task 3: Create config JSON for Video B (unemploy-data-01-graduates)

**Files:**
- Create: `docs/content/config/unemploy-data-01-graduates.json`

**Step 1: Write the config JSON**

Follow the same v3 config structure. Key differences from Video A:

- `video_id`: `unemploy-data-01-graduates`
- No "series" field (this is a new format, not unemploy-story)
- Voiceover is NOT first-person — it's a narrator doing sharp commentary
- Screenshots: data panels, HR email, job listing, 闲鱼 posts (3 case studies)
- Atmosphere: subway crowd, empty office, coffee shop (3 scenes)
- Text cards: data punchlines + CTA

```json
{
  "video_id": "unemploy-data-01-graduates",
  "version": "1.0",
  "series": "unemploy-data",
  "workflow_mode": "unemploy",

  "global": {
    "target_duration_sec": 95,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon",
    "opening_file": "unemploy-story-opening-v1.mp4"
  },

  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "S01", "emotion": "empathy", "text": "2025年，中国有1170万大学毕业生。同一时间，35岁以上求职者平均投了432份简历。1170万新人往前挤，几千万老人往后退。这不是就业市场，这是俄罗斯方块——到顶了就消除。"},
      {"id": "S02", "emotion": "对比", "text": "HR说：我们收到了5000份简历。潜台词：你的简历连垃圾桶都没进，直接进了碎纸机。招聘要求：3年经验，30岁以下。数学好的同学算一下，22岁毕业干3年才25，谁30岁以下还有3年经验？朋友圈流行一句话：35岁以后的人生，要么财务自由，要么自由职业。翻译一下就是：要么你有钱，要么你失业。"},
      {"id": "S03", "emotion": "希望", "text": "但有一群人，他们不投简历。他们把自己的经验拆成服务，直接卖给需要的人。38岁建材人帮人审报价单，月入4000。42岁HR总监帮创业公司搭团队，一单1500。45岁销售老手帮小企业做客户开发，按效果收费。他们不是找到了工作，是发现了一个事实：你做了10年的事，外面有人愿意花钱请你做一遍。"},
      {"id": "S04", "emotion": "力量", "text": "简历投了400多份没回音？别投了。先想想你这些年到底攒了什么，谁会为此付钱。你的经验不是废纸，是你还没拆开的包裹。"},
      {"id": "S05", "emotion": "参与", "text": "你做什么行业？评论区告诉我，我帮你拆成能卖的服务。"}
    ]
  },

  "screenshots": [
    {"id": "SS01", "template": "tpl-data-panel-1170w", "output": "SS01-data-1170w.png"},
    {"id": "SS02", "template": "tpl-hr-email-5000", "output": "SS02-hr-email.png"},
    {"id": "SS03", "template": "tpl-job-requirement-30", "output": "SS03-job-requirement.png"},
    {"id": "SS04", "template": "tpl-case-study-3in1", "output": "SS04-case-study.png"}
  ],

  "atmosphere": [
    {"id": "AT01", "query": "crowded subway station morning rush", "output": "AT01-subway-crowd.jpg"},
    {"id": "AT02", "query": "empty office desks fluorescent lights", "output": "AT02-empty-office.jpg"},
    {"id": "AT03", "query": "coffee shop window laptop working", "output": "AT03-coffee-shop.jpg"}
  ],

  "text_cards": [
    {"id": "TC01", "lines": ["2025年 1170万大学毕业生", "35岁以上 平均投432份简历"], "style": "medvi", "bg_image": "AT01-subway-crowd.jpg", "duration": 4.0},
    {"id": "TC02", "lines": ["俄罗斯方块", "到顶了就消除"], "style": "medvi", "bg_image": "AT01-subway-crowd.jpg", "duration": 3.5},
    {"id": "TC03", "lines": ["5000份简历", "→ 碎纸机"], "style": "medvi", "bg_image": "AT02-empty-office.jpg", "duration": 3.5},
    {"id": "TC04", "lines": ["做了10年的事", "有人愿意花钱请你做"], "style": "medvi", "bg_image": "AT03-coffee-shop.jpg", "duration": 4.0},
    {"id": "TC05", "lines": ["你做什么行业？", "评论区打出来 我帮你拆"], "style": "medvi", "bg_image": "AT03-coffee-shop.jpg", "duration": 4.0}
  ],

  "storyboard": [
    {
      "segment": "S01",
      "clips": [
        {"type": "screenshot", "ref": "SS01", "zoom": true, "pct": 0.4},
        {"type": "atmosphere", "ref": "AT01", "zoom": true, "pct": 0.3},
        {"type": "text_card", "ref": "TC02", "duration": 3.5}
      ]
    },
    {
      "segment": "S02",
      "clips": [
        {"type": "screenshot", "ref": "SS02", "zoom": false, "pct": 0.25},
        {"type": "screenshot", "ref": "SS03", "zoom": false, "pct": 0.25},
        {"type": "text_card", "ref": "TC03", "duration": 3.5},
        {"type": "atmosphere", "ref": "AT02", "zoom": true, "pct": 0.25}
      ]
    },
    {
      "segment": "S03",
      "clips": [
        {"type": "screenshot", "ref": "SS04", "zoom": false, "pct": 0.4},
        {"type": "atmosphere", "ref": "AT03", "zoom": true, "pct": 0.3},
        {"type": "text_card", "ref": "TC04", "duration": 4.0}
      ]
    },
    {
      "segment": "S04",
      "clips": [
        {"type": "text_card", "ref": "TC04", "duration": 4.0},
        {"type": "atmosphere", "ref": "AT03", "zoom": false, "pct": 0.4}
      ]
    },
    {
      "segment": "S05",
      "clips": [
        {"type": "atmosphere", "ref": "AT03", "zoom": false, "pct": 0.4},
        {"type": "text_card", "ref": "TC05", "duration": 4.0}
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
      "1170万毕业生进入职场，35岁以上的人该怎么办",
      "HR收到5000份简历，你的连垃圾桶都没进",
      "35岁以上平均投432份简历，但有人选择不投了"
    ],
    "tags": ["#失业", "#35岁", "#求职", "#毕业生", "#中年危机", "#经验变现", "#职场", "#裁员", "#俄罗斯方块", "#反转"]
  }
}
```

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-data-01-graduates.json
git commit -m "feat: v3 config for unemploy-data-01 graduates (dark humor data-driven)"
```

---

### Task 4: Create screenshot templates for Video B

**Files:**
- Create: `docs/content/templates/tpl-data-panel-1170w.html`
- Create: `docs/content/templates/tpl-hr-email-5000.html`
- Create: `docs/content/templates/tpl-job-requirement-30.html`
- Create: `docs/content/templates/tpl-case-study-3in1.html`

**Step 1: Create tpl-data-panel-1170w.html**

Data dashboard showing: "2025年毕业生 1170万" and "35岁以上求职 平均投递432份" side by side. Use the same stat-card CSS pattern from existing templates. Big numbers, clean layout.

**Step 2: Create tpl-hr-email-5000.html**

Fake HR inbox screenshot showing "5000封未投递简历" or an email with subject "感谢您的投递，但..." followed by 50 similar rows. Use dark corporate email UI style.

**Step 3: Create tpl-job-requirement-30.html**

Job listing card: "3年经验 / 30岁以下" with the contradictory math highlighted. Use a recruitment app UI style (dark header, job card layout).

**Step 4: Create tpl-case-study-3in1.html**

Three case study cards stacked vertically:
1. "38岁建材人 → 审报价单 → 月入4000"
2. "42岁HR总监 → 搭招聘框架 → 一单1500"
3. "45岁销售 → 客户开发 → 按效果收费"

Use warm accent colors (#ffa726) for the arrow transitions.

**Step 5: Commit**

```bash
git add docs/content/templates/tpl-data-panel-1170w.html docs/content/templates/tpl-hr-email-5000.html docs/content/templates/tpl-job-requirement-30.html docs/content/templates/tpl-case-study-3in1.html
git commit -m "feat: screenshot templates for unemploy-data-01 graduates"
```

---

### Task 5: Run Video A production pipeline

**Prerequisite:** API keys loaded (`source docs/content/.env`)

**Step 1: Source env and run full pipeline**

```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/medvi-produce.py --config docs/content/config/unemploy-story-04-zhangwei-v2.json
```

Expected: All 6 stages run (screenshots → atmosphere → voiceover → textcards → compose → upload_copy). Final output: `docs/content/output/unemploy-story-04-zhangwei-v2/unemploy-story-04-zhangwei-v2-final.mp4`

**Step 2: Verify output**

```bash
ffprobe docs/content/output/unemploy-story-04-zhangwei-v2/unemploy-story-04-zhangwei-v2-final.mp4
```

Expected: Duration ~70-95s, resolution 1080x1920, codec h264.

**Step 3: Listen to voiceover spot-check**

Play the S01 voiceover file and verify the "847... 3... 0" numbers are delivered with dramatic pauses.

**Step 4: Commit pipeline outputs**

```bash
git add docs/content/assets/screenshots/unemploy-story-04-zhangwei-v2/ docs/content/assets/unsplash/unemploy-story-04-zhangwei-v2/ docs/content/assets/voiceover/unemploy-story-04-zhangwei-v2/ docs/content/assets/textcards/unemploy-story-04-zhangwei-v2/ docs/content/assets/upload-copy/unemploy-story-04-zhangwei-v2-douyin.md docs/content/output/unemploy-story-04-zhangwei-v2/
git commit -m "feat: unemploy-story-04 zhangwei v2 pipeline outputs"
```

---

### Task 6: Run Video B production pipeline

**Step 1: Run full pipeline**

```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/medvi-produce.py --config docs/content/config/unemploy-data-01-graduates.json
```

Expected: Same 6 stages. Final output: `docs/content/output/unemploy-data-01-graduates/unemploy-data-01-graduates-final.mp4`

**Step 2: Verify output**

```bash
ffprobe docs/content/output/unemploy-data-01-graduates/unemploy-data-01-graduates-final.mp4
```

Expected: Duration ~70-95s, resolution 1080x1920.

**Step 3: Listen to voiceover spot-check**

Play S01 and S02 — verify the fast-paced sarcastic delivery and the "俄罗斯方块" punchline lands well.

**Step 4: Commit pipeline outputs**

```bash
git add docs/content/assets/screenshots/unemploy-data-01-graduates/ docs/content/assets/unsplash/unemploy-data-01-graduates/ docs/content/assets/voiceover/unemploy-data-01-graduates/ docs/content/assets/textcards/unemploy-data-01-graduates/ docs/content/assets/upload-copy/unemploy-data-01-graduates-douyin.md docs/content/output/unemploy-data-01-graduates/
git commit -m "feat: unemploy-data-01 graduates pipeline outputs"
```

---

### Task 7: Manual post-production (剪映)

This task is done by the user manually. Document what needs to happen.

**Video A checklist:**
- [ ] Import rough-cut into 剪映
- [ ] Add 1.5s opening (unemploy-story-opening-spec.md): black → 「你的经验」→ gold「比你想象的值钱」+ bass drum
- [ ] Add subtitles (auto-generated, review accuracy)
- [ ] Add AI label watermark (top-left, "AI生成内容")
- [ ] Color grade: warm tones, slight Kodak Gold 200 feel
- [ ] Export: 1080x1920, H.264, AAC

**Video B checklist:**
- [ ] Same opening template
- [ ] Add subtitles
- [ ] Add AI label watermark
- [ ] Color grade: slightly cooler than A (data-driven feel)
- [ ] Export: same specs

**Upload checklist (both):**
- [ ] Title from upload_copy markdown
- [ ] Tags from upload_copy markdown
- [ ] Publish time: 20:00-22:00
- [ ] Pre-seed comment: "你做什么行业？我先来：____"
