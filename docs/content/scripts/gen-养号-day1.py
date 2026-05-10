"""Generate 6 carousel slides for 养号 Day1: AI 14个月赚4亿"""

from PIL import Image, ImageDraw, ImageFont
import os

# Config
W, H = 1080, 1920
BG = (10, 10, 10)
WHITE = (255, 255, 255)
GOLD = (255, 200, 50)
GRAY = (120, 120, 120)
DARK_GRAY = (60, 60, 60)

FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"
FONT_BOLD = "/System/Library/Fonts/Hiragino Sans GB.ttc"

OUTPUT_DIR = os.path.expanduser("~/Desktop/养号day1-图文")


def font(size, bold=False):
    path = FONT_BOLD if bold else FONT_PATH
    return ImageFont.truetype(path, size, index=1)


def new_slide():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def center_text(draw, text, y, fill, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    draw.text((x, y), text, fill=fill, font=fnt)


def draw_left(draw, text, x, y, fill, fnt):
    draw.text((x, y), text, fill=fill, font=fnt)


def save(img, idx):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"slide_{idx}.png")
    img.save(path, quality=95)
    print(f"Saved: {path}")


# ── Slide 1: Cover ──
def slide_01():
    img, draw = new_slide()

    # Top decorative line
    draw.line([(100, 300), (980, 300)], fill=GOLD, width=2)

    center_text(draw, "一个人", 400, WHITE, font(72, bold=True))
    center_text(draw, "用AI", 500, WHITE, font(72, bold=True))

    # Arrow
    center_text(draw, "14个月  →  4亿美元", 660, GOLD, font(80, bold=True))

    # Bottom info
    center_text(draw, "数据来源：Forbes 2026.04", 1400, GRAY, font(32))

    # Decorative line bottom
    draw.line([(100, 1500), (980, 1500)], fill=GOLD, width=2)

    save(img, 1)


# ── Slide 2: Who is he ──
def slide_02():
    img, draw = new_slide()

    center_text(draw, "这个人是谁？", 300, WHITE, font(64, bold=True))

    draw.line([(100, 410), (980, 410)], fill=GOLD, width=2)

    items = [
        ("创始人", "Matthew Gallagher"),
        ("启动资金", "$20,000（约14万人民币）"),
        ("团队人数", "2人"),
        ("2025年营收", "$4.01亿（约28亿人民币）"),
        ("外部融资", "零"),
    ]

    y = 500
    for label, value in items:
        draw_left(draw, label, 120, y, GRAY, font(40))
        draw_left(draw, value, 120, y + 60, WHITE, font(48))
        y += 160

    save(img, 2)


# ── Slide 3: Key 1 ──
def slide_03():
    img, draw = new_slide()

    center_text(draw, "关键①", 300, GOLD, font(56, bold=True))
    center_text(draw, "代码全部AI写", 400, WHITE, font(64, bold=True))

    draw.line([(100, 510), (980, 510)], fill=GOLD, width=2)

    center_text(draw, "ChatGPT + Claude + Grok", 600, WHITE, font(44))

    # Comparison
    center_text(draw, "传统公司", 780, GRAY, font(40))
    center_text(draw, "2,400人", 840, WHITE, font(56, bold=True))
    center_text(draw, "净利率 5.5%", 920, WHITE, font(44))

    draw.line([(440, 1020), (640, 1020)], fill=GOLD, width=3)

    center_text(draw, "Medvi", 1100, GRAY, font(40))
    center_text(draw, "2人", 1160, GOLD, font(72, bold=True))
    center_text(draw, "净利率 16.2%", 1280, GOLD, font(56, bold=True))

    save(img, 3)


# ── Slide 4: Key 2 ──
def slide_04():
    img, draw = new_slide()

    center_text(draw, "关键②", 300, GOLD, font(56, bold=True))
    center_text(draw, "广告素材AI批量生成", 400, WHITE, font(64, bold=True))

    draw.line([(100, 510), (980, 510)], fill=GOLD, width=2)

    tools = [
        ("Midjourney", "图片素材"),
        ("Runway", "视频素材"),
        ("ElevenLabs", "AI配音"),
    ]

    y = 620
    for name, desc in tools:
        draw_left(draw, name, 120, y, WHITE, font(48, bold=True))
        draw_left(draw, desc, 120, y + 70, GRAY, font(40))
        y += 180

    draw.line([(100, 1180), (980, 1180)], fill=DARK_GRAY, width=1)

    center_text(draw, "日广告投放 > 50万条", 1280, WHITE, font(48))
    center_text(draw, "日营收 > 300万美元", 1380, GOLD, font(56, bold=True))

    save(img, 4)


# ── Slide 5: Key 3 ──
def slide_05():
    img, draw = new_slide()

    center_text(draw, "关键③", 300, GOLD, font(56, bold=True))
    center_text(draw, "客服 = AI机器人", 400, WHITE, font(64, bold=True))

    draw.line([(100, 510), (980, 510)], fill=GOLD, width=2)

    center_text(draw, "250,000", 700, GOLD, font(96, bold=True))
    center_text(draw, "付费客户", 820, WHITE, font(48))

    center_text(draw, "人工客服：0人", 1000, WHITE, font(52, bold=True))

    draw.line([(100, 1140), (980, 1140)], fill=DARK_GRAY, width=1)

    center_text(draw, "整套工具链 月费 ≈ ¥800", 1300, GRAY, font(44))
    center_text(draw, "国内有免费替代方案", 1400, WHITE, font(48))

    save(img, 5)


# ── Slide 6: CTA ──
def slide_06():
    img, draw = new_slide()

    center_text(draw, "国内免费替代方案", 450, WHITE, font(56, bold=True))
    center_text(draw, "全整理好了", 550, WHITE, font(56, bold=True))

    draw.line([(100, 670), (980, 670)], fill=GOLD, width=2)

    # CTA box
    box_y = 800
    draw.rounded_rectangle(
        [(200, box_y), (880, box_y + 300)],
        radius=20,
        fill=(30, 30, 30),
        outline=GOLD,
        width=3,
    )
    center_text(draw, "评论区打", box_y + 50, GRAY, font(40))
    center_text(draw, "「工具」", box_y + 120, GOLD, font(72, bold=True))
    center_text(draw, "发你完整清单", box_y + 220, WHITE, font(40))

    center_text(draw, "关注我 · 每周更新AI工具实测", 1500, GRAY, font(32))

    save(img, 6)


if __name__ == "__main__":
    slide_01()
    slide_02()
    slide_03()
    slide_04()
    slide_05()
    slide_06()
    print(f"\nDone! 6 slides saved to: {OUTPUT_DIR}")
