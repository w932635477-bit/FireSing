# FireSing Technical Architecture

Generated: 2026-04-04
Updated: 2026-04-04 (基于两轮技术验证结果)
Status: DRAFT v2
Based on: DESIGN.md v4 (APPROVED) + 两轮 AutoDL RTX 4090D 验证

## v2 更新记录

基于两轮技术验证 (7/7 PASS, 43.7s 端到端) 的更新:

1. **人声分离: UVR5 → Demucs htdemucs** — UVR5 未验证, Demucs 两轮稳定通过 (6.8s)
2. **歌词对齐: Whisper 优先 → LRC 优先** — Whisper 中文准确度极差且非确定性, LRC 作为主方案
3. **架构精简: Celery + Redis → FastAPI BackgroundTasks** — MVP 单 GPU 不需要分布式任务队列
4. **独白 TTS: CosyVoice → edge-tts** — edge-tts 验证通过 (1.8s), CosyVoice 未验证
5. **性能数字: 用实测数据替代估计** — 所有数字来自 AutoDL RTX 4090D 实测

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User (Browser)                           │
│                   Next.js Web App                            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Song     │  │ Voice    │  │ Process  │  │ Output   │   │
│  │ Upload   │  │ Manager  │  │ Pipeline │  │ Download │   │
│  │ API      │  │ API      │  │ API      │  │ API      │   │
│  └──────────┘  └──────────┘  └─────┬────┘  └──────────┘   │
│                                    │                         │
│  ┌─────────────────────────────────▼───────────────────┐    │
│  │         Background Tasks (FastAPI native)            │    │
│  │                                                     │    │
│  │  Task flow (sequential, single GPU):                │    │
│  │  1. Demucs vocal separation                        │    │
│  │  2. LRC parse + segment cut (or Whisper fallback)   │    │
│  │  3. RVC per-line voice conversion                   │    │
│  │  4. Chorus detection + mixing                       │    │
│  │  5. Monologue insertion                             │    │
│  │  6. Video generation (FFmpeg)                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                 │
│  │ SQLite   │  │ File     │                                 │
│  │ Metadata │  │ Storage  │                                 │
│  └──────────┘  └──────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

### Why FastAPI + BackgroundTasks (not Celery + Redis)

- MVP 阶段只有 1 个 GPU, 并发 = 1。不需要分布式任务调度。
- FastAPI BackgroundTasks 够用: 任务状态存 SQLite, 前端轮询。
- Redis 是 Celery 的依赖, 砍 Celery 就不需要 Redis。
- 以后多 GPU 扩展时, 加 Celery 是一个下午的事。
- 验证脚本 `run_all.py` 就是串行调用, 600 行跑通全链路。MVP 不需要更复杂。

### Why Demucs (not UVR5)

- Demucs htdemucs: 6.8s, 两轮稳定, 42M 参数, pip install 一步搞定
- UVR5: 未验证, 安装更复杂 (需要 Ultimate Vocal Remover GUI 或特定 CLI wrapper)
- 如果后期用户反馈质量不够, 可以引入 UVR5 做对比测试
- 人声分离是模型选择, 不是架构选择, 随时可以换

## Technology Stack

| Component | Technology | Why | 验证状态 |
|-----------|-----------|-----|---------|
| Backend API | FastAPI | Async Python, native ML integration | 未验证 |
| Background Tasks | FastAPI BackgroundTasks | MVP 单 GPU 够用 | 未验证 |
| Database | SQLite | MVP simplicity | 未验证 |
| File Storage | Local filesystem | MVP simplicity | 未验证 |
| Frontend | Next.js 14+ | React SSR, good DX | 未验证 |
| UI Framework | Tailwind CSS | Rapid UI development | 未验证 |
| Vocal Separation | Demucs htdemucs | **已验证**: 6.8s, 稳定 | **PASS** |
| Lyrics (primary) | LRC parser | 用户上传精确时间戳 | 未验证 |
| Lyrics (fallback) | Whisper large-v3 | **已验证**: 29-54s, 中文准确度极差 | **PASS (但不可靠)** |
| Voice Conversion | RVC v2 via rvc-python | MIT open source | Pipeline 已通, 推理未验证 |
| Audio Processing | pydub + soundfile | 切分, 拼接, 混音 | **已验证** |
| Video Synthesis | FFmpeg + ASS | 9:16 vertical + subtitles | **已验证**: 4.3s |
| Monologue TTS | edge-tts | **已验证**: 1.8s, 免费, 零配置 | **PASS** |

