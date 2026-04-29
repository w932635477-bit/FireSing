#!/usr/bin/env python3
"""
Render HTML templates to 1080x1920 PNG screenshots using Playwright.

Usage:
  python3 screenshot-renderer.py --template tpl-boss-search --output ../output/unemploy-01-fired47/SS01.png
  python3 screenshot-renderer.py --all --output-dir ../output/unemploy-01-fired47
"""

import argparse
import sys
import time
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def render_template(template_name: str, output_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    html_path = TEMPLATE_DIR / f"{template_name}.html"
    if not html_path.exists():
        print(f"ERROR: template not found: {html_path}")
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(html_path.as_uri())
        time.sleep(0.5)
        page.screenshot(path=str(output_path), full_page=False)
        browser.close()

    print(f"OK: {output_path} ({output_path.stat().st_size // 1024}KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render HTML templates to PNG")
    parser.add_argument("--template", type=str, help="Template name (without .html)")
    parser.add_argument("--output", type=str, help="Output PNG path")
    parser.add_argument("--all", action="store_true", help="Render all templates")
    parser.add_argument("--output-dir", type=str, help="Output directory for --all")
    args = parser.parse_args()

    if args.all:
        out_dir = Path(args.output_dir) if args.output_dir else Path(".")
        out_dir.mkdir(parents=True, exist_ok=True)
        for html_file in sorted(TEMPLATE_DIR.glob("*.html")):
            name = html_file.stem
            render_template(name, out_dir / f"{name}.png")
    elif args.template and args.output:
        render_template(args.template, Path(args.output))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
