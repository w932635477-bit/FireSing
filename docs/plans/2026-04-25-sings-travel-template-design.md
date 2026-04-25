# Sings 旅行对唱工作流统一模板设计

**日期:** 2026-04-25
**状态:** 已批准
**背景:** 穿搭对比方向废弃，Sings 系列统一走旅行城市对唱路线。基于重庆 pilot 验证的 prompt 方法论。

## 决策

1. **穿搭 prompt 废弃**：Sings 不再做穿搭对比内容
2. **统一用 Travel v1.0 Seedream prompt**：Casual snapshot 风格，不用摄影术语
3. **统一用已验证的 Suno 对唱 prompt**：Duet (Alternating) + [Female]/[Male] 标记
4. **`sings-template.json` 重写为旅行模板**

## Seedream Prompt 方法论

**6 层结构（严格按顺序）：**

1. `Casual travel snapshot, portrait orientation` — 开头声明
2. 角色锚定：`a young Chinese woman, mid-twenties, round face, short black bob haircut, wearing {outfit}`
3. 场景描述：具体城市 + 地标，背景虚化（blurred, soft bokeh）
4. 自然瑕疵：`a few flyaway hairs, uneven skin tone, natural shine on nose, visible pores, slight asymmetry`
5. 随意感：`candid unposed moment, slightly imperfect framing, NOT retouched, NOT posed`
6. `vertical composition 9:16` — 末尾竖版保险

**禁止：** 摄影术语（Canon/Sony/film stock）、"Photograph of"、"Professional"、studio lighting、"catchlight in eyes"、"prompt_priority: quality"

## Suno 对唱 Prompt 方法论

**Style prompt：**
```
Duet (Alternating). Female lead is airy and playful. Male lead is grounded and warm. Clear turn-taking each line. One shared hook in chorus only. catchy mid-tempo pop, sing-song storytelling, educational pop, TikTok viral Chinese pop, light electronic beat, acoustic guitar, whistle, 125 bpm
```

**歌词格式：** 每行标记 [Female]/[Male]/[Both]，[Both] 只用于 Chorus

**参数：**
- BPM: 125（Suno 实际演绎可能 ~103，可接受）
- model: suno-v4.5, custom_mode: true, vocal_gender: "m"
- negative_tags: rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody, autotune

## Negative Prompt（36 项）

```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed, stock photo, 3D render, illustration, cartoon, anime, watermark, text, logo, oversaturated, mannequin, flawless, magazine cover, retouched, poreless skin, dark, moody, film grain, wrinkled clothes, fabric distortion, stiff pose, cropped, out of frame, tilted, cluttered, western face, non-Chinese, blue eyes, blonde hair, too perfect, wax figure, doll-like, plastic texture, symmetrical face, perfectly aligned features, professional photography, studio quality, perfectly composed, smooth skin, overly detailed, sharp focus everywhere, digital art, painting, rendering, CGI, unreal engine
```

## 模板结构

### Segment 布局（4 segments）

| Segment | 类型 | 时长 | 情绪 | 内容 |
|---------|------|------|------|------|
| S01 | hook | 6s | playful | 城市震撼点提问 + 开场 |
| S02 | body | 8s | surprised/excited | 亮点A体验 + 知识 |
| S03 | body | 8s | excited | 亮点B体验 + 知识 |
| S04 | cta | 6s | warm | 总结 + 投票下一站 |

### 歌词结构（6 bars）

- B01: Hook（城市提问）→ S01
- B02-B03: 亮点A（体验+知识）→ S02
- B04-B05: 亮点B（体验+知识）→ S03
- B06: CTA（总结+投票）→ S04

### 新增字段

- `city`: 城市名
- `highlights[]`: [{name, type}]
- `publishing.platforms`: ["douyin", "xiaohongshu"]

## 文件变更

| 文件 | 动作 |
|------|------|
| `sings-template.json` | 重写为旅行对唱模板 |
| `city-chongqing.json` | 保持不变，已是正确范例 |
| `outfit-*.json` configs | 保留但不再维护 |
| `outfit-seedream-prompts.md` | 标记废弃 |

## 验证记录

- 重庆 pilot 3 轮迭代验证通过（commit `c4553e6`）
- Suno 对唱：用户评价"效果特别好，歌曲很好听"
- Seedream 图片：从 AI 味重 → 修复竖版 → 去 AI 味，每轮用户确认效果提升
