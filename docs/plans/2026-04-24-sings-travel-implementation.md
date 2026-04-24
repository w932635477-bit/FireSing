# Sings Travel Duet (城市对唱) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Adapt the existing Sings pipeline to produce 30-60s city edu-duet videos, starting with a Chongqing pilot.

**Architecture:** Reuse existing Sings pipeline (Seedream + Kling + Suno + FFmpeg + CapCut). Key changes: new config template for travel format, FFmpeg script supports mixing official tourism footage with AI clips, only Yang Mun appears visually (male is voice-only).

**Tech Stack:** Python 3, Evolink API (Seedream 4.5, Kling 3.0, Suno v4.5), FFmpeg, CapCut (manual post)

**Design doc:** `docs/plans/2026-04-24-sings-travel-duet-design.md`

---

### Task 1: Create Travel Duet Config Template

**Files:**
- Create: `docs/content/config/sings-travel-template.json`

**Step 1: Create the template config**

Based on `sings-template.json` but adapted for travel:
- Segments: S01 Hook → S02 Highlight A → S03 Highlight B → S04 City Summary → S05 CTA
- Lyrics: 8 bars, city-themed duet (Yang Mun experiential + male factual)
- Audio: Suno duet, 125 bpm, travel/exploration vibe
- New fields: `city`, `highlights[]`, `official_footage[]`
- Publishing: dual platform (douyin + xiaohongshu)
- `reference_images.candidates_per_segment: 1` (cost optimized)
- `video_generation.candidates_per_segment: 1` (cost optimized)

