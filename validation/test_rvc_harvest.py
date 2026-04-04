#!/usr/bin/env python3
"""RVC Real Inference - Harvest Method"""
import os, sys, time, json, torch

print("=" * 60)
print("  RVC Real Inference - Harvest Method")
print("=" * 60)
print(f"\n[GPU] {torch.cuda.get_device_name(0)}")
print(f"[VRAM] {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

os.makedirs("test-data/output/rvc_harvest", exist_ok=True)

# Init RVC
from rvc_python.infer import RVCInference
t0 = time.time()
rvc = RVCInference(
    models_dir="test-data/models/real_voice",
    device="cuda:0",
    version="v2"
)
print(f"RVC init: {time.time()-t0:.1f}s")
print(f"Available models: {list(rvc.models.keys())}")

# Load model
model_name = list(rvc.models.keys())[0]
rvc.load_model(rvc.models[model_name]["pth"], version="v2")
print(f"Model {model_name} loaded")

# Set params: harvest instead of rmvpe
rvc.set_params(f0method="harvest", f0up_key=0, index_rate=0.5, filter_radius=3)
print("Using harvest f0 method (rmvpe model file incompatible)")

# Process segments
seg_dir = "test-data/output/v2_segments"
seg_files = sorted([f for f in os.listdir(seg_dir) if f.endswith(".wav")])
print(f"\nProcessing {len(seg_files)} segments...")

results = []
total_inference_time = 0
for i, seg_file in enumerate(seg_files):
    seg_path = os.path.join(seg_dir, seg_file)
    out_path = f"test-data/output/rvc_harvest/converted_{i:03d}.wav"
    t_start = time.time()
    try:
        rvc.infer_file(seg_path, out_path)
        t_infer = time.time() - t_start
        size_kb = os.path.getsize(out_path) / 1024
        print(f"  [{i+1}/{len(seg_files)}] {seg_file} -> {t_infer:.2f}s ({size_kb:.0f}KB) OK")
        results.append({"file": seg_file, "time_s": round(t_infer, 2), "size_kb": round(size_kb), "status": "success"})
        total_inference_time += t_infer
    except Exception as e:
        print(f"  [{i+1}/{len(seg_files)}] {seg_file} -> FAIL: {e}")
        results.append({"file": seg_file, "status": "failed", "error": str(e)})

rvc.unload_model()

# Summary
success_count = sum(1 for r in results if r.get("status") == "success")
fail_count = sum(1 for r in results if r.get("status") == "failed")
print()
print("=" * 60)
print("  RVC REAL INFERENCE RESULTS")
print("=" * 60)
print(f"  Model: {model_name}")
print(f"  F0 method: harvest")
print(f"  Total segments: {len(seg_files)}")
print(f"  Successful: {success_count}")
print(f"  Failed: {fail_count}")
print(f"  Total inference time: {total_inference_time:.2f}s")
if success_count > 0:
    avg = total_inference_time / success_count
    print(f"  Avg per segment: {avg:.2f}s")

# Save
result_data = {
    "test": "rvc_real_inference",
    "status": "PASS" if success_count > 0 else "FAIL",
    "model": model_name,
    "f0_method": "harvest",
    "total_inference_time_s": round(total_inference_time, 2),
    "success_count": success_count,
    "fail_count": fail_count,
    "segments": results,
}
with open("validation/results/rvc_real_result.json", "w") as f:
    json.dump(result_data, f, indent=2, ensure_ascii=False)
print("  Results saved to validation/results/rvc_real_result.json")