## Data Model

```sql
-- Songs table
CREATE TABLE songs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    original_audio_path TEXT NOT NULL,
    lrc_path TEXT,                    -- 用户上传的 LRC 歌词文件
    vocals_path TEXT,                 -- Demucs 分离后的人声
    instrumental_path TEXT,           -- Demucs 分离后的伴奏
    status TEXT DEFAULT 'uploaded',   -- uploaded/separating/segmented/
                                      -- assigning/processing/done/error
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Lyrics segments (one row per line)
CREATE TABLE segments (
    id TEXT PRIMARY KEY,
    song_id TEXT NOT NULL REFERENCES songs(id),
    line_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,         -- 秒
    end_time REAL NOT NULL,
    vocal_path TEXT,                  -- 切分后的人声片段
    voice_model_id TEXT,              -- 分配的音色模型
    converted_vocal_path TEXT,        -- RVC 输出
    FOREIGN KEY (song_id) REFERENCES songs(id)
);

-- Voice models
CREATE TABLE voice_models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    model_path TEXT NOT NULL,         -- .pth 文件路径
    index_path TEXT,                  -- .index 文件 (可选)
    is_preset BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Outputs
CREATE TABLE outputs (
    id TEXT PRIMARY KEY,
    song_id TEXT NOT NULL REFERENCES songs(id),
    format TEXT NOT NULL,             -- 'video'/'audio'/'video_subtitled'
    file_path TEXT NOT NULL,
    file_size INTEGER,
    duration REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

4 张表 (砍掉了 monologues 和 jobs 表, 简化 MVP):
- Monologue 信息存 songs 表 (加 monologue_text, monologue_audio_path 字段)
- Job 状态用 songs.status 字段 + SQLite 就够了, 不需要单独的 jobs 表

## API Specification

### Song Management

```
POST   /api/songs
  Body: multipart form (audio file + LRC file)
  Response: { song_id, title, status: "uploaded" }

GET    /api/songs/{id}
  Response: { song_id, title, status, segments: [...], outputs: [...] }

GET    /api/songs
  Response: { songs: [...] }

DELETE /api/songs/{id}
  Response: { deleted: true }
```

### Processing Pipeline

```
POST   /api/songs/{id}/process
  触发完整处理管线: 人声分离 → 歌词切分 → 音色转换 → 混音 → 视频
  Body: { voice_pool: ["id1", "id2", ...], strategy: "round-robin"|"random" }
  Response: { status: "processing" }

GET    /api/songs/{id}/segments
  Response: { segments: [
    { line_number, text, start_time, end_time, voice_model_id? }
  ] }

PUT    /api/songs/{id}/voices
  Body: { assignments: [
    { line_number: 1, voice_model_id: "xxx" },
    { line_number: 2, voice_model_id: "yyy" }
  ] }
```

### Voice Models

```
GET    /api/voices
  Response: { voices: [{ id, name, is_preset }] }

POST   /api/voices
  Body: multipart form (.pth + .index files)
  Response: { voice_id, status: "ready" }
```

### Output

```
GET    /api/songs/{id}/outputs
  Response: { outputs: [{ id, format, file_url, file_size, duration }] }

GET    /api/songs/{id}/outputs/{oid}/download
  Response: File download
```

API 端点从 18+ 精简到 **~8 个**。MVP 核心路径: upload → process → download。

## Processing Pipeline Detail

### Step 1: Vocal Separation (Demucs)

```
Input:  original song (mp3/wav)
Output: vocals.wav, instrumental.wav
Tool:   Demucs htdemucs
Time:   ~7s (RTX 4090D 实测, 114s 歌曲)

Parameters:
  - model: htdemucs (42M parameters)
  - device: cuda
  - 输出格式: WAV 44.1kHz stereo

Error handling:
  - 如果 Demucs OOM → 减小 segment_size
  - 如果人声质量差 → 标记人工审核
