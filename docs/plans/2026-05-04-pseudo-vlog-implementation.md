# Pseudo-Vlog Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite unemploy-story-04 video with first-person conversational script, black humor, mixed media (interview clips + screenshots + atmosphere), and fix audio/visual sync.

**Architecture:** Modify `medvi-compose.py` to support `video_clip` type and fixed `duration` per clip (replacing `pct` proportion). Rewrite config JSON with new script, new storyboard with `beat`/`shot_type`/`camera_move`/`emotion_arc` fields per GitHub best practices. Re-run pipeline.

**Tech Stack:** Python 3, FFmpeg, Gemini TTS (Charon voice), Playwright screenshots, existing interview clip MP4s.

---

### Task 1: Add `video_clip` support to medvi-compose.py

**Files:**
- Modify: `docs/content/scripts/medvi-compose.py:19-26` (ASSET_DIRS)
- Modify: `docs/content/scripts/medvi-compose.py:76-89` (find_asset)
- Modify: `docs/content/scripts/medvi-compose.py:92-149` (build_segment_clips)

**Step 1: Add `video_clip` to ASSET_DIRS**

In `ASSET_DIRS` dict, add entry for video clips:

```python
ASSET_DIRS = {
    "screenshot": BASE / "assets" / "screenshots",
    "atmosphere": BASE / "assets" / "unsplash",
    "text_card": BASE / "assets" / "textcards",
    "voiceover": BASE / "assets" / "voiceover",
    "bgm": BASE / "assets" / "bgm",
    "opening": BASE / "output" / "unemploy-story-opening",
    "video_clip": BASE / ".." / ".." / "output",  # docs/content/output/
}
```

**Step 2: Update find_asset for video_clip type**

For `video_clip`, the `ref` is a relative path under `docs/content/output/` (e.g., `"面试/7844862-hd_1080_1920_30fps_副本"`). The `find_asset` function needs to handle this:

```python
def find_asset(ref: str, asset_type: str, video_id: str) -> Path:
    """Find asset file by ref ID and type."""
    if asset_type == "video_clip":
        base_dir = ASSET_DIRS["video_clip"]
        # ref can be a relative path like "面试/7844862-hd_1080_1920_30fps_副本"
        for ext in [".mp4", ".mov"]:
            p = base_dir / f"{ref}{ext}"
            if p.exists():
                return p
        print(f"  ERROR: video_clip asset not found: {ref}")
        sys.exit(1)

    dir_path = ASSET_DIRS[asset_type] / video_id
    for ext in [".png", ".jpg", ".jpeg", ".mp4", ".mp3"]:
        p = dir_path / f"{ref}{ext}"
        if p.exists():
            return p
    for f in dir_path.iterdir():
        if f.name.startswith(ref + "-") or f.name.startswith(ref + "."):
            return f
    print(f"  ERROR: {asset_type} asset not found: {ref} in {dir_path}")
    sys.exit(1)
```

**Step 3: Rewrite build_segment_clips to support fixed duration and video_clip**

Replace the current `build_segment_clips` function. Key changes:
- If a clip has `duration` field, use that exact value (no pct calculation)
- If a clip has `pct` field (backwards compat), calculate from remaining time
- For `video_clip` type: trim the video file to the specified duration, scale to 1080x1920
- After all clips are built, check if visual total matches voiceover duration. If visual < voiceover, pad with a black frame at the end.

