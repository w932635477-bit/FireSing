#!/usr/bin/env python3
"""HTML/CSS text card renderer for short-form video.

Renders clean, high-impact text cards with background images.
Uses TikTok-proven design: bold text + strong stroke on vivid backgrounds.

Supports two color schemes:
  - Medvi: dark warm gold (#c9a96e on #0a0806)
  - Sings: neon pink (#ff6eb4 on #1a0a2e)

Usage:
  python3 text-card-renderer.py --config config/sings02-medvi-tools.json --segment S04
  python3 text-card-renderer.py --lines "6000人 走了" "平台 没崩" --style sings --bg-image photo.jpg
"""

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Color schemes
# ---------------------------------------------------------------------------

SCHEMES = {
    "medvi": {
        "accent": "#c9a96e",
        "accent_rgb": "201, 169, 110",
        "text_primary": "#f5edd8",
        "text_secondary": "#d4c8a8",
        "stroke": "#000000",
        "stroke_width": "4px",
        "overlay": "rgba(10, 8, 6, 0.45)",
        "divider_color": "#c9a96e",
    },
    "sings": {
        "accent": "#ff6eb4",
        "accent_rgb": "255, 110, 180",
        "text_primary": "#ffffff",
        "text_secondary": "#e0c8e8",
        "stroke": "#000000",
        "stroke_width": "4px",
        "overlay": "rgba(10, 5, 20, 0.40)",
        "divider_color": "#ff6eb4",
    },
}


def _image_to_data_uri(path: str) -> str:
    """Read image file and return base64 data URI."""
    p = Path(path)
    if not p.exists():
        return ""
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def build_html(
    lines: list[str],
    scheme: dict[str, str],
    bg_image_path: str | None = None,
    font_size: int = 56,
) -> str:
    """Build clean text card HTML with background image."""

    # Background: image with overlay, or gradient fallback
    if bg_image_path:
        data_uri = _image_to_data_uri(bg_image_path)
        if data_uri:
            bg_css = f"""
      background-image:
        linear-gradient({scheme['overlay']}, {scheme['overlay']}),
        url('{data_uri}');
      background-size: cover;
      background-position: center;
"""
        else:
            bg_css = f"""
      background: radial-gradient(ellipse at 50% 40%, rgba({scheme['accent_rgb']}, 0.12) 0%, #0a0806 100%);
"""
    else:
        bg_css = f"""
      background: radial-gradient(ellipse at 50% 40%, rgba({scheme['accent_rgb']}, 0.12) 0%, #0a0806 100%);
"""

    # Build text lines
    line_parts = []
    for i, line in enumerate(lines):
        is_first = i == 0
        weight = "900" if is_first else "700"
        size = font_size if is_first else int(font_size * 0.72)
        spacing = "0.14em" if is_first else "0.06em"
        cls = "line-hero" if is_first else "line-sub"
        delay = 0.4 + i * 0.45

        line_parts.append(
            f'<p class="{cls}" style="'
            f"font-size:{size}px; font-weight:{weight}; "
            f"letter-spacing:{spacing}; "
            f'animation-delay:{delay}s">'
            f"{line}</p>"
        )
    lines_html = "\n          ".join(line_parts)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
  width:1080px; height:1920px;
  overflow:hidden;
  font-family: 'Noto Sans SC','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;
  display:flex; align-items:center; justify-content:center;
  position:relative;
{bg_css}
}}

/* ---------- text container ---------- */
.text-container {{
  position:relative; z-index:3;
  display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:28px;
  padding: 60px 80px;
}}

/* ---------- text lines ---------- */
.line-hero, .line-sub {{
  margin:0; text-align:center;
  color: {scheme['text_primary']};
  -webkit-text-stroke: {scheme['stroke_width']} {scheme['stroke']};
  paint-order: stroke fill;
  text-shadow:
    0 0 10px rgba(0,0,0,0.8),
    0 2px 4px rgba(0,0,0,0.6),
    0 4px 12px rgba(0,0,0,0.4);
  opacity:0;
  transform:translateY(20px) scale(0.95);
  animation: lineUp 0.7s cubic-bezier(0.16,1,0.3,1) forwards;
}}

.line-hero {{
  color: {scheme['text_primary']};
  -webkit-text-stroke: 5px {scheme['stroke']};
  text-shadow:
    0 0 15px rgba({scheme['accent_rgb']}, 0.3),
    0 2px 6px rgba(0,0,0,0.7),
    0 6px 20px rgba(0,0,0,0.5);
}}

.line-sub {{
  color: {scheme['text_secondary']};
}}

/* ---------- accent divider ---------- */
.divider {{
  width:120px; height:3px;
  background: {scheme['divider_color']};
  border-radius:2px;
  opacity:0;
  animation: growIn 0.5s ease-out 0.25s forwards;
}}

/* ---------- subtle top/bottom gradient for readability ---------- */
body::before {{
  content:''; position:absolute; bottom:0; left:0; right:0;
  height:40%;
  background: linear-gradient(to top, rgba(0,0,0,0.4) 0%, transparent 100%);
  pointer-events:none; z-index:2;
}}

body::after {{
  content:''; position:absolute; top:0; left:0; right:0;
  height:25%;
  background: linear-gradient(to bottom, rgba(0,0,0,0.25) 0%, transparent 100%);
  pointer-events:none; z-index:2;
}}