```json
{
  "video_id": "sings-travel-template",
  "workflow": "sings",
  "version": "1.0",
  "created": "2026-04-24",
  "status": "template",
  "series": "sings-travel",
  "strategy_notes": "城市科普对唱模板。每期一个城市，杨梦用对唱介绍2个亮点，70%文旅局真实素材+30%AI杨梦画面",

  "city": "[城市名]",
  "highlights": [
    {"name": "[亮点A名称]", "type": "[attraction|food|culture]"},
    {"name": "[亮点B名称]", "type": "[attraction|food|culture]"}
  ],

  "global": {
    "target_duration_sec": 45,
    "max_duration_sec": 60,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": null,
    "style": "travel_edu_duet",
    "color_temperature": "natural_daylight",
    "accent_color": "#4a9eff",
    "bg_color": "#f0f4f8"
  },

  "lyrics": {
    "bpm": 125,
    "time_signature": "4/4",
    "style": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "suno_tags": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": ["[Hook提问：城市名+震撼点 ≤14字]", "[女声回应 ≤12字]"],
        "rhyme": "a",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": ["[亮点A体验描述 ≤12字]（女声）", "[亮点A知识背景 ≤12字]（男声）"],
        "rhyme": "e",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B03",
        "beat_count": 4,
        "lines": ["[亮点A感受 ≤12字]（女声）", "[亮点A总结 ≤12字 押韵]（合唱）"],
        "rhyme": "e",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B04",
        "beat_count": 4,
        "lines": ["[亮点B体验描述 ≤12字]（女声）", "[亮点B知识背景 ≤12字]（男声）"],
        "rhyme": "i",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B05",
        "beat_count": 4,
        "lines": ["[亮点B感受 ≤12字]（女声）", "[亮点B总结 ≤12字 押韵]（合唱）"],
        "rhyme": "i",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B06",
        "beat_count": 4,
        "lines": ["[城市气质总结 ≤12字]（女声）", "[城市标签 ≤10字]（男声）"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B07",
        "beat_count": 4,
        "lines": ["[旅行感悟 ≤12字]（合唱）", "[情感升华 ≤10字 押韵]（合唱）"],
        "rhyme": "ao",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B08",
        "beat_count": 4,
        "lines": ["[下一站提问 ≤12字]", "[互动引导 ≤10字 押韵]"],
        "rhyme": "a",
        "segment_ref": "S05",
        "type": "cta"
      }
    ]
  },

  "script": {
    "topic": "[选题：城市名+亮点]",
    "source": "城市科普对唱",
    "hook_type": "city_reveal",
    "cta_action": "下一站投票",
    "cta_keyword": "下一站去哪"
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 6,
      "shot_type": "wide",
      "emotion": "playful",
      "visual_source": "official_footage",
      "visual_description": "[城市震撼开场画面：地标/夜景/航拍]",
      "official_footage_query": "[城市名 landmark/aerial/night]",
      "lyrics_refs": ["B01"]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 8,
      "shot_type": "medium",
      "emotion": "excited",
      "visual_source": "mixed",
      "visual_description": "[亮点A真实画面 + 杨梦体验画面]",
      "official_footage_query": "[亮点A相关画面]",
      "reference_prompt": "[杨梦在亮点A场景的参考图prompt]",
      "lyrics_refs": ["B02", "B03"]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 8,
      "shot_type": "medium",
      "emotion": "warm",
      "visual_source": "mixed",
      "visual_description": "[亮点B真实画面 + 杨梦体验画面]",
      "official_footage_query": "[亮点B相关画面]",
      "reference_prompt": "[杨梦在亮点B场景的参考图prompt]",
      "lyrics_refs": ["B04", "B05"]
    },
    {
      "id": "S04",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "text_card",
      "emotion": "educational",
      "visual_description": "城市标签文字卡",
      "visual_source": "text_card",
      "text_card_config": {
        "lines": ["[城市标签1]", "[城市标签2]"],
        "font_size": 48,
        "font_color": "#2d2d2d",
        "bg_color": "#f0f4f8",
        "animation": "fade_in"
      },
      "lyrics_refs": ["B06", "B07"]
    },
    {
      "id": "S05",
      "type": "cta",
      "duration_sec": 6,
      "shot_type": "close-up",
      "emotion": "warm",
      "visual_source": "ai_generated",
      "visual_description": "[杨梦微笑直视镜头，CTA画面]",
      "reference_prompt": "[杨梦微笑参考图prompt]",
      "motion_prompt": "warm smile, direct eye contact, gentle movement",
      "lyrics_refs": ["B08"]
    }
  ],

  "official_footage": [
    {
      "description": "[素材描述]",
      "source": "tourism_board",
      "source_url": "[文旅局素材URL或本地路径]",
      "target_segment": "S01"
    }
  ],

  "audio": {
    "engine": "suno_ai",
    "mode": "custom",
    "style_prompt": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "negative_tags": "rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody",
    "style_weight": 0.9,
    "weirdness_constraint": 0.3,
    "output_format": "mp3",
    "extract_beats": true,
    "beat_tool": "librosa",
    "generation": {
      "model": "suno-v4.5",
      "custom_mode": true,
      "vocal_gender": "m"
    }
  },

  "beat_sync": {
    "enabled": true,
    "align_to": "bar_lines",
    "min_cut_interval_beats": 2,
    "max_cut_interval_beats": 4
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "resolution": "1440x2560",
    "candidates_per_segment": 1,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, cinematic, film grain"
  },

  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "candidates_per_segment": 1,
    "motion_intensity": 4
  },

  "compositing": {
    "engine": "ffmpeg",
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_lyrics",
    "subtitle_style": "ktv_dynamic"
  },

  "ai_labeling": {
    "enabled": true,
    "watermark_text": "AI生成内容",
    "watermark_duration_sec": 3,
    "watermark_position": "top_left",
    "watermark_font_size": 28,
    "watermark_opacity": 0.8,
    "metadata_key": "comment",
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和音乐"
  },

  "post_production": {
    "film_grain_intensity_pct": 0,
    "lens_glow_intensity_pct": 5,
    "saturation_adjust": 10,
    "contrast_adjust": 5,
    "sharpness_adjust": -2,
    "vignette": 0.05
  },

  "publishing": {
    "platforms": ["douyin", "xiaohongshu"],
    "title_candidates": [
      "[标题1：城市名+震撼点]",
      "[标题2：亮点+感受]",
      "[标题3：互动提问]"
    ],
    "tags": ["城市科普", "旅行", "杨梦", "城市对唱", "旅行音乐"],
    "douyin_tags": ["城市科普", "旅行", "AI旅行", "杨梦带你看世界", "城市对唱", "旅行音乐", "说唱城市"],
    "xiaohongshu_tags": ["城市科普", "旅行", "AI旅行", "杨梦", "城市对唱", "旅行音乐", "旅行攻略"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "杨梦在城市地标前 + 城市名大字 + 明亮旅行风格"
  }
}
```

**Step 2: Validate template loads**

Run: `python3 -c "import json; json.load(open('docs/content/config/sings-travel-template.json')); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add docs/content/config/sings-travel-template.json
git commit -m "feat: add sings-travel config template (城市对唱)"
```

