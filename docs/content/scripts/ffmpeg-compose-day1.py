#!/usr/bin/env python3
"""
FFmpeg Day 1 Video Composer v2
Fixes: correct speed formula, loop instead of stretch, better title cards.

Usage:
  python3 ffmpeg-compose-day1.py
"""

import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VIDEO_DIR = PROJECT_ROOT / "docs" / "content" / "output" / "day1"
AUDIO_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "output"
TEMP_DIR = OUTPUT_DIR / "temp"

SEGMENTS = [
    {
        "id": "S01",
        "audio": "S01-hook-numbers.mp3",
        "video": "S01.mp4",
        "subtitle": "一个人，2万美元启动资金，14个月做到4亿美元营收。",
    },
    {
        "id": "S02",
        "audio": "S02-hook-team.mp3",
        "video": "S02.mp4",
        "subtitle": "团队只有2个人。",
    },
    {
        "id": "S03",
        "audio": "S03-character-intro.mp3",
        "video": "S03.mp4",
        "subtitle": "这个人叫Matthew Gallagher，在拖车公园长大，用叔叔送的笔记本电脑自学编程。",
    },
    {
        "id": "S04",
        "audio": "S04-startup.mp3",
        "video": "S04.mp4",
        "subtitle": "2024年9月，他用2万美元启动了一个远程医疗平台叫Medvi，卖减肥药。",
    },
    {
        "id": "S05",
        "audio": "S05-key-data.mp3",
        "video": "S05.mp4",
        "subtitle": "关键数据来了：2025年，营收4.01亿美元，净利润6500万，净利率16.2%。",
    },
    {
        "id": "S06",
        "audio": "S06-comparison.mp3",
        "video": "S06.mp4",
        "subtitle": "对比一下，行业巨头Hims & Hers有2400多名员工，净利率才5.5%。",
    },
    {
        "id": "S07",
        "audio": "S07-profit-summary.mp3",
        "video": "S07.mp4",
        "subtitle": "他用2个人，跑了同行3倍的利润率。",
    },
    {
        "id": "S08",
        "audio": "S08-ai-tools.mp3",
        "video": None,
        "subtitle": "怎么做到的？全部用AI搭建。代码用ChatGPT和Claude写，广告素材用Midjourney和Runway生成，客服用AI机器人。",
        "title_card_text": "AI TOOLS",
    },
    {
        "id": "S09",
        "audio": "S09-daily-revenue.mp3",
        "video": "S09.mp4",
        "subtitle": "日营收超过300万美元。",
    },
    {
        "id": "S10",
        "audio": "S10-cta.mp3",
        "video": None,
        "subtitle": "这整套工具链，国内都有免费替代。想知道具体怎么用？关注我，接下来一条一条拆。私信AI获客，我发你完整工具清单。",
        "title_card_text": "私信 AI获客",
    },
]


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def find_font(size: int = 48):
    for path in [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def generate_title_card(text: str, sub_text: str, duration: float, output_path: Path) -> None:
    """Generate a styled title card with dark gradient background + gold text."""
    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (10, 10, 10))
    draw = ImageDraw.Draw(img)

    # Draw subtle gradient overlay (dark edges, slightly lighter center)
    for y in range(H):
        progress = abs(y - H / 2) / (H / 2)
        val = max(10, int(25 * (1 - progress)))
        draw.line([(0, y), (W, y)], fill=(val, val, val + 2))

    # Draw decorative lines
    line_y = H // 2 - 120
    draw.line([(100, line_y), (620, line_y)], fill=(60, 50, 20), width=1)
    line_y2 = H // 2 + 120
    draw.line([(100, line_y2), (620, line_y2)], fill=(60, 50, 20), width=1)

    # Main title
    font_big = find_font(64)
    bbox = draw.textbbox((0, 0), text, font=font_big)
    tw = bbox[2] - bbox[0]
    x, y = (W - tw) / 2, H / 2 - 50
    # Shadow
    draw.text((x + 2, y + 2), text, fill=(40, 30, 10), font=font_big)
    # Gold text
    draw.text((x, y), text, fill=(212, 175, 55), font=font_big)

    # Subtitle text (if provided, show first 30 chars)
    if sub_text:
        short = sub_text[:30] + "..." if len(sub_text) > 30 else sub_text
        font_small = find_font(28)
        bbox2 = draw.textbbox((0, 0), short, font=font_small)
        tw2 = bbox2[2] - bbox2[0]
        x2 = (W - tw2) / 2
        draw.text((x2, H / 2 + 50), short, fill=(160, 160, 160), font=font_small)

    card_img = TEMP_DIR / f"{output_path.stem}.png"
    img.save(str(card_img))

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(card_img),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-r", "24",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def prepare_segment(seg: dict, output_path: Path) -> None:
    """Prepare a video segment matching the audio duration."""
    audio_path = AUDIO_DIR / seg["audio"]
    target_duration = get_duration(audio_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if seg["video"] is None:
        print(f"  {seg['id']}: Title card ({target_duration:.1f}s)")
        generate_title_card(seg["title_card_text"], seg["subtitle"], target_duration, output_path)
        return

    video_path = VIDEO_DIR / seg["video"]
    video_duration = get_duration(video_path)

    if target_duration <= video_duration * 1.05:
        # Audio shorter or similar: just trim
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
    elif target_duration <= video_duration * 1.8:
        # Slightly longer: slow down (speed > 1 in setpts = slower)
        speed_factor = target_duration / video_duration
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-filter:v", f"setpts={speed_factor}*PTS",
            "-t", str(target_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-pix_fmt", "yuv420p", "-r", "24",
            str(output_path),
        ]
    else:
        # Much longer: loop the video with crossfade
        loop_and_concat(video_path, target_duration, output_path)
        return

    subprocess.run(cmd, check=True, capture_output=True)


def loop_and_concat(video_path: Path, target_duration: float, output_path: Path) -> None:
    """Loop a video clip with crossfade transitions to fill target duration."""
    clip_duration = get_duration(video_path)
    loops_needed = int(target_duration / clip_duration) + 1

    parts = []
    for i in range(loops_needed):
        part_path = TEMP_DIR / f"{output_path.stem}_loop_{i}.mp4"
        # Alternate: use reverse for seamless loop feel
        if i % 2 == 0:
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", "-pix_fmt", "yuv420p", "-r", "24",
                str(part_path),
            ]
        else:
            # Reverse for smoother looping
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", "reverse",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-an", "-pix_fmt", "yuv420p", "-r", "24",
                str(part_path),
            ]
        subprocess.run(cmd, check=True, capture_output=True)
        parts.append(part_path)

    # Concat all loop parts
    concat_file = TEMP_DIR / f"{output_path.stem}_loops.txt"
    with open(concat_file, "w") as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-t", str(target_duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Cleanup loop parts
    for p in parts:
        p.unlink(missing_ok=True)


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Prepare segments
    print("Step 1: Preparing video segments...")
    prepared = []
    total_duration = 0.0

    for seg in SEGMENTS:
        audio_path = AUDIO_DIR / seg["audio"]
        duration = get_duration(audio_path)
        total_duration += duration
        output_path = TEMP_DIR / f"{seg['id']}_trimmed.mp4"

        print(f"  {seg['id']}: audio={duration:.1f}s", end="")
        prepare_segment(seg, output_path)

        actual = get_duration(output_path)
        print(f" → video={actual:.1f}s")
        prepared.append(output_path)

    print(f"\nTotal audio: {total_duration:.1f}s")

    # Step 2: Concat video
    print("\nStep 2: Concatenating video segments...")
    concat_file = TEMP_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for vp in prepared:
            f.write(f"file '{vp.resolve()}'\n")

    concat_video = TEMP_DIR / "concat_raw.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(concat_video),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    video_dur = get_duration(concat_video)
    print(f"  Concatenated: {video_dur:.1f}s")

    # Step 3: Concat audio
    print("\nStep 3: Concatenating audio segments...")
    concat_audio_file = TEMP_DIR / "audio_concat.txt"
    with open(concat_audio_file, "w") as f:
        for seg in SEGMENTS:
            f.write(f"file '{(AUDIO_DIR / seg['audio']).resolve()}'\n")

    concat_audio = TEMP_DIR / "narration.mp3"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_audio_file),
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(concat_audio),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    audio_dur = get_duration(concat_audio)
    print(f"  Narration: {audio_dur:.1f}s")

    # Step 4: Merge video + audio + post-processing
    print("\nStep 4: Final composite...")
    final_output = OUTPUT_DIR / "day1-rough-cut-v2.mp4"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_video),
        "-i", str(concat_audio),
        "-filter_complex",
        (
            "[0:v]noise=c0s=12:c0f=t+u,"
            "eq=contrast=1.08:saturation=0.92:brightness=0.01,"
            "vignette=angle=0.3:mode=forward"
            "[v]"
        ),
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        # No -shortest: let audio determine length
        str(final_output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FFmpeg error: {result.stderr[-500:]}")
        sys.exit(1)

    final_dur = get_duration(final_output)
    print(f"\n  Output: {final_output}")
    print(f"  Duration: {final_dur:.1f}s (target: {total_duration:.1f}s)")
    print(f"  Resolution: 720x1280 (9:16)")
    print(f"\nNext steps in 剪映:")
    print("  - Add BGM (8-12% volume)")
    print("  - Replace S08 title card with real tool screenshots")
    print("  - Replace S10 title card with branded CTA")
    print("  - Fine-tune color grading")


if __name__ == "__main__":
    main()
