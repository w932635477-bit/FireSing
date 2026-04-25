# Day10 任正非「备胎转正」实施计划 (Medvi v2)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生成 Day10 任正非备胎转正视频的生产素材（故事图 → 故事视频 → 配音），剪映混剪

**Architecture:** Medvi v2 工作流。跳过 Seedream 主参考图 + Kling 杨梦视频。只生成 3 张故事图 + 3 个故事视频 + 4 段 TTS 配音。所有素材在剪映手动混剪。

**Tech Stack:** Python 3, Evolink API (Seedream 4.5, Kling 3.0), Gemini TTS (Aoede), 剪映 (手动)

**v2 Design doc:** `docs/plans/2026-04-25-medvi-workflow-v2-design.md`
**Day10 Design doc:** `docs/plans/2026-04-25-day10-renzhengfei-design.md`

---

### Task 1: Config (DONE)

`docs/content/config/day10-yangmun.json` 已创建并提交 (v2 格式)。

---

### Task 2: Generate Seedream Story Images (3 shots)

**Files:**
- Use: `docs/content/scripts/seedream-story-images.py`
- Config: `docs/content/config/day10-yangmun.json`
- Output: `docs/content/assets/references/day10-yangmun/S01-01.png`, `S02-01.png`, `S03-01.png`

**Step 1: Source API keys**

```bash
source docs/content/.env
```

**Step 2: Dry-run**

```bash
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 3 planned story image generations (S01-01, S02-01, S03-01).

**Step 3: Generate (live)**

```bash
python3 docs/content/scripts/seedream-story-images.py --config docs/content/config/day10-yangmun.json
```

Expected: Generates 3 story PNG files.

**Step 4: Verify output**

```bash
ls -la docs/content/assets/references/day10-yangmun/*.png
```

Expected: 3 story reference images.

**Step 5: Commit**

```bash
git add docs/content/assets/references/day10-yangmun/
git commit -m "feat: Day10 story reference images (3 shots, v2 workflow)"
```

---

### Task 3: Generate Kling Story Videos (3 clips)

**Files:**
- Use: `docs/content/scripts/kling-gen-batch.py`
- Config: `docs/content/config/day10-yangmun.json`
- Input: `docs/content/assets/references/day10-yangmun/*.png`
- Output: `docs/content/output/day10-yangmun/`

**Prerequisites:** Task 2 complete.

**Step 1: Verify reference images**

```bash
ls docs/content/assets/references/day10-yangmun/*.png | wc -l
```

Expected: 3 PNG files.

**Step 2: Dry-run**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day10-yangmun.json --include-stories --dry-run
```

Expected: Shows 3 planned story video generations.

**Step 3: Generate (live)**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/day10-yangmun.json --include-stories
```

Expected: Generates 3 x 5-second story video clips.

**Step 4: Verify output**

```bash
ls -la docs/content/output/day10-yangmun/*.mp4
for f in docs/content/output/day10-yangmun/*.mp4; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")
  echo "$(basename $f): ${dur}s"
done
```

Expected: 3 video files, each ~5s.

**Step 5: Commit**

```bash
git add docs/content/output/day10-yangmun/
git commit -m "feat: Day10 Kling story video clips (3 clips, v2 workflow)"
```

---

### Task 4: Generate Gemini TTS Voiceover (4 segments)

**Files:**
- Use: `docs/content/scripts/gemini-tts-batch.py`
- Config: `docs/content/config/day10-yangmun.json`
- Output: `docs/content/assets/voiceover/day10-yangmun/`

**Step 1: Dry-run**

```bash
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day10-yangmun.json --dry-run
```

Expected: Shows 4 planned TTS generations (S01-S04).

**Step 2: Generate (live)**

```bash
python3 docs/content/scripts/gemini-tts-batch.py --config docs/content/config/day10-yangmun.json
```

Expected: 4 MP3 files. Total duration ~40-46s.

**Step 3: Fallback to Doubao if Gemini fails**

```bash
python3 docs/content/scripts/doubao-tts-batch.py --config docs/content/config/day10-yangmun.json
```

**Step 4: Commit**

```bash
git add docs/content/assets/voiceover/day10-yangmun/
git commit -m "feat: Day10 TTS voiceover (4 segments)"
```

---

### Task 5: 剪映混剪 (Manual)

**Input:**
- 杨梦表情视频: 按 yangmun_clip_hint 从已有素材库选取
  - S01 shock: `day5-yangmun/S01-shock.mp4`
  - S02 tension: `day5-yangmun/S02-determined.mp4`
  - S03 reversal: `day6-yangmun/S03.mp4`
  - S04 warm: `day5-yangmun/S05-warm.mp4`
- 故事视频: `docs/content/output/day10-yangmun/S01-01.mp4`, `S02-01.mp4`, `S03-01.mp4`
- TTS 配音: `docs/content/assets/voiceover/day10-yangmun/S01.mp3` - `S04.mp3`

**混剪顺序:**
```
杨梦(shock) → 故事(S01-01) → 杨梦(tension) → 故事(S02-01) → 杨梦(reversal) → 故事(S03-01) → 杨梦(warm+CTA)
```

**剪映步骤:**
1. 导入所有素材
2. 按 yangmun_clip_hint 对应的杨梦视频 + 故事视频交替排列
3. 合并 TTS 配音（4段拼接）
4. 添加 KTV 字幕（sync to voiceover）
5. 添加文字卡片: "所有备胎一夜转正" / "没有伤痕累累哪来皮糙肉厚"
6. 调色: S01冷 → S02暖 → S03冷暖交替 → S04暖金
7. 添加 "AI生成内容" 水印 (3秒，左上)
8. 导出: 1080x1920, 24fps, H.264

---

### Task 6: Upload Copy (Douyin)

**推荐标题:** 备胎转正那天 全世界都安静了

**文案:**
十年没有名字，没有人鼓掌，没有人看见。但它一直在那里。你的备胎准备了几年？

#任正非 #华为 #备胎 #芯片 #海思 #逆袭 #自强

**备选标题:**
1. 被制裁那天 任正非什么也没说
2. 十年没有名字 但它一直在那里

---

### Task Summary

| Task | Description | Type | Est. Time |
|------|-------------|------|-----------|
| 1 | Create config (v2 format) | DONE | - |
| 2 | Generate Seedream story images (3) | API call | 3 min |
| 3 | Generate Kling story videos (3) | API call | 5 min |
| 4 | Generate TTS voiceover (4 segments) | API call | 2 min |
| 5 | 剪映混剪 | manual | 15-20 min |
| 6 | Upload copy | done | - |
