# Medvi v3 Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 config-driven 的 Medvi v3 失业系列生产管线：CLI 入口 + 通用合成脚本 + spec 文档更新。

**Architecture:** medvi-produce.py（CLI 入口）调度 6 个 stage，每个 stage 调用现有子脚本或内置逻辑。medvi-compose.py 从硬编码的 compose-unemploy-story-01.py 重构为读取 storyboard config 的通用合成器。

**Tech Stack:** Python 3, FFmpeg, Playwright, Unsplash API, Gemini TTS API

---

### Task 1: Create v3 config JSON for Zhang Wei #1

**Files:**
- Create: `docs/content/config/unemploy-story-01-zhangwei-v3.json`

**Context:** This config drives the entire pipeline. Based on the design doc schema (§2). Uses the existing Zhang Wei assets (screenshots, atmosphere photos, text cards, voiceover) as initial test data.

**Step 1: Write the v3 config JSON**

Create `docs/content/config/unemploy-story-01-zhangwei-v3.json` with the full storyboard matching what compose-unemploy-story-01.py currently does:

```json
{
  "video_id": "unemploy-story-01-zhangwei",
  "version": "3.0",
  "series": "unemploy-story",
  "workflow_mode": "unemploy",

  "global": {
    "target_duration_sec": 80,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon",
    "opening_file": "unemploy-story-opening-v1.mp4"
  },

  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "S01", "emotion": "代入", "text": "38岁，建材行业干了12年。投了几十份简历，没人要。12年经验，在HR眼里就是一张废纸。"},
      {"id": "S02", "emotion": "希望", "text": "失业第三个月，装修群里有人问瓷砖怎么选。我回了一大段，那人私信说：哥你太专业了，我给你发个红包吧。那天晚上我睡不着，不是激动，是后悔。12年行业知识，我从来没想过主动拿出来。"},
      {"id": "S03", "emotion": "力量", "text": "我花了三天把经验列成清单。建材避坑指南、报价单审查、全屋材料规划。闲鱼发了个帖子，第二周来了3个人，第二个月赚了4000多。没找到工作，但经验在帮我赚钱。"},
      {"id": "S04", "emotion": "力量", "text": "你这些年攒下来的东西，到底值多少钱。你做了10年的行业，门外汉花多少钱都买不到你的经验。你的经验不是废纸，是你还没包装过的产品。"},
      {"id": "S05", "emotion": "参与", "text": "你做什么行业？评论区告诉我，我帮你拆成能卖的经验。"}
    ]
  },

  "screenshots": [
    {"id": "SS01", "template": "tpl-boss-search-zhangwei.html", "output": "SS01-boss-search.png"},
    {"id": "SS02", "template": "tpl-resume-stats-zhangwei.html", "output": "SS02-resume-stats.png"},
    {"id": "SS03", "template": "tpl-wechat-positive-zhangwei.html", "output": "SS03-wechat-positive.png"},
    {"id": "SS04", "template": "tpl-dingtalk-leave.html", "output": "SS04-dingtalk-leave.png"},
    {"id": "SS05", "template": "tpl-wechat-reject.html", "output": "SS05-wechat-reject.png"}
  ],

  "atmosphere": [
    {"id": "AT01", "query": "empty warehouse industrial", "output": "AT01-warehouse.jpg"},
    {"id": "AT02", "query": "desk lamp night workspace dark", "output": "AT02-desk-lamp.jpg"},
    {"id": "AT03", "query": "empty office night dark", "output": "AT03-empty-office.jpg"},
    {"id": "AT04", "query": "phone light face dark room", "output": "AT04-phone-light.jpg"},
    {"id": "AT05", "query": "laptop desk working late", "output": "AT05-laptop-desk.jpg"},
    {"id": "AT06", "query": "coffee shop window natural light", "output": "AT06-coffee-shop.jpg"}
  ],

  "text_cards": [
    {"id": "TC01", "lines": ["12年经验", "在HR眼里 就是一张废纸"], "style": "medvi", "bg_image": "AT02-desk-lamp.jpg", "duration": 4.0},
    {"id": "TC02", "lines": ["你的经验 不是废纸", "是没包装过的产品"], "style": "medvi", "bg_image": "AT05-laptop-desk.jpg", "duration": 4.0},
    {"id": "TC03", "lines": ["你做什么行业？", "评论区打出来 我帮你拆"], "style": "medvi", "bg_image": "AT06-coffee-shop.jpg", "duration": 4.0}
  ],

  "storyboard": [
    {
      "segment": "S01",
      "clips": [
        {"type": "screenshot", "ref": "SS01", "zoom": false, "pct": 0.55},
        {"type": "screenshot", "ref": "SS02", "zoom": true, "pct": 0.45},
        {"type": "text_card", "ref": "TC01", "duration": 4.0}
      ]
    },
    {
      "segment": "S02",
      "clips": [
        {"type": "atmosphere", "ref": "AT01", "zoom": true, "pct": 0.3},
        {"type": "screenshot", "ref": "SS03", "zoom": false, "pct": 0.4},
        {"type": "atmosphere", "ref": "AT02", "zoom": true, "pct": 0.3}
      ]
    },
    {
      "segment": "S03",
      "clips": [
        {"type": "screenshot", "ref": "SS04", "zoom": false, "pct": 0.0875},
        {"type": "screenshot", "ref": "SS02", "zoom": false, "pct": 0.0875},
        {"type": "screenshot", "ref": "SS05", "zoom": false, "pct": 0.0875},
        {"type": "atmosphere", "ref": "AT03", "zoom": true, "pct": 0.0875},
        {"type": "atmosphere", "ref": "AT03", "zoom": false, "pct": 0.05},
        {"type": "atmosphere", "ref": "AT05", "zoom": true, "pct": 0.6}
      ]
    },
    {
      "segment": "S04",
      "clips": [
        {"type": "atmosphere", "ref": "AT04", "zoom": true, "pct": 0.6},
        {"type": "text_card", "ref": "TC02", "duration": 4.0},
        {"type": "atmosphere", "ref": "AT05", "zoom": true, "pct": 0.4}
      ]
    },
    {
      "segment": "S05",
      "clips": [
        {"type": "atmosphere", "ref": "AT06", "zoom": true, "pct": 0.6},
        {"type": "text_card", "ref": "TC03", "duration": 4.0}
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
      "12年经验在HR眼里就是废纸？他失业后靠经验月赚4000",
      "失业后被装修群一个红包点醒：12年经验不该是废纸",
      "投几十份简历没人要，他反而靠经验月入4000，怎么做到的"
    ],
    "tags": ["#失业", "#经验变现", "#38岁", "#被裁员", "#中年危机", "#闲鱼赚钱", "#行业经验", "#失业逆袭", "#职场", "#建材"]
  }
}
```

