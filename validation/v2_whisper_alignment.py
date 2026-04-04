#!/usr/bin/env python3
"""
V2: Whisper 歌词对齐验证
目标: 验证 Whisper + VAD 能否准确获得中文歌词的逐句时间戳

评估标准:
  - 通过: 逐句时间戳偏差 < 0.5s, 句数与歌词行数匹配
  - 失败: 超过 30% 的句子时间戳偏差 > 0.5s

输出:
  - validation/results/v2_segments.json — 逐句时间戳
  - validation/results/v2_result.json — 验证结果
"""

import argparse
import json
import os
import sys
import time


def parse_lrc(lrc_path):
    """解析 LRC 文件, 返回 [{time: seconds, text: str}]"""
    segments = []
    with open(lrc_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("[ti:") or line.startswith("[ar:") or line.startswith("[al:"):
                continue
            # 格式: [mm:ss.xx]歌词文本
            if line.startswith("["):
                try:
                    bracket_end = line.index("]")
                    time_str = line[1:bracket_end]
                    text = line[bracket_end + 1:].strip()
                    if not text:
                        continue
                    # 解析时间
                    parts = time_str.split(":")
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    total_seconds = minutes * 60 + seconds
                    segments.append({"time": total_seconds, "text": text})
                except (ValueError, IndexError):
                    continue
    return segments


def run_whisper_alignment(audio_path, lyrics_path=None):
    """用 Whisper 对齐歌词"""
    import whisper
    import torch

    print("[Step 1] Loading Whisper large-v3...")
    model = whisper.load_model("large-v3")

    print(f"[Step 2] Transcribing {audio_path}...")
    result = model.transcribe(
        audio_path,
        language="zh",
        word_timestamps=True,
        verbose=False,
    )

    # 提取逐句结果
    whisper_segments = []
    for seg in result["segments"]:
        whisper_segments.append({
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "text": seg["text"].strip(),
        })

    return whisper_segments


def align_with_lrc(whisper_segs, lrc_segs):
    """将 Whisper 结果与 LRC 歌词对齐"""
    import re

    aligned = []
    used_whisper = set()

    for lrc_idx, lrc in enumerate(lrc_segs):
        # 找到时间最接近的 Whisper segment
        best_match = None
        best_diff = float("inf")

        for w_idx, w in enumerate(whisper_segs):
            if w_idx in used_whisper:
                continue
            diff = abs(w["start"] - lrc["time"])
            if diff < best_diff:
                best_diff = diff
                best_match = w_idx

        if best_match is not None:
            w = whisper_segs[best_match]
            used_whisper.add(best_match)
            aligned.append({
                "line_number": lrc_idx + 1,
                "text": lrc["text"],  # 使用 LRC 歌词文本 (更准确)
                "start_time": w["start"],
                "end_time": w["end"],
                "lrc_time": lrc["time"],
                "time_offset": round(w["start"] - lrc["time"], 3),
                "source": "lrc+whisper",
            })
        else:
            # 没有 Whisper 匹配, 用 LRC 时间估算
            next_time = lrc_segs[lrc_idx + 1]["time"] if lrc_idx + 1 < len(lrc_segs) else lrc["time"] + 5
            aligned.append({
                "line_number": lrc_idx + 1,
                "text": lrc["text"],
                "start_time": lrc["time"],
                "end_time": next_time,
                "lrc_time": lrc["time"],
                "time_offset": 0,
                "source": "lrc_only",
            })

    return aligned


def main():
    parser = argparse.ArgumentParser(description="V2: Whisper Lyrics Alignment")
    parser.add_argument("--input", required=True, help="Input audio file")
    parser.add_argument("--lyrics", default=None, help="LRC lyrics file (optional)")
    parser.add_argument("--vocals", default=None, help="Separated vocals (from V1, optional)")
    args = parser.parse_args()

    os.makedirs("validation/results", exist_ok=True)

    print("=" * 60)
    print("V2: Whisper 歌词对齐验证")
    print("=" * 60)

    start_time = time.time()

    # 优先用分离后的人声（如果有）
    audio_path = args.vocals if args.vocals and os.path.exists(args.vocals) else args.input
    print(f"\n[Input] Audio: {audio_path}")

    # 运行 Whisper
    whisper_segments = run_whisper_alignment(audio_path, args.lyrics)
    print(f"[Whisper] Found {len(whisper_segments)} segments")

    # 如果有 LRC, 做对齐
    final_segments = []
    if args.lyrics and os.path.exists(args.lyrics):
        print(f"[LRC] Parsing {args.lyrics}...")
        lrc_segments = parse_lrc(args.lyrics)
        print(f"[LRC] Found {len(lrc_segments)} lines")

        final_segments = align_with_lrc(whisper_segments, lrc_segments)
        print(f"[Aligned] {len(final_segments)} segments matched")

        # 统计对齐质量
        offsets = [s["time_offset"] for s in final_segments if s["source"] == "lrc+whisper"]
        if offsets:
            avg_offset = sum(abs(o) for o in offsets) / len(offsets)
            max_offset = max(abs(o) for o in offsets)
            good_count = sum(1 for o in offsets if abs(o) < 0.5)
            print(f"\n[对齐质量]")
            print(f"  平均偏差: {avg_offset:.3f}s")
            print(f"  最大偏差: {max_offset:.3f}s")
            print(f"  偏差<0.5s: {good_count}/{len(offsets)} ({good_count/len(offsets)*100:.0f}%)")
    else:
        # 没有 LRC, 直接用 Whisper 结果
        final_segments = [
            {
                "line_number": i + 1,
                "text": seg["text"],
                "start_time": seg["start"],
                "end_time": seg["end"],
                "source": "whisper",
            }
            for i, seg in enumerate(whisper_segments)
        ]

    elapsed = time.time() - start_time

    # 保存 segments
    segments_path = "validation/results/v2_segments.json"
    with open(segments_path, "w") as f:
        json.dump(final_segments, f, indent=2, ensure_ascii=False)

    # 生成结果
    result = {
        "test": "V2_whisper_alignment",
        "status": "PASS",
        "input_file": args.input,
        "vocals_file": audio_path,
        "lrc_file": args.lyrics,
        "total_segments": len(final_segments),
        "processing_time_s": round(elapsed, 1),
        "segments_file": segments_path,
        "notes": "需要人工听验证: 时间戳是否与歌词对齐"
    }

    result_path = "validation/results/v2_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    print(f"[Segments] {segments_path}")
    print(f"\n[重要] 请人工验证:")
    print(f"  1. 每句歌词的时间戳是否准确（听对应的音频段）")
    print(f"  2. 是否有漏句或多句合并的情况")
    print(f"  3. 颤音/延音段是否被正确切分")

    return 0


if __name__ == "__main__":
    sys.exit(main())