```

### Step 2: Lyrics Alignment + Segmentation

```
Input:  vocals.wav + LRC 歌词文件 (必须)
Output: segments[] with {text, start_time, end_time, vocal_path}
Tools:  LRC parser + pydub
Time:   ~3s (解析 + 切分)

主路径 (LRC):
  1. 解析 LRC 文件获取 [mm:ss.xx] 时间戳和歌词文本
  2. 用 pydub 按 LRC 时间戳切分 vocals.wav
  3. 验证每段时长 > 0.3s (太短的可能是时间戳错误)
  4. 生成 segment 文件

回退路径 (无 LRC):
  1. Whisper large-v3 转录 vocals.wav (29-54s)
  2. 注意: Whisper 中文歌词准确度极差, 仅供草稿使用
  3. 用户必须在 UI 中修正歌词文本和时间戳
  4. 修正后保存为 LRC 格式

重要: LRC 是主方案, Whisper 只是生成草稿的辅助工具
```

### Step 3: Voice Assignment

```
Input:  segments[] with lyrics
Output: segments[] with voice_model_id assigned

Auto-assign strategies:
  - round-robin: [A, B, C, D, A, B, C, D, ...]
  - random: 从 voice pool 随机选
  - manual: 用户在 UI 中手动分配

Voice pool: 5-10 preset models
```

### Step 4: RVC Per-Line Conversion

```
Input:  segment vocal + voice model (.pth)
Output: converted vocal segment
Tool:   rvc-python (已验证: 安装成功, GPU 检测通过, 真实推理成功)

实测数据 (RTX 4090D, samaschen/RVC_rc_voice 模型):
  - 模型加载: 3.08s
  - 5 段推理总时间: 22.98s
  - 平均每段: 4.60s (含 f0 提取 + 推理)
  - 推算 30 段 (典型歌曲): ~138s
  - 推算 40 段 (密集歌曲): ~184s

Parameters:
  - f0_method: harvest (实测)
    注意: rmvpe 理论上更快更好, 但 rmvpe.pt 在 PyTorch 2.11+ 有 weights_only 兼容问题
    需要: 找到兼容 PyTorch 2.11 的 rmvpe 模型, 或 patch fairseq 的 torch.load
  - index_rate: 0.5
  - filter_radius: 3
  - rms_mix_rate: 0.25
  - protect: 0.33

Optimization (MUST DO):
  - 预加载 voice pool 到 GPU memory (减少模型加载时间)
  - 同模型段落 batch 处理 (减少 f0 重复计算)
  - 切换到 rmvpe f0 方法 (比 harvest 快 2-3x)
  - 以上优化可将 30 段推理从 ~138s 降到 ~60-80s
```

### Step 5: Harmony & Chorus

```
Input:  converted vocal segments + instrumental
Output: full mixed audio with harmony and chorus

Chorus detection:
  - 歌词重复模式检测 (已验证: V5 PASS)
  - 回退: 最后 30s
  - 检测到的 "高潮" 区域用所有 voice models 重新推理

Mixing:
  - 所有 converted vocals 拼接 (crossfade 100ms, V4 已验证)
  - 加入 monologue (位置: 开头前奏期间, 或结尾)
  - vocals + instrumental 混音
  - Normalize to -14 LUFS
```

### Step 6: Monologue Processing

```
Input:  text (用户输入的自我介绍)
Output: processed monologue audio
Tool:   edge-tts
Time:   ~2s (实测)

Process:
  1. edge-tts 生成语音 (zh-CN-YunxiNeural)
  2. 背景音乐降低 12dB
  3. 插入位置: 歌曲前奏 (如果 > 3s), 否则结尾
```

### Step 7: Video Generation

```
Input:  final audio + segments[] (字幕时间)
Output: 9:16 vertical video (MP4)
Tool:   FFmpeg + ASS subtitle generator
Time:   ~5s (实测)