/* ---------- animations ---------- */
@keyframes lineUp {{
  0%   {{ opacity:0; transform:translateY(20px) scale(0.95); }}
  100% {{ opacity:1; transform:translateY(0) scale(1); }}
}}
@keyframes growIn {{
  0%   {{ opacity:0; width:0; }}
  100% {{ opacity:0.85; width:120px; }}
}}
</style>
</head>
<body>
  <div class="text-container">
    <div class="divider"></div>
    {lines_html}
    <div class="divider"></div>
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_card(
    lines: list[str],
    output_png: Path,
    scheme_name: str = "sings",
    bg_image_path: str | None = None,
    font_size: int = 56,
    width: int = 1080,
    height: int = 1920,
    scale: float = 1.0,
) -> bool:
    """Render text card HTML to PNG via Playwright."""
    scheme = SCHEMES.get(scheme_name, SCHEMES["sings"])
    html = build_html(
        lines=lines,
        scheme=scheme,
        bg_image_path=bg_image_path,
        font_size=font_size,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(2500)
        page.screenshot(path=str(output_png), full_page=False)
        browser.close()

    return output_png.exists()


def render_card_to_video(
    lines: list[str],
    output_mp4: Path,
    duration: float = 5.0,
    scheme_name: str = "sings",
    bg_image_path: str | None = None,
    emotion: str = "shock",
    font_size: int = 56,
    animation: str = "fade_in",
) -> bool:
    """Render text card to MP4 with gentle zoom."""
    with tempfile.TemporaryDirectory() as tmpdir:
        png_path = Path(tmpdir) / "card.png"
        ok = render_card(
            lines=lines,
            output_png=png_path,
            scheme_name=scheme_name,
            bg_image_path=bg_image_path,
            font_size=font_size,
        )
        if not ok:
            return False

        frames = int(duration * 24)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(png_path),
            "-vf",
            f"zoompan=z='min(zoom+0.0006,1.04)':d={frames}:s=1080x1920:fps=24,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration - 0.4}:d=0.4",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", "24",
            "-t", str(duration),
            str(output_mp4),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr[-300:]}", file=sys.stderr)
            return False
    return output_mp4.exists()


# ---------------------------------------------------------------------------
# Config-based rendering
# ---------------------------------------------------------------------------

def render_from_config(
    config_path: Path,
    segment_id: str | None = None,
    output_path: Path | None = None,
    bg_image_path: str | None = None,
) -> bool:
    """Render text card(s) from a video config JSON file."""
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    workflow = config.get("workflow", "medvi")
    scheme_name = "sings" if workflow == "sings" else "medvi"
    global_style = config.get("global", {}).get("style", "")
    if "sings" in global_style or "mv" in global_style:
        scheme_name = "sings"

    segments = config.get("segments", [])
    targets = [s for s in segments if s.get("shot_type") == "text_card"
               and (not segment_id or s["id"] == segment_id)]

    if not targets:
        print(f"No text_card segments found" + (f" matching {segment_id}" if segment_id else ""))
        return False

    for seg in targets:
        cfg = seg.get("text_card_config", {})
        lines = cfg.get("lines", [])
        font_size = cfg.get("font_size", 56)
        emotion = seg.get("emotion", "shock")
        animation = cfg.get("animation", "fade_in")

        if not lines:
            print(f"  {seg['id']}: no lines, skipping")
            continue

        if output_path:
            mp4_path = output_path
        else:
            output_dir = Path(config_path).parent.parent / "output" / video_id
            output_dir.mkdir(parents=True, exist_ok=True)
            mp4_path = output_dir / f"{seg['id']}.mp4"

        seg_bg = bg_image_path
        if not seg_bg:
            ref_dir = Path(config_path).parent.parent / "assets" / "references" / video_id
            for pattern in [f"{seg['id']}*.png", f"{seg['id']}*.jpg"]:
                matches = list(ref_dir.glob(pattern))
                if matches:
                    seg_bg = str(matches[0])
                    break

        print(f"Rendering {seg['id']}: {lines}")
        print(f"  scheme: {scheme_name}, bg: {'image' if seg_bg else 'gradient'}")

        ok = render_card_to_video(
            lines=lines,
            output_mp4=mp4_path,
            duration=seg.get("duration_sec", 5.0),
            scheme_name=scheme_name,
            bg_image_path=seg_bg,
            emotion=emotion,
            font_size=font_size,
            animation=animation,
        )
        if ok:
            print(f"  -> {mp4_path} ({mp4_path.stat().st_size // 1024}KB)")
        else:
            print("  FAILED", file=sys.stderr)
            return False

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Render text cards for video")
    parser.add_argument("--config", type=Path, help="Video config JSON file")
    parser.add_argument("--segment", help="Segment ID to render")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--lines", nargs="+", help="Text lines (quick mode)")
    parser.add_argument("--style", choices=["medvi", "sings"], default="sings")
    parser.add_argument("--bg-image", type=str, help="Background image path")
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--png-only", action="store_true", help="Output PNG not MP4")
    parser.add_argument("--font-size", type=int, default=56)

    args = parser.parse_args()

    if args.config:
        ok = render_from_config(
            config_path=args.config,
            segment_id=args.segment,
            output_path=args.output,
            bg_image_path=args.bg_image,
        )
        sys.exit(0 if ok else 1)

    if args.lines:
        output = args.output or Path("text_card.png" if args.png_only else "text_card.mp4")
        if args.png_only:
            ok = render_card(
                lines=args.lines,
                output_png=output,
                scheme_name=args.style,
                bg_image_path=args.bg_image,
                font_size=args.font_size,
            )
        else:
            ok = render_card_to_video(
                lines=args.lines,
                output_mp4=output,
                duration=args.duration,
                scheme_name=args.style,
                bg_image_path=args.bg_image,
                font_size=args.font_size,
            )
        print(f"Output: {output}")
        sys.exit(0 if ok else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
