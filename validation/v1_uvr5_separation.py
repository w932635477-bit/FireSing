#!/usr/bin/env python3
"""
V1: UVR5 人声分离验证
目标: 验证 UVR5 (MDX-Net) 能否干净地分离中文流行歌曲的人声和伴奏

评估标准:
  - 通过: 人声中无明显伴奏残留, 伴奏中无明显人声残留
  - 失败: 人声中有明显鼓点/贝斯残留, 或伴奏中能听到人声

输出:
  - test-data/output/v1_vocals.wav — 分离后的人声
  - test-data/output/v1_instrumental.wav — 分离后的伴奏
  - validation/results/v1_result.json — 验证结果
"""

import argparse
import json
import os
import sys
import time
import torch

def main():
    parser = argparse.ArgumentParser(description="V1: UVR5 Vocal Separation")
    parser.add_argument("--input", required=True, help="Input audio file (mp3/wav)")
    parser.add_argument("--output-dir", default="test-data/output", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("validation/results", exist_ok=True)

    print("=" * 60)
    print("V1: UVR5 人声分离验证")
    print("=" * 60)

    # 检查 GPU
    print(f"\n[GPU] CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[GPU] Device: {torch.cuda.get_device_name(0)}")
        print(f"[GPU] VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")

    # 检查输入
    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)

    file_size_mb = os.path.getsize(args.input) / 1024 / 1024
    print(f"\n[Input] {args.input} ({file_size_mb:.1f} MB)")

    # 运行 UVR5 分离
    print("\n[Step 1] Running UVR5 separation...")
    start_time = time.time()

    try:
        from audio_separator import Separator

        sep = Separator(
            model_name="UVR-MDX-NET-Inst_HQ_4",  # MDX-Net 高质量模型
            output_dir=args.output_dir,
            output_format="WAV",
        )

        # 分离
        primary_stem, secondary_stem = sep.separate(args.input)

        elapsed = time.time() - start_time
        print(f"[OK] Separation complete in {elapsed:.1f}s")

        # 检查输出
        vocals_path = os.path.join(args.output_dir, primary_stem)
        instrumental_path = os.path.join(args.output_dir, secondary_stem)

        result = {
            "test": "V1_uvr5_separation",
            "status": "PASS",
            "input_file": args.input,
            "input_size_mb": round(file_size_mb, 1),
            "output_vocals": vocals_path,
            "output_instrumental": instrumental_path,
            "processing_time_s": round(elapsed, 1),
            "gpu_used": torch.cuda.is_available(),
            "notes": "自动验证通过。需要人工听分离结果确认质量。"
        }

    except Exception as e:
        elapsed = time.time() - start_time
        result = {
            "test": "V1_uvr5_separation",
            "status": "FAIL",
            "error": str(e),
            "processing_time_s": round(elapsed, 1),
        }
        print(f"[FAIL] {e}")

    # 保存结果
    result_path = "validation/results/v1_result.json"
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[Result] {result['status']}")
    print(f"[Output] {result_path}")
    print(f"\n[重要] 请人工听 test-data/output/v1_vocals.wav 确认:")
    print(f"  1. 人声中是否有伴奏残留 (鼓点、贝斯)")
    print(f"  2. 伴奏中是否有人声残留")
    print(f"  3. 人声音质是否清晰 (无失真、无金属感)")

    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