```python
def trim_video_clip(source: Path, duration: float, output: Path) -> None:
    """Trim a video file to exact duration, scale to 1080x1920."""
    run([
        "ffmpeg", "-y", "-i", str(source),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-an",
        str(output)
    ], f"video-clip {output.name}")


def build_segment_clips(
    segment_id: str,
    clips_config: list[dict],
    vo_duration: float,
    video_id: str,
    temp_dir: Path,
) -> Path:
    """Build all clips for one segment, concat them, merge voiceover."""
    # Separate clips with fixed duration from those needing proportion
    fixed_clips = [c for c in clips_config if "duration" in c]
    pct_clips = [c for c in clips_config if "duration" not in c]

    fixed_time = sum(c["duration"] for c in fixed_clips)
    remaining = max(0.1, vo_duration - fixed_time)

    clip_files: list[Path] = []
    clip_idx = 0

    # Process all clips in order
    for clip_cfg in clips_config:
        clip_type = clip_cfg["type"]
        ref = clip_cfg["ref"]
        out = temp_dir / f"{segment_id}_clip{clip_idx}.mp4"

        if "duration" in clip_cfg:
            dur = clip_cfg["duration"]
        else:
            pct = clip_cfg.get("pct", 1.0 / max(len(pct_clips), 1))
            dur = remaining * pct

        if clip_type == "video_clip":
            asset_path = find_asset(ref, "video_clip", video_id)
            trim_video_clip(asset_path, dur, out)
        elif clip_type in ("screenshot", "atmosphere"):
            asset_path = find_asset(ref, clip_type, video_id)
            zoom = clip_cfg.get("zoom", False)
            image_to_video(asset_path, dur, out, zoom=zoom)
        elif clip_type == "text_card":
            tc_src = find_asset(ref, "text_card", video_id)
            run([
                "ffmpeg", "-y", "-i", str(tc_src),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920",
                "-t", f"{dur:.3f}",
                str(out)
            ], f"TC-resize {ref}")

        clip_files.append(out)
        clip_idx += 1

    # Concat segment clips
    seg_list = temp_dir / f"{segment_id}_list.txt"
    seg_list.write_text("".join(f"file '{c}'\n" for c in clip_files))
    seg_visual = temp_dir / f"{segment_id}_visual.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(seg_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
         str(seg_visual)], f"{segment_id}-concat")

    # Verify visual duration matches voiceover, pad if needed
    visual_dur = get_duration(seg_visual)
    if visual_dur < vo_duration - 0.1:
        pad_dur = vo_duration - visual_dur
        print(f"  Padding {pad_dur:.1f}s (visual {visual_dur:.1f}s < vo {vo_duration:.1f}s)")
        # Generate black frame and concat
        black = temp_dir / f"{segment_id}_black.mp4"
        frames = max(1, int(pad_dur * 24))
        run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"color=c=black:s=1080x1920:d={pad_dur:.3f}:r=24",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            str(black)
        ], f"black-pad {segment_id}")
        pad_list = temp_dir / f"{segment_id}_pad_list.txt"
        pad_list.write_text(f"file '{seg_visual}'\nfile '{black}'\n")
        seg_visual_padded = temp_dir / f"{segment_id}_visual_padded.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(pad_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
             str(seg_visual_padded)], f"{segment_id}-pad-concat")
        seg_visual = seg_visual_padded

    # Merge voiceover — NO -shortest, audio plays in full
    vo_path = find_asset(segment_id, "voiceover", video_id)
    seg_merged = temp_dir / f"{segment_id}_merged.mp4"
    concat_video_audio(seg_visual, vo_path, seg_merged)
    return seg_merged
```

**Step 4: Verify the fix**

Run: `python3 docs/content/scripts/medvi-compose.py --config docs/content/config/unemploy-story-04-zhangwei-v2.json --dry-run`

Expected: dry-run output shows clips with types.

**Step 5: Commit**

```bash
git add docs/content/scripts/medvi-compose.py
git commit -m "feat: add video_clip type + fixed duration + black-frame padding to compose"
```

---

### Task 2: Rewrite config JSON with pseudo-vlog script and storyboard

**Files:**
- Create: `docs/content/config/unemploy-story-04-zhangwei-v3.json`

**Step 1: Write the new config**

Create `unemploy-story-04-zhangwei-v3.json` with the new first-person conversational script from the design doc. Key differences from v2:

- Voiceover text is rewritten as first-person conversational with black humor
- Storyboard uses fixed `duration` per clip (no `pct`)
- New clip type: `video_clip` referencing interview footage
- Storyboard includes GitHub best-practice fields: `beat`, `shot_type`, `camera_move`, `emotion_arc`
- Only 3 text cards (reduced from 5) — used only for punchlines

The voiceover segments:

```json
{
  "id": "S01", "emotion": "代入",
  "text": "你知道我这三个月投了多少简历吗？847份。我自己都数了，不是编的。收到3个面试，0个offer。你说我是不是该去买彩票？"
},
{
  "id": "S02", "emotion": "共鸣",
  "text": "38岁，建材行业干了12年。从仓库管理员干到区域经理。瓷砖地板卫浴五金，哪个牌子好哪个是贴牌哪个报价有水分，我闭着眼睛都知道。但在HR眼里呢？38岁建材人，就是一张废纸。嗯...说实话，废纸好歹还能卖五毛钱一斤。我连这个价都没有。"
},
{
  "id": "S03", "emotion": "希望",
  "text": "失业第三个月，装修业主群里有人问：瓷砖怎么选？怕被建材城坑。我回了一大段，从品牌到报价到怎么避坑，写了快半小时。那人私信我说：哥你太专业了，我给你发个红包吧。那天晚上我睡不着。不是激动。是后悔。12年的行业知识，我以前从来没想过，这玩意儿还能卖钱。"
},
{
  "id": "S04", "emotion": "力量",
  "text": "后来我花了三天把经验列了个清单。闲鱼发了个帖子，第二个月赚了4000多。847份简历教会我一件事：你的经验不是废纸，是你还没包装过的产品。"
},
{
  "id": "S05", "emotion": "参与",
  "text": "你做什么行业？评论区打出来，我帮你拆成能卖的经验。"
}
```

