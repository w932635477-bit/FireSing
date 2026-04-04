#!/usr/bin/env python3
"""
V3: RVC 逐句音色转换验证
目标: 验证 RVC 能否对逐句人声进行音色转换, 不同音色之间自然切换

评估标准:
  - 通过: 转换后音频清晰, 音色可辨识, 无明显伪影
  - 失败: 转换后有明显金属感、机器人感、或音色崩坏

前置: V1 (人声分离) + V2 (逐句切分) 已完成

输出:
  - test-data/output/v3_converted/ — 每句转换后的音频
  - test-data/output/v3_mixed.wav — 拼接后的完整人声
  - validation/results/v3_result.json — 验证结果
"""

import argparse
import json
import os
import sys
import time


def segment_vocals(vocals_path, segments, output_dir):
    """根据 segments 时间戳切分人声文件"""
    from pydub import AudioSegment

    vocals = AudioSegment.from_wav(vocals_path)
    segments_dir = os.path.join(output_dir, "segments")
    os.makedirs(segments_dir, exist_ok=True)

    segment_files = []
    for seg in segments:
        start_ms = int(seg["start_time"] * 1000)
        end_ms = int(seg["end_time"] * 1000)
        clip = vocals[start_ms:end_ms]

        filename = f"line_{seg['line_number']:03d}.wav"
        filepath = os.path.join(segments_dir, filename)
        clip.export(filepath, format="wav")
        segment_files.append(filepath)

    return segment_files


def load_rvc_model(model_path, index_path=None):
    """加载 RVC 模型 (占位, 实际使用 RVC 推理代码)"""
    # RVC 推理代码需要从 RVC 仓库导入
    # 这里是接口定义, 实际调用时需要 RVC 环境
    return {"model_path": model_path, "index_path": index_path}