---

### Task 2: Update FFmpeg Script for Mixed Footage

**Files:**
- Modify: `docs/content/scripts/ffmpeg-compose-sings.py`

**Step 1: Add official footage lookup to clip collection loop**

In the `main()` function, around line 280, the clip collection loop checks for Runway video, then reference image. Add support for `official_footage` — segments with `visual_source: "official_footage"` or `visual_source: "mixed"` can use a real video file from `output/{video_id}/footage/`.

Add a new helper function before `main()`:

```python
OFFICIAL_FOOTAGE_DIR_NAME = "footage"


def find_official_footage(seg_id: str, video_dir: Path) -> Path | None:
    """Find official tourism footage for a segment in output/{video_id}/footage/."""
    footage_dir = video_dir / OFFICIAL_FOOTAGE_DIR_NAME
    if not footage_dir.is_dir():
        return None
    for pattern in [f"{seg_id}.mp4", f"{seg_id}_footage.mp4"]:
        p = footage_dir / pattern
        if p.exists():
            return p
    # Fallback: any mp4 starting with seg_id
    for p in sorted(footage_dir.glob(f"{seg_id}*.mp4")):
        return p
    return None
```

**Step 2: Update clip collection loop**

In the `main()` function, update the clip collection loop (around line 280-301) to check for official footage:

```python
    for seg in segments:
        seg_id = seg["id"]
        clip_path = find_video_clip(seg_id, video_dir)
        is_text_card = seg.get("shot_type") == "text_card"
        ref_image = find_reference_image(seg)
        visual_source = seg.get("visual_source", "ai_generated")
        official_footage = find_official_footage(seg_id, video_dir)

        if is_text_card:
            seg["_video_id"] = video_id
            clips.append({"id": seg_id, "type": "text_card", "seg": seg})
        elif visual_source == "official_footage" and official_footage:
            clips.append({"id": seg_id, "type": "video", "path": official_footage, "seg": seg, "source": "official"})
        elif clip_path:
            clips.append({"id": seg_id, "type": "video", "path": clip_path, "seg": seg, "source": "kling"})
        elif official_footage and visual_source == "mixed":
            clips.append({"id": seg_id, "type": "video", "path": official_footage, "seg": seg, "source": "official"})
        elif ref_image:
            motion_idx = len(clips) % len(MOTIONS)
            clips.append({
                "id": seg_id,
                "type": "image",
                "image_path": ref_image,
                "motion": MOTIONS[motion_idx],
                "seg": seg,
            })
        else:
            print(f"  {seg_id}: SKIP — no video, image, or official footage found")
```

**Step 3: Update clip print to show source**

```python
    for c in clips:
        source_tag = c.get("source", "kburns")
        if c["type"] == "video":
            dur = get_duration(c["path"])
            print(f"  {c['id']}: [{source_tag}] {c['path'].name} ({dur:.1f}s)")
        elif c["type"] == "image":
            print(f"  {c['id']}: [KenBurns:{c['motion']}] {c['image_path'].name}")
        else:
            print(f"  {c['id']}: text_card")
```

**Step 4: Test with dry-run on existing config**

Run: `python3 docs/content/scripts/ffmpeg-compose-sings.py --config docs/content/config/outfit-day1-date.json --dry-run`
Expected: No errors (existing behavior preserved, no official footage found so falls through to existing logic)

**Step 5: Commit**

```bash
git add docs/content/scripts/ffmpeg-compose-sings.py
git commit -m "feat: support official tourism footage in FFmpeg sings composer"
```

---

### Task 3: Create Chongqing Pilot Config

**Files:**
- Create: `docs/content/config/city-chongqing.json`

**Step 1: Write the pilot config with real content**

City: 重庆, Highlights: 轻轨穿楼 + 九宫格火锅

