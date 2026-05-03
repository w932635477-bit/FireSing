# 张伟#1 视频完整生产 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成失业系列第1条视频（张伟#1）的全部素材制作，输出粗剪视频供剪映后期。

**Architecture:** 沿用已有管线——Playwright渲染UI截图、Unsplash下载氛围空镜、Gemini TTS配音、FFmpeg拼接粗剪。新增Unsplash下载脚本。3个已有脚本补充分镜表。

**Tech Stack:** Python 3 + Playwright + Unsplash API + Gemini TTS + FFmpeg

---

## Task 1: 为张伟#1创建/修改Playwright UI截图模板

**背景：** 现有6个HTML模板（tpl-boss-search等）数据是硬编码的。张伟的故事需要特定数据：建材行业、38岁、装修群等。需要为张伟创建专属模板变体。

**Files:**
- Create: `docs/content/templates/tpl-boss-search-zhangwei.html`
- Create: `docs/content/templates/tpl-wechat-positive-zhangwei.html`
- Create: `docs/content/templates/tpl-resume-stats-zhangwei.html`
- Modify: (none — 原模板不动)

**Step 1: 创建张伟版Boss搜索模板**

复制 `tpl-boss-search.html` 为 `tpl-boss-search-zhangwei.html`，修改数据：
- 搜索关键词改为"建材 区域经理"
- 职位卡片改为建材相关：建材区域经理、建材销售总监、瓷砖卫浴运营经理等
- 薪资改为15-25K、12-20K等（建材行业薪资）
- 全部状态改为"已读不回"
- 筛选标签改为"3-5年经验""大专""10-20K"

**Step 2: 创建张伟版微信正面消息模板**

复制 `tpl-wechat-positive.html` 为 `tpl-wechat-positive-zhangwei.html`，修改数据：
- 联系人改为"李哥-装修业主群"
- 对话内容改为：
  - 李哥："瓷砖怎么选？怕被建材城坑"
  - 我：[大段回复关于瓷砖品牌、报价、避坑]
  - 李哥："哥你太专业了，我给你发个红包吧"

**Step 3: 创建张伟版简历数据面板**

复制 `tpl-resume-stats.html` 为 `tpl-resume-stats-zhangwei.html`，修改数据：
- 投递总数：47
- 已读：38
- 回复：0
- 面试：0
- 进度条全部灰掉

**Step 4: 用screenshot-renderer渲染3个新模板**

```bash
source docs/content/.env
cd docs/content/scripts
python3 screenshot-renderer.py --template tpl-boss-search-zhangwei --output ../assets/screenshots/unemploy-story-01-zhangwei/SS01-boss-search.png
python3 screenshot-renderer.py --template tpl-resume-stats-zhangwei --output ../assets/screenshots/unemploy-story-01-zhangwei/SS02-resume-stats.png
python3 screenshot-renderer.py --template tpl-wechat-positive-zhangwei --output ../assets/screenshots/unemploy-story-01-zhangwei/SS03-wechat-positive.png
```

**Step 5: 复用已有模板渲染钉钉退群和微信拒绝截图**

张伟S03蒙太奇需要钉钉退群和微信拒绝截图，直接复用现有模板：

```bash
python3 screenshot-renderer.py --template tpl-dingtalk-leave --output ../assets/screenshots/unemploy-story-01-zhangwei/SS04-dingtalk-leave.png
python3 screenshot-renderer.py --template tpl-wechat-reject --output ../assets/screenshots/unemploy-story-01-zhangwei/SS05-wechat-reject.png
```

**Step 6: 验证截图**

```bash
ls -la ../assets/screenshots/unemploy-story-01-zhangwei/
# 应该看到5个PNG文件，每个100-300KB
```

**Step 7: Commit**

```bash
git add docs/content/templates/tpl-boss-search-zhangwei.html docs/content/templates/tpl-wechat-positive-zhangwei.html docs/content/templates/tpl-resume-stats-zhangwei.html docs/content/assets/screenshots/unemploy-story-01-zhangwei/
git commit -m "feat: zhangwei #1 Playwright UI screenshot templates"
```

---

## Task 2: 创建Unsplash下载脚本

**Files:**
- Create: `docs/content/scripts/unsplash-downloader.py`

**Step 1: 编写下载脚本**

