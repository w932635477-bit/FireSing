# FireSing 技术验证方案

## 验证环境

| 组件 | 规格 |
|------|------|
| GPU 服务器 | AutoDL RTX 4090D (24GB VRAM) |
| 本地开发 | MacBook Pro M5 (32GB) |

## 验证清单

| # | 验证项 | 关键问题 | 风险等级 | 状态 |
|---|--------|----------|----------|------|
| V1 | UVR5 人声分离 | 中文流行歌人声分离质量是否达标？ | 低 | PENDING |
| V2 | Whisper 歌词对齐 | 能否准确获得逐句时间戳？ | 中 | PENDING |
| V3 | RVC 逐句音色转换 | 不同音色逐句切换是否自然？ | 中 | PENDING |
| V4 | 音色切换自然度 | 句间切换是否有明显割裂感？ | 高 | PENDING |
| V5 | 合唱检测与合成 | 能否自动识别结尾高潮并合成多音色合唱？ | 高 | PENDING |
| V6 | 独白处理 | 录音/TTS 插入歌曲是否平滑？ | 低 | PENDING |
| V7 | 视频生成 | FFmpeg 能否生成抖音风格竖版视频+字幕？ | 低 | PENDING |
| V8 | 端到端管线 | 完整流程耗时和质量是否达标？ | 中 | PENDING |

## 验证方法

每个验证项包含：
1. **安装脚本** — 在 AutoDL 上安装所需依赖
2. **测试脚本** — 用测试音频运行验证
3. **评估标准** — 客观指标 + 主观评分

## 测试音频

需要准备：
- 一首中文流行歌曲（如《珊瑚海》），mp3 格式，3-5 分钟
- 对应的 LRC 歌词文件
- 3-5 个 RVC 预训练音色模型（.pth + .index）

## 使用方法

```bash
# 1. 在 AutoDL 上克隆项目
cd /root
git clone <repo> && cd FireSing

# 2. 运行环境安装
bash validation/setup_env.sh

# 3. 逐个运行验证
python validation/v1_uvr5_separation.py --input test-data/song.mp3
python validation/v2_whisper_alignment.py --input test-data/song.mp3 --lyrics test-data/lyrics.lrc
python validation/v3_rvc_conversion.py --input test-data/song.mp3 --models test-data/models/
python validation/v4_voice_switching.py
python validation/v5_chorus_detection.py --input test-data/song.mp3
python validation/v6_monologue.py --input test-data/song.mp3
python validation/v7_video_generation.py --input test-data/song.mp3 --lyrics test-data/lyrics.lrc
python validation/v8_e2e_pipeline.py --input test-data/song.mp3 --lyrics test-data/lyrics.lrc --models test-data/models/

# 4. 生成验证报告
python validation/generate_report.py
```
