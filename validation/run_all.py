#!/usr/bin/env python3
"""
FireSing 一键技术验证脚本
在 AutoDL RTX 4090D 上运行
用法: python3 validation/run_all.py
"""

import json
import os
import sys
import time
import torch

print("=" * 60)
print("  FireSing 技术验证 - AutoDL RTX 4090D")
print("=" * 60)

print(f"\n[GPU] {torch.cuda.get_device_name(0)}")
print(f"[VRAM] {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
print(f"[PyTorch] {torch.__version__}")
print(f"[CUDA] {torch.version.cuda}")

os.makedirs("test-data/output", exist_ok=True)
os.makedirs("validation/results", exist_ok=True)

results = {}

# Initialize paths (will be set by V1 if successful)
vocals_path = None
instrumental_path = None

# ========== V1: Demucs 人声分离 ==========
print(f"\n{'='*60}")
print("  V1: 人声分离 (Demucs htdemucs)")
print(f"{'='*60}")

v1_start = time.time()
try:
    import torchaudio
    from demucs.pretrained import get_model
    from demucs.apply import apply_model

    # Load model
    print("[Step 1] Loading htdemucs model...")
    model = get_model('htdemucs')
    device = torch.device('cuda')
    model = model.to(device)
    model.eval()
    print(f"  Model loaded, parameters: {sum(p.numel() for p in model.parameters())/1e6:.1f}M")

    # Load audio - convert mp3 to wav via ffmpeg, then use soundfile to avoid torchcodec issues
    audio_path = "test-data/song.mp3"
    print(f"[Step 2] Loading {audio_path}...")
    import subprocess
    wav_tmp = "/tmp/firesing_input.wav"
    subprocess.run(["ffmpeg", "-y", "-i", audio_path, "-ar", "44100", "-ac", "2", wav_tmp],
                    capture_output=True, check=True)
    import soundfile as sf
    import numpy as np
    audio_np, sr = sf.read(wav_tmp, dtype='float32')
    # soundfile returns (samples, channels), we need (channels, samples)
    if audio_np.ndim == 1:
        wav = torch.from_numpy(audio_np).unsqueeze(0)
    else:
        wav = torch.from_numpy(audio_np.T)
    print(f"  Duration: {wav.shape[-1]/sr:.1f}s, Sample rate: {sr}Hz, Channels: {wav.shape[0]}")

    # Resample to 44100 if needed
    if sr != 44100:
        print(f"  Resampling {sr} -> 44100Hz...")
        wav = torchaudio.transforms.Resample(sr, 44100)(wav)
        sr = 44100

    # Convert to stereo if mono
    if wav.shape[0] == 1:
        wav = wav.repeat(2, 1)

    # Run separation
    print("[Step 3] Running vocal separation on GPU...")
    ref = wav.mean(0)
    wav_input = wav.unsqueeze(0).to(device)  # [1, 2, T]

    with torch.no_grad():
        sources = apply_model(model, wav_input, progress=True)

    # sources shape: [1, 4, 2, T] - drums, bass, other, vocals
    source_names = ['drums', 'bass', 'other', 'vocals']
    vocals_idx = source_names.index('vocals')

    vocals = sources[0, vocals_idx].cpu()
    instrumental = sources[0, :3].sum(0).cpu()  # drums + bass + other

    # Save outputs
    vocals_path = "test-data/output/v1_vocals.wav"
    instrumental_path = "test-data/output/v1_instrumental.wav"
    # Save using soundfile to avoid torchcodec issues
    import soundfile as sf
    sf.write(vocals_path, vocals.numpy().T, sr)
    sf.write(instrumental_path, instrumental.numpy().T, sr)

    v1_time = time.time() - v1_start
    print(f"\n  [OK] Vocals: {vocals_path} ({os.path.getsize(vocals_path)/1024/1024:.1f}MB)")
    print(f"  [OK] Instrumental: {instrumental_path} ({os.path.getsize(instrumental_path)/1024/1024:.1f}MB)")
    print(f"  Time: {v1_time:.1f}s")

    results["V1"] = {
        "test": "V1_vocal_separation",
        "status": "PASS",
        "tool": "demucs_htdemucs",
        "processing_time_s": round(v1_time, 1),
        "vocals_file": vocals_path,
        "instrumental_file": instrumental_path,
        "gpu_used": True,
        "notes": "人声分离完成, 需要人工听确认质量"
    }
except Exception as e:
    v1_time = time.time() - v1_start
    print(f"  [FAIL] {e}")
    results["V1"] = {"test": "V1_vocal_separation", "status": "FAIL", "error": str(e), "time_s": round(v1_time, 1)}

# ========== V2: Whisper 歌词对齐 ==========
print(f"\n{'='*60}")
print("  V2: 歌词对齐 (Whisper large-v3)")
print(f"{'='*60}")

v2_start = time.time()
try:
    import whisper

    print("[Step 1] Loading Whisper large-v3...")
    model = whisper.load_model("large-v3")
    print(f"  Model loaded")

    # Use separated vocals for better accuracy
    audio_input = vocals_path if (vocals_path and os.path.exists(vocals_path)) else "test-data/song.mp3"
    print(f"[Step 2] Transcribing {audio_input}...")

    result = model.transcribe(
        audio_input,
        language="zh",
        word_timestamps=True,
        verbose=False,
    )

    segments = []
    for seg in result["segments"]:
        segments.append({
            "line_number": len(segments) + 1,
            "text": seg["text"].strip(),
            "start_time": round(seg["start"], 3),
            "end_time": round(seg["end"], 3),
            "duration": round(seg["end"] - seg["start"], 2),
        })

    # Save segments
    segments_path = "validation/results/v2_segments.json"
    with open(segments_path, "w") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    # Cut into individual files
    print(f"[Step 3] Cutting into {len(segments)} segments...")
    from pydub import AudioSegment
    cut_audio_path = vocals_path if (vocals_path and os.path.exists(vocals_path)) else audio_input
    vocals_audio = AudioSegment.from_file(cut_audio_path)

    seg_dir = "test-data/output/v2_segments"
    os.makedirs(seg_dir, exist_ok=True)

    for seg in segments:
        start_ms = int(seg["start_time"] * 1000)
        end_ms = int(seg["end_time"] * 1000)
        clip = vocals_audio[start_ms:end_ms]
        clip.export(os.path.join(seg_dir, f"line_{seg['line_number']:03d}.wav"), format="wav")

    v2_time = time.time() - v2_start

    # Stats
    durations = [s["duration"] for s in segments]
    print(f"\n  [OK] {len(segments)} segments found")
    print(f"  Avg duration: {sum(durations)/len(durations):.2f}s")
    print(f"  Min: {min(durations):.2f}s, Max: {max(durations):.2f}s")
    print(f"  Total lyrics: {''.join(s['text'] for s in segments)}")
    print(f"  Time: {v2_time:.1f}s")

    results["V2"] = {
        "test": "V2_lyrics_alignment",
        "status": "PASS",
        "tool": "whisper_large_v3",
        "processing_time_s": round(v2_time, 1),
        "total_segments": len(segments),
        "avg_segment_duration_s": round(sum(durations)/len(durations), 2),
        "segments_file": segments_path,
        "notes": "歌词对齐完成, 需要人工确认时间戳准确性"
    }
except Exception as e:
    v2_time = time.time() - v2_start
    print(f"  [FAIL] {e}")
    results["V2"] = {"test": "V2_lyrics_alignment", "status": "FAIL", "error": str(e), "time_s": round(v2_time, 1)}

# ========== V3: RVC 音色转换 (基础验证 - 无RVC模型时用pitch shift模拟) ==========
print(f"\n{'='*60}")
print("  V3: 逐句音色转换 (验证可行性)")
print(f"{'='*60}")

v3_start = time.time()
try:
    from pydub import AudioSegment
    import numpy as np

    seg_dir = "test-data/output/v2_segments"
    converted_dir = "test-data/output/v3_converted"
    os.makedirs(converted_dir, exist_ok=True)

    segment_files = sorted([f for f in os.listdir(seg_dir) if f.endswith(".wav")])
    if not segment_files:
        raise RuntimeError(f"No segment files found in {seg_dir}. V2 must run first.")

    # Try real RVC inference via rvc-python
    real_rvc_done = False
    rvc_tool = "pitch_shift_simulation"
    rvc_models_dir = "test-data/models"

    # rvc-python expects: models_dir/model_name/model.pth
    voice_models = {}
    if os.path.exists(rvc_models_dir):
        for d in os.listdir(rvc_models_dir):
            sub = os.path.join(rvc_models_dir, d)
            if os.path.isdir(sub):
                pth_files = [f for f in os.listdir(sub) if f.endswith(".pth")]
                if pth_files:
                    voice_models[d] = os.path.join(sub, pth_files[0])

    if voice_models:
        print(f"  Found {len(voice_models)} voice model(s): {list(voice_models.keys())}")
        try:
            from rvc_python.infer import RVCInference
            print("  [Step 1] rvc-python loaded, initializing RVC on GPU...")
            rvc = RVCInference(
                models_dir=rvc_models_dir,
                device="cuda:0",
                version="v2"
            )
            print(f"  Available RVC models: {list(rvc.models.keys())}")

            if rvc.models:
                model_name = list(rvc.models.keys())[0]
                print(f"  [Step 2] Loading model: {model_name}")
                rvc.load_model(rvc.models[model_name]["pth"], version="v2")

                print(f"  [Step 3] Converting {len(segment_files)} segments with real RVC...")
                converted_files = []
                f0_keys = [-2, 0, 2, -1, 1]  # Different pitch shifts per "voice"

                for i, seg_file in enumerate(segment_files):
                    seg_path = os.path.join(seg_dir, seg_file)
                    out_path = os.path.join(converted_dir, f"converted_{i:03d}.wav")

                    f0_key = f0_keys[i % len(f0_keys)]
                    rvc.set_params(f0method="rmvpe", f0up_key=f0_key)
                    print(f"    [{i+1}/{len(segment_files)}] {seg_file} f0_key={f0_key}")
                    rvc.infer_file(seg_path, out_path)
                    converted_files.append(out_path)

                rvc.unload_model()
                real_rvc_done = True
                rvc_tool = "rvc_python_real"
                print(f"  Real RVC inference completed!")
            else:
                print(f"  [WARN] rvc-python found no loadable models")

        except ImportError:
            print("  [WARN] rvc-python not installed, falling back to simulation")
        except Exception as e:
            print(f"  [WARN] RVC inference failed: {e}")
            print(f"  Falling back to pitch-shift simulation...")

    if not real_rvc_done:
        # Fallback: pitch-shift simulation
        print(f"  Converting {len(segment_files)} segments with pitch-shift simulation...")
        converted_files = []
        pitch_shifts = [-2, 0, 2, -1, 1]

        for i, seg_file in enumerate(segment_files):
            audio = AudioSegment.from_wav(os.path.join(seg_dir, seg_file))
            shift = pitch_shifts[i % len(pitch_shifts)]

            if shift != 0:
                new_sample_rate = int(audio.frame_rate * (2 ** (shift / 12.0)))
                shifted = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
                shifted = shifted.set_frame_rate(audio.frame_rate)
            else:
                shifted = audio

            out_path = os.path.join(converted_dir, f"converted_{i:03d}.wav")
            shifted.export(out_path, format="wav")
            converted_files.append(out_path)

    # Concatenate converted segments (skip zero-length, cap crossfade)
    print(f"  Concatenating {len(converted_files)} converted segments...")
    mixed = AudioSegment.empty()
    skipped = 0
    for cf in converted_files:
        clip = AudioSegment.from_wav(cf)
        if len(clip) == 0:
            skipped += 1
            continue
        if len(mixed) > 0:
            cf_ms = min(50, len(clip) // 2, len(mixed) // 2)
            mixed = mixed.append(clip, crossfade=max(cf_ms, 0))
        else:
            mixed = clip
    if skipped:
        print(f"  Skipped {skipped} zero-length segments")

    mixed_path = "test-data/output/v3_mixed_vocals.wav"
    mixed.export(mixed_path, format="wav")

    v3_time = time.time() - v3_start
    print(f"\n  [OK] Converted {len(converted_files)} segments")
    print(f"  Tool: {rvc_tool}")
    print(f"  Output: {mixed_path} ({len(mixed)/1000:.1f}s)")
    print(f"  Time: {v3_time:.1f}s")

    results["V3"] = {
        "test": "V3_voice_conversion",
        "status": "PASS",
        "tool": rvc_tool,
        "rvc_real": real_rvc_done,
        "voice_models_found": list(voice_models.keys()) if voice_models else [],
        "processing_time_s": round(v3_time, 1),
        "total_segments": len(converted_files),
        "output_file": mixed_path,
        "notes": "音色转换完成" + (" (真实 RVC)" if real_rvc_done else " (pitch-shift 模拟)")
    }

except Exception as e:
    v3_time = time.time() - v3_start
    print(f"  [FAIL] {e}")
    results["V3"] = {"test": "V3_voice_conversion", "status": "FAIL", "error": str(e), "time_s": round(v3_time, 1)}

# ========== V4: 音色切换自然度 ==========
print(f"\n{'='*60}")
print("  V4: 音色切换自然度 (交叉淡化对比)")
print(f"{'='*60}")

v4_start = time.time()
try:
    from pydub import AudioSegment

    converted_dir = "test-data/output/v3_converted"
    if not os.path.exists(converted_dir):
        raise FileNotFoundError("V3 output not found. Run V3 first.")

    output_dir = "test-data/output/v4_crossfade"
    os.makedirs(output_dir, exist_ok=True)

    converted_files = sorted([os.path.join(converted_dir, f) for f in os.listdir(converted_dir) if f.endswith(".wav")])

    cf_list = [0, 50, 100, 200, 500]
    for cf_ms in cf_list:
        mixed = AudioSegment.empty()
        for i, cf in enumerate(converted_files):
            clip = AudioSegment.from_wav(cf)
            if len(mixed) > 0 and cf_ms > 0:
                actual_cf = min(cf_ms, len(clip) // 2, len(mixed) // 2)
                mixed = mixed.append(clip, crossfade=actual_cf)
            else:
                mixed += clip

        out_path = os.path.join(output_dir, f"crossfade_{cf_ms}ms.wav")
        mixed.export(out_path, format="wav")
        print(f"  crossfade_{cf_ms}ms.wav ({len(mixed)/1000:.1f}s)")

    v4_time = time.time() - v4_start
    print(f"\n  [OK] Generated {len(cf_list)} crossfade comparison files")
    print(f"  Time: {v4_time:.1f}s")
    print(f"  RECOMMENDATION: 100ms crossfade")

    results["V4"] = {
        "test": "V4_voice_switching",
        "status": "PASS",
        "processing_time_s": round(v4_time, 1),
        "crossfade_options_ms": cf_list,
        "recommendation": "100ms",
        "notes": "生成了 5 个对比文件, 请人工选择最自然的参数"
    }
except Exception as e:
    v4_time = time.time() - v4_start
    print(f"  [FAIL] {e}")
    results["V4"] = {"test": "V4_voice_switching", "status": "FAIL", "error": str(e), "time_s": round(v4_time, 1)}

# ========== V5: 合唱检测 ==========
print(f"\n{'='*60}")
print("  V5: 合唱检测 (自动识别结尾高潮)")
print(f"{'='*60}")

v5_start = time.time()
try:
    if "V2" not in results or results["V2"]["status"] != "PASS":
        raise RuntimeError("V2 must pass first")

    with open("validation/results/v2_segments.json") as f:
        segments = json.load(f)

    total = len(segments)
    last_30_start = int(total * 0.7)

    # Find lyric repetition (chorus pattern)
    early_texts = {}
    for i, seg in enumerate(segments[:last_30_start]):
        text = seg["text"].strip()
        if text and len(text) > 2:
            early_texts.setdefault(text, []).append(i)

    chorus_lines = []
    for i in range(last_30_start, total):
        text = segments[i]["text"].strip()
        if text in early_texts:
            chorus_lines.append(i)

    if chorus_lines:
        start = segments[chorus_lines[0]]
        end = segments[chorus_lines[-1]]
        confidence = "high" if len(chorus_lines) >= 3 else "medium"
        method = "lyric_repetition"
        print(f"  Detected chorus: lines {chorus_lines[0]+1}-{chorus_lines[-1]+1}")
        print(f"  Time: {start['start_time']:.1f}s - {end['end_time']:.1f}s ({end['end_time']-start['start_time']:.1f}s)")
        print(f"  Repeated lines: {len(chorus_lines)}")
        print(f"  Confidence: {confidence}")
    else:
        # Fallback: last 30s
        last_seg = segments[-1]
        target_start = max(0, last_seg["end_time"] - 30)
        chorus_lines = [i for i, s in enumerate(segments) if s["start_time"] >= target_start]
        start = segments[chorus_lines[0]]
        end = segments[chorus_lines[-1]]
        confidence = "low"
        method = "last_30s_fallback"
        print(f"  Fallback: last 30s, lines {chorus_lines[0]+1}-{chorus_lines[-1]+1}")

    v5_time = time.time() - v5_start
    print(f"  Method: {method}")
    print(f"  Time: {v5_time:.1f}s")

    results["V5"] = {
        "test": "V5_chorus_detection",
        "status": "PASS",
        "processing_time_s": round(v5_time, 1),
        "chorus": {
            "start_line": chorus_lines[0] + 1,
            "end_line": chorus_lines[-1] + 1,
            "start_time": start["start_time"],
            "end_time": end["end_time"],
            "line_count": len(chorus_lines),
            "confidence": confidence,
            "method": method,
        },
        "notes": "需要人工确认检测的高潮段落是否正确"
    }
except Exception as e:
    v5_time = time.time() - v5_start
    print(f"  [FAIL] {e}")
    results["V5"] = {"test": "V5_chorus_detection", "status": "FAIL", "error": str(e), "time_s": round(v5_time, 1)}

# ========== V6: 独白处理 ==========
print(f"\n{'='*60}")
print("  V6: 独白处理 (TTS + 插入)")
print(f"{'='*60}")

v6_start = time.time()
try:
    # Generate TTS monologue
    print("[Step 1] Generating TTS monologue...")
    import subprocess
    monologue_path = "test-data/output/v6_monologue.mp3"
    tts_result = subprocess.run(
        ["edge-tts", "--voice", "zh-CN-YunxiNeural", "--text",
         "大家好，我是一位火锅店老板，很高兴能和大家一起完成这首歌。欢迎大家来我的火锅店坐坐！",
         "--write-media", monologue_path],
        capture_output=True, text=True, timeout=30
    )

    if tts_result.returncode == 0:
        print(f"  TTS generated: {monologue_path}")
        tts_ok = True
    else:
        print(f"  TTS failed: {tts_result.stderr[:100]}")
        tts_ok = False

    # Insert into song
    if tts_ok and os.path.exists(vocals_path):
        from pydub import AudioSegment

        print("[Step 2] Inserting monologue at beginning...")
        song = AudioSegment.from_wav(instrumental_path)
        monologue = AudioSegment.from_file(monologue_path)
        monologue = monologue.set_frame_rate(44100).set_channels(2)

        # Add monologue at beginning with background music
        bg = song[:len(monologue)] - 12  # Lower volume during monologue
        monologue_with_bg = monologue.overlay(bg)

        result_audio = monologue_with_bg + AudioSegment.silent(duration=1500) + song[len(monologue):]

        beginning_path = "test-data/output/v6_with_monologue_beginning.wav"
        result_audio.export(beginning_path, format="wav")

        print(f"  Output: {beginning_path} ({len(result_audio)/1000:.1f}s)")
        print(f"  Monologue duration: {len(monologue)/1000:.1f}s")

        v6_time = time.time() - v6_start
        results["V6"] = {
            "test": "V6_monologue",
            "status": "PASS",
            "tts_available": True,
            "tts_voice": "zh-CN-YunxiNeural",
            "processing_time_s": round(v6_time, 1),
            "monologue_duration_s": len(monologue) / 1000,
            "output_file": beginning_path,
            "notes": "独白已插入开头, 需要人工确认过渡平滑"
        }
    elif not tts_ok:
        v6_time = time.time() - v6_start
        results["V6"] = {"test": "V6_monologue", "status": "SKIP", "error": "TTS not available", "time_s": round(v6_time, 1)}
    else:
        v6_time = time.time() - v6_start
        results["V6"] = {"test": "V6_monologue", "status": "SKIP", "error": "No vocals file", "time_s": round(v6_time, 1)}

except Exception as e:
    v6_time = time.time() - v6_start
    print(f"  [FAIL] {e}")
    results["V6"] = {"test": "V6_monologue", "status": "FAIL", "error": str(e), "time_s": round(v6_time, 1)}

# ========== V7: 视频生成 ==========
print(f"\n{'='*60}")
print("  V7: 视频生成 (FFmpeg + ASS字幕)")
print(f"{'='*60}")

v7_start = time.time()
try:
    # Generate ASS subtitles from segments
    print("[Step 1] Generating ASS subtitles...")
    colors = ["&H00FFFFFF", "&H0000FFFF", "&H00FF00FF", "&H00FF6600", "&H0000FF00"]

    ass_content = f"""[Script Info]
Title: FireSing Test
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,48,{colors[0]},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,30,30,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    with open("validation/results/v2_segments.json") as f:
        segments = json.load(f)

    for i, seg in enumerate(segments):
        color = colors[i % len(colors)]
        start_h = int(seg["start_time"] // 3600)
        start_m = int((seg["start_time"] % 3600) // 60)
        start_s = int(seg["start_time"] % 60)
        start_cs = int((seg["start_time"] % 1) * 100)
        end_h = int(seg["end_time"] // 3600)
        end_m = int((seg["end_time"] % 3600) // 60)
        end_s = int(seg["end_time"] % 60)
        end_cs = int((seg["end_time"] % 1) * 100)

        ass_content += f'Dialogue: 0,{start_h}:{start_m:02d}:{start_s:02d}.{start_cs:02d},{end_h}:{end_m:02d}:{end_s:02d}.{end_cs:02d},Default,,0,0,80,,{seg["text"]}\n'

    ass_path = "test-data/output/v7_subtitles.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    print(f"  ASS file: {ass_path}")

    # Generate video
    print("[Step 2] Generating video with FFmpeg...")
    audio_input = "test-data/output/v3_mixed_vocals.wav" if os.path.exists("test-data/output/v3_mixed_vocals.wav") else "test-data/song.mp3"

    # Get duration
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_input],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip()) if probe.stdout.strip() else "180"

    video_path = "test-data/output/v7_video.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_input,
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}:r=30",
        "-vf", f"ass={ass_path}",
        "-c:v", "libopenh264",
        "-c:a", "aac",
        "-shortest",
        video_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode == 0 and os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / 1024 / 1024
        v7_time = time.time() - v7_start
        print(f"  Output: {video_path} ({size_mb:.1f}MB)")
        print(f"  Time: {v7_time:.1f}s")

        results["V7"] = {
            "test": "V7_video_generation",
            "status": "PASS",
            "processing_time_s": round(v7_time, 1),
            "output_file": video_path,
            "video_size_mb": round(size_mb, 1),
            "resolution": "1080x1920",
            "codec": "h264+aac",
            "notes": "视频+字幕生成成功, 请人工确认播放效果"
        }
    else:
        print(f"  FFmpeg error: {result.stderr[-200:]}")
        results["V7"] = {"test": "V7_video_generation", "status": "FAIL", "error": result.stderr[-200:]}

except Exception as e:
    v7_time = time.time() - v7_start
    print(f"  [FAIL] {e}")
    results["V7"] = {"test": "V7_video_generation", "status": "FAIL", "error": str(e), "time_s": round(v7_time, 1)}

# ========== 保存所有结果 ==========
print(f"\n{'='*60}")
print("  验证总结")
print(f"{'='*60}")

total_time = sum(r.get("processing_time_s", r.get("time_s", 0)) for r in results.values())
pass_count = sum(1 for r in results.values() if r["status"] == "PASS")
fail_count = sum(1 for r in results.values() if r["status"] == "FAIL")

for key, r in results.items():
    status = r["status"]
    time_s = r.get("processing_time_s", r.get("time_s", "?"))
    print(f"  [{status}] {key}: {time_s}s - {r.get('notes', r.get('error', ''))}")

print(f"\n  Total time: {total_time:.1f}s")
print(f"  PASS: {pass_count}, FAIL: {fail_count}")

# Save all results
for key, r in results.items():
    path = f"validation/results/{key.lower()}_result.json"
    with open(path, "w") as f:
        json.dump(r, f, indent=2, ensure_ascii=False)

print(f"\n  Results saved to validation/results/")

print(f"\n[IMPORTANT] 下一步:")
print(f"  1. 下载所有 output 文件到本地验证")
print(f"  2. 人工听 v1_vocals.wav 确认人声分离质量")
print(f"  3. 人工听 v3_mixed_vocals.wav 确认音色切换自然度")
print(f"  4. 人工看 v7_video.mp4 确认视频+字幕效果")
print(f"  5. 下载 RVC 模型到 test-data/models/ 后重跑真实音色转换")
