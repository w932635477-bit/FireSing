# FireSing /autoplan 全面审查报告

**Date:** 2026-04-09
**Branch:** main
**Commit:** 5ad83ba
**Reviewers:** Primary + Codex + Claude Subagent (design phase)

---

## Phase 1: CEO Review (Strategy & Scope)

### Premise Challenge

**Premise 1: "抖音上'一人一句合唱'视频格式已经验证了病毒式传播力"**
- 评估：部分成立。博主收费 50 元/人是真实的，但样本量小（一个群），且没有验证这些视频是否真的有高传播力。
- 风险：Medium。如果传播力不足，整个商业模式崩塌。
- 建议：在 Phase 0 就验证。发 3 个测试视频到抖音，观察播放量。

**Premise 2: "RVC 开源管线可以实现生产级音质"**
- 评估：技术可行，但"生产级"定义模糊。RVC 推理质量依赖训练数据、参数调优和后处理。
- 风险：Medium。如果音质不过关，抖音用户不会买单。
- 建议：Phase 0 先手动跑一首歌的完整管线，验证音质可接受。

**Premise 3: "用户技术能力低" → 需要 Web 界面**
- 评估：成立。目标用户确实不会用命令行工具。

**Premise 4: "GPU 月租 ~2,000-3,500 元"**
- 评估：成立但低估了。高峰期 GPU 可能涨价，且没算带宽、存储和域名成本。

### 6-Month Regret Scenario

1. **最大遗憾风险：** 6 个月后如果发现用户要的不是"AI 音色切换"而是"AI 方言唱歌"，整个 MVP 方向就偏了。当前 MVP 只做音色切换，不做方言。但 DESIGN.md 明确说"方言是核心愿景"。如果核心愿景和 MVP 之间的鸿沟太大，MVP 验证完了用户也不会留下。

2. **竞争风险：** 妙音 AI、天工 SkyMusic 已经在做 AI 音乐。如果它们加上"多人合唱"功能，FireSing 就没有护城河。RVC 是开源的，技术壁垒为零。

3. **版权风险：** 魔改流行歌曲是灰色地带。抖音可能随时收紧政策。需要考虑公版歌曲或原创歌曲的替代方案。

### Dream State Delta

```
CURRENT → MVP → 12-MONTH IDEAL

CURRENT: 代码框架完成，前端 6 页面，后端 API 完整，GPU 推理未验证
  ↓ 缺口：端到端管线未跑通，没有真实用户

MVP (Phase 1): 用户可上传歌曲 → 系统自动处理 → 下载竖版视频
  ↓ 缺口：单用户，无协作，无方言

12-MONTH IDEAL: 多人协作平台，支持 5+ 方言，抖音小程序入口，创作者付费生态
  ↓ 差距：需要方言 TTS、协作模式、小程序开发、支付系统扩展
```

---

## Phase 2: Design Review (completed via /design-review)

**已运行完整的 design-review。结果：**

- Design Score: **B-**
- AI Slop Score: **C** (6/10 黑名单命中)
- 总发现：24 项 (5 High, 10 Medium, 9 Polish)
- 已修复：5 项 (5 commits)
- 遗留：19 项

详见：`~/.gstack/projects/w932635477-bit-FireSing/designs/design-audit-20260409/`

---