```json
{
  "video_id": "city-chongqing",
  "workflow": "sings",
  "version": "1.0",
  "created": "2026-04-24",
  "status": "draft",
  "series": "sings-travel",
  "strategy_notes": "城市科普对唱Pilot：重庆8D魔幻城市，轻轨穿楼+九宫格火锅",

  "city": "重庆",
  "highlights": [
    {"name": "轻轨穿楼", "type": "attraction"},
    {"name": "九宫格火锅", "type": "food"}
  ],

  "global": {
    "target_duration_sec": 45,
    "max_duration_sec": 60,
    "min_duration_sec": 30,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "kling_seed": 12345,
    "style": "travel_edu_duet",
    "color_temperature": "warm_night",
    "accent_color": "#ff6b35",
    "bg_color": "#1a1a2e"
  },

  "lyrics": {
    "bpm": 125,
    "time_signature": "4/4",
    "style": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "suno_tags": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "bars": [
      {
        "id": "B01",
        "beat_count": 4,
        "lines": [
          "重庆这座城市你真的懂吗",
          "8D魔幻上上下下把你绕晕啦"
        ],
        "rhyme": "a",
        "segment_ref": "S01",
        "type": "hook"
      },
      {
        "id": "B02",
        "beat_count": 4,
        "lines": [
          "轻轨从居民楼里穿过去",
          "李子坝站设计用了立体思维"
        ],
        "rhyme": "i",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B03",
        "beat_count": 4,
        "lines": [
          "住在六楼列车就在窗边飞",
          "重庆人却说这没什么大不了嘞"
        ],
        "rhyme": "ei",
        "segment_ref": "S02",
        "type": "body"
      },
      {
        "id": "B04",
        "beat_count": 4,
        "lines": [
          "九宫格火锅辣到冒烟",
          "其实九格是九种不同温度区"
        ],
        "rhyme": "an",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B05",
        "beat_count": 4,
        "lines": [
          "中间格涮毛肚只要八秒",
          "边格慢炖牛油越煮越香飘"
        ],
        "rhyme": "ao",
        "segment_ref": "S03",
        "type": "body"
      },
      {
        "id": "B06",
        "beat_count": 4,
        "lines": [
          "上坡下坎爬出重庆的味",
          "魔幻8D赛博朋克第一城"
        ],
        "rhyme": "ei",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B07",
        "beat_count": 4,
        "lines": [
          "火锅和夜景是这座城的魂",
          "来过一次你就别想能转身"
        ],
        "rhyme": "en",
        "segment_ref": "S04",
        "type": "body"
      },
      {
        "id": "B08",
        "beat_count": 4,
        "lines": [
          "下一站你想去哪座城",
          "评论区告诉我你心动的旅程"
        ],
        "rhyme": "eng",
        "segment_ref": "S05",
        "type": "cta"
      }
    ]
  },

  "script": {
    "topic": "重庆：8D魔幻城市，轻轨穿楼+九宫格火锅",
    "source": "城市科普对唱",
    "hook_type": "city_reveal",
    "cta_action": "下一站投票",
    "cta_keyword": "下一站去哪"
  },

  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 6,
      "shot_type": "wide",
      "emotion": "playful",
      "visual_source": "official_footage",
      "visual_description": "重庆城市航拍夜景，洪崖洞灯光，江景",
      "official_footage_query": "chongqing aerial night hongyadong",
      "lyrics_refs": ["B01"]
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 8,
      "shot_type": "medium",
      "emotion": "excited",
      "visual_source": "mixed",
      "visual_description": "轻轨穿楼画面 + 杨梦在李子坝站前打卡",
      "official_footage_query": "chongqing monorail liziba building",
      "reference_file": "city-chongqing/S02-excited.png",
      "reference_prompt": "Travel editorial photograph, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream-colored linen shirt and light denim jacket, standing in front of the Chongqing Liziba monorail station where a train passes through a residential building, looking up excitedly at the train overhead, bright overcast sky, modern urban Chinese cityscape background, full-body shot, 50mm lens, vertical composition 9:16",
      "motion_prompt": "looking up in amazement, gentle wind movement, natural daylight",
      "lyrics_refs": ["B02", "B03"]
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 8,
      "shot_type": "medium",
      "emotion": "warm",
      "visual_source": "mixed",
      "visual_description": "火锅沸腾画面 + 杨梦在街边吃火锅",
      "official_footage_query": "chongqing hotpot nine-grid boiling",
      "reference_file": "city-chongqing/S03-warm.png",
      "reference_prompt": "Travel editorial photograph, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream-colored linen shirt, sitting at an outdoor street-side hotpot table in Chongqing, nine-grid divided red hotpot boiling in front of her, steam rising, holding chopsticks about to cook a piece of beef tripe, warm orange lighting from hotpot and street lanterns, lively night market atmosphere, waist-up shot, 50mm lens, vertical composition 9:16",
      "motion_prompt": "steam rising, warm ambient lighting, natural eating gesture",
      "lyrics_refs": ["B04", "B05"]
    },
    {
      "id": "S04",
      "type": "body",
      "duration_sec": 6,
      "shot_type": "text_card",
      "emotion": "educational",
      "visual_source": "text_card",
      "visual_description": "城市标签文字卡",
      "text_card_config": {
        "lines": ["魔幻8D城", "火锅之都"],
        "font_size": 48,
        "font_color": "#2d2d2d",
        "bg_color": "#1a1a2e",
        "animation": "fade_in"
      },
      "lyrics_refs": ["B06", "B07"]
    },
    {
      "id": "S05",
      "type": "cta",
      "duration_sec": 6,
      "shot_type": "close-up",
      "emotion": "warm",
      "visual_source": "ai_generated",
      "visual_description": "杨梦微笑直视镜头，CTA画面",
      "reference_file": "city-chongqing/S05-warm.png",
      "reference_prompt": "Warm intimate portrait, a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing minimal jewelry, natural makeup, warm and approachable expression, shot on Kodak Portra 400, natural skin texture, visible pores, fine hair strands, slight asymmetry, authentic beauty, NOT perfect, NOT retouched, wearing a cream-colored linen shirt, direct eye contact with camera, warm genuine smile, slightly tilted head, blurred Chongqing night cityscape with warm lights in background, soft catchlight in eyes, close-up face and shoulders, 85mm portrait lens, shallow depth of field, vertical composition 9:16",
      "motion_prompt": "warm smile, direct eye contact, gentle movement",
      "lyrics_refs": ["B08"]
    }
  ],

  "official_footage": [
    {
      "description": "重庆城市航拍夜景",
      "source": "tourism_board",
      "target_segment": "S01"
    },
    {
      "description": "李子坝轻轨穿楼",
      "source": "tourism_board",
      "target_segment": "S02"
    },
    {
      "description": "重庆九宫格火锅",
      "source": "tourism_board",
      "target_segment": "S03"
    }
  ],

  "audio": {
    "engine": "suno_ai",
    "api": "evolink",
    "mode": "custom",
    "style_prompt": "upbeat Chinese city pop duet, catchy melody, sing-song storytelling, travel adventure, warm acoustic guitar, light electronic beat, Chinese pop, 125 bpm",
    "negative_tags": "rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody",
    "style_weight": 0.9,
    "weirdness_constraint": 0.3,
    "output_format": "mp3",
    "extract_beats": true,
    "beat_tool": "librosa",
    "generation": {
      "model": "suno-v4.5",
      "custom_mode": true,
      "vocal_gender": "m"
    }
  },

  "beat_sync": {
    "enabled": true,
    "align_to": "bar_lines",
    "min_cut_interval_beats": 2,
    "max_cut_interval_beats": 4
  },

  "reference_images": {
    "engine": "seedream_4.5",
    "api": "evolink",
    "resolution": "1440x2560",
    "candidates_per_segment": 1,
    "style_suffix": "vertical composition 9:16",
    "negative_prompt": "airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, studio lighting, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, cinematic, film grain"
  },

  "video_generation": {
    "engine": "kling_v3",
    "mode": "image_to_video",
    "resolution": "720x1280",
    "duration_sec": 5,
    "fps": 24,
    "fixed_seed": true,
    "candidates_per_segment": 1,
    "motion_intensity": 4,
    "post_processing": {
      "trim_unstable_frames": true,
      "handheld_shake_pct": 5
    }
  },

  "compositing": {
    "engine": "ffmpeg",
    "transitions": "hard_cut",
    "subtitle_source": "auto_from_lyrics",
    "subtitle_style": "ktv_dynamic"
  },

  "ai_labeling": {
    "enabled": true,
    "watermark_text": "AI生成内容",
    "watermark_duration_sec": 3,
    "watermark_position": "top_left",
    "watermark_font_size": 28,
    "watermark_opacity": 0.8,
    "metadata_key": "comment",
    "metadata_value": "本视频由AI生成合成，包含AI生成的图像和音乐"
  },

  "post_production": {
    "film_grain_intensity_pct": 0,
    "lens_glow_intensity_pct": 5,
    "saturation_adjust": 10,
    "contrast_adjust": 5,
    "sharpness_adjust": -2,
    "vignette": 0.05
  },

  "publishing": {
    "platforms": ["douyin", "xiaohongshu"],
    "title_candidates": [
      "重庆的轻轨居然从楼里穿过去？8D城市太魔幻",
      "重庆火锅九宫格的秘密：每个格子温度不一样",
      "下一站去哪？杨梦带你用唱歌看重庆"
    ],
    "tags": ["城市科普", "重庆", "杨梦", "城市对唱", "旅行音乐"],
    "douyin_tags": ["城市科普", "重庆旅行", "AI旅行", "杨梦带你看世界", "城市对唱", "说唱城市", "重庆火锅", "李子坝轻轨"],
    "xiaohongshu_tags": ["城市科普", "重庆旅行", "AI旅行", "杨梦", "城市对唱", "旅行音乐", "重庆攻略", "重庆打卡"],
    "publish_times": ["12:00", "18:00"],
    "cover_description": "杨梦在洪崖洞前 + '重庆' 大字 + 霓虹夜景风格"
  }
}
```

