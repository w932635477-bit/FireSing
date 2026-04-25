# 强制女声配音设计

**Goal:** 所有 Medvi 视频统一使用 Aoede 女声配音，禁止使用男声。重新生成 Day10 配音。

**变更范围：**
1. `gemini-tts-batch.py` 默认 voice 从 Charon 改为 Aoede，NARRATOR_PROFILE 默认用 FEMALE
2. `video-production-spec.md` 明确规定"统一使用女声 Aoede，禁止使用男声"
3. Day10 重新生成 TTS（当前是 Charon 男声，需替换为 Aoede 女声）
4. 所有 config JSON 的 voiceover.voice 固定为 "Aoede"

**不变更：**
- 降级链不变（Google → 云雾AI → Doubao）
- Director's Notes 机制不变
- 情绪控制方式不变