```python
#!/usr/bin/env python3
"""Download atmosphere stock photos from Unsplash for video production.

Usage:
  source docs/content/.env
  python3 unsplash-downloader.py --query "empty warehouse" --output ../assets/unsplash/unemploy-story-01-zhangwei/AT01-warehouse.jpg
  python3 unsplash-downloader.py --config unsplash-manifest.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import urllib.request


def search_photos(
    query: str,
    access_key: str,
    per_page: int = 10,
    orientation: str = "portrait",
) -> list[dict]:
    """Search Unsplash for photos matching query."""
    url = (
        f"https://api.unsplash.com/search/photos?"
        f"query={query}&per_page={per_page}&orientation={orientation}"
    )
    req = urllib.request.Request(url, headers={
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("results", [])


def download_photo(photo_url: str, output_path: Path) -> bool:
    """Download photo from URL to local file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(photo_url)
    with urllib.request.urlopen(req) as resp:
        output_path.write_bytes(resp.read())
    return output_path.exists()


def pick_best(photos: list[dict], prefer_no_people: bool = True) -> dict | None:
    """Pick best photo: prefer no people, high likes, portrait orientation."""
    scored = []
    for p in photos:
        score = p.get("likes", 0)
        if prefer_no_people:
            desc = (p.get("description") or "").lower()
            alt = (p.get("alt_description") or "").lower()
            people_words = ["person", "people", "man", "woman", "face", "portrait"]
            if any(w in desc or w in alt for w in people_words):
                score -= 100
        scored.append((score, p))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Unsplash stock photos")
    parser.add_argument("--query", type=str, help="Search query (English)")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--config", type=str, help="Manifest JSON with batch downloads")
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument("--list-only", action="store_true", help="Show search results without downloading")
    args = parser.parse_args()

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        print("ERROR: UNSPLASH_ACCESS_KEY not set. Run: source docs/content/.env")
        sys.exit(1)

    if args.config:
        with open(args.config) as f:
            manifest = json.load(f)
        for item in manifest.get("downloads", []):
            query = item["query"]
            output = Path(item["output"])
            print(f"\n--- {query} -> {output.name} ---")
            photos = search_photos(query, access_key, args.per_page)
            if args.list_only:
                for i, p in enumerate(photos[:5]):
                    print(f"  {i+1}. {p.get('alt_description', '?')[:60]} | {p['likes']} likes | {p['urls']['regular']}")
                continue
            best = pick_best(photos)
            if best:
                url = best["urls"]["regular"]
                ok = download_photo(url, output)
                print(f"  -> {output} ({'OK' if ok else 'FAIL'})")
            else:
                print(f"  -> No suitable photo found")
            time.sleep(1)  # Rate limit
        return

    if args.query and args.output:
        photos = search_photos(args.query, access_key, args.per_page)
        if args.list_only:
            for i, p in enumerate(photos[:5]):
                print(f"  {i+1}. {p.get('alt_description', '?')[:60]} | {p['likes']} likes | {p['urls']['regular']}")
            return
        best = pick_best(photos)
        if best:
            url = best["urls"]["regular"]
            ok = download_photo(url, Path(args.output))
            print(f"{'OK' if ok else 'FAIL'}: {args.output}")
        else:
            print("No suitable photo found")
            sys.exit(1)
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: 测试API连接**

```bash
source docs/content/.env
cd docs/content/scripts
python3 unsplash-downloader.py --query "empty warehouse" --list-only
```

Expected: 打印5条搜索结果，每条包含描述、点赞数、URL。

**Step 3: Commit**

```bash
git add docs/content/scripts/unsplash-downloader.py
git commit -m "feat: unsplash stock photo downloader script"
```

---

## Task 3: 为张伟#1下载Unsplash氛围空镜

**Files:**
- Create: `docs/content/scripts/unsplash-manifest-zhangwei.json`
- Download: `docs/content/assets/unsplash/unemploy-story-01-zhangwei/` (6张照片)

**Step 1: 创建下载清单**

张伟#1需要6张氛围空镜（根据设计文档§4）：

```json
{
  "downloads": [
    {"query": "empty warehouse industrial", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT01-warehouse.jpg"},
    {"query": "desk lamp night coffee paper", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT02-desk-lamp.jpg"},
    {"query": "empty office night fluorescent lights", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT03-empty-office.jpg"},
    {"query": "phone screen light dark room", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT04-phone-light.jpg"},
    {"query": "laptop document desk working", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT05-laptop-desk.jpg"},
    {"query": "coffee shop window phone", "output": "../assets/unsplash/unemploy-story-01-zhangwei/AT06-coffee-shop.jpg"}
  ]
}
```

**Step 2: 先预览搜索结果，人工确认**

```bash
python3 unsplash-downloader.py --config unsplash-manifest-zhangwei.json --list-only
```

Expected: 每个query打印5条结果。检查描述是否匹配需求。

**Step 3: 下载照片**

```bash
python3 unsplash-downloader.py --config unsplash-manifest-zhangwei.json
```

Expected: 6张照片下载到 `assets/unsplash/unemploy-story-01-zhangwei/`。

**Step 4: 人工审核照片**

```bash
open ../assets/unsplash/unemploy-story-01-zhangwei/
```

检查：
- 没有人脸
- 没有可读文字
- 自然光线
- 构图可用
- 竖版或可裁剪到9:16

如果某张不合适，手动更换搜索关键词重新下载。

**Step 5: Commit**

```bash
git add docs/content/scripts/unsplash-manifest-zhangwei.json docs/content/assets/unsplash/unemploy-story-01-zhangwei/
git commit -m "feat: zhangwei #1 unsplash atmosphere shots (6 photos)"
```

---

## Task 4: 为张伟#1生成Gemini TTS配音

**背景：** 配音规格已在设计文档§5确认。Charon男声，第一人称，6段。

**Files:**
- Create: `docs/content/assets/voiceover/unemploy-story-01-zhangwei/S01.mp3` (及S02-S06)
- Reference: 现有TTS脚本作为参考

**Step 1: 编写配音配置**

在 `docs/content/config/` 创建 `unemploy-story-01-zhangwei-tts.json`：

```json
{
  "video_id": "unemploy-story-01-zhangwei",
  "engine": "gemini",
  "voice": "Charon",
  "segments": [
    {
      "id": "S01",
      "text": "38岁，建材行业干了12年。从仓库管理员干到区域经理，瓷砖地板卫浴五金，哪个牌子好、哪个是贴牌、哪个报价有水分，我闭着眼睛都知道。投了几十份简历，没人要。38岁建材人，在新行业的HR眼里，就是一张废纸。",
      "notes": "平静叙述，'一张废纸'稍加重"
    },
    {
      "id": "S02",
      "text": "失业第三个月，我在一个装修业主群里看到有人问：瓷砖怎么选，怕被建材城坑。我主动回了一大段，从品牌到报价到怎么避坑，写了快半小时。那人私信我说：哥你太专业了，我给你发个红包吧。那天晚上我睡不着。不是激动，是后悔。12年的行业知识，我以前从来没想过主动拿出来。",
      "notes": "稍快，'给你发个红包吧'之后停顿1秒"
    },
    {
      "id": "S03",
      "text": "我花了三天做了一件事：把自己的经验列了个清单。建材避坑指南、报价单审查、全屋材料规划。每一条都是我12年踩过的坑、省过的钱。然后在闲鱼发了个帖子：10年建材人帮你审报价单。第一周没人问。第二周来了3个人。第三周，有人主动问我能不能全程陪同买材料。第二个月，我靠这个赚了4000多。没找到工作，但我的经验在帮我赚钱。",
      "notes": "踏实有节奏，数字说得不夸张"
    },
    {
      "id": "S04",
      "text": "你觉得自己没用，可能只是你从来没认真想过，你这些年攒下来的东西，到底值多少钱。你做了10年的行业，门外汉花多少钱都买不到你的经验。你的经验不是废纸，是你还没包装过的产品。",
      "notes": "真诚，像在给朋友出主意"
    },
    {
      "id": "S05",
      "text": "你做什么行业？评论区告诉我，我逐条回复，帮你看你的经验能怎么变现。",
      "notes": "自然放松，最后一句像聊天"
    }
  ]
}
```

**Step 2: 调用Gemini TTS生成配音**

使用已有的Gemini TTS流程（参考 `docs/content/scripts/` 中现有TTS脚本）。每段生成一个MP3文件。

```bash
# 根据现有TTS脚本模式生成
# 输出: docs/content/assets/voiceover/unemploy-story-01-zhangwei/S01.mp3 ~ S05.mp3
```

注意：实际TTS调用取决于项目中现有的Gemini TTS脚本。需查看现有脚本确认调用方式。

**Step 3: 验证配音文件**

```bash
ls -la ../assets/voiceover/unemploy-story-01-zhangwei/
# 5个MP3文件
for f in ../assets/voiceover/unemploy-story-01-zhangwei/*.mp3; do
  echo "$f: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")s"
done
```

Expected: 5段MP3，总时长约70-90秒。

**Step 4: Commit**

```bash
git add docs/content/config/unemploy-story-01-zhangwei-tts.json docs/content/assets/voiceover/unemploy-story-01-zhangwei/
git commit -m "feat: zhangwei #1 voiceover (Gemini TTS Charon, 5 segments)"
```

---

## Task 5: 为张伟#1创建FFmpeg粗剪脚本

**Files:**
- Create: `docs/content/scripts/compose-unemploy-story-01.py`

**Step 1: 编写粗剪脚本**

基于现有 `compose-unemploy-01.py` 模式，按设计文档§4的分镜表实现：

- S01(钩子): SS01-boss-search.png 静态图 + S01.mp3
- S02(设定): AT01-warehouse.jpg (4s) → AT02-desk-lamp.jpg (4s) + S02.mp3（图片静态展示，配Ken Burns轻微缩放动效）
- S03(蒙太奇): 快切4个画面 — SS04-dingtalk-leave(1.5s) → SS02-resume-stats(2s) → SS05-wechat-reject(2s) → AT03-empty-office(4s) + S03.mp3
- S04(转折): AT04-phone-light(4s) → SS03-wechat-positive(3s) → 暖光空镜(3s) + S04.mp3
- S05(CTA): AT06-coffee-shop(6s) + 文字卡片(6s) + S05.mp3

使用FFmpeg的concat demuxer拼接所有segment。

**Step 2: 运行粗剪**

```bash
source docs/content/.env
cd docs/content/scripts
python3 compose-unemploy-story-01.py
```

Expected: 输出 `docs/content/output/unemploy-story-01-zhangwei/unemploy-story-01-zhangwei-rough-cut.mp4`

**Step 3: 验证输出**

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 ../output/unemploy-story-01-zhangwei/unemploy-story-01-zhangwei-rough-cut.mp4
# Expected: ~70-90 seconds
open ../output/unemploy-story-01-zhangwei/
```

**Step 4: Commit**

```bash
git add docs/content/scripts/compose-unemploy-story-01.py docs/content/output/unemploy-story-01-zhangwei/
git commit -m "feat: zhangwei #1 rough-cut composition script"
```

---

## Task 6: 为刘娜#2和陈明#3补充视觉分镜表

**Files:**
- Modify: `docs/content/scripts/unemploy-story-02-liuna.md` — 追加视觉分镜表
- Modify: `docs/content/scripts/unemploy-story-03-chenming.md` — 追加视觉分镜表

**Step 1: 为刘娜#2补充分镜表**

在 `unemploy-story-02-liuna.md` 末尾"制作备注"之前，插入完整分镜表：

```
## 视觉分镜表

| 时间 | 段落 | 画面 | 声音 |
|------|------|------|------|
| 0-1.5s | 片头 | 统一片头 | 片头音效 |
| 1.5-6s | S01 钩子 | UI: Boss搜索"HR总监 15年经验"，已读不回（tpl-boss-search变体） | "42岁，HR总监，干了15年..." |
| 6-14s | S02 设定 | 空镜①: 办公桌招聘网站屏幕（Unsplash: "laptop recruitment"）→ 空镜②: 手机微信（Unsplash: "phone notification"） | "...从3人团队建到40人团队..." |
| 14-23s | S03 蒙太奇 | ①UI: 简历数据面板（tpl-resume-stats变体, 2s）→ ②UI: HR拒绝"年龄不符"（tpl-wechat-reject, 1.5s）→ ③空镜: 空办公椅（Unsplash: "empty office chair", 3s）→ ④空镜: 深夜屏幕（Unsplash: "dark screen", 2.5s） | "...干了15年招聘的人，被招聘市场拒绝了..." |
| 23-33s | S04 转折 | 空镜: 手机微信大段回复（Unsplash: "typing phone"）→ UI: 微信"姐你帮我搭一下招聘框架吧"（tpl-wechat-positive变体, 3s） | "...突然想明白了一件事..." |
| 33-48s | S05 行动 | 空镜: 文档列表（Unsplash: "checklist"）→ 文字卡片: "岗位画像 + 面试流程 + 招聘诊断" → 文字卡片: "第一单1500 第一个月5000+" | "...朋友圈发了一条..." |
| 48-60s | S06 CTA | 空镜: 街道走路看手机（Unsplash: "walking street phone"）→ 文字卡片: "干了十几年的事 外面有人愿意花钱请你做" → 文字卡片: "你做什么行业？评论区打出来" | CTA旁白 |
```

**Step 2: 为陈明#3补充分镜表**

在 `unemploy-story-03-chenming.md` 末尾"制作备注"之前，插入完整分镜表：

```
## 视觉分镜表

| 时间 | 段落 | 画面 | 声音 |
|------|------|------|------|
| 0-1.5s | 片头 | 统一片头 | 片头音效 |
| 1.5-6s | S01 钩子 | UI: Boss搜索"销售 15年经验 45岁"，回复率5%（tpl-boss-search变体） | "45岁，To B销售干了15年..." |
| 6-14s | S02 设定 | 空镜①: 夜晚车内手机通讯录（Unsplash: "car night phone"）→ 空镜②: 咖啡店独坐（Unsplash: "coffee alone"） | "...2000多个联系人..." |
| 14-23s | S03 蒙太奇 | ①UI: 简历数据面板 投80份/回复4（tpl-resume-stats变体, 2s）→ ②UI: HR拒绝"年龄偏大"（tpl-wechat-reject变体, 1.5s）→ ③空镜: 地铁疲惫（Unsplash: "subway tired", 3s）→ ④空镜: 空停车场（Unsplash: "empty parking", 2.5s） | "...投了两个月简历，回复不到5%..." |
| 23-33s | S04 转折 | 空镜: 手机微信群聊消息（Unsplash: "chat message"）→ UI: 微信"老哥太专业了，能不能帮我对比一下"（tpl-wechat-positive变体, 3s） | "...我脑子里直接蹦出来三个名字..." |
| 33-48s | S05 行动 | 空镜: 笔记本列表（Unsplash: "notebook list"）→ 文字卡片: "通讯录分组 + 主动问候 + 低价试单" → 文字卡片: "第一个月 4单 3000+" | "...第一个月接了4单..." |
| 48-60s | S06 CTA | 空镜: 城市街道白天走路打电话（Unsplash: "walking phone confident"）→ 文字卡片: "圈内人的常识 = 圈外人值钱的信息" → 文字卡片: "你做什么行业？评论区打出来" | CTA旁白 |
```

**Step 3: Commit**

```bash
git add docs/content/scripts/unemploy-story-02-liuna.md docs/content/scripts/unemploy-story-03-chenming.md
git commit -m "docs: add visual storyboard tables for liuna #2 and chenming #3"
```

---

## Task 7: 更新张伟#1脚本添加视觉分镜表

**Files:**
- Modify: `docs/content/scripts/unemploy-story-01-zhangwei.md` — 追加设计文档§4的完整分镜表

**Step 1: 在张伟脚本"制作备注"之前插入完整分镜表**

内容就是设计文档§4的样例分镜表，格式与Task 6一致。

**Step 2: Commit**

```bash
git add docs/content/scripts/unemploy-story-01-zhangwei.md
git commit -m "docs: add visual storyboard table for zhangwei #1"
```

---

## 依赖关系

```
Task 1 (UI截图模板) → Task 5 (粗剪脚本)
Task 2 (Unsplash脚本) → Task 3 (下载空镜) → Task 5 (粗剪脚本)
Task 4 (配音) → Task 5 (粗剪脚本)
Task 6, 7 (分镜表) — 独立，可并行
```

可并行执行：
- Task 1 + Task 2 + Task 4 同时进行
- Task 6 + Task 7 独立进行
- Task 3 等Task 2完成
- Task 5 等Task 1 + 3 + 4全部完成

---

## 预计时间

| Task | 内容 | 预计时间 |
|------|------|---------|
| 1 | UI截图模板 | 30min |
| 2 | Unsplash脚本 | 15min |
| 3 | 下载空镜 | 10min |
| 4 | TTS配音 | 20min |
| 5 | 粗剪脚本 | 25min |
| 6 | 刘娜+陈明分镜表 | 15min |
| 7 | 张伟分镜表 | 5min |
| **Total** | | **~2h** |
