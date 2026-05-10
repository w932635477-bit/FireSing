#!/usr/bin/env python3
"""
Qidian Day4 Video Builder — moviepy 2.x + PIL (v3)

v3 fixes (Codex blockers):
- Gray text → bright silver/white for contrast on dark gradient
- Mini bar chart (290,000 vs 3,000) as visual anchor in Scene 2
- Geometric accent shapes (top-left corner bracket, bottom-right dots)
- Brand watermark moved to bottom-right safe area
- Yellow subtitles synced to SRT for silent viewers

Usage:
  python3 build-qidian-day4.py
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

# === Config ===
W, H = 1080, 1920
FPS = 30
BG_COLOR = (26, 26, 46)
RED = (255, 69, 0)
GREEN = (0, 230, 118)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 50)  # Subtitle color for silent viewers
SILVER = (210, 210, 215)  # Replaces GRAY — high contrast on dark bg
DARK_OVERLAY = (10, 10, 20)

FONT_PATH = "/System/Library/Fonts/STHeiti Medium.ttc"
VOICEOVER_DIR = Path(
    "/Users/weilei/FireSing/docs/content/assets/voiceover/qidian-week1-day4"
)
OUTPUT_PATH = Path(
    "/Users/weilei/FireSing/docs/content/assets/video/qidian-day4.mp4"
)
CACHE_DIR = Path("/tmp/qidian-day4-text-cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
BG_CACHE = Path("/tmp/qidian-day4-bg.png")
WATERMARK_CACHE = Path("/tmp/qidian-day4-watermark-v3.png")
CHART_CACHE = Path("/tmp/qidian-day4-chart.png")
ACCENT_CACHE = Path("/tmp/qidian-day4-accent.png")

# Audio-anchored timeline
TIMELINE = [
    {"id": "S01", "start": 0.0, "end": 5.99},
    {"id": "S02", "start": 5.99, "end": 11.50},
    {"id": "S03", "start": 11.50, "end": 15.32},
    {"id": "S04", "start": 15.32, "end": 23.80},
    {"id": "S05", "start": 23.80, "end": 29.78},
    {"id": "S06", "start": 29.78, "end": 33.76},
]
TOTAL_DURATION = 33.76
COVER_DURATION = 1.0

# Subtitle data (synced to audio segments)
SUBTITLES = [
    {"start": 0.0, "end": 5.99, "text": "公司里最被低估的人是谁？不是清洁工，不是实习生，是那个帮公司省过钱的人。"},
    {"start": 5.99, "end": 11.50, "text": "29万够提一辆Model Y。年终奖？连四个轮子都买不起。"},
    {"start": 11.50, "end": 15.32, "text": "给老板省钱，不等于给自己赚钱。"},
    {"start": 15.32, "end": 23.80, "text": "砍价砍掉30%，避开2个坑，锁住1个好渠道——换个地方叫咨询服务。"},
    {"start": 23.80, "end": 29.78, "text": "从明天开始，怎么把帮老板省钱的本事，变成自己的收入。"},
    {"start": 29.78, "end": 33.76, "text": "你帮公司省过钱吗？评论区说说你省了多少。"},
]

DANMAKU = [
    "真实", "说得太对了", "我就是这样", "29万啊",
    "3000也好意思", "还有年终奖为0的", "我省了50万老板说应该的",
    "同采购路过", "这不是我吗", "换个老板确实是真理",
]


# === Asset generation ===

def create_gradient_background() -> str:
    """Create radial gradient background with vignette."""
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
    """Brand watermark — bottom-right safe area."""
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
    """Mini bar chart: 290,000 vs 3,000 visual comparison."""
    if CHART_CACHE.exists():
        return str(CHART_CACHE)

    img = Image.new("RGBA", (600, 250), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bar_max_h = 160
    bar_w = 80
    gap = 120
    x1, x2 = 80, 80 + bar_w + gap
    base_y = 180

    # Bar 1: 290,000 (full height, red)
    h1 = bar_max_h
    draw.rounded_rectangle(
        [x1, base_y - h1, x1 + bar_w, base_y],
        radius=8, fill=(*RED, 220),
    )

    # Bar 2: 3,000 (tiny, gray)
    h2 = max(6, int(bar_max_h * 3000 / 290000))
    draw.rounded_rectangle(
        [x2, base_y - h2, x2 + bar_w, base_y],
        radius=4, fill=(*SILVER, 180),
    )

    # Labels
    font_label = ImageFont.truetype(FONT_PATH, 24, index=0)
    font_num = ImageFont.truetype(FONT_PATH, 20, index=0)

    draw.text((x1 - 10, base_y + 10), "省下的", font=font_label, fill=(*WHITE, 200))
    draw.text((x2 - 10, base_y + 10), "年终奖", font=font_label, fill=(*SILVER, 160))

    draw.text((x1 - 20, base_y - h1 - 35), "29万", font=font_num, fill=(*RED, 255))
    draw.text((x2 - 5, base_y - h2 - 35), "3千", font=font_num, fill=(*SILVER, 200))

    # Baseline
    draw.line([x1 - 20, base_y, x2 + bar_w + 20, base_y], fill=(*WHITE, 60), width=2)

    img.save(CHART_CACHE)
    return str(CHART_CACHE)


def create_accent_shapes() -> str:
    """Decorative corner bracket and dots for visual anchoring."""
    if ACCENT_CACHE.exists():
        return str(ACCENT_CACHE)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Top-left corner bracket (subtle red accent)
    bracket_len = 120
    bracket_w = 3
    draw.line([40, 40, 40 + bracket_len, 40], fill=(*RED, 80), width=bracket_w)
    draw.line([40, 40, 40, 40 + bracket_len], fill=(*RED, 80), width=bracket_w)

    # Bottom-right corner bracket
    draw.line([W - 40, H - 40, W - 40 - bracket_len, H - 40], fill=(*RED, 80), width=bracket_w)
    draw.line([W - 40, H - 40, W - 40, H - 40 - bracket_len], fill=(*RED, 80), width=bracket_w)

    # Three subtle dots (decorative, right side)
    for i, y in enumerate([500, 520, 540]):
        alpha = 60 - i * 15
        draw.ellipse([W - 60, y, W - 48, y + 12], fill=(*GREEN, max(alpha, 20)))

    img.save(ACCENT_CACHE)
    return str(ACCENT_CACHE)


# === Text rendering ===

def render_text(
    text: str,
    size: int,
    color: tuple,
    opacity: int = 255,
) -> str:
    """Render text to transparent PNG (cached)."""
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
    """Render subtitle with word wrap for bottom bar display."""
    cache_key = hashlib.sha1(f"sub|{text}".encode()).hexdigest()[:16]
    path = CACHE_DIR / f"sub_{cache_key}.png"
    if path.exists():
        return str(path)

    font = ImageFont.truetype(FONT_PATH, 30, index=0)

    # Word wrap
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
    text: str,
    size: int,
    color: tuple,
    start: float,
    duration: float,
    position: tuple = ("center", "center"),
    opacity: float = 1.0,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
) -> ImageClip:
    """Create ImageClip from text."""
    path = render_text(text, size, color)
    clip = (
        ImageClip(path)
        .with_duration(duration)
        .with_start(start)
        .with_position(position)
    )
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
    """Create yellow subtitle clips for silent viewers, positioned at bottom safe area."""
    clips = []
    for sub in subtitles:
        dur = sub["end"] - sub["start"]
        path = render_subtitle(sub["text"])
        clip = (
            ImageClip(path)
            .with_duration(dur)
            .with_start(sub["start"])
            .with_position(("center", H - 180))
        )
        clips.append(clip)
    return clips


def make_danmaku_clips(
    texts: list[str],
    start_time: float,
    end_time: float,
) -> list[ImageClip]:
    """Create danmaku clips with fade-in/fade-out."""
    clips = []
    duration = end_time - start_time
    interval = duration / len(texts)
    x_positions = [80, 200, 350, 500, 650, 130, 280, 420, 580, 720]
    y_positions = [250, 400, 550, 700, 850, 330, 480, 630, 780, 1000]

    for i, text in enumerate(texts):
        t_start = start_time + i * interval
        visible_duration = min(2.5, interval * 0.8)
        path = render_text(text, 28, WHITE, opacity=180)

        x = x_positions[i % len(x_positions)]
        y = y_positions[i % len(y_positions)]

        clip = (
            ImageClip(path)
            .with_duration(visible_duration)
            .with_start(t_start)
            .with_position((x, y))
            .with_effects([FadeIn(0.3), FadeOut(0.3)])
        )
        clips.append(clip)

    return clips


# === Counter animation via make_frame ===

def build_counter_clip(start: float, total_scene_duration: float) -> VideoClip:
    """Counter 0→290,000 using make_frame."""
    counter_duration = 3.0
    font = ImageFont.truetype(FONT_PATH, 96, index=0)

    final_text = "290,000"
    tmp = Image.new("RGBA", (1, 1))
    final_bbox = ImageDraw.Draw(tmp).textbbox((0, 0), final_text, font=font)
    text_w = final_bbox[2] - final_bbox[0]
    text_h = final_bbox[3] - final_bbox[1]

    frame_w = text_w + 120
    frame_h = text_h + 60
    frame_x = (W - frame_w) // 2
    frame_y = 700 - 30

    number_cache: dict[int, Image.Image] = {}

    def _render_number(value: int) -> Image.Image:
        if value in number_cache:
            return number_cache[value]
        text = f"{value:,}"
        img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (frame_w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        y = (frame_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        draw.text((x, y), text, font=font, fill=(*RED, 255))
        number_cache[value] = img
        return img

    def make_frame(t: float):
        import numpy as np
        if t < counter_duration:
            progress = t / counter_duration
            eased = 1 - (1 - progress) ** 3
            value = min(int(eased * 290000), 290000)
            if value < 10000:
                value = round(value / 100) * 100
            elif value < 100000:
                value = round(value / 1000) * 1000
            else:
                value = round(value / 5000) * 5000
            value = min(value, 290000)
        else:
            value = 290000

        num_img = _render_number(value)
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        frame.paste(num_img, (frame_x, frame_y), num_img)
        return np.array(frame)

    import numpy as np
    clip = VideoClip(make_frame, is_mask=False, duration=total_scene_duration)
    clip = clip.with_start(start)
    return clip


# === Cover frame ===

def build_cover_clip(duration: float) -> list:
    """Cover frame: large title + red 290,000 for thumbnail."""
    clips = []
    cover_title = make_text_clip(
        "公司里最被低估的人", 64, WHITE,
        0.0, duration, ("center", 550), fade_out=0.3,
    )
    cover_number = make_text_clip(
        "290,000", 140, RED,
        0.0, duration, ("center", 750), fade_out=0.3,
    )
    cover_sub = make_text_clip(
        "是那个帮公司省过钱的人", 40, SILVER,
        0.0, duration, ("center", 950), fade_out=0.3,
    )
    clips.extend([cover_title, cover_number, cover_sub])
    return clips


# === Build video ===

def build() -> None:
    print("Building Day 4 video (v3)...")
    print(f"  Timeline: {TOTAL_DURATION}s, {W}x{H}@{FPS}fps")

    # Prepare assets
    bg_path = create_gradient_background()
    watermark_path = create_watermark()
    chart_path = create_bar_chart()
    accent_path = create_accent_shapes()

    # Background
    bg = ImageClip(bg_path).with_duration(TOTAL_DURATION)

    # Accent shapes (always visible, very subtle)
    accent_clip = ImageClip(accent_path).with_duration(TOTAL_DURATION)

    # Watermark: bottom-right safe area (Douyin UI avoids bottom-right corner)
    wm_img = Image.open(watermark_path)
    wm_w, wm_h = wm_img.size
    watermark = (
        ImageClip(watermark_path)
        .with_duration(TOTAL_DURATION)
        .with_position((W - wm_w - 30, H - 120))
        .with_opacity(0.6)
    )

    # Audio
    audio_path = VOICEOVER_DIR / "qidian-week1-day4-full-narration-gemini.mp3"
    audio = AudioFileClip(str(audio_path))

    # Yellow subtitles for silent viewers
    subtitle_clips = make_subtitle_clips(SUBTITLES)

    # Cover frame (0-1.0s)
    cover_clips = build_cover_clip(COVER_DURATION)

    # Scene 1: Counter (1.0s-5.99s)
    s01_start = COVER_DURATION
    s01_duration = TIMELINE[0]["end"] - COVER_DURATION
    counter_clip = build_counter_clip(s01_start, s01_duration)

    s01_title = make_text_clip(
        "公司里最被低估的人", 56, WHITE,
        s01_start + 0.3, s01_duration - 0.3,
        ("center", 450), fade_in=0.3,
    )
    s01_subtitle = make_text_clip(
        "是那个帮公司省过钱的人", 44, SILVER,
        s01_start + 2.5, max(0, s01_duration - 2.5),
        ("center", 900), fade_in=0.3,
    )

    # Scene 2: Contrast with bar chart (5.99s-11.50s)
    s02_duration = TIMELINE[1]["end"] - TIMELINE[1]["start"]
    s02_start = TIMELINE[1]["start"]

    s02_big_number = make_text_clip(
        "290,000", 120, RED,
        s02_start + 0.2, min(2.3, s02_duration),
        ("center", 500), fade_in=0.3,
    )
    s02_yuan = make_text_clip(
        "替老板省下 29 万", 40, WHITE,
        s02_start + 0.2, min(2.3, s02_duration),
        ("center", 630), fade_in=0.2,
    )

    # Bar chart visual anchor
    s02_chart = (
        ImageClip(chart_path)
        .with_duration(min(2.3, s02_duration))
        .with_start(s02_start + 0.2)
        .with_position(("center", 780))
        .with_effects([FadeIn(0.3)])
    )

    # Hard cut
    cut_time = s02_start + 2.5
    remaining = TIMELINE[1]["end"] - cut_time

    s02_small_number = make_text_clip(
        "3,000", 64, SILVER,
        cut_time, remaining,
        ("center", 550), fade_in=0.2,
    )
    s02_bonus_label = make_text_clip(
        "年终奖（税前）", 28, WHITE,
        cut_time, remaining,
        ("center", 650),
    )
    s02_wheels = make_text_clip(
        "连四个轮子都买不起", 36, WHITE,
        cut_time + 0.8, max(0, remaining - 0.8),
        ("center", 780), fade_in=0.2,
    )

    # Scene 3: Attitude (11.50s-15.32s)
    s03_duration = TIMELINE[2]["end"] - TIMELINE[2]["start"]
    s03_start = TIMELINE[2]["start"]

    s03_attitude = make_text_clip(
        "给老板省钱", 56, WHITE,
        s03_start + 0.2, s03_duration - 0.2,
        ("center", 700), fade_in=0.3,
    )
    s03_not_equal = make_text_clip(
        "≠", 80, GREEN,
        s03_start + 0.5, s03_duration - 0.5,
        ("center", 830), fade_in=0.2,
    )
    s03_make_money = make_text_clip(
        "给自己赚钱", 56, WHITE,
        s03_start + 0.8, s03_duration - 0.8,
        ("center", 960), fade_in=0.3,
    )

    # Scene 4: AR data (15.32s-23.80s)
    s04_duration = TIMELINE[3]["end"] - TIMELINE[3]["start"]
    s04_start = TIMELINE[3]["start"]

    s04_rehook = make_text_clip(
        "那怎么办？", 48, WHITE,
        s04_start, 2.0,
        ("center", 350), fade_in=0.3, fade_out=0.3,
    )
    s04_item1 = make_text_clip(
        "砍掉 30%", 72, RED,
        s04_start + 0.3, s04_duration - 0.3,
        ("center", 500), fade_in=0.4,
    )
    s04_item2 = make_text_clip(
        "避开 2 个坑", 72, RED,
        s04_start + 2.3, s04_duration - 2.3,
        ("center", 680), fade_in=0.4,
    )
    s04_item3 = make_text_clip(
        "锁住 1 个渠道", 72, GREEN,
        s04_start + 4.3, max(0, s04_duration - 4.3),
        ("center", 860), fade_in=0.4,
    )
    s04_label = make_text_clip(
        '换个地方，叫"咨询服务"', 36, WHITE,
        s04_start + 5.5, max(0, s04_duration - 5.5),
        ("center", 1080), fade_in=0.3,
    )

    danmaku_clips = make_danmaku_clips(
        DANMAKU, s04_start + 2.0, TIMELINE[3]["end"],
    )

    # Scene 5: Transition (23.80s-29.78s)
    s05_duration = TIMELINE[4]["end"] - TIMELINE[4]["start"]
    s05_start = TIMELINE[4]["start"]

    s05_overlay = (
        ColorClip((W, H), color=(0, 0, 0))
        .with_duration(s05_duration)
        .with_start(s05_start)
        .with_opacity(0.3)
    )
    s05_text = make_text_clip(
        "从明天开始", 72, WHITE,
        s05_start + 0.3, s05_duration - 0.3,
        ("center", 700), fade_in=0.4,
    )
    s05_sub = make_text_clip(
        "怎么把帮老板省钱的本事", 36, SILVER,
        s05_start + 1.8, max(0, s05_duration - 1.8),
        ("center", 880), fade_in=0.3,
    )
    s05_sub2 = make_text_clip(
        "变成自己的收入", 48, GREEN,
        s05_start + 3.0, max(0, s05_duration - 3.0),
        ("center", 980), fade_in=0.3,
    )

    # Scene 6: CTA (29.78s-33.76s)
    s06_duration = TIMELINE[5]["end"] - TIMELINE[5]["start"]
    s06_start = TIMELINE[5]["start"]

    s06_cta = make_text_clip(
        "你帮公司省过钱吗？", 56, WHITE,
        s06_start + 0.2, s06_duration - 0.2,
        ("center", 750), fade_in=0.3,
    )
    s06_prompt = make_text_clip(
        "评论区说说你省了多少", 36, SILVER,
        s06_start + 1.0, max(0, s06_duration - 1.0),
        ("center", 900),
    )

    # Compose all clips
    all_clips = [
        bg,
        accent_clip,
        watermark,
        # Cover
        *cover_clips,
        # Scene 1
        counter_clip, s01_title, s01_subtitle,
        # Scene 2
        s02_big_number, s02_yuan, s02_chart,
        s02_small_number, s02_bonus_label, s02_wheels,
        # Scene 3
        s03_attitude, s03_not_equal, s03_make_money,
        # Scene 4
        s04_rehook, s04_item1, s04_item2, s04_item3, s04_label,
        # Scene 5
        s05_overlay, s05_text, s05_sub, s05_sub2,
        # Scene 6
        s06_cta, s06_prompt,
    ]
    all_clips.extend(danmaku_clips)
    all_clips.extend(subtitle_clips)

    final = CompositeVideoClip(all_clips, size=(W, H))
    final = final.with_audio(audio)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Rendering to {OUTPUT_PATH}...")
    final.write_videofile(
        str(OUTPUT_PATH),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="5000k",
        logger="bar",
    )
    print(f"  Done: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
