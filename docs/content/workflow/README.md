# 内容生产工作流

## 工作流索引

### Medvi 工作流
- **风格**: 电影纪录片风格商业内容
- **驱动方式**: 旁白驱动，深色暖金色调
- **规范文档**: [video-production-spec.md](video-production-spec.md)
- **旧版参考**: [ai-video-production-workflow.md](ai-video-production-workflow.md)
- **Medvi 拆解**: [medvi-video-multidimensional-analysis.md](medvi-video-multidimensional-analysis.md)

### Sings 工作流
- **风格**: 说唱科普风格 FireSing 推广内容
- **驱动方式**: 音乐节拍驱动，高对比 MV 风格
- **规范文档**: [sings-video-production-spec.md](sings-video-production-spec.md)

---

## 共用工具链

| 工具 | 用途 | 两个工作流共用 |
|------|------|--------------|
| Seedream 4.5 | 参考图生成 | 是 |
| Runway Gen-4 | 图生视频 | 是 |
| FFmpeg | 拼接+音频合并 | 是 |
| 剪映 | 字幕+后期+精修 | 是 |

## 共用规范

- [去AI味 4 步法](#去ai味-4-步法)（两个工作流通用）
- [Runway 参数模板](runway-params-template.md)
- [后期模板](post-production-template.md)
- [预飞检查清单](pre-flight-checklist.md)

---

# 去AI味工作流备忘

> 来源：抖音创作者分享（2026-04-17）
> 核心方法：4 步去除 AI 塑料感

## 4 步法

1. **先定电影级参考图**（决定质感上限）
   - 不要一上来就生成视频
   - 先找/生成高质量的参考图
   - 参考图的质感 = 视频质感的天花板

2. **做分镜**（明确情绪和镜头语言）
   - 每个镜头要有明确的情绪目标
   - 镜头之间要有节奏变化
   - 不要一路平到底

3. **画面驱动生成，不是堆提示词**
   - 用参考图驱动 Runway 生成
   - 提示词只写运动描述（slow pan, zoom in）
   - 不要写长篇画面描述

4. **后期加颗粒 + 光晕**（点睛之笔）
   - 这 10% 决定了"像AI"还是"像真实拍摄"
   - 胶片颗粒：强度 15-20%
   - 柔光/光晕：强度 10-15%
   - 饱和度降低：-5~-10%

## 为什么有效

AI 生成的视频有几个特征：
- 过于干净（没有噪点）
- 过于锐利（边缘太清晰）
- 过于饱和（颜色太鲜艳）
- 运动太流畅（没有手持的微小抖动）

4 步法逐一解决这些问题。
