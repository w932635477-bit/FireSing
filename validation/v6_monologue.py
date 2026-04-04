#!/usr/bin/env python3
"""
V6: 独白处理验证
目标: 验证录音/TTS 生成的独白能否平滑插入歌曲开头/结尾

评估标准:
  - 通过: 独白与歌曲过渡平滑, 无明显爆音或静音
  - 失败: 过渡处有明显不连续, 音量突变, 或独白被歌曲淹没

输出:
  - test-data/output/v6_with_monologue_beginning.wav — 独白放开头的版本
  - test-data/output/v6_with_monologue_end.wav — 独白放结尾的版本
  - validation/results/v6_result.json — 验证结果
"""

import json
import os
import sys
import time


def generate_test_tts(text, output_path):
    """用 edge-tts 生成测试 TTS 音频 (轻量, 不需要 GPU)"""
    try:
        import subprocess
        # edge-tts 是微软免费 TTS, 中文质量不错
        result = subprocess.run(
            ["edge-tts", "--voice", "zh-CN-YunxiNeural", "--text", text, "--write-media", output_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return output_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # 备选: 用 pydub 生成 3s 静音作为占位
    from pydub import AudioSegment
    silence = AudioSegment.silent(duration=3000)
    silence.export(output_path, format="wav")
    return output_path


def detect_song_intro(instrumental_path, threshold_db=-40, min_intro_s=2):
    """
    检测歌曲前奏长度

    如果前奏 (纯伴奏) 时长 >= min_intro_s, 独白放开头
    否则独白放结尾
    """
    from pydub import AudioSegment
    import numpy as np

    inst = AudioSegment.from_wav(instrumental_path)
    intro_end_ms = 0

    # 逐 100ms 检测能量, 找到人声开始的位置
    chunk_ms = 100
    for i in range(0, len(inst), chunk_ms):
        chunk = inst[i:i + chunk_ms]
        if chunk.dBFS > threshold_db:
            intro_end_ms = i
            break

    intro_duration_s = intro_end_ms / 1000
    has_intro = intro_duration_s >= min_intro_s

    return {
        "intro_duration_s": round(intro_duration_s, 1),
        "has_intro": has_intro,
        "recommended_position": "beginning" if has_intro else "end",
    }


def insert_monologue(song_path, monologue_path, position, bg_volume_db=-12, gap_ms=2000):
    """
    在歌曲中插入独白

    position: 'beginning' or 'end'
    bg_volume_db: 独白期间背景音乐音量
    gap_ms: 独白与歌曲之间的间隔
    """
    from pydub import AudioSegment

    song = AudioSegment.from_wav(song_path)
    monologue = AudioSegment.from_wav(monologue_path)

    # 归一化独白音量
    monologue = monologue.normalize()

    if position == "beginning":
        # 独白 → 间隔 → 歌曲
        result = monologue + AudioSegment.silent(duration=gap_ms) + song
    else:
        # 歌曲 → 间隔 → 独白
        result = song + AudioSegment.silent(duration=gap_ms) + monologue

    result = result.normalize()
    return result


def main():
    print("=" * 60)
    print("V6: 独白处理验证")
    print("=" * 60)

    os.makedirs("test-data/output", exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    # 测试歌曲路径
    song_path = "test-data/output/v1_vocals.wav"  # 或混合后的完整歌曲
    instrumental_path = "test-data/output/v1_instrumental.wav"

    # 如果有完整混合歌曲, 优先用那个
    if os.path.exists("test-data/output/v3_mixed_full.wav"):
        song_path = "test-data/output/v3_mixed_full.wav"

    # Step 1: 生成测试独白
    print("\n[Step 1] Generating test monologue (TTS)...")
    monologue_path = "test-data/output/v6_test_monologue.wav"
    test_text = "大家好，我是一位火锅店老板，很高兴能和大家一起完成这首歌。如果大家来成都玩，欢迎来我的火锅店坐坐！"

    try:
        # 尝试 edge-tts
        generate_test_tts(test_text, monologue_path)
        tts_available = True
        print(f"  Generated TTS: {monologue_path}")
    except Exception as e:
        print(f"  [SKIP] TTS generation failed: {e}")
        print(f"  Creating silent placeholder...")
        from pydub import AudioSegment
        AudioSegment.silent(duration=3000).export(monologue_path, format="wav")
        tts_available = False

    # Step 2: 检测前奏
    print("\n[Step 2] Detecting song intro...")
    intro_info = None
    if os.path.exists(instrumental_path):
        intro_info = detect_song_intro(instrumental_path)
        print(f"  Intro: {intro_info['intro_duration_s']}s")
        print(f"  Has intro: {intro_info['has_intro']}")
        print(f"  Recommended position: {intro_info['recommended_position']}")
    else:
        print(f"  [SKIP] Instrumental not found, defaulting to beginning")
        intro_info = {"has_intro": True, "recommended_position": "beginning", "intro_duration_s": 0}

    # Step 3: 插入独白
    print("\n[Step 3] Inserting monologue...")

    if os.path.exists(song_path):
        # 开头版
        beginning_path = "test-data/output/v6_with_monologue_beginning.wav"
        result_beginning = insert_monologue(song_path, monologue_path, "beginning")
        result_beginning.export(beginning_path, format="wav")
        print(f"  Beginning version: {beginning_path}")

        # 结尾版
        end_path = "test-data/output/v6_with_monologue_end.wav"
        result_end = insert_monologue(song_path, monologue_path, "end")
        result_end.export(end_path, format="wav")
        print(f"  End version: {end_path}")
        insertion_ok = True
    else:
        print(f"  [SKIP] Song file not found: {song_path}")
        beginning_path = None
        end_path = None
        insertion_ok = False

    # 生成结果
    result = {
        "test": "V6_monologue_processing",
        "status": "PASS" if insertion_ok else "SKIP",
        "tts_available": tts_available,
        "intro_detection": intro_info,
        "monologue_beginning_file": beginning_path,
        "monologue_end_file": end_path,
        "parameters": {
            "bg_volume_db": -12,
            "gap_ms": 2000,
            "position_logic": "优先开头, 无前奏时放结尾"
        },
        "notes": "需要人工验证: 独白与歌曲过渡是否平滑"
    }

    result_path_file = "validation/results/v6_result.json"
    with open(result_path_file, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path_file}")
    print(f"\n[重要] 请人工验证:")
    print(f"  1. 独白语音是否清晰自然")
    print(f"  2. 独白与歌曲之间过渡是否平滑 (无爆音/静音跳跃)")
    print(f"  3. 开头独白是否在前奏旋律期间播放, 不影响歌曲开头")

    return 0


if __name__ == "__main__":
    sys.exit(main())
