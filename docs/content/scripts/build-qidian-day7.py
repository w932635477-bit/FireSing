#!/usr/bin/env python3
"""
Qidian Day7 Video Builder — moviepy 2.x + PIL
Topic: 装修行业的信息差有多大
Based on Day5 template with Day7-specific content.
"""

import hashlib
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
)
from moviepy.video.fx.FadeIn import FadeIn
from moviepy.video.fx.FadeOut import FadeOut

W, H = 1080, 1920
FPS = 30
BG_COLOR = (26, 26, 46)
RED = (255, 69, 0)
GREEN = (0, 230, 118)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 50)
SILVER = (210, 210, 215)

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
VOICEOVER_DIR = Path(
    "/Users/weilei/FireSing/docs/content/assets/voiceover/qidian-week1-day7"
)
OUTPUT_PATH = Path(
    "/Users/weilei/FireSing/docs/content/assets/video/qidian-day7.mp4"
)
CACHE_DIR = Path("/tmp/qidian-day7-text-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
BG_CACHE = Path("/tmp/qidian-day7-bg.png")
WATERMARK_CACHE = Path("/tmp/qidian-day7-watermark.png")
CHART_CACHE = Path("/tmp/qidian-day7-chart.png")
ACCENT_CACHE = Path("/tmp/qidian-day7-accent.png")

TIMELINE = [
    {"id": "S01", "start": 0.0, "end": 6.33},
    {"id": "S02", "start": 6.33, "end": 14.31},
    {"id": "S03", "start": 14.31, "end": 23.77},
    {"id": "S04", "start": 23.77, "end": 27.93},
    {"id": "S05", "start": 27.93, "end": 34.73},
]
TOTAL_DURATION = 34.73
COVER_DURATION = 1.0

SUBTITLES = [
    {"start": 0.0, "end": 6.33, "text": "朋友刚装完103平，花了10万。你知道实际成本多少吗？大概4万。"},
    {"start": 6.33, "end": 14.31, "text": "另外6万去哪了？被3个环节赚走了：设计费1万，渠道费2万，信息差3万。"},
    {"start": 14.31, "end": 23.77, "text": "三万块瓷砖，工厂1.2万就出。全屋定制标价8万，出厂价不到3万。"},
    {"start": 23.77, "end": 27.93, "text": "你以为你在买材料，其实你在为信息差买单。"},
    {"start": 27.93, "end": 34.73, "text": "装过修的朋友，你觉得你被坑了多少？评论区说说，让没装的人长个心眼。"},
]

DANMAKU = [
    "装修太坑了", "10万成本4万", "信息差3万",
    "瓷砖差1.8万", "全屋定制差5万", "买材料=买信息差",
    "我装修被坑了", "工厂价才是真实价", "评论区长心眼",
]


# === Asset generation ===

def create_gradient_background() -> str:
    if BG_CACHE.exists():
        return str(BG_CACHE)
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    max_radius = math.sqrt(cx**2 + cy**2)
    for y in range(0, H, 4):
        for x in range(0, W, 4):
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            t = min(dist / max_radius, 1.0)
            factor = 1.0 - t * 0.3
            r = min(255, int(BG_COLOR[0] * factor + 15 * (1 - t)))
            g = min(255, int(BG_COLOR[1] * factor + 10 * (1 - t)))
            b = min(255, int(BG_COLOR[2] * factor + 25 * (1 - t)))
            draw.rectangle([x, y, x + 3, y + 3], fill=(r, g, b))
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)
    for i in range(80):
        alpha = int(40 * (1 - i / 80))
        vdraw.rectangle([i, i, W - 1 - i, H - 1 - i], outline=(0, 0, 0, alpha))
    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, vignette)
    img = img_rgba.convert("RGB")
    img.save(BG_CACHE)
    return str(BG_CACHE)