**Step 2: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('docs/content/config/unemploy-story-01-zhangwei-v3.json')); print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add docs/content/config/unemploy-story-01-zhangwei-v3.json
git commit -m "feat: v3 config JSON for Zhang Wei #1 (test data for pipeline)"
```

---

### Task 2: Create medvi-compose.py (generic composition script)

**Files:**
- Create: `docs/content/scripts/medvi-compose.py`
- Reference: `docs/content/scripts/compose-unemploy-story-01.py` (extract core logic)

**Context:** This is the core of v3. It reads a v3 config JSON and produces a rough-cut MP4. All the hardcoded Zhang Wei logic in compose-unemploy-story-01.py becomes generic config-driven code.

**Step 1: Write medvi-compose.py**

Create `docs/content/scripts/medvi-compose.py` with these components:

1. **Config loading + path resolution**: Read JSON, build asset directories
2. **FFmpeg helpers** (extracted from compose-unemploy-story-01.py):
   - `run(cmd, label)` — subprocess wrapper
   - `image_to_video(image, duration, output, zoom=False)` — static image → video clip
   - `concat_video_audio(video, audio, output)` — merge audio track
   - `get_duration(path)` — ffprobe duration
3. **Asset lookup**: Given a ref like "SS01", find the file in the right directory
4. **build_segment_clips**: The core function that replaces hardcoded S01/S02/S03 logic
5. **Opening hook prepend**: Re-encode opening to 24fps
6. **BGM mixing**: amix with volume/fade config
7. **main()**: argparse with --config

Key design for `build_segment_clips`:
```
For each storyboard entry:
  1. Get voiceover duration for this segment
  2. Calculate total fixed-duration clip time (text_cards with explicit duration)
  3. Remaining time = vo_duration - total_text_card_duration
  4. For non-text-card clips, allocate remaining time by pct
  5. For each clip:
     - screenshot → image_to_video(SS_DIR/ref, allocated_dur, output, zoom)
     - atmosphere → image_to_video(AT_DIR/ref, allocated_dur, output, zoom)
     - text_card → re-encode TC_DIR/ref to 24fps
  6. Concat all clips for this segment → merge voiceover → add to final clips list
