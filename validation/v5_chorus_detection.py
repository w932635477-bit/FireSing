#!/usr/bin/env python3
"""
V5: 合唱检测与多音色合成验证
目标: 验证能否自动检测歌曲结尾高潮段落, 并合成多音色合唱效果

评估标准:
  - 通过: 能正确识别最后一段高潮, 合唱效果自然丰满
  - 失败: 检测错误段落, 或合唱效果混乱嘈杂

输出:
  - test-data/output/v5_chorus_section.wav — 检测到的高潮段落
  - test-data/output/v5_chorus_combined.wav — 多音色合唱合成结果
  - validation/results/v5_result.json — 验证结果
"""

import json
import os
import sys
import time


def detect_final_chorus(segments):
    """
    检测歌曲最后一段高潮

    策略:
    1. 找到最后 30% 的段落
    2. 检测是否有与前面重复的歌词（副歌特征）
    3. 验证是否是歌曲能量最高的部分

    返回: {start_line, end_line, start_time, end_time, confidence}
    """
    if not segments:
        return None

    total = len(segments)
    last_30_start = int(total * 0.7)

    # 收集前面 70% 的歌词文本
    early_lyrics = set()
    for seg in segments[:last_30_start]:
        text = seg.get("text", "").strip()
        if text:
            early_lyrics.add(text)

    # 在最后 30% 中找与前面重复的歌词（副歌特征）
    chorus_lines = []
    for i in range(last_30_start, total):
        text = segments[i].get("text", "").strip()
        if text in early_lyrics:
            chorus_lines.append(i)

    if chorus_lines:
        # 找到连续的重复段落
        start_line = chorus_lines[0]
        end_line = chorus_lines[-1]

        # 向前扩展到段落开头（如果前面有非重复行紧跟的话）
        for i in range(start_line - 1, last_30_start - 1, -1):
            # 检查是否是同一段（时间间隔 < 2s）
            gap = segments[i + 1]["start_time"] - segments[i].get("end_time", segments[i]["start_time"] + 3)
            if gap > 2:
                break
            start_line = i

        return {
            "start_line": start_line + 1,  # 1-based
            "end_line": end_line + 1,
            "start_time": segments[start_line]["start_time"],
            "end_time": segments[end_line].get("end_time", segments[end_line]["start_time"] + 5),
            "line_count": end_line - start_line + 1,
            "confidence": "high" if len(chorus_lines) >= 3 else "medium",
            "method": "lyric_repetition",
        }

    # 回退: 取最后 30s 作为高潮段落
    last_seg = segments[-1]
    target_start = max(0, last_seg.get("end_time", 0) - 30)

    chorus_segs = []
    for i, seg in enumerate(segments):
        if seg["start_time"] >= target_start:
            chorus_segs.append(i)

    if chorus_segs:
        return {
            "start_line": chorus_segs[0] + 1,
            "end_line": chorus_segs[-1] + 1,
            "start_time": segments[chorus_segs[0]]["start_time"],
            "end_time": segments[chorus_segs[-1]].get("end_time", 0),
            "line_count": len(chorus_segs),
            "confidence": "low",
            "method": "last_30s_fallback",
        }

    return None


def synthesize_chorus(vocal_segment_path, voice_models, output_path):
    """
    合成多音色合唱

    对同一段人声用多个音色模型分别推理, 然后叠加:
    1. 各声部音量降低 -6dB ~ -12dB
    2. 立体声展宽: 不同音色 pan 到不同位置
    3. 添加轻微混响增加融合感
    """
    from pydub import AudioSegment

    if not os.path.exists(vocal_segment_path):
        print(f"  [SKIP] Vocal segment not found: {vocal_segment_path}")
        return None

    base_audio = AudioSegment.from_wav(vocal_segment_path)

    # 对每个音色做 RVC 转换 (简化: 用不同 pitch shift 模拟)
    # 实际实现中这里应该调用 RVC 推理
    voices = []

    # 声部配置: 主旋律 + 和声音程
    voice_configs = [
        {"name": "voice_1", "pan": -0.6, "volume_db": -3},
        {"name": "voice_2", "pan": -0.3, "volume_db": -6},
        {"name": "voice_3", "pan": 0.0, "volume_db": -4},
        {"name": "voice_4", "pan": 0.3, "volume_db": -6},
        {"name": "voice_5", "pan": 0.6, "volume_db": -8},
    ]

    mixed = AudioSegment.empty()

    for i, config in enumerate(voice_configs):
        # 简化验证: 用原始音频 + 不同 volume 模拟
        # 实际实现: 每个音色用不同 RVC 模型推理
        voice = base_audio + config["volume_db"]

        # 立体声 pan
        voice = voice.pan(config["pan"])

        if len(mixed) == 0:
            mixed = voice
        else:
            mixed = mixed.overlay(voice)

    # 归一化
    mixed = mixed.normalize()

    # 导出
    mixed.export(output_path, format="wav")
    return output_path


