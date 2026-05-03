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
