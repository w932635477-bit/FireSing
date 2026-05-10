"""Generate 6 carousel slides for 养号 Day2: 870块AI工具箱"""

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

OUTPUT_DIR = os.path.expanduser("~/Desktop/养号day2-图文")


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


def draw_kv(draw, label, value, x, y, label_fnt, value_fnt, label_color, value_color):
    draw.text((x, y), label, fill=label_color, font=label_fnt)
    draw.text((x, y + 55), value, fill=value_color, font=value_fnt)


def save(img, idx):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"slide_{idx}.png")
    img.save(path, quality=95)
    print(f"Saved: {path}")


# ── Slide 1: Cover ──
def slide_01():
    img, draw = new_slide()

    draw.line([(100, 300), (980, 300)], fill=GOLD, width=2)

    center_text(draw, "2个人", 380, WHITE, font(72, bold=True))
    center_text(draw, "的AI工具箱", 480, WHITE, font(72, bold=True))

    center_text(draw, "月费 ¥870", 660, GOLD, font(80, bold=True))
    center_text(draw, "→  年营收 4亿", 800, GOLD, font(64, bold=True))

    draw.line([(100, 1000), (980, 1000)], fill=GOLD, width=2)

    center_text(draw, "数据来源：Forbes 2026.04", 1100, GRAY, font(32))

    save(img, 1)


# ── Slide 2: Code tools ──
def slide_02():
    img, draw = new_slide()

    center_text(draw, "代码 — AI 全写", 280, GOLD, font(60, bold=True))

    draw.line([(100, 390), (980, 390)], fill=GOLD, width=2)

    tools = [
        ("ChatGPT", "¥150/月"),
        ("Claude", "¥150/月"),
        ("Grok", "¥110/月"),
    ]

    y = 500
    for name, price in tools:
        draw_kv(draw, name, price, 150, y, font(52, bold=True), font(48), WHITE, GOLD)
        y += 200

    draw.line([(100, y + 40), (980, y + 40)], fill=DARK_GRAY, width=1)

    center_text(draw, "整个平台代码  零人工编写", y + 100, WHITE, font(40))

    save(img, 2)


# ── Slide 3: Ad tools ──
def slide_03():
    img, draw = new_slide()

    center_text(draw, "广告素材 — AI 批量生成", 280, GOLD, font(56, bold=True))

    draw.line([(100, 390), (980, 390)], fill=GOLD, width=2)

    tools = [
        ("Midjourney", "¥218/月 → 图片"),
        ("Runway", "¥109/月 → 视频"),
        ("ElevenLabs", "¥36/月 → 配音"),
    ]

    y = 500
    for name, desc in tools:
        draw_kv(draw, name, desc, 150, y, font(48, bold=True), font(42), WHITE, GOLD)
        y += 220

    draw.line([(100, y + 20), (980, y + 20)], fill=DARK_GRAY, width=1)

    center_text(draw, "日投放广告 > 50万条", y + 80, WHITE, font(40))

    save(img, 3)


# ── Slide 4: Customer service ──
def slide_04():
    img, draw = new_slide()

    center_text(draw, "客服 — AI 自动回复", 280, GOLD, font(60, bold=True))

    draw.line([(100, 390), (980, 390)], fill=GOLD, width=2)

    stats = [
        ("付费用户", "25万"),
        ("人工客服", "0人"),
        ("AI Agent", "全自动处理"),
    ]

    y = 520
    for label, value in stats:
        center_text(draw, label, y, GRAY, font(40))
        center_text(draw, value, y + 60, WHITE, font(56, bold=True) if "0" in value else font(52))
        y += 200

    draw.line([(100, y + 20), (980, y + 20)], fill=DARK_GRAY, width=1)

    center_text(draw, "自己搭建的 AI Agent 串联所有系统", y + 80, GRAY, font(32))

    save(img, 4)


# ── Slide 5: Total cost ──
def slide_05():
    img, draw = new_slide()

    center_text(draw, "全部工具费用", 280, WHITE, font(60, bold=True))

    draw.line([(100, 390), (980, 390)], fill=GOLD, width=2)

    center_text(draw, "$120/月", 520, GOLD, font(100, bold=True))
    center_text(draw, "≈  ¥870", 680, GOLD, font(72, bold=True))

    draw.line([(300, 820), (780, 820)], fill=DARK_GRAY, width=1)

    no_list = [
        "没有开发团队",
        "没有设计师",
        "没有客服部",
    ]

    y = 880
    for item in no_list:
        center_text(draw, item, y, WHITE, font(42))
        y += 80

    draw.line([(100, y + 40), (980, y + 40)], fill=GOLD, width=2)

    center_text(draw, "2个人 + AI = 年营收4亿", y + 80, GOLD, font(48, bold=True))

    save(img, 5)


# ── Slide 6: CTA ──
def slide_06():
    img, draw = new_slide()

    draw.line([(100, 400), (980, 400)], fill=GOLD, width=2)

    center_text(draw, "国内免费替代方案", 500, WHITE, font(56, bold=True))
    center_text(draw, "我全整理好了", 600, WHITE, font(56, bold=True))

    center_text(draw, "评论区打「工具」", 850, GOLD, font(60, bold=True))
    center_text(draw, "发你完整清单", 960, GOLD, font(60, bold=True))

    draw.line([(100, 1100), (980, 1100)], fill=GOLD, width=2)

    center_text(draw, "关注我 · 每周更新AI工具实测", 1200, GRAY, font(32))

    save(img, 6)


if __name__ == "__main__":
    slide_01()
    slide_02()
    slide_03()
    slide_04()
    slide_05()
    slide_06()
    print(f"\nDone! 6 slides saved to {OUTPUT_DIR}")
