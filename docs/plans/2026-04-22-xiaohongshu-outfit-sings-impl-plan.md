# 小红书穿搭对比 Sings 实施计划

**日期**: 2026-04-22
**设计文档**: 2026-04-22-xiaohongshu-outfit-sings-design.md
**状态**: 待实施

## 实施步骤

### Phase 1: 模板和基础设施（1天）

1. **创建 `sings-outfit-template.json`**
   - 基于 `sings-template.json` 修改
   - 改动项：
     - `global.style`: `"outfit_compare"`
     - `global.color_temperature`: `"warm_bright"`
     - `global.accent_color`: `"#e8a87c"`
     - `global.bg_color`: `"#f5e6d3"`
     - `lyrics.style`: 男女对唱 pop（复用 sings04-yangmun 的风格）
     - `lyrics.suno_tags`: `"catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, 130 bpm"`
     - `lyrics.negative_tags`: `"rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock"`
     - `audio.style_prompt`: 同上
     - `audio.generation.vocal_gender`: `"duet"` 或分别标注男女
     - `post_production`: 降低对比度，提高饱和度，去掉 film grain（时尚感不需要）
     - `publishing.platforms`: `["xiaohongshu"]`
   - 歌词模板改为穿搭场景对比格式
   - segments 改为 5 段（hook + 2 body + 法则 + CTA）

2. **创建 Seedream 穿搭 Prompt 模板**
   - 位置：`docs/content/config/outfit-seedream-prompts.md`
   - 包含：
     - 杨梦全身照基础 prompt（复用已有角色锚定经验）
     - 穿搭变体 prompt 结构：`[基础角色], wearing [服装描述], [场景], [姿势]`
     - 明亮背景 prompt：`bright studio lighting, cream white background, fashion lookbook style`
     - 负面 prompt（复用现有的，增加 `dark, moody, cinematic, film grain`）
   - 每集需要至少 2 套穿搭图片（A 套和 B 套）

3. **更新 Sings 工作流 Spec**
   - 在 `sings-video-production-spec.md` 末尾增加 `## 附录：穿搭对比模式`
   - 或创建独立 spec：`sings-outfit-production-spec.md`
   - 内容：穿搭模式的差异点、分屏编辑指南、色调要求

### Phase 2: 第一集制作（1-2天）

4. **创建第一集 config: `day1-outfit-interview.json`**
   - 场景：面试穿搭 A vs B
   - 歌词：按设计文档中的示例填写 10 bars
   - segments：
     - S01 (hook): 杨梦两套穿搭并排对比
     - S02 (body): A 套穿搭特写 + 文字卡
     - S03 (body): B 套穿搭特写 + 文字卡
     - S04 (body): 穿搭法则总结 + 文字卡
     - S05 (cta): 杨梦直视镜头，"你选 A 还是 B"

5. **生成 Seedream 参考图**
   - 杨梦穿深蓝西装白衬衫（面试 A 套），明亮背景，全身照
   - 杨梦穿针织衫深色裤子（面试 B 套），明亮背景，全身照
   - 每套 2 张候选

6. **Kling 视频生成**
   - 用参考图生成 5s 视频片段
   - 每段 1 个候选

7. **Suno 对唱音频生成**
   - 用 `suno-rap-batch.py` 脚本生成
   - 男女对唱 pop 风格
   - 生成 2 个版本选最佳

8. **FFmpeg 拼接**
   - 5 段视频 + Suno 音频
   - 输出到 `docs/content/output/outfit-day1/`

9. **剪映后期**
   - 用户手动完成：
     - 裁剪音频到 30-45s
     - A/B 穿搭分屏或快速切换
     - KTV 歌词字幕
     - 穿搭对比文字叠加
     - 去 AI 化 4 步处理
     - 导出最终版

### Phase 3: 批量化（第1周内容）

10. **批量创建 config**
    - day2-outfit-firstday.json（入职第一天）
    - day3-outfit-presentation.json（述职报告）
    - day4-outfit-dinner.json（商务晚宴）
    - day5-outfit-commute.json（通勤日常）

11. **批量生图和视频**
    - 每集 2 套穿搭 = 4 张参考图 + 4 个视频
    - 5 集 = 20 张图 + 20 个视频
    - Seedream 和 Kling 可并行

12. **批量生成 Suno 音频**
    - 5 集 = 5 × 2 版本 = 10 条音频
    - 用 `suno-rap-batch.py` 批量提交

### Phase 4: 发布和迭代

13. **小红书发布**
    - 每天 1 条，周一到周五
    - 封面：杨梦 A/B 穿搭对比，大字"面试穿A还是B"
    - 标签：#穿搭对比 #面试穿搭 #杨梦穿搭 #职场穿搭 #OOTD

14. **数据监控**
    - 记录每条播放量、点赞、收藏、评论数
    - 重点关注评论中 A/B 投票比例（验证互动模型）
    - 第 1 周结束后复盘，调整选题方向

## 文件清单

| 文件 | 类型 | Phase |
|---|---|---|
| `docs/content/config/sings-outfit-template.json` | 新建 | 1 |
| `docs/content/config/outfit-seedream-prompts.md` | 新建 | 1 |
| `docs/content/workflow/sings-outfit-production-spec.md` | 新建 | 1 |
| `docs/content/config/day1-outfit-interview.json` | 新建 | 2 |
| `docs/content/output/outfit-day1/` | 新建目录 | 2 |
| `docs/content/config/day2-5-outfit-*.json` | 新建 | 3 |

## 依赖和风险

- **Suno 时长问题**：Suno v4.5 生成 120s+ 音频，需要手动裁剪。短期接受，长期考虑 API 参数优化。
- **Seedream 穿搭一致性**：AI 生成的服装细节可能不一致，需要多次迭代。用固定的角色锚定 prompt 减少偏差。
- **分屏编辑**：剪映中的左右分屏对比是新的编辑步骤，需要学习成本。
- **小红书算法冷启动**：新账号 + 新内容类型，前 5 条可能数据很低。需要坚持发布至少 2 周再判断。