```

```python
#!/usr/bin/env python3
"""
Generic rough-cut composer for Medvi v3 videos.
Reads a v3 config JSON and produces a rough-cut MP4.

Usage:
  python3 medvi-compose.py --config config/unemploy-story-01-zhangwei-v3.json
  python3 medvi-compose.py --config config/xxx.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"

ASSET_DIRS = {
    "screenshot": BASE / "assets" / "screenshots",
    "atmosphere": BASE / "assets" / "unsplash",
    "text_card": BASE / "assets" / "textcards",
    "voiceover": BASE / "assets" / "voiceover",
    "bgm": BASE / "assets" / "bgm",
    "opening": BASE / "output" / "unemploy-story-opening",
}


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:4])}...")
    import subprocess
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:300]}")
        sys.exit(1)


def get_duration(path: Path) -> float:
    import subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def image_to_video(image: Path, duration: float, output: Path, zoom: bool = False) -> None:
    vf = "scale=1080:1920"
    if zoom:
        frames = int(duration * 24)
        vf = (
            f"scale=1152:2048,crop=1080:1920:36:64,"
            f"zoompan=z='min(zoom+0.0008,1.08)':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=1080x1920"
        )
    run([
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(image),
        "-c:v", "libx264", "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p", "-vf", vf, "-r", "24",
        str(output)
    ], f"img→vid {output.name}")


def concat_video_audio(video: Path, audio: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y",
        "-i", str(video), "-i", str(audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(output)
    ], f"merge {output.name}")


def find_asset(ref: str, asset_type: str, video_id: str) -> Path:
    """Find asset file by ref ID and type."""
    dir_path = ASSET_DIRS[asset_type] / video_id
    # Try exact filename patterns
    for ext in [".png", ".jpg", ".jpeg", ".mp4", ".mp3"]:
        p = dir_path / f"{ref}{ext}"
        if p.exists():
            return p
    # Try prefix match (e.g., TC01-waste-paper.mp4)
    for f in dir_path.iterdir():
        if f.name.startswith(ref + "-") or f.name.startswith(ref + "."):
            return f
    print(f"  ERROR: {asset_type} asset not found: {ref} in {dir_path}")
    sys.exit(1)


def build_segment_clips(
    segment_id: str,
    clips_config: list[dict],
    vo_duration: float,
    video_id: str,
    temp_dir: Path,
) -> Path:
    """Build all clips for one segment, concat them, merge voiceover."""
    # Separate text cards (fixed duration) from flexible clips
    text_card_clips = [c for c in clips_config if c["type"] == "text_card"]
    flexible_clips = [c for c in clips_config if c["type"] != "text_card"]

    fixed_time = sum(c.get("duration", 4.0) for c in text_card_clips)
    remaining = max(0.1, vo_duration - fixed_time)

    clip_files: list[Path] = []
    clip_idx = 0

    # Process flexible clips (screenshot / atmosphere)
    for clip_cfg in flexible_clips:
        pct = clip_cfg.get("pct", 1.0 / max(len(flexible_clips), 1))
        dur = remaining * pct
        zoom = clip_cfg.get("zoom", False)
        asset_type = clip_cfg["type"]  # "screenshot" or "atmosphere"
        ref = clip_cfg["ref"]
        asset_path = find_asset(ref, asset_type, video_id)
        out = temp_dir / f"{segment_id}_clip{clip_idx}.mp4"
        image_to_video(asset_path, dur, out, zoom=zoom)
        clip_files.append(out)
        clip_idx += 1

    # Process text cards
    for tc_cfg in text_card_clips:
        ref = tc_cfg["ref"]
        tc_src = find_asset(ref, "text_card", video_id)
        out = temp_dir / f"{segment_id}_tc{clip_idx}.mp4"
        run([
            "ffmpeg", "-y", "-i", str(tc_src),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            "-vf", "scale=1080:1920",
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

    # Merge voiceover
    vo_path = find_asset(segment_id, "voiceover", video_id)
    seg_merged = temp_dir / f"{segment_id}_merged.mp4"
    concat_video_audio(seg_visual, vo_path, seg_merged)
    return seg_merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Medvi v3 generic composer")
    parser.add_argument("--config", type=str, required=True, help="v3 config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = BASE / "config" / config_path.name
    if not config_path.exists():
        config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    storyboard = config["storyboard"]
    global_cfg = config["global"]
    bgm_cfg = config.get("bgm", {})

    out_dir = BASE / "output" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "temp_clips"
    temp_dir.mkdir(parents=True, exist_ok=True)

    final_output = out_dir / f"{video_id}-rough-cut.mp4"

    if args.dry_run:
        print(f"Dry run: {video_id}")
        for seg_entry in storyboard:
            seg_id = seg_entry["segment"]
            print(f"\n  {seg_id}: {len(seg_entry['clips'])} clips")
            for c in seg_entry["clips"]:
                print(f"    {c['type']} {c['ref']} zoom={c.get('zoom', False)} pct={c.get('pct', '-')}")
        return

    # Get voiceover durations
    print(f"Composing: {video_id}")
    vo_durations = {}
    for seg_entry in storyboard:
        seg_id = seg_entry["segment"]
        vo_path = find_asset(seg_id, "voiceover", video_id)
        vo_durations[seg_id] = get_duration(vo_path)

    total_vo = sum(vo_durations.values())
    print(f"Voiceover total: {total_vo:.1f}s")
    for seg_id, d in vo_durations.items():
        print(f"  {seg_id}: {d:.1f}s")

    clips: list[Path] = []

    # Opening hook
    opening_file = global_cfg.get("opening_file", "")
    if opening_file:
        opening_src = ASSET_DIRS["opening"] / opening_file
        if opening_src.exists():
            opening_24 = temp_dir / "opening_24fps.mp4"
            run([
                "ffmpeg", "-y", "-i", str(opening_src),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920",
                str(opening_24)
            ], "opening-24fps")
            clips.append(opening_24)
        else:
            print(f"  WARNING: opening file not found: {opening_src}")

    # Build each segment
    for seg_entry in storyboard:
        seg_id = seg_entry["segment"]
        vo_dur = vo_durations[seg_id]
        print(f"\n=== {seg_id} ({vo_dur:.1f}s) ===")
        merged = build_segment_clips(
            segment_id=seg_id,
            clips_config=seg_entry["clips"],
            vo_duration=vo_dur,
            video_id=video_id,
            temp_dir=temp_dir,
        )
        clips.append(merged)

    # Final concat
    concat_list = temp_dir / "final_list.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clips))
    no_bgm = temp_dir / "no_bgm.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(no_bgm)
    ], "FINAL-concat")

    # BGM mixing
    bgm_file = ASSET_DIRS["bgm"] / bgm_cfg.get("file", "") if bgm_cfg.get("file") else None
    if bgm_file and bgm_file.exists():
        video_dur = get_duration(no_bgm)
        bgm_volume = bgm_cfg.get("volume", 0.08)
        bgm_fade_in = bgm_cfg.get("fade_in", 2.0)
        bgm_fade_out = bgm_cfg.get("fade_out", 3.0)
        fade_out_start = max(0, video_dur - bgm_fade_out)

        print(f"  BGM: {bgm_file.name} at {bgm_volume*100:.0f}%")
        run([
            "ffmpeg", "-y",
            "-i", str(no_bgm),
            "-stream_loop", "-1", "-i", str(bgm_file),
            "-filter_complex",
            f"[1:a]volume={bgm_volume},afade=t=in:st=0:d={bgm_fade_in},"
            f"afade=t=out:st={fade_out_start:.3f}:d={bgm_fade_out}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(final_output)
        ], "FINAL+bgm")
    else:
        print("  No BGM, copying without music")
        import shutil
        shutil.copy2(str(no_bgm), str(final_output))

    # Report
    dur = get_duration(final_output)
    size = final_output.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {final_output}")
    print(f"  Duration: {dur:.1f}s")
    print(f"  Size: {size}MB")
    if dur > 90:
        print("  WARNING: Exceeds 90s target")
    elif dur < 60:
        print("  WARNING: Below 60s minimum!")


if __name__ == "__main__":
    main()
```

**Step 2: Validate syntax**

Run: `python3 -c "import ast; ast.parse(open('docs/content/scripts/medvi-compose.py').read()); print('SYNTAX OK')"`
Expected: SYNTAX OK

**Step 3: Test dry-run with Zhang Wei config**

Run: `cd docs/content && python3 scripts/medvi-compose.py --config config/unemploy-story-01-zhangwei-v3.json --dry-run`
Expected: Shows segment plan without executing FFmpeg

**Step 4: Commit**

```bash
git add docs/content/scripts/medvi-compose.py
git commit -m "feat: generic medvi-compose.py — config-driven video composition"
```

---

### Task 3: Verify medvi-compose.py produces identical output to hardcoded script

**Files:**
- Test: `docs/content/scripts/medvi-compose.py`
- Reference: `docs/content/scripts/compose-unemploy-story-01.py`

**Context:** Before trusting the generic script, verify it produces the same video structure as the original hardcoded script.

**Step 1: Run generic composer on Zhang Wei config**

Run: `cd docs/content && python3 scripts/medvi-compose.py --config config/unemploy-story-01-zhangwei-v3.json`

This requires existing assets (screenshots, atmosphere photos, text cards, voiceover) in `docs/content/assets/`. If any are missing, the script will report which ones.

**Step 2: Compare output duration**

Run: `ffprobe -v error -show_entries format=duration -of csv=p=0 docs/content/output/unemploy-story-01-zhangwei/unemploy-story-01-zhangwei-rough-cut.mp4`

Compare with the original output duration. They should be within 1-2 seconds (minor differences from rounding in pct allocation).

**Step 3: Visually spot-check**

Open the output video and verify:
- Opening hook present (1.5s)
- S01: Boss search + resume stats + text card
- S02: Warehouse + WeChat + desk lamp
- S03: Fast montage cuts
- S04: Phone light + text card
- S05: Coffee shop + CTA text card
- BGM audible under voiceover

**Step 4: Commit any fixes**

If adjustments are needed to the config or script, commit them:

```bash
git add docs/content/scripts/medvi-compose.py docs/content/config/unemploy-story-01-zhangwei-v3.json
git commit -m "fix: adjust compose logic to match original Zhang Wei output"
```

---

### Task 4: Create medvi-produce.py (CLI entry point)

**Files:**
- Create: `docs/content/scripts/medvi-produce.py`

**Context:** Single CLI entry point that dispatches to sub-scripts for each stage. Supports `--stage` (run specific stage), `--skip` (skip stages), and default "all stages" mode.

**Step 1: Write medvi-produce.py**

```python
#!/usr/bin/env python3
"""
Medvi v3 production pipeline — single CLI entry point.
Reads a v3 config JSON and runs the full production pipeline.

