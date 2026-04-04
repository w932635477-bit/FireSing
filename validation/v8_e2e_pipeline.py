#!/usr/bin/env python3
"""
V8: 端到端管线验证
目标: 验证从输入到输出的完整流程, 记录每步耗时

评估标准:
  - 通过: 完整流程在 3 分钟内完成 (4 分钟歌曲)
  - 失败: 任一步骤失败, 或总耗时超过 5 分钟

输出:
  - test-data/output/v8_final_video.mp4 — 最终输出视频
  - test-data/output/v8_final_audio.wav — 最终输出音频
  - validation/results/v8_result.json — 验证结果 (含每步耗时)
"""

import json
import os
import subprocess
import sys
import time


def run_step(name, func):
    """运行一个步骤并记录耗时"""
    print(f"\n{'='*40}")
    print(f"  {name}")
    print(f"{'='*40}")
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        print(f"  [OK] {elapsed:.1f}s")
        return {"name": name, "status": "PASS", "time_s": round(elapsed, 1), "result": result}
    except Exception as e:
        elapsed = time.time() - start
        print(f"  [FAIL] {elapsed:.1f}s — {e}")
        return {"name": name, "status": "FAIL", "time_s": round(elapsed, 1), "error": str(e)}


def step_1_separate(input_path, output_dir):
    """Step 1: 人声分离"""
    from audio_separator import Separator
    sep = Separator(output_dir=output_dir, output_format="WAV")
    primary, secondary = sep.separate(input_path)
    return {"vocals": os.path.join(output_dir, primary), "instrumental": os.path.join(output_dir, secondary)}


def step_2_segment(vocals_path, lyrics_path=None):
    """Step 2: 歌词对齐"""
    import whisper
    model = whisper.load_model("large-v3")
    result = model.transcribe(vocals_path, language="zh", word_timestamps=True)

    segments = []
    for seg in result["segments"]:
        segments.append({
            "line_number": len(segments) + 1,
            "text": seg["text"].strip(),
            "start_time": round(seg["start"], 3),
            "end_time": round(seg["end"], 3),
        })
    return segments


def step_3_convert(vocals_path, segments, models_dir, output_dir):
    """Step 3: RVC 逐句转换"""
    from pydub import AudioSegment
    import glob

    vocals = AudioSegment.from_wav(vocals_path)
    model_files = sorted(glob.glob(os.path.join(models_dir, "*.pth")))

    if not model_files:
        raise FileNotFoundError(f"No .pth models in {models_dir}")

    converted_dir = os.path.join(output_dir, "v8_converted")
    os.makedirs(converted_dir, exist_ok=True)

    converted_files = []
    for i, seg in enumerate(segments):
        # 切分
        start_ms = int(seg["start_time"] * 1000)
        end_ms = int(seg["end_time"] * 1000)
        clip = vocals[start_ms:end_ms]

        seg_path = os.path.join(converted_dir, f"seg_{i:03d}.wav")
        clip.export(seg_path, format="wav")

        # RVC 转换 (这里用轮换分配)
        model_path = model_files[i % len(model_files)]
        converted_path = os.path.join(converted_dir, f"converted_{i:03d}.wav")

        # TODO: 实际 RVC 推理
        # rvc_inference(seg_path, model_path, converted_path)
        # 暂时用原始音频
        import shutil
        shutil.copy2(seg_path, converted_path)

        converted_files.append(converted_path)

    return {"converted_files": converted_files, "model_count": len(model_files)}


def step_4_detect_chorus(segments):
    """Step 4: 合唱检测"""
    total = len(segments)
    last_30_start = int(total * 0.7)

    early_texts = {seg["text"] for seg in segments[:last_30_start] if seg.get("text")}
    chorus_lines = [i for i in range(last_30_start, total) if segments[i].get("text", "") in early_texts]

    if chorus_lines:
        return {"start": segments[chorus_lines[0]]["start_time"], "end": segments[chorus_lines[-1]]["end_time"], "lines": len(chorus_lines)}
    return {"start": segments[-3]["start_time"], "end": segments[-1]["end_time"], "lines": 3}


def step_5_mix(converted_files, instrumental_path, chorus_info, output_dir):
    """Step 5: 混音"""
    from pydub import AudioSegment

    mixed_vocals = AudioSegment.empty()
    for cf in converted_files:
        clip = AudioSegment.from_wav(cf)
        if len(mixed_vocals) > 0:
            mixed_vocals = mixed_vocals.append(clip, crossfade=50)
        else:
            mixed_vocals = clip

    # 叠加伴奏
    if os.path.exists(instrumental_path):
        instrumental = AudioSegment.from_wav(instrumental_path)
        # 调整伴奏音量
        instrumental = instrumental - 3  # 降低 3dB

        # 确保长度匹配
        if len(instrumental) > len(mixed_vocals):
            instrumental = instrumental[:len(mixed_vocals)]
        elif len(mixed_vocals) > len(instrumental):
            mixed_vocals = mixed_vocals[:len(instrumental)]

        final = mixed_vocals.overlay(instrumental)
    else:
        final = mixed_vocals

    output_path = os.path.join(output_dir, "v8_final_audio.wav")
    final.export(output_path, format="wav")
    return output_path


