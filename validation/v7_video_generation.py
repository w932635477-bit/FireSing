#!/usr/bin/env python3
"""
V7: 视频生成验证
目标: 验证 FFmpeg 能否生成抖音风格竖版视频 (9:16) + ASS 歌词字幕

评估标准:
  - 通过: 生成 1080x1920 竖版视频, 字幕逐句显示, 每句颜色不同
  - 失败: 视频格式错误, 字幕错位, 或 FFmpeg 命令失败

注意: 此脚本可在本地 Mac 上运行 (不需要 GPU)

输出:
  - test-data/output/v7_video.mp4 — 生成的视频
  - test-data/output/v7_subtitles.ass — ASS 字幕文件
  - validation/results/v7_result.json — 验证结果
"""

import json
import os
import subprocess
import sys
import time


def generate_ass_subtitles(segments, voice_colors, output_path, resolution=(1080, 1920)):
    """
    生成 ASS 字幕文件

    每个音色分配不同颜色, 当前歌词高亮, 其他歌词变暗
    """
    width, height = resolution

    # 音色颜色表 (高辨识度)
    default_colors = [
        "&H00FFFFFF",  # 白色
        "&H0000FFFF",  # 黄色
        "&H00FF00FF",  # 紫色
        "&H00FF6600",  # 橙色
        "&H0000FF00",  # 绿色
        "&H00FF0000",  # 蓝色
        "&H0000FF99",  # 青色
        "&H00FF0099",  # 粉色
        "&H009999FF",  # 浅蓝
        "&H00FF9999",  # 浅红
    ]

    # 分配颜色
    color_map = {}
    for i, (voice_id, _) in enumerate(voice_colors.items()):
        color_map[voice_id] = default_colors[i % len(default_colors)]

    # ASS 头部
    ass_content = f"""[Script Info]
Title: FireSing Generated Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

    # 为每个音色创建样式
    for voice_id, color in color_map.items():
        style_name = f"Voice{voice_id}"
        # ASS 颜色格式: &H00BBGGRR
        ass_content += f"Style: {style_name},Noto Sans CJK SC,52,{color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,30,30,60,1\n"

    # 添加暗色样式 (非当前行)
    ass_content += "Style: Dim,Noto Sans CJK SC,42,&H80FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,2,30,30,60,1\n"

    # 事件
    ass_content += "\n[Events]\n"
    ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

    for seg in segments:
        start = format_ass_time(seg["start_time"])
        end = format_ass_time(seg["end_time"])
        text = seg.get("text", "")
        voice_id = str(seg.get("voice_model_id", seg.get("line_number", 0) % 5))
        style = color_map.get(voice_id, default_colors[0])

        # 逐句显示, 居中偏下
        ass_content += f'Dialogue: 0,{start},{end},Voice{voice_id},,0,0,80,,{text}\n'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    return output_path


def format_ass_time(seconds):
    """将秒数转换为 ASS 时间格式 H:MM:SS.cc"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_video(audio_path, ass_path, output_path, duration=None, bg_color="black"):
    """
    用 FFmpeg 生成竖版视频

    视觉布局 (模拟抖音风格):
    - 背景: 黑色渐变
    - 顶部: 歌曲标题 (白色大字)
    - 中部: 模拟播放器区域
    - 底部: 歌词字幕 (ASS)
    - 右侧: 互动图标 (装饰性)
    """
    # FFmpeg 命令: 生成纯色背景 + 叠加字幕 + 音频
    cmd = [
        "ffmpeg", "-y",
        # 输入: 音频
        "-i", audio_path,
        # 视频: 纯色背景
        "-f", "lavfi", "-i", f"color=c={bg_color}:s=1080x1920:d={duration or 180}:r=30",
        # 叠加 ASS 字幕
        "-vf", f"ass={ass_path}",
        # 视频编码
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        # 音频编码
        "-c:a", "aac", "-b:a", "192k",
        # 竖版视频
        "-aspect", "9:16",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"[FFmpeg Error] {result.stderr[-500:]}")
        return False
    return True