## Phase 3: Eng Review (Architecture & Code Quality)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│  Landing / Dashboard / Song Detail / Process        │
│  Pricing / Login                                     │
│  Auth: useAuth() → WeChat OAuth                     │
│  API: lib/api.ts → fetch() to backend               │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────┐
│                  Backend (FastAPI)                    │
│  Routers: songs, voices, pipeline, auth, orders,     │
│           music, outputs                              │
│  Services: demucs, lrc, rvc, tts, chorus, harmony,  │
│            video, audio, wechat                       │
│  DB: SQLite (SQLAlchemy)                              │
│  Auth: WeChat OAuth + JWT                             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────┐
│               GPU Server (AutoDL)                    │
│  RVC inference, Demucs separation                    │
└─────────────────────────────────────────────────────┘
```

### Code Quality Findings

| ID | Finding | Severity | File |
|----|---------|----------|------|
| ENG-001 | API 无认证保护（songs/pipeline/voices 路由无 auth 依赖） | Critical | backend/routers/*.py |
| ENG-002 | SQLite 不适合生产（单写锁，并发写入会阻塞） | High | backend/database.py |
| ENG-003 | 音频处理用 asyncio.to_thread() 包装同步 pydub，但无超时保护 | Medium | backend/services/audio_service.py |
| ENG-004 | 硬编码文件路径（/tmp, ./data/），部署到不同环境会出错 | Medium | backend/config.py |
| ENG-005 | 前端 API 错误处理粗糙（catch {} 空 catch） | Medium | frontend/lib/api.ts |
| ENG-006 | SSE 进度推送无心跳，长任务可能被代理超时断开 | Medium | backend/routers/pipeline.py |
| ENG-007 | 前端 useSongDetail.ts 没有清理 SSE 连接（内存泄漏） | Medium | frontend/app/songs/[id]/useSongDetail.ts |
| ENG-008 | Order 模型没有幂等性保护（重复支付可能创建多个订单） | High | backend/routers/orders.py |
| ENG-009 | CORS 配置允许所有来源（`allow_origins=["*"]`） | Critical | backend/main.py |
| ENG-010 | 密钥管理：WeChat app_secret 在代码中而非环境变量 | Critical | backend/services/wechat_service.py |

### Test Coverage

| Area | Files | Status |
|------|-------|--------|
| Backend Unit | 9 test files | Exists, unknown pass rate |
| Backend Integration | 0 | Missing |
| Frontend Unit | 0 | Missing |
| Frontend E2E | 0 | Missing |
| GPU Server | 0 | Missing |

---

## Phase 3.5: DX Review

**跳过。** 产品面向内容创作者，不是开发者工具。API 访问是专业版功能，不是核心产品。

---

## Cross-Phase Themes

1. **安全性** — CEO 阶段提到版权风险，Eng 阶段发现 API 无认证 + CORS 全开 + 密钥硬编码。这是一个系统性问题，不是个别 bug。

2. **端到端验证缺失** — 架构完整但管线的每一步都没有在实际环境中验证过。从"代码存在"到"用户能用"之间差距很大。

3. **移动端体验** — Design review 发现首页无移动端导航。Eng review 发现前端缺少响应式优化。CEO 层面，抖音用户 90%+ 是移动端。

---

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle |
|---|-------|----------|-----------|-----------|
| 1 | CEO | 接受 MVP 范围（不做方言） | Auto (P6) | 偏向行动 |
| 2 | CEO | Phase 0 验证必须先于 Phase 1 | Auto (P1) | 完整性 |
| 3 | Design | 修复 footer/链接/focus ring | Auto (P1) | 完整性 |
| 4 | Design | 推迟移动端导航（结构性改动） | Auto (P3) | 务实 |
| 5 | Design | 推迟 border-radius 层级重构 | Auto (P3) | 务实 |
| 6 | Eng | API 认证为 Critical，需要立即修复 | Auto (P1) | 完整性 |
| 7 | Eng | SQLite 短期可接受，生产前需迁移 | Auto (P3) | 务实 |
| 8 | Eng | 跳过 DX review（非开发者工具） | Auto (P3) | 务实 |

---

## Final Scores

| Phase | Score | Status |
|-------|-------|--------|
| CEO (Strategy) | B | 前提基本成立，但验证不足 |
| Design | B- | 视觉系统好，AI slop 偏多 |
| Eng | C+ | 架构完整但有 3 个 Critical 安全问题 |
| DX | Skipped | N/A |

---

## Priority Action Items

### Critical (立即修复)
1. **API 认证** — 所有写操作路由添加 `Depends(get_current_user)`
2. **CORS 限制** — 将 `allow_origins=["*"]` 改为实际域名
3. **密钥管理** — WeChat app_secret 移到环境变量

### High (本周)
4. 端到端管线验证（手动跑一首歌完整流程）
5. 移动端导航（首页汉堡菜单）
6. 订单幂等性保护

### Medium (本月)
7. 前端错误处理改进
8. SSE 心跳机制
9. A11y 改进（aria labels, contrast）
10. 测试覆盖提升
