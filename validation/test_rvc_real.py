#!/usr/bin/env python3
"""
FireSing RVC 真实推理验证
测试 rvc-python 对真实训练模型的推理效果
"""

import os, sys, time, json, torch

print("=" * 60)
print("  FireSing RVC 真实推理验证")
print("=" * 60)

print(f"\n[GPU] {torch.cuda.get_device_name(0)}")
print(f"[VRAM] {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

os.makedirs("test-data/output/rvc_test", exist_ok=True)
os.makedirs("validation/results", exist_ok=True)

# ========== 1. 检查输入文件 ==========
print(f"\n{'='*60}")
print("  Step 1: 检查输入文件")
print(f"{'='*60}")

segments_dir = "test-data/output/v2_segments"
if not os.path.exists(segments_dir):
    print("  [ERROR] v2_segments 目录不存在, 先运行 run_all.py")
    sys.exit(1)

segment_files = sorted([f for f in os.listdir(segments_dir) if f.endswith(".wav")])
if not segment_files:
    print("  [ERROR] 没有找到分段文件, 先运行 run_all.py")
    sys.exit(1)

print(f"  找到 {len(segment_files)} 个分段文件")
for f in segment_files[:5]:
    size = os.path.getsize(os.path.join(segments_dir, f))
    print(f"    {f} ({size/1024:.0f}KB)")
if len(segment_files) > 5:
    print(f"    ... 还有 {len(segment_files) - 5} 个")

# ========== 2. 初始化 RVC ==========
print(f"\n{'='*60}")
print("  Step 2: 初始化 rvc-python")
print(f"{'='*60}")

t_start = time.time()
try:
    from rvc_python.infer import RVCInference
    print("  rvc-python 导入成功")

    models_dir = "test-data/models/real_voice"
    rvc = RVCInference(
        models_dir=models_dir,
        device="cuda:0",
        version="v2"
    )
    print(f"  RVC 初始化完成 ({time.time()-t_start:.1f}s)")

    # List available models
    print(f"  可用模型: {list(rvc.models.keys())}")
    if not rvc.models:
        print("  [ERROR] 没有找到可用模型")
        sys.exit(1)

except Exception as e:
    print(f"  [ERROR] RVC 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== 3. 加载模型 ==========
print(f"\n{'='*60}")
print("  Step 3: 加载音色模型")
print(f"{'='*60}")

model_name = list(rvc.models.keys())[0]
model_info = rvc.models[model_name]
print(f"  模型: {model_name}")
print(f"  PTH: {model_info['pth']}")
print(f"  Index: {model_info.get('index', 'None')}")

t_load_start = time.time()
try:
    rvc.load_model(model_info["pth"], version="v2", index_path=model_info.get("index"))
    t_load = time.time() - t_load_start
    print(f"  模型加载成功 ({t_load:.2f}s)")
    print(f"  GPU 显存使用: {torch.cuda.memory_allocated()/1024**2:.0f}MB")
except Exception as e:
    print(f"  [ERROR] 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== 4. 逐段推理 ==========
print(f"\n{'='*60}")
print("  Step 4: RVC 逐段推理")
print(f"{'='*60}")

output_dir = "test-data/output/rvc_test"
converted_files = []
inference_times = []

# 测试不同的 f0 参数
f0_methods = ["rmvpe", "harvest", "crepe"] if "crepe" in dir() else ["rmvpe", "harvest"]
# 用第一段测试不同 f0 方法
test_seg = segment_files[0]
test_seg_path = os.path.join(segments_dir, test_seg)

print(f"\n  === A. F0 方法对比 (使用 {test_seg}) ===")
for f0_method in f0_methods:
    try:
        out_path = os.path.join(output_dir, f"f0_test_{f0_method}.wav")
        rvc.set_params(f0method=f0_method, f0up_key=0, index_rate=0.5)

        t_inf = time.time()
        rvc.infer_file(test_seg_path, out_path)
        t_inf = time.time() - t_inf

        size = os.path.getsize(out_path)
        print(f"  [{f0_method}] {t_inf:.2f}s, output {size/1024:.0f}KB")
        inference_times.append({"method": f0_method, "time": t_inf, "size": size})
    except Exception as e:
        print(f"  [{f0_method}] FAILED: {e}")

# 测试不同 pitch shift
print(f"\n  === B. 音高偏移测试 (f0up_key) ===")
for key in [-5, -2, 0, 2, 5]:
    try:
        out_path = os.path.join(output_dir, f"pitch_test_key{key}.wav")
        rvc.set_params(f0method="rmvpe", f0up_key=key, index_rate=0.5)

        t_inf = time.time()
        rvc.infer_file(test_seg_path, out_path)
        t_inf = time.time() - t_inf

        size = os.path.getsize(out_path)
        print(f"  [key={key:+d}] {t_inf:.2f}s, output {size/1024:.0f}KB")
    except Exception as e:
        print(f"  [key={key:+d}] FAILED: {e}")

# 测试不同 index_rate
print(f"\n  === C. Index Rate 对比 ===")
for ir in [0.0, 0.3, 0.5, 0.7, 1.0]:
    try:
        out_path = os.path.join(output_dir, f"index_test_ir{ir:.1f}.wav")
        rvc.set_params(f0method="rmvpe", f0up_key=0, index_rate=ir)

        t_inf = time.time()
        rvc.infer_file(test_seg_path, out_path)
        t_inf = time.time() - t_inf

        size = os.path.getsize(out_path)
        print(f"  [ir={ir:.1f}] {t_inf:.2f}s, output {size/1024:.0f}KB")
    except Exception as e:
        print(f"  [ir={ir:.1f}] FAILED: {e}")

# ========== 5. 全段推理 (模拟真实使用) ==========
print(f"\n{'='*60}")
print("  Step 5: 全段推理 (模拟真实产品流程)")
print(f"{'='*60}")

rvc.set_params(f0method="rmvpe", f0up_key=0, index_rate=0.5)

t_all_start = time.time()
full_converted = []
for i, seg_file in enumerate(segment_files):
    seg_path = os.path.join(segments_dir, seg_file)
    out_path = os.path.join(output_dir, f"converted_{i:03d}.wav")

    t_seg = time.time()
    try:
        rvc.infer_file(seg_path, out_path)
        t_seg = time.time() - t_seg
        size = os.path.getsize(out_path)
        full_converted.append({"file": out_path, "time": t_seg, "size": size})
        print(f"  [{i+1}/{len(segment_files)}] {seg_file} -> {t_seg:.2f}s ({size/1024:.0f}KB)")
    except Exception as e:
        print(f"  [{i+1}/{len(segment_files)}] {seg_file} -> FAILED: {e}")

t_all = time.time() - t_all_start

# ========== 6. 混音合成 ==========
print(f"\n{'='*60}")
print("  Step 6: 混音合成")
print(f"{'='*60}")

if full_converted:
    try:
        from pydub import AudioSegment
        mixed = AudioSegment.empty()
        for cf in full_converted:
            clip = AudioSegment.from_wav(cf["file"])
            if len(clip) == 0:
                continue
            if len(mixed) > 0:
                cf_ms = min(50, len(clip) // 2, len(mixed) // 2)
                mixed = mixed.append(clip, crossfade=max(cf_ms, 0))
            else:
                mixed = clip

        mixed_path = "test-data/output/rvc_mixed_vocals.wav"
        mixed.export(mixed_path, format="wav")
        print(f"  混音输出: {mixed_path} ({len(mixed)/1000:.1f}s, {os.path.getsize(mixed_path)/1024/1024:.1f}MB)")
    except Exception as e:
        print(f"  混音失败: {e}")
        mixed_path = None
else:
    mixed_path = None

# ========== 7. 模型卸载 ==========
print(f"\n{'='*60}")
print("  Step 7: 清理")
print(f"{'='*60}")

try:
    rvc.unload_model()
    print(f"  模型已卸载")
    print(f"  GPU 显存: {torch.cuda.memory_allocated()/1024**2:.0f}MB (释放后)")
except:
    pass

# ========== 8. 结果汇总 ==========
print(f"\n{'='*60}")
print("  RVC 真实推理结果汇总")
print(f"{'='*60}")

seg_times = [cf["time"] for cf in full_converted] if full_converted else []
total_output_files = len(os.listdir(output_dir))

print(f"\n  模型加载时间: {t_load:.2f}s")
print(f"  推理段数: {len(full_converted)}/{len(segment_files)}")
if seg_times:
    print(f"  平均每段推理: {sum(seg_times)/len(seg_times):.2f}s")
    print(f"  最快: {min(seg_times):.2f}s")
    print(f"  最慢: {max(seg_times):.2f}s")
    print(f"  总推理时间: {t_all:.1f}s")
    print(f"  吞吐量: {len(full_converted)/t_all:.1f} segments/s")
print(f"  输出文件数: {total_output_files}")

# 估算 40 句 (典型 4 分钟歌曲)
if seg_times:
    avg_per_seg = sum(seg_times)/len(seg_times)
    est_40 = avg_per_seg * 40
    print(f"\n  === 估算: 40 句歌曲 ===")
    print(f"  预计推理时间: {est_40:.0f}s ({est_40/60:.1f}min)")
    print(f"  端到端 (含 Demucs 7s + LRC 3s + 混音 5s + 视频 5s): ~{est_40+20:.0f}s")

# Save results
result = {
    "test": "RVC_real_inference",
    "status": "PASS" if full_converted else "FAIL",
    "model_name": model_name,
    "model_load_time_s": round(t_load, 2),
    "total_segments": len(segment_files),
    "successful_conversions": len(full_converted),
    "total_inference_time_s": round(t_all, 1),
    "avg_per_segment_s": round(sum(seg_times)/len(seg_times), 2) if seg_times else 0,
    "min_segment_s": round(min(seg_times), 2) if seg_times else 0,
    "max_segment_s": round(max(seg_times), 2) if seg_times else 0,
    "estimated_40_lines_s": round(avg_per_seg * 40, 0) if seg_times else 0,
    "f0_tests": inference_times,
    "output_dir": output_dir,
    "mixed_output": mixed_path,
    "notes": "RVC 真实推理验证完成, 请人工听确认质量"
}

with open("validation/results/rvc_real_result.json", "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"\n  结果已保存到 validation/results/rvc_real_result.json")

print(f"\n[IMPORTANT] 下一步:")
print(f"  1. 听 f0_test_*.wav 对比不同音高提取方法")
print(f"  2. 听 pitch_test_*.wav 确认音高偏移效果")
print(f"  3. 听 converted_*.wav 确认逐段转换质量")
print(f"  4. 听 rvc_mixed_vocals.wav 确认整体效果")