Usage:
  python3 medvi-produce.py --config config/unemploy-story-01-zhangwei-v3.json
  python3 medvi-produce.py --config config/xxx.json --stage screenshots
  python3 medvi-produce.py --config config/xxx.json --skip screenshots,voiceover
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
CONFIG_DIR = BASE / "config"

ALL_STAGES = ["screenshots", "atmosphere", "voiceover", "textcards", "compose", "upload_copy"]


def load_config(config_path: str) -> dict:
    p = Path(config_path)
    if not p.is_absolute():
        p = CONFIG_DIR / config_path
    if not p.exists():
        p = Path(config_path).resolve()
    if not p.exists():
        print(f"ERROR: config not found: {config_path}")
        sys.exit(1)
    with open(p) as f:
        return json.load(f)


def stage_screenshots(config: dict) -> None:
    """Render HTML templates to PNG screenshots."""
    screenshots = config.get("screenshots", [])
    if not screenshots:
        print("  No screenshots defined in config, skipping")
        return
    video_id = config["video_id"]
    out_dir = BASE / "assets" / "screenshots" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for ss in screenshots:
        template = ss["template"]
        output = out_dir / ss["output"]
        print(f"  Rendering: {template} -> {ss['output']}")
        subprocess.run([
            sys.executable, str(SCRIPTS / "screenshot-renderer.py"),
            "--template", template.replace(".html", ""),
            "--output", str(output),
        ], check=True)