def create_watermark() -> str:
    if WATERMARK_CACHE.exists():
        return str(WATERMARK_CACHE)
    font = ImageFont.truetype(FONT_PATH, 22, index=0)
    text = "启点·经验变现"
    tmp = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("RGBA", (tw + 16, th + 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((8 - bbox[0], 4 - bbox[1]), text, font=font, fill=(255, 255, 255, 90))
    img.save(WATERMARK_CACHE)
    return str(WATERMARK_CACHE)


def create_bar_chart() -> str:
    """Bar chart: 花10万 vs 成本4万."""
    if CHART_CACHE.exists():
        return str(CHART_CACHE)
    img = Image.new("RGBA", (600, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bar_max_h = 140
    bar_w = 70
    gap = 100
    x1, x2 = 100, 100 + bar_w + gap
    base_y = 160

    h1 = bar_max_h
    draw.rounded_rectangle(
        [x1, base_y - h1, x1 + bar_w, base_y], radius=8, fill=(*RED, 220),
    )
    h2 = int(bar_max_h * 4 / 10)
    draw.rounded_rectangle(
        [x2, base_y - h2, x2 + bar_w, base_y], radius=4, fill=(*GREEN, 200),
    )

    font_label = ImageFont.truetype(FONT_PATH, 22, index=0)
    font_num = ImageFont.truetype(FONT_PATH, 24, index=0)

    draw.text((x1 - 5, base_y + 10), "你花的", font=font_label, fill=(*WHITE, 200))
    draw.text((x2 - 5, base_y + 10), "成本", font=font_label, fill=(*GREEN, 180))
    draw.text((x1 - 15, base_y - h1 - 35), "10万", font=font_num, fill=(*RED, 255))
    draw.text((x2 - 10, base_y - h2 - 35), "4万", font=font_num, fill=(*GREEN, 220))
    draw.line([x1 - 20, base_y, x2 + bar_w + 20, base_y], fill=(*WHITE, 60), width=2)

    diff_font = ImageFont.truetype(FONT_PATH, 28, index=0)
    mid_x = (x1 + x2 + bar_w) // 2
    draw.text((mid_x - 40, base_y - h1 + 30), "差6万", font=diff_font, fill=(*YELLOW, 230))

    img.save(CHART_CACHE)
    return str(CHART_CACHE)


def create_accent_shapes() -> str:
    if ACCENT_CACHE.exists():
        return str(ACCENT_CACHE)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bracket_len = 120
    bracket_w = 3
    draw.line([40, 40, 40 + bracket_len, 40], fill=(*RED, 80), width=bracket_w)
    draw.line([40, 40, 40, 40 + bracket_len], fill=(*RED, 80), width=bracket_w)
    draw.line([W - 40, H - 40, W - 40 - bracket_len, H - 40], fill=(*RED, 80), width=bracket_w)
    draw.line([W - 40, H - 40, W - 40, H - 40 - bracket_len], fill=(*RED, 80), width=bracket_w)
    for i, y in enumerate([500, 520, 540]):
        alpha = 60 - i * 15
        draw.ellipse([W - 60, y, W - 48, y + 12], fill=(*GREEN, max(alpha, 20)))
    img.save(ACCENT_CACHE)
    return str(ACCENT_CACHE)


# === Text rendering ===

def render_text(text: str, size: int, color: tuple, opacity: int = 255) -> str:
    key = hashlib.sha1(f"{text}|{size}|{color}|{opacity}".encode()).hexdigest()[:16]
    path = CACHE_DIR / f"{key}.png"
    if path.exists():
        return str(path)
    font = ImageFont.truetype(FONT_PATH, size, index=0)
    tmp = Image.new("RGBA", (1, 1))
    bbox = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = max(20, size // 4)
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    xy = (pad - bbox[0], pad - bbox[1])
    draw.text(xy, text, font=font, fill=(*color[:3], opacity))
    img.save(path)
    return str(path)


def render_subtitle(text: str, max_width: int = 900) -> str:
    cache_key = hashlib.sha1(f"sub|{text}".encode()).hexdigest()[:16]
    path = CACHE_DIR / f"sub_{cache_key}.png"
    if path.exists():
        return str(path)
    font = ImageFont.truetype(FONT_PATH, 30, index=0)
    lines = []
    current = ""
    for char in text:
        test = current + char
        tmp = Image.new("RGBA", (1, 1))
        bbox = ImageDraw.Draw(tmp).textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    line_h = 42
    total_h = line_h * len(lines) + 20
    img = Image.new("RGBA", (max_width + 40, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        tmp = Image.new("RGBA", (1, 1))
        bbox = ImageDraw.Draw(tmp).textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (max_width + 40 - tw) // 2 - bbox[0]
        y = 10 + i * line_h - bbox[1]
        draw.text((x, y), line, font=font, fill=(*YELLOW, 230))
    img.save(path)
    return str(path)


def make_text_clip(
    text: str, size: int, color: tuple, start: float, duration: float,
    position: tuple = ("center", "center"), opacity: float = 1.0,
    fade_in: float = 0.0, fade_out: float = 0.0,
) -> ImageClip:
    path = render_text(text, size, color)
    clip = ImageClip(path).with_duration(duration).with_start(start).with_position(position)
    effects = []
    if fade_in > 0:
        effects.append(FadeIn(fade_in))
    if fade_out > 0:
        effects.append(FadeOut(fade_out))
    if effects:
        clip = clip.with_effects(effects)
    if opacity < 1.0:
        clip = clip.with_opacity(opacity)
    return clip


def make_subtitle_clips(subtitles: list[dict]) -> list[ImageClip]:
    clips = []
    for sub in subtitles:
        dur = sub["end"] - sub["start"]
        path = render_subtitle(sub["text"])
        clip = ImageClip(path).with_duration(dur).with_start(sub["start"]).with_position(("center", H - 180))
        clips.append(clip)
    return clips


def make_danmaku_clips(texts: list[str], start_time: float, end_time: float) -> list[ImageClip]:
    clips = []
    duration = end_time - start_time
    interval = duration / len(texts)
    x_positions = [80, 200, 350, 500, 650, 130, 280, 420, 580]
    y_positions = [250, 400, 550, 700, 850, 330, 480, 630, 780]
    for i, text in enumerate(texts):
        t_start = start_time + i * interval
        visible_duration = min(2.5, interval * 0.8)
        path = render_text(text, 28, WHITE, opacity=180)
        x = x_positions[i % len(x_positions)]
        y = y_positions[i % len(y_positions)]
        clip = (
            ImageClip(path).with_duration(visible_duration).with_start(t_start)
            .with_position((x, y)).with_effects([FadeIn(0.3), FadeOut(0.3)])
        )
        clips.append(clip)
    return clips


# === Build ===

def build() -> None:
    print("Building Day 7 video...")
    print(f"  Timeline: {TOTAL_DURATION}s, {W}x{H}@{FPS}fps")

    bg_path = create_gradient_background()
    watermark_path = create_watermark()
    chart_path = create_bar_chart()
    accent_path = create_accent_shapes()

    bg = ImageClip(bg_path).with_duration(TOTAL_DURATION)
    accent_clip = ImageClip(accent_path).with_duration(TOTAL_DURATION)

    wm_img = Image.open(watermark_path)
    wm_w = wm_img.size[0]
    watermark = (
        ImageClip(watermark_path).with_duration(TOTAL_DURATION)
        .with_position((W - wm_w - 30, H - 120)).with_opacity(0.6)
    )

    audio = AudioFileClip(str(VOICEOVER_DIR / "qidian-week1-day7-full-narration-gemini.mp3"))
    subtitle_clips = make_subtitle_clips(SUBTITLES)

    # Cover frame (0-1.0s)
    cover_title = make_text_clip("花10万", 72, RED, 0.0, COVER_DURATION, ("center", 550), fade_out=0.3)
    cover_title2 = make_text_clip("成本4万", 72, GREEN, 0.0, COVER_DURATION, ("center", 680), fade_out=0.3)
    cover_sub = make_text_clip("装修行业的信息差", 40, SILVER, 0.0, COVER_DURATION, ("center", 840), fade_out=0.3)

    # Scene 1: Hook (1.0s-6.33s) — 花10万成本4万
    s01_start = COVER_DURATION
    s01_dur = TIMELINE[0]["end"] - COVER_DURATION

    s01_hook = make_text_clip(
        "103平 花10万 成本4万", 48, YELLOW,
        s01_start + 0.2, s01_dur - 0.2,
        ("center", 700), fade_in=0.3,
    )

    # Scene 2: Breakdown (6.33s-14.31s) — 6万去哪了
    s02_start = TIMELINE[1]["start"]
    s02_dur = TIMELINE[1]["end"] - TIMELINE[1]["start"]

    s02_label = make_text_clip(
        "另外6万去哪了？", 48, RED,
        s02_start + 0.2, s02_dur - 0.2,
        ("center", 450), fade_in=0.3,
    )
    s02_item1 = make_text_clip(
        "设计费  1万", 40, WHITE,
        s02_start + 1.0, max(0, s02_dur - 1.0),
        ("center", 580), fade_in=0.3,
    )
    s02_item2 = make_text_clip(
        "渠道费  2万", 40, WHITE,
        s02_start + 1.8, max(0, s02_dur - 1.8),
        ("center", 670), fade_in=0.3,
    )
    s02_item3 = make_text_clip(
        "信息差  3万", 48, YELLOW,
        s02_start + 2.6, max(0, s02_dur - 2.6),
        ("center", 780), fade_in=0.3,
    )

    # Scene 3: Examples (14.31s-23.77s) — 瓷砖+全屋定制
    s03_start = TIMELINE[2]["start"]
    s03_dur = TIMELINE[2]["end"] - TIMELINE[2]["start"]

    # Part 1: 瓷砖
    s03_tile_label = make_text_clip(
        "瓷砖", 44, WHITE,
        s03_start + 0.2, min(4.0, s03_dur),
        ("center", 450), fade_in=0.3,
    )
    s03_chart = (
        ImageClip(chart_path).with_duration(min(4.5, s03_dur)).with_start(s03_start + 0.3)
        .with_position(("center", 580)).with_effects([FadeIn(0.4)])
    )

    # Part 2: 具体对比
    cut_time = s03_start + 5.0
    remaining = TIMELINE[2]["end"] - cut_time

    s03_tile = make_text_clip(
        "瓷砖 3万 → 工厂1.2万", 40, YELLOW,
        cut_time, remaining, ("center", 500), fade_in=0.3,
    )
    s03_custom = make_text_clip(
        "全屋定制 8万 → 出厂3万", 40, RED,
        cut_time + 1.5, max(0, remaining - 1.5), ("center", 630), fade_in=0.3,
    )
    s03_source = make_text_clip(
        "15年工头看一眼就知道水分", 32, SILVER,
        cut_time + 3.0, max(0, remaining - 3.0), ("center", 780), fade_in=0.2,
    )

    # Scene 4: Attitude (23.77s-27.93s) — 买材料 vs 买信息差
    s04_start = TIMELINE[3]["start"]
    s04_dur = TIMELINE[3]["end"] - TIMELINE[3]["start"]

    s04_line1 = make_text_clip(
        "你以为在买材料", 52, WHITE,
        s04_start + 0.2, s04_dur - 0.2,
        ("center", 600), fade_in=0.3,
    )
    s04_not = make_text_clip(
        "其实在为", 44, SILVER,
        s04_start + 1.0, max(0, s04_dur - 1.0),
        ("center", 730), fade_in=0.3,
    )
    s04_line2 = make_text_clip(
        "信息差买单", 56, RED,
        s04_start + 1.5, max(0, s04_dur - 1.5),
        ("center", 850), fade_in=0.3,
    )

    danmaku_clips = make_danmaku_clips(DANMAKU, s04_start, TIMELINE[3]["end"])

    # Scene 5: CTA (27.93s-34.73s)
    s05_start = TIMELINE[4]["start"]
    s05_dur = TIMELINE[4]["end"] - TIMELINE[4]["start"]

    s05_cta = make_text_clip(
        "你被坑了多少？", 52, YELLOW,
        s05_start + 0.2, s05_dur - 0.2,
        ("center", 700), fade_in=0.3,
    )
    s05_prompt = make_text_clip(
        "评论区说说 让没装的人长个心眼", 32, SILVER,
        s05_start + 1.2, max(0, s05_dur - 1.2),
        ("center", 850),
    )

    # Compose
    all_clips = [
        bg, accent_clip, watermark,
        cover_title, cover_title2, cover_sub,
        s01_hook,
        s02_label, s02_item1, s02_item2, s02_item3,
        s03_tile_label, s03_chart, s03_tile, s03_custom, s03_source,
        s04_line1, s04_not, s04_line2,
        s05_cta, s05_prompt,
    ]
    all_clips.extend(danmaku_clips)
    all_clips.extend(subtitle_clips)

    final = CompositeVideoClip(all_clips, size=(W, H))
    final = final.with_audio(audio)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Rendering to {OUTPUT_PATH}...")
    final.write_videofile(
        str(OUTPUT_PATH), fps=FPS, codec="libx264",
        audio_codec="aac", preset="medium", bitrate="5000k", logger="bar",
    )
    print(f"  Done: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
