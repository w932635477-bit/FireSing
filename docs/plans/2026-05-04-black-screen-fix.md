# Black Screen Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate 48.6s of black frames in the v3 video by downloading Unsplash images, expanding config durations, and removing black padding from compose.py.

**Architecture:** Three changes: (1) new unsplash-download.py script reads config atmosphere entries and downloads missing images, (2) config JSON expands atmosphere array from 4 to 10 and recalculates storyboard durations to match voiceover, (3) compose.py removes black padding and uses last-frame freeze for tiny gaps.

**Tech Stack:** Python 3, requests, Unsplash API, FFmpeg

---

### Task 1: Create unsplash-download.py

**Files:**
- Create: `docs/content/scripts/unsplash-download.py`

**Step 1: Write the script**

```python
#!/usr/bin/env python3
"""
Download atmosphere images from Unsplash based on config JSON.
Reads the 'atmosphere' array, skips existing files, downloads missing ones.

Usage:
  source docs/content/.env
  python3 unsplash-download.py --config config/unemploy-story-04-zhangwei-v3.json
  python3 unsplash-download.py --config config/xxx.json --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"


def download_atmosphere(config_path: Path, dry_run: bool = False) -> None:
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    atmosphere = config.get("atmosphere", [])
    if not atmosphere:
        print("No atmosphere entries in config.")
        return

    out_dir = BASE / "assets" / "unsplash" / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
    if not access_key:
        print("ERROR: UNSPLASH_ACCESS_KEY not set. Run: source docs/content/.env")
        sys.exit(1)

    for entry in atmosphere:
        entry_id = entry["id"]
        query = entry["query"]
        output = entry["output"]
        out_path = out_dir / output

        if out_path.exists():
            print(f"  SKIP {entry_id}: {output} already exists")
            continue

        if dry_run:
            print(f"  WOULD DOWNLOAD {entry_id}: query='{query}' → {out_path}")
            continue

        print(f"  DOWNLOAD {entry_id}: query='{query}' → {output}")
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": query, "per_page": 1, "orientation": "portrait"},
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            print(f"    WARNING: no results for '{query}'")
            continue

        image_url = results[0]["urls"]["regular"]
        img_resp = requests.get(image_url, timeout=30)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)
        print(f"    OK: {len(img_resp.content) // 1024}KB")

    print("\nDone.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Unsplash atmosphere images")
    parser.add_argument("--config", type=str, required=True, help="v3 config JSON")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = BASE / "config" / config_path.name
    if not config_path.exists():
        config_path = Path(args.config).resolve()
    if not config_path.exists():
        print(f"ERROR: config not found: {args.config}")
        sys.exit(1)

    download_atmosphere(config_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

**Step 2: Test with --dry-run**

Run:
```bash
cd /Users/weilei/FireSing/docs/content
source .env
python3 scripts/unsplash-download.py --config config/unemploy-story-04-zhangwei-v3.json --dry-run
```

Expected: Shows 4 SKIP (existing) + 6 WOULD DOWNLOAD (new entries). But we haven't updated config yet, so it shows 4 SKIP only. That's fine — this validates the script works with current config.

**Step 3: Commit**

```bash
git add docs/content/scripts/unsplash-download.py
git commit -m "feat: add unsplash-download.py for atmosphere image fetching"
```

---

### Task 2: Update config JSON — expand atmosphere + recalculate storyboard

**Files:**
- Modify: `docs/content/config/unemploy-story-04-zhangwei-v3.json`

**Step 1: Update atmosphere array**

Replace the `atmosphere` section (lines 35-40) with 10 entries:

```json
"atmosphere": [
  {"id": "AT01", "query": "empty warehouse industrial golden light", "output": "AT01-warehouse.jpg"},
  {"id": "AT02", "query": "desk lamp night workspace coffee phone", "output": "AT02-desk-night.jpg"},
  {"id": "AT03", "query": "building materials market tiles samples", "output": "AT03-market.jpg"},
  {"id": "AT04", "query": "coffee shop window phone typing natural light", "output": "AT04-coffee-shop.jpg"},
  {"id": "AT05", "query": "resume papers scattered on desk", "output": "AT05-resume-papers.jpg"},
  {"id": "AT06", "query": "empty office corridor fluorescent light", "output": "AT06-empty-office.jpg"},
  {"id": "AT07", "query": "man walking alone city street night", "output": "AT07-lonely-walk.jpg"},
  {"id": "AT08", "query": "smartphone screen glow dark room", "output": "AT08-phone-glow.jpg"},
  {"id": "AT09", "query": "tiles samples building materials showroom", "output": "AT09-tiles-showroom.jpg"},
  {"id": "AT10", "query": "sunrise through window hope morning", "output": "AT10-sunrise-hope.jpg"}
]
```

**Step 2: Update storyboard clips**

Replace the entire `storyboard` section (lines 48-90) with recalculated durations:

- S01 (vo 16.7s): SS01(3.5) + video7844862(5.5) + AT05-zoom(5.0) + TC01(3.0) = 17.0s
- S02 (vo 34.1s): video7844951(8.0) + AT01-zoom(6.0) + AT06-zoom(6.0) + SS02(4.0) + AT07-zoom(6.0) + TC02(4.0) = 34.0s
- S03 (vo 38.5s): SS03(3.5) + AT02-zoom(7.0) + video7644024(8.0) + AT08-zoom(6.0) + AT09-zoom(6.0) + AT03-zoom(5.0) + AT10-zoom(3.5) = 39.0s
- S04 (vo 14.8s): SS04(3.5) + video7643444(7.5) + TC03(3.8) = 14.8s
- S05 (vo 4.8s): AT04(3.0) + video7844862(2.0) = 5.0s

```json
"storyboard": [
  {
    "segment": "S01",
    "clips": [
      {"type": "screenshot", "ref": "SS01", "duration": 3.5, "beat": "hook", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "curiosity→shock"},
      {"type": "video_clip", "ref": "面试/7844862-hd_1080_1920_30fps_副本", "duration": 5.5, "beat": "context", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "shock→self_deprecating"},
      {"type": "atmosphere", "ref": "AT05", "zoom": true, "duration": 5.0, "beat": "mood", "shot_type": "WS", "camera_move": "slow dolly in", "emotion_arc": "resignation"},
      {"type": "text_card", "ref": "TC01", "duration": 3.0, "beat": "punchline", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "self_deprecating"}
    ]
  },
  {
    "segment": "S02",
    "clips": [
      {"type": "video_clip", "ref": "面试/7844951-hd_1080_1920_30fps_副本", "duration": 8.0, "beat": "context", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "resignation"},
      {"type": "atmosphere", "ref": "AT01", "zoom": true, "duration": 6.0, "beat": "mood", "shot_type": "WS", "camera_move": "slow dolly in", "emotion_arc": "loneliness"},
      {"type": "atmosphere", "ref": "AT06", "zoom": true, "duration": 6.0, "beat": "mood", "shot_type": "WS", "camera_move": "slow dolly in", "emotion_arc": "isolation"},
      {"type": "screenshot", "ref": "SS02", "duration": 4.0, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "frustration"},
      {"type": "atmosphere", "ref": "AT07", "zoom": true, "duration": 6.0, "beat": "mood", "shot_type": "MS", "camera_move": "slow dolly in", "emotion_arc": "defeat"},
      {"type": "text_card", "ref": "TC02", "duration": 4.0, "beat": "dark_humor", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "self_deprecating"}
    ]
  },
  {
    "segment": "S03",
    "clips": [
      {"type": "screenshot", "ref": "SS03", "duration": 3.5, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "surprise"},
      {"type": "atmosphere", "ref": "AT02", "zoom": true, "duration": 7.0, "beat": "mood", "shot_type": "MS", "camera_move": "slow dolly in", "emotion_arc": "contemplation"},
      {"type": "video_clip", "ref": "面试/7644024-uhd_2160_4096_25fps_副本", "duration": 8.0, "beat": "turning_point", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "realization"},
      {"type": "atmosphere", "ref": "AT08", "zoom": true, "duration": 6.0, "beat": "mood", "shot_type": "CU", "camera_move": "slow dolly in", "emotion_arc": "reflection"},
      {"type": "atmosphere", "ref": "AT09", "zoom": true, "duration": 6.0, "beat": "mood", "shot_type": "MS", "camera_move": "slow dolly in", "emotion_arc": "nostalgia"},
      {"type": "atmosphere", "ref": "AT03", "zoom": true, "duration": 5.0, "beat": "mood", "shot_type": "MS", "camera_move": "locked", "emotion_arc": "regret→hope"},
      {"type": "atmosphere", "ref": "AT10", "zoom": true, "duration": 3.5, "beat": "mood", "shot_type": "WS", "camera_move": "slow dolly in", "emotion_arc": "hope"}
    ]
  },
  {
    "segment": "S04",
    "clips": [
      {"type": "screenshot", "ref": "SS04", "duration": 3.5, "beat": "evidence", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "action"},
      {"type": "video_clip", "ref": "面试/7643444-uhd_2160_4096_25fps_副本", "duration": 7.5, "beat": "resolve", "shot_type": "MS", "camera_move": "handheld", "emotion_arc": "confidence"},
      {"type": "text_card", "ref": "TC03", "duration": 3.8, "beat": "punchline", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "conviction"}
    ]
  },
  {
    "segment": "S05",
    "clips": [
      {"type": "atmosphere", "ref": "AT04", "zoom": false, "duration": 3.0, "beat": "cta", "shot_type": "WS", "camera_move": "slow pull out", "emotion_arc": "warmth"},
      {"type": "video_clip", "ref": "面试/7844862-hd_1080_1920_30fps_副本", "duration": 2.0, "beat": "cta", "shot_type": "CU", "camera_move": "locked", "emotion_arc": "invitation"}
    ]
  }
]
```

**Step 3: Validate JSON**

Run: `python3 -c "import json; json.load(open('docs/content/config/unemploy-story-04-zhangwei-v3.json')); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add docs/content/config/unemploy-story-04-zhangwei-v3.json
git commit -m "feat: expand atmosphere to 10 images + recalculate storyboard durations"
```

---

### Task 3: Download new Unsplash images

**Prerequisites:** Task 1 and Task 2 complete.

**Step 1: Run download script**

Run:
```bash
cd /Users/weilei/FireSing/docs/content
source .env
python3 scripts/unsplash-download.py --config config/unemploy-story-04-zhangwei-v3.json
```

Expected: 4 SKIP (AT01-AT04 exist) + 6 downloads (AT05-AT10).

**Step 2: Verify files exist**

Run: `ls -la docs/content/assets/unsplash/unemploy-story-04-zhangwei-v3/`
Expected: 10 .jpg files (AT01 through AT10).

**Step 3: Commit downloaded assets**

```bash
git add docs/content/assets/unsplash/unemploy-story-04-zhangwei-v3/
git commit -m "chore: add 6 new Unsplash atmosphere images for black screen fix"
```

---

### Task 4: Remove black padding from compose.py

**Files:**
- Modify: `docs/content/scripts/medvi-compose.py:169-187`

**Step 1: Replace black padding with last-frame freeze**

In `build_segment_clips()`, replace lines 169-187 (the "Pad visual if shorter than voiceover" block) with:

```python
    # Pad visual if shorter than voiceover — freeze last frame
    visual_dur = get_duration(seg_visual)
    if visual_dur < vo_duration - 0.1:
        pad_dur = vo_duration - visual_dur
        print(f"  Freeze-pad {pad_dur:.1f}s (visual {visual_dur:.1f}s < vo {vo_duration:.1f}s)")
        freeze = temp_dir / f"{segment_id}_freeze.mp4"
        run([
            "ffmpeg", "-y", "-i", str(seg_visual),
            "-vf", f"select='eq(n,0)',trim=end=1,setpts=PTS-STARTPTS,"
                   f"tpad=stop=-1:stop_mode=clone:dur={pad_dur:.3f},"
                   f"scale=1080:1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
            "-t", f"{pad_dur:.3f}",
            str(freeze)
        ], f"freeze-frame {segment_id}")
        freeze_list = temp_dir / f"{segment_id}_freeze_list.txt"
        freeze_list.write_text(f"file '{seg_visual}'\nfile '{freeze}'\n")
        seg_visual_frozen = temp_dir / f"{segment_id}_visual_frozen.mp4"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(freeze_list), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
             str(seg_visual_frozen)], f"{segment_id}-freeze-concat")
        seg_visual = seg_visual_frozen