Format: 1080x1920, 30fps, libopenh264 + AAC
Subtitles: ASS format, 每句不同颜色对应不同音色
```

## Performance Benchmarks

4 分钟歌曲 (114.8s 实测), 30 段歌词, 5-voice pool:

| Step | 实测时间 | 来源 | 备注 |
|------|---------|------|------|
| Demucs vocal separation | 6.8s | **实测** | RTX 4090D, 114.8s 歌曲 |
| LRC parse + segment cut | ~3s | 估算 | 纯 CPU 操作 |
| Whisper fallback (无 LRC 时) | 29-54s | **实测** | 不可靠, 仅做草稿 |
| RVC conversion (30 段) | ~138s | **实测推算** | 5段实测 22.98s, 推算 30 段 |
| RVC conversion (优化后 30 段) | ~60-80s | **估算** | 切换 rmvpe + batch 优化 |
| Crossfade mixing | 0.2s | **实测** | |
| Chorus detection | 0.0s | **实测** | |
| Monologue (edge-tts) | 1.8s | **实测** | |
| Video generation | 4.3s | **实测** | |
| **总计 (LRC, 30 段, 优化前)** | **~154s** | | |
| **总计 (LRC, 30 段, 优化后)** | **~80-100s** | | |

⚠️ RVC 真实推理速度是性能瓶颈。实测单段平均 4.60s (harvest f0),
推算 30 段 ~138s, 加其他步骤 ~154s。优化后 (rmvpe f0 + batch) 预计 80-100s。

**对比文档 v1 的 "~62s" 估计, 实际慢 2.5x, 主要因为 RVC 比预期慢很多。**

## Directory Structure

```
firesing/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # 配置
│   ├── database.py             # SQLite connection
│   ├── routers/
│   │   ├── songs.py            # Song API
│   │   └── voices.py           # Voice model API
│   ├── services/
│   │   ├── demucs_service.py   # Demucs wrapper
│   │   ├── lyrics_service.py   # LRC parser + Whisper fallback
│   │   ├── rvc_service.py      # RVC inference wrapper
│   │   ├── tts_service.py      # edge-tts wrapper
│   │   ├── audio_service.py    # pydub/soundfile utilities
│   │   └── video_service.py    # FFmpeg video generation
│   └── pipeline.py             # 端到端处理管线
│
├── frontend/                   # Next.js application
│   ├── app/
│   ├── components/
│   └── lib/api.ts
│
├── models/                     # Pre-trained models
│   ├── rvc/                    # RVC voice models (.pth + .index)
│   ├── demucs/                 # Demucs htdemucs (auto-download)
│   └── whisper/                # Whisper large-v3 (auto-download)
│
├── requirements.txt
└── README.md
```

从 v1 的 6 个 service + 7 个 task module + workers.py 精简到 **6 个 service + 1 个 pipeline.py**。没有 Celery workers, 没有 Redis, 没有独立的 task 模块。

## Error Handling & Fallbacks

| Step | Failure Mode | Fallback |
|------|-------------|----------|
| Vocal separation | Demucs OOM | Reduce segment size, retry |
| Lyrics alignment | No LRC provided | Whisper fallback + user correction |
| RVC conversion | Model load OOM | Load one model at a time |
| RVC conversion | Quality artifacts | Lower index_rate, retry |
| Chorus detection | Can't find chorus | Last 30s fallback |
| Monologue TTS | edge-tts unavailable | Skip monologue |
| Video generation | FFmpeg crash | Retry with simpler format |

## Security Considerations

1. File upload limits: Max 50MB per song
2. Allowed formats: mp3, wav, flac (audio); lrc, txt (lyrics)
3. File path validation: no user-controlled paths
4. GPU resource: single concurrent task

## MVP Development Plan (4 Weeks)

| Week | Scope |
|------|-------|
| 1 | Backend skeleton: FastAPI + SQLite. Song upload + LRC parsing. Demucs integration. |
| 2 | RVC integration: rvc-python wrapper. Voice assignment. Get real trained voice models. |
| 3 | Full pipeline: chorus detection + mixing + monologue + video generation. |
| 4 | Frontend: upload UI, voice assignment, processing status, video download. Deploy. |

## 待验证项 (Backlog)

1. **RVC 真实推理**: 下载真实训练音色模型, 验证推理速度和质量
2. **UVR5 对比测试**: 如果 Demucs 质量不够, 引入 UVR5 做 A/B 测试
3. **CosyVoice 方言 TTS**: Phase 2 方言扩展时评估
4. **多 GPU 扩展**: 如果需求超过单 GPU, 引入 Celery + Redis
