# FireSing 需求符合性审计报告

生成日期: 2026-04-05
基准文档: DESIGN.md (v4, APPROVED)
审计范围: backend/, frontend/, gpu_server/

## 总览

| 类别 | 符合 | 部分 | 缺失 |
|------|------|------|------|
| 核心管线 (7步) | 4/7 | 1/7 | 2/7 |
| v4 新增需求 | 2/5 | 2/5 | 1/5 |
| 技术栈 | 6/8 | 0/8 | 2/8 |
| MVP 约束 | 4/4 | 0/4 | 0/4 |
| 前端功能 | 5/8 | 2/8 | 1/8 |

**总体符合率: ~60%**

---

## 1. 核心管线需求对照

### Step 1: 人声分离
| 需求 (DESIGN.md) | 实现 | 状态 |
|---|---|---|
| 使用 UVR5 | 使用 Demucs (htdemucs) | **偏差** |

**分析:** DESIGN.md 明确选择 UVR5 而非 Demucs，理由是"比 Demucs 更快更干净"。实际代码使用 `demucs.api.Separator`。功能上可工作，但与需求文档不一致。CLAUDE.md 也写的是 "Upload + Demucs"，存在文档自相矛盾。

**建议:** 统一文档和实现。如果选择 Demucs，更新 DESIGN.md；如果选择 UVR5，需修改 gpu_server。

### Step 2: 逐句切分
| 需求 (DESIGN.md) | 实现 | 状态 |
|---|---|---|
| Whisper 获取歌词级时间戳 | 未实现 Whisper | **缺失** |
| Silero VAD 检测静音边界 | 未实现 | **缺失** |
| 自动将人声切分为逐句独立文件 | 仅通过 LRC 文件切分 | **部分** |
| 回退策略 (PyAnnote / 手动校准) | 未实现 | **缺失** |

**分析:** `lyrics_service.py` 完全依赖 LRC 文件解析。DESIGN.md 的管线设计是 Whisper 自动获取时间戳，LRC 只是辅助。当前实现跳过了自动歌词检测环节，必须手动提供 LRC 文件。

### Step 3: RVC 逐句音色转换 ✅
| 需求 | 实现 | 状态 |
|---|---|---|
| 逐句分别用不同音色 RVC 推理 | ✅ `rvc_service.py` | **符合** |
| harvest f0 方法 | ✅ `f0_method: "harvest"` | **符合** |
| index_rate 0.5, filter_radius 3 | ✅ | **符合** |
| 模型缓存避免重复加载 | ✅ `_model_cache` | **符合** |

### Step 4: 和声处理 ❌
| 需求 (DESIGN.md) | 实现 | 状态 |
|---|---|---|
| RVC f0_up_key=+3 大三度声部 | 未实现 | **缺失** |
| +4(小三度), +5(纯四度), +7(纯五度) | 未实现 | **缺失** |
| 各声部叠加降音量 -6~-12dB | 未实现 | **缺失** |

**分析:** DESIGN.md 明确描述了和声处理方案：使用 RVC 的 f0_up_key 参数进行音高偏移生成多声部。当前代码完全没有实现。`rvc_service.py` 的 `f0up_key` 参数固定为 0。

### Step 5: 大合唱合成 ❌
| 需求 (DESIGN.md) | 实现 | 状态 |
|---|---|---|
| 自动检测歌曲最后一段(高潮/结尾) | 仅检测重复歌词 | **部分** |
| 5个不同音色模型分别推理 | 未实现 | **缺失** |
| 叠加 + 立体声分布 + 混响 | 未实现 | **缺失** |

**分析:** `chorus_service.py` 只做了简单的歌词重复检测（`Counter(seg.text)`），没有实现真正的合唱合成。v4 需求明确说"自动检测歌曲最后一段（高潮/结尾），将所有单人音色合并生成大合唱"。

### Step 6: 混音合成 ✅
| 需求 | 实现 | 状态 |
|---|---|---|
| 转换后人声 + 原始伴奏 → 混音 | ✅ `audio_service.py` | **符合** |
| pydub/FFmpeg 同步操作 | ✅ `asyncio.to_thread()` | **符合** |
| Crossfade 拼接 | ✅ 100ms crossfade | **符合** |

### Step 7: 视频输出 ✅
| 需求 | 实现 | 状态 |
|---|---|---|
| 9:16 竖版视频 | ✅ 1080x1920 | **符合** |
| ASS 字幕 | ✅ 每句不同颜色 | **符合** |
| FFmpeg 生成 | ✅ libx264 + AAC | **符合** |

---

## 2. v4 新增需求对照