**Step 2: Validate config loads**

Run: `python3 -c "import json; json.load(open('docs/content/config/city-chongqing.json')); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add docs/content/config/city-chongqing.json
git commit -m "feat: add city-chongqing pilot config (重庆轻轨穿楼+九宫格火锅)"
```

---

### Task 4: Generate Suno Duet Music

**Files:**
- Use: `docs/content/scripts/suno-rap-batch.py`
- Config: `docs/content/config/city-chongqing.json`

**Step 1: Source API keys**

```bash
source docs/content/.env
```

**Step 2: Generate music (dry-run first)**

```bash
cd /Users/weilei/FireSing
python3 docs/content/scripts/suno-rap-batch.py --config docs/content/config/city-chongqing.json --dry-run
```

Expected: Shows planned lyrics and style, no API call.

**Step 3: Generate music (live)**

```bash
python3 docs/content/scripts/suno-rap-batch.py --config docs/content/config/city-chongqing.json --count 1
```

Expected: Generates 1 duet track via Suno API, downloads mp3 to `docs/content/assets/rap/city-chongqing/`.

**Step 4: Verify output**

```bash
ls -la docs/content/assets/rap/city-chongqing/
```

Expected: At least 1 mp3 file, duration 30-60 seconds.

**Note:** If `suno-rap-batch.py` doesn't support `--config` flag for sings configs, check the script's `bars_to_suno_lyrics()` function — it reads `lyrics.bars` from config which matches our format. May need to verify the `--config` path handling.