The storyboard (with GitHub best-practice fields):

```json
"storyboard": [
  {
    "segment": "S01",
    "clips": [
      {"type": "screenshot", "ref": "SS01", "duration": 3.0, "beat": "hook", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "curiosity→shock"},
      {"type": "video_clip", "ref": "面试/7844862-hd_1080_1920_30fps_副本", "duration": 4.0, "beat": "context", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "shock→self_deprecating"},
      {"type": "text_card", "ref": "TC01", "duration": 3.0, "beat": "punchline", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "self_deprecating"}
    ]
  },
  {
    "segment": "S02",
    "clips": [
      {"type": "video_clip", "ref": "面试/7844951-hd_1080_1920_30fps_副本", "duration": 6.0, "beat": "context", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "resignation"},
      {"type": "atmosphere", "ref": "AT01", "zoom": true, "duration": 5.0, "beat": "mood", "shot_type": "WS", "camera_move": "slow dolly in", "emotion_arc": "loneliness"},
      {"type": "screenshot", "ref": "SS02", "duration": 3.0, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "frustration"},
      {"type": "text_card", "ref": "TC02", "duration": 3.0, "beat": "dark_humor", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "self_deprecating"}
    ]
  },
  {
    "segment": "S03",
    "clips": [
      {"type": "screenshot", "ref": "SS03", "duration": 3.0, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "surprise"},
      {"type": "atmosphere", "ref": "AT02", "zoom": true, "duration": 5.0, "beat": "mood", "shot_type": "MS", "camera_move": "slow dolly in", "emotion_arc": "contemplation"},
      {"type": "video_clip", "ref": "面试/7644024-uhd_2160_4096_25fps_副本", "duration": 5.0, "beat": "turning_point", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "realization"},
      {"type": "atmosphere", "ref": "AT03", "zoom": true, "duration": 4.0, "beat": "mood", "shot_type": "MS", "camera_move": "locked", "emotion_arc": "regret→hope"}
    ]
  },
  {
    "segment": "S04",
    "clips": [
      {"type": "screenshot", "ref": "SS04", "duration": 3.0, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "action"},
      {"type": "video_clip", "ref": "面试/7643444-uhd_2160_4096_25fps_副本", "duration": 5.0, "beat": "resolve", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "confidence"},
      {"type": "text_card", "ref": "TC03", "duration": 3.5, "beat": "punchline", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "conviction"}
    ]
  },
  {
    "segment": "S05",
    "clips": [
      {"type": "atmosphere", "ref": "AT04", "zoom": false, "duration": 4.0, "beat": "cta", "shot_type": "WS", "camera_move": "slow pull out", "emotion_arc": "warmth"},
      {"type": "video_clip", "ref": "面试/7844862-hd_1080_1920_30fps_副本", "duration": 3.0, "beat": "cta", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "invitation"}
    ]
  }
]
```

Full text cards (only 3, for punchlines only):

```json
"text_cards": [
  {"id": "TC01", "lines": ["你说我是不是", "该去买彩票？"], "style": "medvi", "bg_image": "AT01-warehouse.jpg", "duration": 3.0},
  {"id": "TC02", "lines": ["废纸好歹能卖五毛一斤", "我连这个价都没有"], "style": "medvi", "bg_image": "AT01-warehouse.jpg", "duration": 3.0},
  {"id": "TC03", "lines": ["你的经验不是废纸", "是没包装过的产品"], "style": "medvi", "bg_image": "AT04-coffee-shop.jpg", "duration": 3.5}
]
```