### 个人独白 (Personal Monologue) — 部分
| 需求 | 实现 | 状态 |
|---|---|---|
| TTS 生成 | ✅ edge-tts (zh-CN-YunxiNeural) | **符合** |
| 用户录音上传 | 未实现 | **缺失** |
| 音色处理(保留原始/RVC) | 未实现 | **缺失** |
| 位置逻辑(开头优先，无前奏放结尾) | ✅ beginning/end 参数 | **符合** |

### 和声/合唱处理逻辑 ❌
| 需求 | 实现 | 状态 |
|---|---|---|
| 跟随原歌曲结构 | 未实现 | **缺失** |
| 自动检测最后一段→大合唱 | 仅歌词重复检测 | **部分** |

### 输入输出格式 — 部分
| 需求 | 实现 | 状态 |
|---|---|---|
| 输入: 音频 + LRC | ✅ | **符合** |
| 输入: 纯文本歌词 | 未实现 | **缺失** |
| 输出: 竖版视频 | ✅ MP4 | **符合** |
| 输出: 音频 mp3/wav | 仅 WAV | **部分** |
| 输出: 带字幕视频 | ✅ (同一视频文件) | **符合** |

### 视频视觉风格 ❌
| 需求 | 实现 | 状态 |
|---|---|---|
| 模拟抖音界面风格 | 纯黑背景 | **缺失** |
| 头像使用系统预设 | 未实现 | **缺失** |

---

## 3. 技术栈偏差

| 需求 (DESIGN.md) | 实际使用 | 状态 |
|---|---|---|
| UVR5 (人声分离) | Demucs (htdemucs) | **偏差** |
| Whisper + Silero VAD (切分) | 仅 LRC 解析 | **缺失** |
| RVC v2 (音色转换) | ✅ rvc-python | **符合** |
| pydub (音频处理) | ✅ | **符合** |
| librosa (音频处理) | 未引入 | **缺失** |
| FFmpeg (视频合成) | ✅ subprocess | **符合** |
| Next.js (前端) | ✅ Next.js 16 | **符合** |
| FastAPI (后端) | ✅ | **符合** |

---

## 4. 前端功能对照

### 已实现 ✅
- 着陆页 (app/page.tsx) — 完整的营销页面
- 仪表盘 (app/dashboard/page.tsx) — 歌曲列表、上传对话框、状态显示
- 歌曲详情 (app/songs/[id]/page.tsx) — LRC 上传、音色管理、段落编辑、处理设置
- 处理进度 (app/songs/[id]/process/page.tsx) — SSE 实时进度、步骤可视化
- API 客户端 (lib/api.ts) — 完整的后端 API 覆盖

### 需要关注的问题
1. **"后台运行"按钮无功能** — `process/page.tsx:209` 的 button 没有 onClick 处理器
2. **导航链接未实现** — "音乐库"、"语音模型"、"工作站" 都链接到 `/dashboard`
3. **删除功能不完整** — `songs.py:103` 只删除 SONGS_DIR，不清理 SEGMENTS_DIR/CONVERTED_DIR/OUTPUTS_DIR
4. **Demo 数据回退** — API 不可用时显示假数据，可能误导用户

---

## 5. 代码质量发现

### 安全问题
1. **文件路径遍历风险** — 上传文件名未清洗，`Path(audio.filename).suffix` 可能被利用
2. **无文件大小限制** — 音色模型上传没有大小限制（音频有 50MB 限制）
3. **FFmpeg 命令注入** — `ass_path` 直接传入命令行参数，虽然目前是系统生成的路径

### 可靠性问题
1. **FFmpeg 视频固定 3600s** — `color=c=black:d=3600` 生成 1 小时黑色背景，依赖 `-shortest` 裁剪。如果音频超过 1 小时会截断
2. **Pipeline 错误恢复缺失** — 失败后无法从断点续传，必须重新开始
3. **内存中的进度存储** — `_pipeline_progress` 字典在服务器重启后丢失

### 性能问题
1. **无并发控制** — 多个 pipeline 可同时运行，无队列机制
2. **RVC 模型每次重新加载** — `gpu_server/server.py:180` 每次推理都 `RVCInference()` + `load_model()`，虽然 `_model_cache` 缓存了路径，但模型对象没有缓存

---

## 6. 需求优先级排序

按产品影响排序，最重要的缺失功能：