**Step 5: Commit**

```bash
git add docs/content/assets/rap/city-chongqing/
git commit -m "feat: generate Suno duet music for city-chongqing pilot"
```

---

### Task 5: Prepare Chongqing Official Footage

**Files:**
- Create: `docs/content/output/city-chongqing/footage/`

**Step 1: Create footage directory**

```bash
mkdir -p docs/content/output/city-chongqing/footage
```

**Step 2: Source Chongqing tourism footage**

Find and download Chongqing official tourism footage from:
- 重庆文旅局官方抖音号
- 重庆文旅官方网站 (http://lyj.cq.gov.cn/)
- 抖音搜索"重庆文旅宣传片"

Rename and place files:
- `S01_footage.mp4` — 重庆城市航拍/夜景/洪崖洞 (for hook segment)
- `S02_footage.mp4` — 李子坝轻轨穿楼 (for highlight A segment)
- `S03_footage.mp4` — 九宫格火锅/火锅沸腾 (for highlight B segment)

**Step 3: Verify footage files**

```bash
for f in docs/content/output/city-chongqing/footage/*.mp4; do
  echo "$f: $(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$f")s"
done
```

Expected: 3 video files with valid durations.

**Note:** This is a manual step. The footage must be sourced by the user from official tourism channels. Document the source URLs in the config's `official_footage[].source_url` field.

**Step 4: Commit**

```bash
git add docs/content/output/city-chongqing/footage/
git commit -m "feat: add Chongqing official tourism footage for pilot"
```

---

### Task 6: Generate Yang Mun Images via Seedream

**Files:**
- Use: `docs/content/scripts/seedream-batch.py`
- Config: `docs/content/config/city-chongqing.json`
- Output: `docs/content/assets/references/city-chongqing/`

**Step 1: Create reference directory**

```bash
mkdir -p docs/content/assets/references/city-chongqing
```

**Step 2: Generate Yang Mun images (dry-run)**

```bash
source docs/content/.env
python3 docs/content/scripts/seedream-batch.py --config docs/content/config/city-chongqing.json --dry-run
```

Expected: Shows planned image prompts for S02, S03, S05 (segments with `reference_prompt`).

**Step 3: Generate images (live)**

```bash
python3 docs/content/scripts/seedream-batch.py --config docs/content/config/city-chongqing.json --candidates 1
```

Expected: Generates 3 images (S02 李子坝站前, S03 火锅桌旁, S05 微笑CTA) at 1440x2560.

**Step 4: Verify output**

```bash
ls -la docs/content/assets/references/city-chongqing/
```

Expected: 3 PNG files named S02-excited.png, S03-warm.png, S05-warm.png (or similar).

**Step 5: Commit**

```bash
git add docs/content/assets/references/city-chongqing/
git commit -m "feat: generate Yang Mun reference images for city-chongqing"
```

---

### Task 7: Generate Kling Videos from Yang Mun Images

**Files:**
- Use: `docs/content/scripts/kling-gen-batch.py`
- Config: `docs/content/config/city-chongqing.json`
- Output: `docs/content/output/city-chongqing/`

**Step 1: Generate Kling videos (dry-run)**

```bash
source docs/content/.env
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/city-chongqing.json --dry-run
```

Expected: Shows planned video generation for S02, S03, S05 (segments with reference images).

**Step 2: Generate videos (live)**

```bash
python3 docs/content/scripts/kling-gen-batch.py --config docs/content/config/city-chongqing.json --quality 720p --duration 5
```

Expected: Generates 3 x 5-second video clips from Yang Mun images.

**Step 3: Verify output**

```bash
ls -la docs/content/output/city-chongqing/*.mp4
```

Expected: 3 video files for S02, S03, S05.

**Step 4: Commit**

```bash
git add docs/content/output/city-chongqing/
git commit -m "feat: generate Kling videos for city-chongqing Yang Mun scenes"
```

---

### Task 8: FFmpeg Compose Pilot Video

**Files:**
- Use: `docs/content/scripts/ffmpeg-compose-sings.py`
- Config: `docs/content/config/city-chongqing.json`
- Output: `docs/content/output/city-chongqing-sings.mp4`

**Step 1: Dry-run compose**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/city-chongqing.json \
  --audio docs/content/assets/rap/city-chongqing/[latest_duet_file].mp3 \
  --dry-run
```

Expected: Shows clip plan with official footage + Kling videos + text card. No errors.

**Step 2: Compose video**

```bash
python3 docs/content/scripts/ffmpeg-compose-sings.py \
  --config docs/content/config/city-chongqing.json \
  --audio docs/content/assets/rap/city-chongqing/[latest_duet_file].mp3
```

Expected: Produces `docs/content/output/city-chongqing-sings.mp4`.

**Step 3: Verify output**

```bash
ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1 docs/content/output/city-chongqing-sings.mp4
```

Expected: Duration 30-60 seconds, resolution 720x1280.

**Step 4: Commit**

```bash
git add docs/content/output/city-chongqing-sings.mp4
git commit -m "feat: compose city-chongqing pilot video (FFmpeg)"
```

---

### Task 9: CapCut Post-Production (Manual)

**Files:**
- Input: `docs/content/output/city-chongqing-sings.mp4`
- Output: Final video for publishing

**Manual steps in CapCut:**
1. Import `city-chongqing-sings.mp4`
2. Add K-style dynamic lyrics subtitles (sync to Suno audio)
3. Add info cards: "重庆" city name card, "轻轨穿楼" / "九宫格火锅" highlight labels
4. Add transitions between segments
5. Add "AI生成内容" watermark label (3 seconds, top-left)
6. Color grade: warm night tones for Chongqing scenes
7. Export: 1080x1920, 24fps, H.264

**Note:** This is a manual step. No code to write.

---

### Task 10: Document Pilot Results

**Files:**
- Update: `docs/plans/2026-04-24-sings-travel-duet-design.md`

**Step 1: Add pilot results section to design doc**

Append to the design doc:

```markdown
## Pilot Results (city-chongqing)

**Status**: [DONE/WIP]
**Duration**: [actual]s
**Cost**: $[actual]
**Issues**: [any pipeline issues encountered]
**Next steps**: [based on pilot learnings]
```

**Step 2: Commit**

```bash
git add docs/plans/2026-04-24-sings-travel-duet-design.md
git commit -m "docs: add city-chongqing pilot results"
```