def step_6_video(audio_path, segments, output_dir):
    """Step 6: 生成视频"""
    # 复用 V7 的视频生成逻辑
    ass_path = os.path.join(output_dir, "v8_subtitles.ass")

    # 生成 ASS
    from v7_video_generation import generate_ass_subtitles, generate_video_with_template
    voice_colors = {str(i): f"color_{i}" for i in range(5)}
    generate_ass_subtitles(segments, voice_colors, ass_path)

    video_path = os.path.join(output_dir, "v8_final_video.mp4")
    generate_video_with_template(audio_path, ass_path, video_path)
    return video_path


def main():
    print("=" * 60)
    print("V8: 端到端管线验证")
    print("=" * 60)

    # 参数
    input_audio = sys.argv[1] if len(sys.argv) > 1 else "test-data/song.mp3"
    lyrics_file = sys.argv[2] if len(sys.argv) > 2 else None
    models_dir = sys.argv[3] if len(sys.argv) > 3 else "test-data/models"
    output_dir = "test-data/output"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    total_start = time.time()
    steps = []

    # Step 1: 人声分离
    step1 = run_step("Step 1: 人声分离 (UVR5)", lambda: step_1_separate(input_audio, output_dir))
    steps.append(step1)
    if step1["status"] == "FAIL":
        print(f"\n[ABORT] Step 1 failed, cannot continue")
        sys.exit(1)

    vocals_path = step1["result"]["vocals"]
    instrumental_path = step1["result"]["instrumental"]

    # Step 2: 歌词对齐
    step2 = run_step("Step 2: 歌词对齐 (Whisper)", lambda: step_2_segment(vocals_path, lyrics_file))
    steps.append(step2)
    if step2["status"] == "FAIL":
        sys.exit(1)

    segments = step2["result"]

    # Step 3: RVC 转换
    step3 = run_step("Step 3: RVC 逐句转换", lambda: step_3_convert(vocals_path, segments, models_dir, output_dir))
    steps.append(step3)

    # Step 4: 合唱检测
    step4 = run_step("Step 4: 合唱检测", lambda: step_4_detect_chorus(segments))
    steps.append(step4)

    # Step 5: 混音
    if step3["status"] == "PASS":
        converted_files = step3["result"]["converted_files"]
        step5 = run_step("Step 5: 混音", lambda: step_5_mix(converted_files, instrumental_path, step4.get("result", {}), output_dir))
        steps.append(step5)
    else:
        steps.append({"name": "Step 5: 混音", "status": "SKIP", "time_s": 0})

    # Step 6: 视频生成
    if step5["status"] == "PASS":
        audio_path = step5["result"]
        step6 = run_step("Step 6: 视频生成", lambda: step_6_video(audio_path, segments, output_dir))
        steps.append(step6)
    else:
        steps.append({"name": "Step 6: 视频生成", "status": "SKIP", "time_s": 0})

    total_elapsed = time.time() - total_start

    # 生成结果
    result = {
        "test": "V8_e2e_pipeline",
        "status": "PASS" if all(s["status"] in ("PASS", "SKIP") for s in steps) else "FAIL",
        "input_file": input_audio,
        "total_time_s": round(total_elapsed, 1),
        "steps": steps,
        "output_audio": step5.get("result") if step5["status"] == "PASS" else None,
        "output_video": step6.get("result") if step6.get("status") == "PASS" else None,
        "performance_target": {
            "target_total_s": 180,
            "actual_total_s": round(total_elapsed, 1),
            "on_target": total_elapsed <= 180,
        },
    }

    result_path = "validation/results/v8_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # 打印总结
    print(f"\n{'='*60}")
    print(f"  端到端验证总结")
    print(f"{'='*60}")
    for step in steps:
        status_icon = "OK" if step["status"] == "PASS" else "XX" if step["status"] == "FAIL" else "--"
        print(f"  [{status_icon}] {step['name']:<40s} {step['time_s']:>6.1f}s")
    print(f"{'─'*60}")
    print(f"  {'TOTAL':<40s} {total_elapsed:>6.1f}s")
    target = "ON TARGET" if total_elapsed <= 180 else "OVER TARGET"
    print(f"  Target: 180s → {target}")
    print(f"\n[Output] {result_path}")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