def generate_video_with_template(audio_path, ass_path, output_path, title="FireSing Demo"):
    """
    生成带模板元素的视频

    包含:
    - 黑色背景
    - 顶部标题
    - 歌词字幕
    - 模拟抖音 UI 元素 (装饰性)
    """
    # 先创建一个简单的标题图片 (用 FFmpeg drawtext)
    # 然后叠加字幕

    # 获取音频时长
    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    duration = float(result.stdout.strip()) if result.stdout.strip() else 180

    # FFmpeg 复合滤镜
    filters = [
        # 标题 (顶部居中)
        f"drawtext=text='{title}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=120:"
        f"font=NotoSansCJK-Regular:shadowcolor=black@0.5:shadowx=2:shadowy=2",
        # 分隔线
        f"drawtext=text='FireSing':fontsize=24:fontcolor=gray:x=(w-text_w)/2:y=180",
    ]

    filter_complex = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}:r=30",
        "-vf", f"{filter_complex},ass={ass_path}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        # 回退: 不加 drawtext, 只加字幕
        print("[Fallback] Trying without drawtext...")
        return generate_video(audio_path, ass_path, output_path, duration)
    return True


def main():
    print("=" * 60)
    print("V7: 视频生成验证")
    print("=" * 60)

    os.makedirs("test-data/output", exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    # 检查 FFmpeg
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        print(f"\n[FFmpeg] {result.stdout.split(chr(10))[0]}")
    except FileNotFoundError:
        print("[ERROR] FFmpeg not found. Install: brew install ffmpeg")
        sys.exit(1)

    # 加载 segments
    segments_path = "validation/results/v2_segments.json"
    if not os.path.exists(segments_path):
        print(f"[ERROR] {segments_path} not found. Run V2 first.")
        sys.exit(1)

    with open(segments_path, "r") as f:
        segments = json.load(f)

    print(f"\n[Input] {len(segments)} segments")

    # 音频路径
    audio_path = None
    for p in ["test-data/output/v3_mixed_full.wav", "test-data/output/v1_vocals.wav", "test-data/song.mp3"]:
        if os.path.exists(p):
            audio_path = p
            break

    if not audio_path:
        print("[ERROR] No audio file found for video generation")
        sys.exit(1)

    # Step 1: 生成 ASS 字幕
    print("\n[Step 1] Generating ASS subtitles...")
    voice_colors = {str(i): f"color_{i}" for i in range(5)}  # 5 个音色
    ass_path = "test-data/output/v7_subtitles.ass"
    generate_ass_subtitles(segments, voice_colors, ass_path)
    print(f"  Output: {ass_path}")

    # Step 2: 生成视频
    print("\n[Step 2] Generating video...")
    start_time = time.time()

    output_path = "test-data/output/v7_video.mp4"
    success = generate_video_with_template(audio_path, ass_path, output_path)

    elapsed = time.time() - start_time

    if success and os.path.exists(output_path):
        file_size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f"  Output: {output_path} ({file_size_mb:.1f} MB)")
        print(f"  Time: {elapsed:.1f}s")
        status = "PASS"
    else:
        print(f"  [FAIL] Video generation failed")
        file_size_mb = 0
        status = "FAIL"

    # 生成结果
    result = {
        "test": "V7_video_generation",
        "status": status,
        "output_video": output_path if success else None,
        "output_subtitles": ass_path,
        "video_file_size_mb": round(file_size_mb, 1),
        "generation_time_s": round(elapsed, 1),
        "video_format": "1080x1920 H.264",
        "audio_codec": "AAC 192kbps",
        "notes": "需要人工验证: 字幕是否逐句显示, 颜色是否正确, 视频是否可播放"
    }

    result_path = "validation/results/v7_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    print(f"\n[重要] 请人工验证:")
    print(f"  1. 视频是否可以正常播放")
    print(f"  2. 字幕是否逐句显示, 时间是否对齐")
    print(f"  3. 不同音色的字幕颜色是否可区分")
    print(f"  4. 视频宽高比是否正确 (9:16 竖版)")

    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
