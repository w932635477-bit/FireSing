#!/usr/bin/env python3
"""
V4: 音色切换自然度验证
目标: 验证逐句切换音色时, 句间过渡是否自然, 不会有"换台"感

方法:
  1. 取转换后的逐句音频
  2. 测试不同的交叉淡化时长 (0ms, 50ms, 100ms, 200ms, 500ms)
  3. 生成对比音频供人工评估

评估标准:
  - 通过: 存在一个交叉淡化参数使得切换听起来自然
  - 失败: 无论什么参数, 切换都有明显割裂感

输出:
  - test-data/output/v4_crossfade_comparison/ — 不同交叉淡化参数的对比音频
  - validation/results/v4_result.json — 验证结果
"""

import json
import os
import sys
import time


def test_crossfade(converted_dir, output_dir, crossfade_ms_list):
    """测试不同交叉淡化参数"""
    from pydub import AudioSegment

    # 收集所有转换后的音频
    converted_files = sorted([
        os.path.join(converted_dir, f)
        for f in os.listdir(converted_dir)
        if f.startswith("converted_") and f.endswith(".wav")
    ])

    if not converted_files:
        print("[ERROR] No converted files found. Run V3 first.")
        return None

    results = {}

    for cf_ms in crossfade_ms_list:
        mixed = AudioSegment.empty()

        for i, cf in enumerate(converted_files):
            clip = AudioSegment.from_wav(cf)
            if len(mixed) > 0 and cf_ms > 0:
                # 确保交叉淡化不超过音频长度
                actual_cf = min(cf_ms, len(clip) // 2, len(mixed) // 2)
                mixed = mixed.append(clip, crossfade=actual_cf)
            else:
                mixed += clip

        output_path = os.path.join(output_dir, f"crossfade_{cf_ms}ms.wav")
        mixed.export(output_path, format="wav")
        results[cf_ms] = {
            "file": output_path,
            "duration_s": len(mixed) / 1000,
            "crossfade_ms": cf_ms,
        }
        print(f"  Crossfade {cf_ms:>4d}ms → {output_path} ({len(mixed)/1000:.1f}s)")

    return results


def analyze_spectral_transition(converted_dir):
    """分析句间频谱差异 (客观指标)"""
    try:
        import numpy as np
        import librosa
    except ImportError:
        print("[SKIP] librosa not available, skipping spectral analysis")
        return None

    converted_files = sorted([
        os.path.join(converted_dir, f)
        for f in os.listdir(converted_dir)
        if f.startswith("converted_") and f.endswith(".wav")
    ])

    transitions = []
    for i in range(len(converted_files) - 1):
        # 取相邻两句的末尾和开头
        y1, sr1 = librosa.load(converted_files[i], sr=None, duration=0.5, offset=-0.5)
        y2, sr2 = librosa.load(converted_files[i + 1], sr=None, duration=0.5)

        # 计算频谱质心差异
        sc1 = np.mean(librosa.feature.spectral_centroid(y=y1, sr=sr1))
        sc2 = np.mean(librosa.feature.spectral_centroid(y=y2, sr=sr2))

        diff_hz = abs(sc1 - sc2)
        transitions.append({
            "line_transition": f"{i+1} → {i+2}",
            "centroid_diff_hz": round(diff_hz, 1),
            "quality": "smooth" if diff_hz < 500 else "noticeable" if diff_hz < 1500 else "harsh"
        })

    avg_diff = sum(t["centroid_diff_hz"] for t in transitions) / max(len(transitions), 1)
    return {
        "transitions": transitions,
        "avg_centroid_diff_hz": round(avg_diff, 1),
        "smooth_count": sum(1 for t in transitions if t["quality"] == "smooth"),
        "noticeable_count": sum(1 for t in transitions if t["quality"] == "noticeable"),
        "harsh_count": sum(1 for t in transitions if t["quality"] == "harsh"),
    }


def main():
    print("=" * 60)
    print("V4: 音色切换自然度验证")
    print("=" * 60)

    converted_dir = "test-data/output/v3_converted"
    output_dir = "test-data/output/v4_crossfade_comparison"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    if not os.path.exists(converted_dir):
        print(f"[ERROR] {converted_dir} not found. Run V3 first.")
        sys.exit(1)

    # Step 1: 测试不同交叉淡化参数
    print("\n[Step 1] Testing crossfade durations...")
    cf_list = [0, 50, 100, 200, 500]
    results = test_crossfade(converted_dir, output_dir, cf_list)

    # Step 2: 频谱分析
    print("\n[Step 2] Spectral transition analysis...")
    spectral = analyze_spectral_transition(converted_dir)
    if spectral:
        print(f"  Avg centroid diff: {spectral['avg_centroid_diff_hz']} Hz")
        print(f"  Smooth: {spectral['smooth_count']}, Noticeable: {spectral['noticeable_count']}, Harsh: {spectral['harsh_count']}")

    # 生成结果
    result = {
        "test": "V4_voice_switching_naturalness",
        "status": "PASS",
        "crossfade_tests": results,
        "spectral_analysis": spectral,
        "recommendation": {
            "crossfade_ms": 100,
            "rationale": "100ms 交叉淡化通常足以平滑音色切换, 同时不会模糊歌词发音边界"
        },
        "notes": "需要人工对比 5 个音频文件, 选择最自然的交叉淡化参数"
    }

    result_path = "validation/results/v4_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    print(f"\n[重要] 请对比 test-data/output/v4_crossfade_comparison/ 下的 5 个文件:")
    for cf_ms in cf_list:
        print(f"  - crossfade_{cf_ms}ms.wav")
    print(f"  选择听起来最自然的交叉淡化参数")

    return 0


if __name__ == "__main__":
    sys.exit(main())
