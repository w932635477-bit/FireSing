#!/usr/bin/env python3
"""
Qidian Day5 Video Builder — moviepy 2.x + PIL
Topic: 你工资配不上你脑子里的东西
Based on Day4 v3 template with Day5-specific content.
"""

import hashlib
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    ColorClip,
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
DARK_OVERLAY = (10, 10, 20)

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
VOICEOVER_DIR = Path(
    "/Users/weilei/FireSing/docs/content/assets/voiceover/qidian-week1-day5"
)
OUTPUT_PATH = Path(
    "/Users/weilei/FireSing/docs/content/assets/video/qidian-day5.mp4"
)
CACHE_DIR = Path("/tmp/qidian-day5-text-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
BG_CACHE = Path("/tmp/qidian-day5-bg.png")
WATERMARK_CACHE = Path("/tmp/qidian-day5-watermark.png")
CHART_CACHE = Path("/tmp/qidian-day5-chart.png")
ACCENT_CACHE = Path("/tmp/qidian-day5-accent.png")

TIMELINE = [
    {"id": "S01", "start": 0.0, "end": 4.52},
    {"id": "S02", "start": 4.52, "end": 11.92},
    {"id": "S03", "start": 11.92, "end": 20.32},
    {"id": "S04", "start": 20.32, "end": 38.20},
    {"id": "S05", "start": 38.20, "end": 44.08},
]
TOTAL_DURATION = 44.08
COVER_DURATION = 1.0

SUBTITLES = [
    {"start": 0.0, "end": 4.52, "text": "每个行业都有这种人——工资配不上脑子里的东西。"},
    {"start": 4.52, "end": 11.92, "text": "14年外贸老炮，年入18万，但他帮客户省的钱，一年300万起步。"},
    {"start": 11.92, "end": 20.32, "text": "你的工资不是你的价值。你的工资，是你老板愿意付你的最低价。"},
    {"start": 20.32, "end": 38.20, "text": "人才市场给你标的价，是500块一小时。你真正的客户不是HR，是那些需要你经验的人。"},
    {"start": 38.20, "end": 44.08, "text": "@一个被低估的朋友。评论区说说他有多懂行。"},
]

DANMAKU = [
    "说得太对了", "我就是那个人", "18万vs300万",
    "工资是最低价", "500一小时才对", "客户不是HR",
    "@朋友来看看", "经验就是产品", "懂行的都穷",
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
    """Bar chart: 年入18万 vs 帮客户省300万."""
    if CHART_CACHE.exists():
        return str(CHART_CACHE)
    img = Image.new("RGBA", (600, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bar_max_h = 140
    bar_w = 70
    gap = 100
    x1, x2 = 100, 100 + bar_w + gap
    base_y = 160

    # Bar 1: 300万 (tall, red)
    h1 = bar_max_h
    draw.rounded_rectangle(
        [x1, base_y - h1, x1 + bar_w, base_y], radius=8, fill=(*RED, 220),
    )
    # Bar 2: 18万 (short, silver)
    h2 = max(8, int(bar_max_h * 18 / 300))
    draw.rounded_rectangle(
        [x2, base_y - h2, x2 + bar_w, base_y], radius=4, fill=(*SILVER, 180),
    )

    font_label = ImageFont.truetype(FONT_PATH, 22, index=0)
    font_num = ImageFont.truetype(FONT_PATH, 20, index=0)

    draw.text((x1 - 15, base_y + 10), "帮客户省", font=font_label, fill=(*WHITE, 200))
    draw.text((x2 - 5, base_y + 10), "年入", font=font_label, fill=(*SILVER, 160))
    draw.text((x1 - 20, base_y - h1 - 35), "300万", font=font_num, fill=(*RED, 255))
    draw.text((x2 - 5, base_y - h2 - 35), "18万", font=font_num, fill=(*SILVER, 200))
    draw.line([x1 - 20, base_y, x2 + bar_w + 20, base_y], fill=(*WHITE, 60), width=2)
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


# === Counter animation ===

def build_counter_clip(start: float, total_scene_duration: float) -> VideoClip:
    counter_duration = 2.5
    font = ImageFont.truetype(FONT_PATH, 72, index=0)
    final_text = "500/小时"
    tmp = Image.new("RGBA", (1, 1))
    final_bbox = ImageDraw.Draw(tmp).textbbox((0, 0), final_text, font=font)
    text_w = final_bbox[2] - final_bbox[0]
    frame_w = text_w + 120
    frame_h = 120
    frame_x = (W - frame_w) // 2
    frame_y = 690

    targets = [0, 50, 100, 200, 300, 350, 400, 450, 500]
    number_cache: dict[int, Image.Image] = {}

    def _render_number(value: int) -> Image.Image:
        if value in number_cache:
            return number_cache[value]
        text = f"{value}/小时" if value > 0 else "?/小时"
        img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (frame_w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        y = (frame_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        color = (*GREEN, 255) if value >= 500 else (*SILVER, 200)
        draw.text((x, y), text, font=font, fill=color)
        number_cache[value] = img
        return img

    def make_frame(t: float):
        import numpy as np
        if t < counter_duration:
            progress = t / counter_duration
            eased = 1 - (1 - progress) ** 3
            idx = min(int(eased * (len(targets) - 1)), len(targets) - 1)
            value = targets[idx]
        else:
            value = 500
        num_img = _render_number(value)
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        frame.paste(num_img, (frame_x, frame_y), num_img)
        return np.array(frame)

    clip = VideoClip(make_frame, is_mask=False, duration=total_scene_duration)
    clip = clip.with_start(start)
    return clip


# === Build ===

def build() -> None:
    print("Building Day 5 video...")
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

    audio = AudioFileClip(str(VOICEOVER_DIR / "qidian-week1-day5-full-narration-gemini.mp3"))
    subtitle_clips = make_subtitle_clips(SUBTITLES)

    # Cover frame (0-1.0s)
    cover_title = make_text_clip("工资配不上", 64, WHITE, 0.0, COVER_DURATION, ("center", 550), fade_out=0.3)
    cover_title2 = make_text_clip("脑子里的东西", 64, RED, 0.0, COVER_DURATION, ("center", 660), fade_out=0.3)
    cover_sub = make_text_clip("每个行业都有这种人", 40, SILVER, 0.0, COVER_DURATION, ("center", 820), fade_out=0.3)

    # Scene 1: Hook (1.0s-4.48s) — "工资配不上脑子"
    s01_start = COVER_DURATION
    s01_dur = TIMELINE[0]["end"] - COVER_DURATION

    s01_hook = make_text_clip(
        "工资配不上脑子里的东西", 56, RED,
        s01_start + 0.2, s01_dur - 0.2,
        ("center", 700), fade_in=0.3,
    )

    # Scene 2: Examples (4.48s-14.44s) — 18万 vs 300万 + 400 vs 2000
    s02_start = TIMELINE[1]["start"]
    s02_dur = TIMELINE[1]["end"] - TIMELINE[1]["start"]

    s02_case1_title = make_text_clip(
        "14年外贸老炮", 44, WHITE,
        s02_start + 0.2, min(4.5, s02_dur),
        ("center", 450), fade_in=0.3,
    )
    s02_case1_num = make_text_clip(
        "年入 18 万", 40, SILVER,
        s02_start + 0.5, min(4.5, s02_dur),
        ("center", 530),
    )

    s02_chart = (
        ImageClip(chart_path).with_duration(min(4.5, s02_dur)).with_start(s02_start + 0.5)
        .with_position(("center", 600)).with_effects([FadeIn(0.4)])
    )

    # Second case: 装修工头
    cut_time = s02_start + 5.0
    remaining = TIMELINE[1]["end"] - cut_time

    s02_case2_title = make_text_clip(
        "10年装修工头", 44, WHITE,
        cut_time, remaining, ("center", 450), fade_in=0.3,
    )
    s02_case2_daily = make_text_clip(
        "日薪 400", 48, SILVER,
        cut_time + 0.3, remaining - 0.3, ("center", 550), fade_in=0.2,
    )
    s02_case2_vs = make_text_clip(
        "避坑门道值", 36, WHITE,
        cut_time + 1.5, remaining - 1.5, ("center", 660), fade_in=0.2,
    )
    s02_case2_value = make_text_clip(
        "2,000/半天", 56, GREEN,
        cut_time + 2.0, remaining - 2.0, ("center", 760), fade_in=0.3,
    )

    # Scene 3: Attitude (14.44s-20.96s)
    s03_start = TIMELINE[2]["start"]
    s03_dur = TIMELINE[2]["end"] - TIMELINE[2]["start"]

    s03_line1 = make_text_clip(
        "你的工资", 56, WHITE,
        s03_start + 0.3, s03_dur - 0.3,
        ("center", 650), fade_in=0.3,
    )
    s03_not = make_text_clip(
        "≠", 80, RED,
        s03_start + 0.6, s03_dur - 0.6,
        ("center", 780), fade_in=0.2,
    )
    s03_line2 = make_text_clip(
        "你的价值", 56, GREEN,
        s03_start + 0.9, s03_dur - 0.9,
        ("center", 910), fade_in=0.3,
    )
    s03_sub = make_text_clip(
        "工资是老板愿意付你的最低价", 36, SILVER,
        s03_start + 2.5, max(0, s03_dur - 2.5),
        ("center", 1080), fade_in=0.3,
    )

    # Scene 4: Data + conclusion (20.96s-27.44s)
    s04_start = TIMELINE[3]["start"]
    s04_dur = TIMELINE[3]["end"] - TIMELINE[3]["start"]

    counter_clip = build_counter_clip(s04_start + 0.3, s04_dur - 0.3)

    s04_label = make_text_clip(
        "人才市场标价", 36, WHITE,
        s04_start + 0.3, s04_dur - 0.3,
        ("center", 600), fade_in=0.3,
    )
    s04_conclusion = make_text_clip(
        "你真正的客户", 48, WHITE,
        s04_start + 3.0, max(0, s04_dur - 3.0),
        ("center", 880), fade_in=0.3,
    )
    s04_conclusion2 = make_text_clip(
        "不是 HR", 48, RED,
        s04_start + 3.5, max(0, s04_dur - 3.5),
        ("center", 980), fade_in=0.3,
    )

    danmaku_clips = make_danmaku_clips(DANMAKU, s04_start, TIMELINE[3]["end"])

    # Scene 5: CTA (27.44s-31.94s)
    s05_start = TIMELINE[4]["start"]
    s05_dur = TIMELINE[4]["end"] - TIMELINE[4]["start"]

    s05_cta = make_text_clip(
        "@一个被低估的朋友", 48, WHITE,
        s05_start + 0.2, s05_dur - 0.2,
        ("center", 700), fade_in=0.3,
    )
    s05_prompt = make_text_clip(
        "评论区说说他有多懂行", 36, SILVER,
        s05_start + 1.0, max(0, s05_dur - 1.0),
        ("center", 830),
    )

    # Compose
    all_clips = [
        bg, accent_clip, watermark,
        # Cover
        cover_title, cover_title2, cover_sub,
        # Scene 1
        s01_hook,
        # Scene 2
        s02_case1_title, s02_case1_num, s02_chart,
        s02_case2_title, s02_case2_daily, s02_case2_vs, s02_case2_value,
        # Scene 3
        s03_line1, s03_not, s03_line2, s03_sub,
        # Scene 4
        counter_clip, s04_label, s04_conclusion, s04_conclusion2,
        # Scene 5
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