def stage_atmosphere(config: dict) -> None:
    """Download Unsplash atmosphere photos."""
    atmosphere = config.get("atmosphere", [])
    if not atmosphere:
        print("  No atmosphere defined in config, skipping")
        return
    video_id = config["video_id"]
    out_dir = BASE / "assets" / "unsplash" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for at in atmosphere:
        query = at["query"]
        output = out_dir / at["output"]
        if output.exists():
            print(f"  Already exists: {at['output']}")
            continue
        print(f"  Downloading: {query} -> {at['output']}")
        subprocess.run([
            sys.executable, str(SCRIPTS / "unsplash-downloader.py"),
            "--query", query,
            "--output", str(output),
        ], check=True)


def stage_voiceover(config: dict) -> None:
    """Generate TTS voiceover via Gemini."""
    voiceover = config.get("voiceover", {})
    if not voiceover:
        print("  No voiceover defined in config, skipping")
        return
    video_id = config["video_id"]
    voice = voiceover.get("voice", "Charon")

    # Build a temporary TTS config in the format gemini-tts-batch.py expects
    tts_config = {
        "video_id": video_id,
        "segments": [
            {"id": s["id"], "emotion": s["emotion"], "voiceover_text": s["text"]}
            for s in voiceover["segments"]
        ]
    }
    tts_config_path = BASE / "config" / f"_{video_id}-tts-temp.json"
    with open(tts_config_path, "w", encoding="utf-8") as f:
        json.dump(tts_config, f, ensure_ascii=False, indent=2)

    print(f"  Voice: {voice}")
    subprocess.run([
        sys.executable, str(SCRIPTS / "gemini-tts-batch.py"),
        "--config", str(tts_config_path),
        "--voice", voice,
    ], check=True)