| 优先级 | 缺失项 | 影响 | 工作量估计 |
|--------|--------|------|-----------|
| P0 | 和声处理 (Step 4) | 核心音质，无和声=半成品 | M |
| P0 | 大合唱合成 (Step 5) | 产品核心卖点 | M |
| P1 | Whisper 自动切分 | 当前必须手动准备 LRC | S |
| P1 | 删除清理 bug | 数据泄漏，磁盘占用 | XS |
| P2 | 抖音风格视频 | 当前只是黑底字幕 | M |
| P2 | 用户录音独白 | v4 需求 | S |
| P3 | 纯文本歌词支持 | 可用 LRC 替代 | XS |
| P3 | MP3 输出格式 | WAV 可用 | XS |
| P3 | UVR5 替代 Demucs | 功能可工作 | S |

---

## 7. 结论

### 做得好的部分
- 数据模型设计合理，Song → Segment → VoiceModel 关系清晰
- API 设计 RESTful，前后端接口完整对齐
- Pipeline 8 步流程完整，进度追踪 (SSE) 实现到位
- 前端 UI 专业，深色设计系统一致
- 幂等处理（重复调用不重复执行）
- GPU 服务器模型缓存和重试机制

### 主要差距
1. **和声+合唱是核心产品价值但完全缺失** — 这是"多人多音色合唱"的关键，没有它产品只有"换声"，没有"合唱"
2. **Whisper 自动切分未实现** — 用户必须手动准备 LRC 文件，使用门槛高
3. **文档与实现不一致** — DESIGN.md 写 UVR5，代码用 Demucs；DESIGN.md 写 Whisper，代码只用 LRC

### 下一步建议
1. 优先实现和声处理（利用现有 RVC f0_up_key 参数，工作量不大）
2. 实现大合唱合成（在 chorus_service.py 扩展，复用 RVC 推理）
3. 在 Demucs 和 UVR5 之间做决定，统一文档和代码
4. 修复 delete_song 的文件清理 bug

---

## 8. QA 测试结果

### 测试环境
- macOS Darwin 25.3.0 (ARM)
- Backend: FastAPI + Uvicorn (venv)
- Frontend: Next.js 16.2.2 + Turbopack
- GPU 服务器: 不可用（AutoDL 远端）

### API 测试结果

| 测试 | 端点 | 结果 |
|------|------|------|
| Health check | GET /api/health | ✅ PASS |
| 上传歌曲 (无歌词) | POST /api/songs | ✅ PASS — 返回 song 对象，status=uploaded |
| 上传歌曲 (带歌词) | POST /api/songs | ✅ PASS — LRC 正确保存 |
| 歌曲列表 | GET /api/songs | ✅ PASS — 返回所有歌曲 |
| 歌曲详情 | GET /api/songs/{id} | ✅ PASS |
| 段落列表 (空) | GET /api/songs/{id}/segments | ✅ PASS — 返回空数组 |
| 音色列表 (空) | GET /api/voices | ✅ PASS |
| 上传音色 | POST /api/voices | ✅ PASS — .pth 文件正确保存 |
| 音色分配 (无段落) | PUT /api/songs/{id}/voices | ✅ PASS — 正确返回 400 错误 |
| 触发管线 | POST /api/songs/{id}/process | ✅ PASS — 返回 processing |
| SSE 进度 | GET /api/songs/{id}/progress | ✅ PASS — 正确推送 error 事件 |
| 删除歌曲 | DELETE /api/songs/{id} | ✅ PASS (但有文件清理 bug) |
| 管线错误处理 | — | ✅ PASS — 无 GPU 时 502 正确上报 |

### 单元测试结果

```
52 passed in 0.38s
```

覆盖: songs CRUD, LRC 解析, 音频切分, Demucs mock, RVC mock, 音色管理, 输出管理, Pipeline 集成

### 前端构建

```
Next.js 16.2.2 (Turbopack) — 6 routes compiled successfully
○ / (Static)
○ /dashboard (Static)
○ /login (Static)
ƒ /songs/[id] (Dynamic)
ƒ /songs/[id]/process (Dynamic)
```

TypeScript 类型检查: ✅ PASS (零错误)

### API 代理配置

`next.config.ts` 正确配置了 API rewrite: `/api/:path*` → `http://localhost:8000/api/:path*`

---

## 9. 代码质量指标

| 指标 | 值 |
|------|-----|
| 后端代码行数 | 2,883 行 |
| 前端代码行数 | 2,078 行 |
| 测试数量 | 52 个 |
| 测试通过率 | 100% |
| TypeScript 错误 | 0 |
| TODO/FIXME 注释 | 0 |
| 裸 except 语句 | 0 |
| 硬编码密钥 | 0 |
| 数据库迁移策略 | `create_all()` (开发阶段可接受) |

### 安全问题汇总

1. **文件路径遍历** — 上传文件名未清洗 (低风险，内部使用)
2. **无音色模型大小限制** — 可能被滥用上传大文件
3. **FFmpeg 路径注入** — ASS 路径由系统生成，风险低但应参数化