Screenshots stay the same (SS01-SS05).
Atmosphere stays the same (AT01-AT04).

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-story-04-zhangwei-v3.json
git commit -m "feat: v3 config with pseudo-vlog script, black humor, video_clip storyboard"
```

---

### Task 3: Update TTS Director's Notes for conversational delivery

**Files:**
- Modify: `docs/content/scripts/gemini-tts-batch.py:136-166` (EMOTION_PROMPTS)

**Step 1: Update the "代入" emotion prompt**

The current "代入" Director's Notes say to speak calmly about being laid off. Change to sound like talking to a friend:

```python
"代入": {
    "profile": NARRATOR_PROFILE_UNEMPLOY,
    "scene": "开场跟朋友吐槽自己投简历的经历。",
    "director": "像跟老朋友聊天，不是演讲。开口要自然'你知道吗'。念数字'847'的时候要慢，一个字一个字念，像在回忆一个自己都不敢相信的数字。'该去买彩票'要带一点苦笑，不是真的觉得好笑，是那种'我能怎么办呢'的笑。允许语气词：嗯、说实话、你知道吗、你说。偶尔停顿一下，像在想怎么说。",
},
```

**Step 2: Update the "共鸣" emotion prompt**

```python
"共鸣": {
    "profile": NARRATOR_PROFILE_UNEMPLOY,
    "scene": "自嘲自己连废纸都不如。",
    "director": "先正常叙述，到了'废纸'那句声音要轻。然后停顿。'嗯...说实话'之后转成自嘲语气。'五毛钱一斤'要说得漫不经心，'我连这个价都没有'要轻，像自言自语。不是愤怒，是那种苦笑到麻木的感觉。结尾不要收太干净，留一点余味。",
},
```

**Step 3: Update the "希望" emotion prompt**

```python
"希望": {
    "profile": NARRATOR_PROFILE_UNEMPLOY,
    "scene": "转折点，发现经验能卖钱。",
    "director": "前面讲群里的事要平淡，像回忆一件普通的事。'哥你太专业了'那句话可以稍微模仿一下对方语气。然后'那天晚上我睡不着'之后要明显停顿。'不是激动'稍顿。'是后悔'要重。最后一句'这玩意儿还能卖钱'要带一种不可思议的感觉，像突然发现了什么。",
},
```

**Step 4: Commit**

```bash
git add docs/content/scripts/gemini-tts-batch.py
git commit -m "feat: update Director's Notes for conversational first-person delivery"
```

---

### Task 4: Run pipeline and verify AV sync

**Step 1: Run full pipeline**

```bash
cd /Users/weilei/FireSing
source docs/content/.env
python3 docs/content/scripts/medvi-produce.py --config docs/content/config/unemploy-story-04-zhangwei-v3.json
```

Expected: All 6 stages complete. Watch for:
- Voiceover segments generated (S01-S05) — total should be 70-90s
- Each segment's visual clips sum should be ≤ voiceover duration (padding fills the gap)
- No `-shortest` flag — audio plays in full
- Final output: `docs/content/output/unemploy-story-04-zhangwei-v3/unemploy-story-04-zhangwei-v3-rough-cut.mp4`

**Step 2: Verify AV sync**

```bash
ffprobe docs/content/output/unemploy-story-04-zhangwei-v3/unemploy-story-04-zhangwei-v3-rough-cut.mp4
```

Check:
- Duration matches total voiceover duration (should not be truncated)
- Resolution: 1080x1920
- Audio codec: AAC 192k

**Step 3: Spot-check voiceover**

Play the S01 audio file and verify:
- "你知道吗" sounds conversational, not robotic
- "847" is spoken slowly with pauses
- "该去买彩票" has a wry/self-deprecating tone

**Step 4: Commit**

```bash
git add docs/content/assets/voiceover/unemploy-story-04-zhangwei-v3/ docs/content/assets/textcards/unemploy-story-04-zhangwei-v3/ docs/content/assets/upload-copy/unemploy-story-04-zhangwei-v3-douyin.md
git commit -m "feat: unemploy-story-04 v3 pseudo-vlog pipeline outputs"
```

---

### Task 5: Manual review and post-production notes

This is a documentation task — record what the user needs to do in 剪映.

Write a post-production checklist:

```markdown
## 剪映后期清单

- [ ] 导入 rough-cut
- [ ] 加 1.5 秒统一开头（unemploy-story-opening-spec.md）
- [ ] 检查面试镜头画面是否与配音情绪匹配（不匹配就微调剪辑点）
- [ ] 加字幕（AI自动生成，校对关键数字：847、12年、4000）
- [ ] 加 AI 水印（左上角 "AI生成内容"）
- [ ] 调色：暖色调，轻微胶片感
- [ ] 导出：1080x1920，H.264，AAC
```