def stage_textcards(config: dict) -> None:
    """Render text cards via text-card-renderer.py."""
    text_cards = config.get("text_cards", [])
    if not text_cards:
        print("  No text_cards defined in config, skipping")
        return
    video_id = config["video_id"]
    out_dir = BASE / "assets" / "textcards" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    for tc in text_cards:
        tc_id = tc["id"]
        lines = tc["lines"]
        style = tc.get("style", "medvi")
        duration = tc.get("duration", 4.0)
        bg_image = tc.get("bg_image")
        output = out_dir / f"{tc_id}.mp4"

        bg_path = None
        if bg_image:
            candidate = BASE / "assets" / "unsplash" / video_id / bg_image
            if candidate.exists():
                bg_path = str(candidate)

        print(f"  Rendering: {tc_id} ({' '.join(lines)})")
        subprocess.run([
            sys.executable, str(SCRIPTS / "text-card-renderer.py"),
            "--lines", *lines,
            "--style", style,
            "--duration", str(duration),
            "--output", str(output),
        ] + (["--bg-image", bg_path] if bg_path else []), check=True)


def stage_compose(config: dict) -> None:
    """Compose final rough-cut video."""
    print("  Composing rough-cut...")
    config_path = BASE / "config" / f"{config['video_id']}-v3.json"
    # Try to find the config file
    if not config_path.exists():
        # Use the original path passed to medvi-produce
        pass
    subprocess.run([
        sys.executable, str(SCRIPTS / "medvi-compose.py"),
        "--config", config_path if config_path.exists() else _current_config_path,
    ], check=True)