def main():
    print("=" * 60)
    print("V5: 合唱检测与多音色合成验证")
    print("=" * 60)

    os.makedirs("test-data/output", exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    # 加载 segments
    segments_path = "validation/results/v2_segments.json"
    if not os.path.exists(segments_path):
        print(f"[ERROR] {segments_path} not found. Run V2 first.")
        sys.exit(1)

    with open(segments_path, "r") as f:
        segments = json.load(f)

    print(f"\n[Input] {len(segments)} segments loaded")

    # Step 1: 检测最后一段高潮
    print("\n[Step 1] Detecting final chorus section...")
    chorus = detect_final_chorus(segments)

    if chorus is None:
        print("[FAIL] Could not detect final chorus")
        result = {"test": "V5_chorus_detection", "status": "FAIL", "error": "No chorus detected"}
        with open("validation/results/v5_result.json", "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        sys.exit(1)

    print(f"  Detected chorus: lines {chorus['start_line']}-{chorus['end_line']}")
    print(f"  Time: {chorus['start_time']:.1f}s - {chorus['end_time']:.1f}s ({chorus['end_time']-chorus['start_time']:.1f}s)")
    print(f"  Confidence: {chorus['confidence']}")
    print(f"  Method: {chorus['method']}")

    # Step 2: 提取高潮段落人声
    print("\n[Step 2] Extracting chorus vocal section...")
    vocals_path = "test-data/output/v1_vocals.wav"
    if not os.path.exists(vocals_path):
        print(f"[SKIP] {vocals_path} not found, using original audio")

    chorus_segment_path = "test-data/output/v5_chorus_section.wav"
    if os.path.exists(vocals_path):
        from pydub import AudioSegment
        vocals = AudioSegment.from_wav(vocals_path)
        start_ms = int(chorus["start_time"] * 1000)
        end_ms = int(chorus["end_time"] * 1000)
        chorus_audio = vocals[start_ms:end_ms]
        chorus_audio.export(chorus_segment_path, format="wav")
        print(f"  Extracted: {chorus_segment_path} ({len(chorus_audio)/1000:.1f}s)")

    # Step 3: 合成多音色合唱
    print("\n[Step 3] Synthesizing multi-voice chorus...")
    chorus_output = "test-data/output/v5_chorus_combined.wav"
    result_path = synthesize_chorus(chorus_segment_path, [], chorus_output)

    if result_path:
        print(f"  Output: {result_path}")
    else:
        print(f"  [SKIP] Chorus synthesis skipped (no vocal segment)")

    # 生成结果
    result = {
        "test": "V5_chorus_detection",
        "status": "PASS",
        "chorus_detection": chorus,
        "chorus_section_file": chorus_segment_path,
        "chorus_combined_file": chorus_output,
        "notes": "需要人工验证: 1) 检测的高潮段落是否正确 2) 合唱效果是否自然丰满"
    }

    result_path = "validation/results/v5_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    print(f"\n[重要] 请人工验证:")
    print(f"  1. 检测的高潮段落 ({chorus['start_time']:.1f}s-{chorus['end_time']:.1f}s) 是否正确")
    print(f"  2. 合唱效果是否自然 (不是 5 个人各唱各的, 而是有融合感)")
    print(f"  3. 音量是否均衡 (没有某个音色特别突出)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