```

**Step 2: Verify the edit is correct**

Run: `python3 -c "import ast; ast.parse(open('docs/content/scripts/medvi-compose.py').read()); print('syntax OK')"`
Expected: `syntax OK`

**Step 3: Commit**

```bash
git add docs/content/scripts/medvi-compose.py
git commit -m "fix: replace black padding with last-frame freeze in compose.py"
```

---

### Task 5: End-to-end test — dry run

**Step 1: Run compose.py dry-run**

Run:
```bash
cd /Users/weilei/FireSing/docs/content
python3 scripts/medvi-compose.py --config config/unemploy-story-04-zhangwei-v3.json --dry-run
```

Expected: Shows all segments with their clip counts and durations. No errors about missing assets.

**Step 2: Run full compose**

Run:
```bash
python3 scripts/medvi-compose.py --config config/unemploy-story-04-zhangwei-v3.json
```

Expected:
- No "Padding Xs" messages (or very small <1s freeze-pads)
- No ERROR messages
- Output file at `docs/content/output/unemploy-story-04-zhangwei-v3/unemploy-story-04-zhangwei-v3-rough-cut.mp4`
- Duration ≈ 108-110s (voiceover total + opening)
- No black frames visible

**Step 3: Verify output**

Run: `ffprobe -v error -show_entries format=duration -of csv=p=0 docs/content/output/unemploy-story-04-zhangwei-v3/unemploy-story-04-zhangwei-v3-rough-cut.mp4`
Expected: ~108-110s

---

### Task 6: Commit final state

**Step 1: Verify no unintended changes**

Run: `git status`
Expected: Only the expected modified/new files from Tasks 1-4.

**Step 2: Final commit if needed**

If any uncommitted files remain from the compose run (temp files should be in output dir, not committed):

```bash
git status
# Review and commit any remaining changes
```