def stage_upload_copy(config: dict) -> None:
    """Generate upload copy for Douyin."""
    uc = config.get("upload_copy", {})
    if not uc:
        print("  No upload_copy defined in config, skipping")
        return

    video_id = config["video_id"]
    platform = uc.get("platform", "douyin")
    titles = uc.get("title_candidates", [])
    tags = uc.get("tags", [])

    output_dir = BASE / "assets" / "upload-copy"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video_id}-{platform}.md"

    # Build upload copy markdown
    title = titles[0] if titles else video_id
    tags_str = " ".join(tags[:10])

    content = f"""# {platform.upper()}上传文案 — {video_id}

## 标题

{title}

## 标签

{tags_str}

---

## 备选标题（3选1）

"""
    for i, t in enumerate(titles, 1):
        content += f"{i}. {t}\n"

    content += f"""
## 发布建议

- 发布时间：晚8-10点（失业/焦虑人群活跃时段）
- 标签控制在10个以内
- 评论区预埋行业打卡引导
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Upload copy saved: {output_path}")


STAGE_FUNCS = {
    "screenshots": stage_screenshots,
    "atmosphere": stage_atmosphere,
    "voiceover": stage_voiceover,
    "textcards": stage_textcards,
    "compose": stage_compose,
    "upload_copy": stage_upload_copy,
}

# Global to track config path for compose stage
_current_config_path = ""


def main() -> None:
    global _current_config_path

    parser = argparse.ArgumentParser(description="Medvi v3 production pipeline")
    parser.add_argument("--config", type=str, required=True, help="v3 config JSON")
    parser.add_argument("--stage", type=str, help="Run single stage")
    parser.add_argument("--skip", type=str, help="Comma-separated stages to skip")
    args = parser.parse_args()

    _current_config_path = args.config
    config = load_config(args.config)
    video_id = config["video_id"]

    skip = set(args.skip.split(",")) if args.skip else set()
    stages = [args.stage] if args.stage else ALL_STAGES

    print(f"Medvi v3 — {video_id}")
    print(f"Stages: {', '.join(s for s in stages if s not in skip)}")
    print("=" * 50)

    start = datetime.now()
    for stage in stages:
        if stage in skip:
            print(f"\n[SKIP] {stage}")
            continue
        if stage not in STAGE_FUNCS:
            print(f"\n[WARN] Unknown stage: {stage}")
            continue
        print(f"\n{'=' * 20} {stage} {'=' * 20}")
        STAGE_FUNCS[stage](config)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'=' * 50}")
    print(f"Done in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
```

**Step 2: Validate syntax**

Run: `python3 -c "import ast; ast.parse(open('docs/content/scripts/medvi-produce.py').read()); print('SYNTAX OK')"`
Expected: SYNTAX OK

**Step 3: Test individual stages (non-destructive)**

Run: `cd docs/content && python3 scripts/medvi-produce.py --config config/unemploy-story-01-zhangwei-v3.json --stage upload_copy`
Expected: Creates upload copy markdown file

**Step 4: Commit**

```bash
git add docs/content/scripts/medvi-produce.py
git commit -m "feat: medvi-produce.py — CLI entry point for v3 pipeline"
```

---

### Task 5: Update video-production-spec.md with v3 chapters

**Files:**
- Modify: `docs/content/workflow/video-production-spec.md`

**Context:** Add v3-specific sections without modifying existing v2 content. Key additions: §0.2 mode routing, §2.5 opening hook, §6.5 Playwright screenshots, §6.6 Unsplash atmosphere, §9.3 v3 compose pipeline, §9.5 upload copy template.

**Step 1: Add §0.2 workflow mode routing after §0 section**

Insert after the existing §0 "如何使用本规范" section, before §1:

```markdown
### 0.2 工作流模式路由

JSON config 中的 `workflow_mode` 决定走哪套规则：

| workflow_mode | 适用 | 规则版本 |
|--------------|------|---------|
| `"unemploy"` | 失业系列（匿名真实故事） | **v3**（本文档新增章节） |
| `"yangmun"` | 杨梦IP系列 | v2（Day10 起生效） |

v3 模式标记：JSON config 中 `version` 为 `"3.0"` 时按 v3 规则执行。
```

**Step 2: Add §2.5 opening hook spec (after §2 钩子设计规范)**

```markdown
### 2.5 统一开场钩子（v3 失业系列 MUST）

> 详细设计见 unemploy-story-opening-spec.md

每条失业系列视频前 1.5s 使用统一开场动画：

| 规则 | 值 | 标记 |
|------|----|------|
| 时长 | 1.5s | MUST |
| 动画 | 黑屏→bass hit→"你的经验"淡入→"比你想象的值钱"滑入（金色"值钱"） | MUST |
| 切换方式 | 硬切到 S01（不做淡出） | MUST |
| 配置 | config 中 `global.opening_file` 指定 MP4 文件 | MUST |
| 复用 | 每集使用同一个 opening MP4 | MUST |

现有开场文件：`output/unemploy-story-opening/unemploy-story-opening-v1.mp4`（1.5s, 1080x1920）
```

**Step 3: Add §6.5 Playwright UI screenshots and §6.6 Unsplash atmosphere (after §6.4)**

```markdown
### 6.5 Playwright UI 截图（v3 失业系列）

v3 模式下，用 Playwright 渲染 HTML 模板替代 Seedream AI 生图。

| 规则 | 值 | 标记 |
|------|----|------|
| 模板目录 | `templates/tpl-{name}.html` | MUST |
| 渲染工具 | `screenshot-renderer.py` → 1080x1920 PNG | MUST |
| 模板类型 | Boss 搜索、简历数据面板、微信聊天、钉钉退群等 | — |
| 后处理 | 不做任何后处理，保持像素级真实 | MUST |
| 配置 | config 中 `screenshots[]` 数组 | MUST |

**模板复用：** 通用模板（Boss 搜索、简历面板）可跨视频复用，只需替换文字内容。

### 6.6 Unsplash 氛围空镜（v3 失业系列）

v3 模式下，用 Unsplash 图库照片替代 Kling AI 视频。

| 规则 | 值 | 标记 |
|------|----|------|
| 下载工具 | `unsplash-downloader.py` | MUST |
| 搜索关键词 | config 中 `atmosphere[].query`（英文） | MUST |
| 自动选图 | pick_best（按宽度+相关度打分） | SHOULD |
| 输出 | 1080x1920 JPG | MUST |
| FFmpeg 动画 | zoompan 效果（可选） | SHOULD |
| 配置 | config 中 `atmosphere[]` 数组 | MUST |
```

**Step 4: Add §9.3 v3 compose pipeline and §9.5 upload copy (after §9.2)**

```markdown
### 9.3 v3 FFmpeg 合成管线（失业系列）

v3 模式下，FFmpeg 做完整结构合成（不只是简单拼接）：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | Prepend 开场钩子 | opening_file re-encode 到 24fps |
| 2 | 逐 segment 构建 clips | 按 storyboard 配置分配时长 |
| 3 | Concat segment clips | 硬切拼接 |
| 4 | Merge voiceover | 配音对齐 |
| 5 | BGM amix | 8% volume, fade in/out |
| 6 | 输出粗剪 | `output/{video_id}/{video_id}-rough-cut.mp4` |

**BGM 配置：**

| 参数 | 默认值 | 说明 |
|------|-------|------|
| `bgm.file` | — | BGM MP3 文件名 |
| `bgm.volume` | 0.08 | 8% 音量（-22dB，不盖旁白） |
| `bgm.fade_in` | 2.0s | 渐入时长 |
| `bgm.fade_out` | 3.0s | 渐出时长 |

**工具：** `medvi-compose.py --config config/{video_id}-v3.json`

剪映仍负责：字幕、色彩校正、去AI滤镜、AI标识水印、封面帧。

### 9.5 上传文案模板（v3 失业系列）

v3 模式下，config 中 `upload_copy` 字段驱动文案生成。

**标题模板：** `{钩子反差句}？{转折结果句}`

**正文结构：** S01 浓缩 → S02 浓缩 → S03 浓缩 → CTA

**标签数量：** ≤ 10 个，优先 #失业 #经验变现 #{行业} #{年龄}

**工具：** `medvi-produce.py --config config/{video_id}-v3.json --stage upload_copy`

**完整文案示例见：** `assets/upload-copy/unemploy-story-01-zhangwei-douyin.md`
```

**Step 5: Update §8.4 配音 section — add Charon voice option**

Add after the existing Aoede rules:

```markdown
**失业系列 override：** 当 `workflow_mode: "unemploy"` 时，使用 Charon 男声第一人称自述，覆盖 Aoede 女声规则。失业系列 narrator profile 见 `gemini-tts-batch.py` 中 `NARRATOR_PROFILE_UNEMPLOY`。
```

**Step 6: Update §9.0 FFmpeg 分工原则 — add v3 note**

Add after existing text:

```markdown
**v3 模式例外：** 失业系列（`workflow_mode: "unemploy"`）FFmpeg 做结构合成（开场+文字卡片+空镜+截图+配音+BGM）。字幕和视觉后期仍由剪映完成。
```

**Step 7: Commit**

```bash
git add docs/content/workflow/video-production-spec.md
git commit -m "docs: add Medvi v3 pipeline chapters to production spec"
```

---

### Task 6: End-to-end validation

**Files:**
- Test: `docs/content/scripts/medvi-produce.py`
- Test: `docs/content/scripts/medvi-compose.py`

**Context:** Final validation that the entire pipeline works end-to-end with the Zhang Wei config.

**Step 1: Run upload_copy stage (safe, no external APIs)**

Run: `cd docs/content && python3 scripts/medvi-produce.py --config config/unemploy-story-01-zhangwei-v3.json --stage upload_copy`
Expected: Creates upload copy markdown

**Step 2: Run compose stage with existing assets**

Run: `cd docs/content && python3 scripts/medvi-produce.py --config config/unemploy-story-01-zhangwei-v3.json --stage compose`
Expected: Produces rough-cut MP4

**Step 3: Verify output**

Run: `ffprobe -v error -show_entries format=duration -of csv=p=0 docs/content/output/unemploy-story-01-zhangwei/unemploy-story-01-zhangwei-rough-cut.mp4`
Expected: ~88-90 seconds (1.5s opening + ~87s content)

**Step 4: Verify all stages listed**

Run: `cd docs/content && python3 scripts/medvi-produce.py --help`
Expected: Shows --config, --stage, --skip options

**Step 5: Final commit if any fixes needed**

```bash
git add -A docs/content/scripts/ docs/content/config/ docs/content/workflow/
git commit -m "fix: v3 pipeline end-to-end validation fixes"
```