def rvc_inference(audio_path, model, output_path, f0_method="rmvpe", index_rate=0.5):
    """
    RVC 推理
    实际实现需要调用 RVC 项目的推理代码

    关键参数:
      f0_method: rmvpe (最佳歌声音高提取)
      index_rate: 0.5-0.7 (平衡源音色和模型音色)
      filter_radius: 3 (平滑音高曲线)
      protect: 0.33 (保护清辅音)
    """
    import torch

    # 检查 RVC 是否可用
    try:
        # 尝试导入 RVC 推理模块
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "RVC"))
        from infer.lib.infer_pack.models import get_vc
        from infer.modules.vc.modules import VC

        vc = VC()
        vc.get_vc(model["model_path"])
        result = vc.vc_single(
            sid=0,
            input_audio_path=audio_path,
            f0_up_key=0,
            f0_method=f0_method,
            index_file=model.get("index_path", ""),
            index_rate=index_rate,
            filter_radius=3,
            resample_sr=0,
            rms_mix_rate=0.25,
            protect=0.33,
        )

        # 保存结果
        import soundfile as sf
        sf.write(output_path, result[1], result[0])
        return True

    except ImportError:
        # RVC 未安装, 使用替代方案
        print("[WARNING] RVC not installed, using fallback (copy original)")
        import shutil
        shutil.copy2(audio_path, output_path)
        return False
    except Exception as e:
        print(f"[ERROR] RVC inference failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="V3: RVC Voice Conversion")
    parser.add_argument("--vocals", required=True, help="Separated vocals (from V1)")
    parser.add_argument("--segments", required=True, help="Segment timestamps (from V2, JSON)")
    parser.add_argument("--models-dir", required=True, help="Directory with RVC models (.pth)")
    parser.add_argument("--output-dir", default="test-data/output", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)
    converted_dir = os.path.join(args.output_dir, "v3_converted")
    os.makedirs(converted_dir, exist_ok=True)

    print("=" * 60)
    print("V3: RVC 逐句音色转换验证")
    print("=" * 60)

    # 加载 segments
    with open(args.segments, "r") as f:
        segments = json.load(f)
    print(f"\n[Segments] {len(segments)} lines")

    # 发现可用模型
    model_files = []
    for f in sorted(os.listdir(args.models_dir)):
        if f.endswith(".pth"):
            model_path = os.path.join(args.models_dir, f)
            index_path = model_path.replace(".pth", ".index")
            if not os.path.exists(index_path):
                index_path = None
            model_files.append({"name": f, "model_path": model_path, "index_path": index_path})

    if not model_files:
        print(f"[ERROR] No .pth models found in {args.models_dir}")
        print(f"  请下载 RVC 模型到该目录")
        print(f"  推荐来源: https://huggingface.co/models?search=rvc")
        sys.exit(1)

    print(f"[Models] Found {len(model_files)} voice models:")
    for m in model_files:
        print(f"  - {m['name']}")

    # Step 1: 切分人声
    print(f"\n[Step 1] Segmenting vocals...")
    segment_files = segment_vocals(args.vocals, segments, args.output_dir)
    print(f"  Created {len(segment_files)} segment files")

    # Step 2: 逐句 RVC 转换
    print(f"\n[Step 2] RVC conversion (round-robin voice assignment)...")
    import torch
    print(f"  GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

    start_time = time.time()
    converted_files = []
    conversion_times = []
    rvc_available = True

    for i, (seg_file, seg) in enumerate(zip(segment_files, segments)):
        # 轮换分配音色
        model = model_files[i % len(model_files)]
        output_file = os.path.join(converted_dir, f"converted_{seg['line_number']:03d}.wav")

        t0 = time.time()
        success = rvc_inference(
            seg_file, model, output_file,
            f0_method="rmvpe", index_rate=0.5
        )
        t1 = time.time()

        if success:
            converted_files.append(output_file)
            conversion_times.append(t1 - t0)
            print(f"  Line {seg['line_number']:3d} → {model['name']:<30s} ({t1-t0:.2f}s)")
        else:
            converted_files.append(seg_file)  # Fallback: 使用原始音频
            rvc_available = False

    elapsed = time.time() - start_time

    # Step 3: 拼接转换后的音频
    print(f"\n[Step 3] Concatenating converted segments...")
    from pydub import AudioSegment

    mixed = AudioSegment.empty()
    for cf in converted_files:
        clip = AudioSegment.from_wav(cf)
        # 添加 50ms 交叉淡化
        if len(mixed) > 0:
            mixed = mixed.append(clip, crossfade=50)
        else:
            mixed = clip

    mixed_path = os.path.join(args.output_dir, "v3_mixed_vocals.wav")
    mixed.export(mixed_path, format="wav")
    print(f"  Output: {mixed_path} ({len(mixed)/1000:.1f}s)")

    # 生成结果
    result = {
        "test": "V3_rvc_conversion",
        "status": "PASS" if rvc_available else "FALLBACK",
        "total_lines": len(segments),
        "voice_models_used": len(model_files),
        "total_conversion_time_s": round(elapsed, 1),
        "avg_per_line_s": round(sum(conversion_times) / max(len(conversion_times), 1), 2) if conversion_times else 0,
        "output_mixed_vocals": mixed_path,
        "output_converted_dir": converted_dir,
        "rvc_available": rvc_available,
        "notes": "需要人工听验证: 音色是否自然, 切换是否平滑"
    }

    result_path = "validation/results/v3_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    if not rvc_available:
        print(f"\n[WARNING] RVC inference not available, used original audio as fallback")
        print(f"  请在 AutoDL 上运行此脚本以使用 GPU 加速的 RVC 推理")
    print(f"\n[重要] 请人工听 test-data/output/v3_mixed_vocals.wav 确认:")
    print(f"  1. 每句音色是否可辨识且不同")
    print(f"  2. 音色切换处是否自然（无明显割裂）")
    print(f"  3. 转换后音质是否清晰（无金属感/机器人感）")

    return 0


if __name__ == "__main__":
    sys.exit(main())
