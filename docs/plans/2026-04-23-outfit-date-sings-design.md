# Sings 穿搭对比对唱: 初次约会穿搭 (outfit-day1-date)

> 视频ID: outfit-day1-date
> 工作流: Sings v2.0 (穿搭对比对唱)
> 平台: 小红书 9:16 竖版
> 角色: 杨梦 (Yang Mun)
> 对唱: 男女声对唱 (Suno AI)
> 素材: 全新生成
> 日期: 2026-04-23

---

## 1. 歌词脚本

**场景**: 初次约会穿搭纠结
**A套 - 用力过猛**: 碎花裙 + 细高跟 + 精致妆
**B套 - 自然舒服**: 针织衫 + 牛仔裤 + 小白鞋

```
[Chorus]                    ← Hook (男问女答)
男：初次约会到底怎么穿        (chuān)
女：太用力反而让人难堪        (kān)

[Verse 1]                   ← Outfit A (男声点评)
男：A套碎花长裙细高跟        (gēn)
男：精致是精致不像本人        (rén)
男：妆浓到走路不敢低头        (tóu)
男：约会变成走红毯的秀        (xiù)

[Verse 2]                   ← Outfit B (女声展示)
女：B套针织衫搭牛仔裤        (kù)
女：干净舒服自在不装酷        (kù)
女：小白鞋走哪都不紧张        (zhāng)
女：做自己就是最好的装        (zhuāng)

[Verse 3]                   ← 法则 (男女交替)
男：法则一 场合定基调        (diào)
女：约会穿太正式会吓跑        (pǎo)
男：法则二 合身最重要        (yào)
女：穿得舒服才敢放开笑        (xiào)

[Outro]                     ← CTA (合唱)
合唱：初次约会你站A还是B
合唱：评论区投票告诉我你的品味
```

### 质量检查

- [x] 总行数: 16 行
- [x] 最长单行: 10 字 ("精致是精致不像本人", "评论区投票告诉我你的品味")
- [x] 押韵对: an(Chorus), en(V1前2), ou/iu(V1后2), u(V2前2), ang(V2后2), ao(V3) = 6 对
- [x] 穿搭信息密度: 每 2 行 ≥ 1 个知识点
- [x] 法则: 2 条 (场合定基调, 合身最重要)
- [x] CTA: 投票 A/B 格式

---

## 2. 参考图方案 (8 张, Seedream 4.5)

### 2.1 统一设置

**角色锚定块** (每张图逐字不变):
```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
```

**Negative Prompt**:
```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain,
wrinkled clothes, fabric distortion, texture error, stiff pose,
cropped, cut off, out of frame, tilted, cluttered
```

**背景**: 明亮现代咖啡馆, cream white 墙面 + 木质桌椅 + 绿植

### 2.2 Prompt 结构 (7 层, 基于行业最佳实践)

1. **整体美学/mood** — 前 5-8 词决定基调
2. **角色锚定** — 逐字不变的 identity block
3. **服装描述** — 具体面料名 + 颜色名 + 版型 + 配饰
4. **场景背景** — 明亮咖啡馆
5. **姿势** — 站立/转身/微笑
6. **光影** — 自然日光, 柔和温暖, 5500K
7. **相机/技术** — 镜头 + 景别 + 构图 + `vertical composition 9:16`

### 2.3 各图 Prompt

#### S01-1: Hook - A套全身

```
Bright fashion lookbook editorial, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a navy blue floral print chiffon midi dress with V-neckline and flutter sleeves,
paired with beige suede pointed-toe kitten heels, delicate gold chain necklace,
standing in a bright modern cafe with cream white walls, wooden tables, and green potted plants,
hands clasped gently in front, confident but slightly nervous smile,
natural daylight streaming through large windows, soft warm shadows, 5500K white balance,
full-body shot, 50mm lens, model centered with negative space above, vertical composition 9:16
```

#### S01-2: Hook - B套全身

```
Bright fashion lookbook editorial, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a cream white ribbed knit sweater with relaxed fit, paired with medium blue
straight-leg denim jeans and clean white canvas sneakers, silver stud earrings,
standing in a bright modern cafe with cream white walls, wooden tables, and green potted plants,
one hand in jeans pocket, relaxed natural smile,
natural daylight streaming through large windows, soft warm shadows, 5500K white balance,
full-body shot, 50mm lens, model centered with negative space above, vertical composition 9:16
```

#### S02-1: Outfit A 中景 (正面)

```
Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a navy blue floral print chiffon midi dress with V-neckline and flutter sleeves,
delicate gold chain necklace, chiffon fabric catching light with natural drape,
in a bright modern cafe, blurred cream white background with warm bokeh,
standing with arms relaxed at sides, looking slightly to the side,
natural daylight from left side, soft directional shadows on fabric texture,
waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

#### S02-2: Outfit A 中景 (转身)

```
Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a navy blue floral print chiffon midi dress, back detail showing open V-back design,
delicate gold chain necklace visible from behind,
in a bright modern cafe, blurred warm background,
gentle half-turn looking back over shoulder, warm smile,
natural daylight from right side, rim light on hair,
waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

#### S03-1: Outfit B 中景 (正面)

```
Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a cream white ribbed knit sweater with relaxed fit, silver stud earrings,
knit texture visible with natural yarn detail and soft drape,
in a bright modern cafe, blurred cream white background with warm bokeh,
standing casually with one hand touching hair, natural confident smile,
natural daylight from left side, soft shadows, warm skin tones,
waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

#### S03-2: Outfit B 中景 (转身)

```
Fashion lookbook detail shot, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing a cream white ribbed knit sweater, medium blue straight-leg denim jeans visible at waist,
silver stud earrings,
in a bright modern cafe, blurred warm background,
slight turn showing profile, relaxed smile, hand adjusting sleeve,
natural daylight from right, rim light on hair and shoulder,
waist-up shot, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

#### S05-1: CTA 特写 (微笑)

```
Warm intimate fashion portrait, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing cream white ribbed knit sweater, natural minimal makeup,
in a bright modern cafe, soft blurred background,
direct eye contact with camera, warm genuine smile, slightly tilted head,
natural daylight, soft catchlight in eyes, warm skin tones,
close-up face and shoulders, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

#### S05-2: CTA 特写 (自然)

```
Warm intimate fashion portrait, a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing cream white ribbed knit sweater, natural minimal makeup,
in a bright modern cafe, soft blurred background,
looking at camera with relaxed natural expression, slight laugh lines visible,
natural daylight, soft catchlight in eyes, warm tones,
close-up face and shoulders, 85mm portrait lens, shallow depth of field, vertical composition 9:16
```

---

## 3. Stage 3: Kling 视频生成

| 段落 | 参考图 | 运动提示 | 运动强度 | 候选数 |
|------|--------|---------|---------|--------|
| S01 | S01-1 + S01-2 (剪映分屏) | `gentle sway, fashion lookbook style, bright lighting` | 4/10 | 2 |
| S02 | S02-1 或 S02-2 (选最佳) | `slow turn, detail showcase, bright studio lighting` | 4/10 | 2 |
| S03 | S03-1 或 S03-2 (选最佳) | `slow turn, detail showcase, bright studio lighting` | 4/10 | 2 |
| S04 | 无 (文字卡) | FFmpeg/剪映生成 | - | - |
| S05 | S05-1 或 S05-2 (选最佳) | `warm smile, direct eye contact, gentle movement` | 3/10 | 2 |

- Kling 参数: 720x1280, 5s/段, fixed seed (12345)
- 后处理: Retime→Trim, Handheld Shake 5%, 4K Upscale 最终选中片段

---

## 4. Stage 4: Suno 对唱音频

- 模型: Suno v4.5 (via Evolink API)
- 模式: custom_mode=true
- 风格 tags: `catchy mid-tempo pop, male female duet, playful melody, bouncy rhythm, sing-song storytelling, cute, fashion, TikTok viral Chinese pop, light electronic beat, xylophone, whistle, 130 bpm`
- 负面 tags: `rap, hip hop, EDM, aggressive, heavy metal, slow ballad, sad, dramatic, rock, dark, moody`
- 候选: ≥ 2 版本
- 后处理: librosa 提取 beats.json

---

## 5. Stage 5-6: 合成 + 去 AI 化

### FFmpeg 合成
- 拼接 S01-S05 视频段
- 合并 Suno 对唱音频

### 剪映后期
- A/B 分屏 (S01)
- 穿搭标签 "A" / "B" (S02/S03)
- 歌词字幕 KTV 风格
- 投票提示 "A / B" (S05)
- 音频裁剪 (90-130s → 30-45s)
- 封面帧制作

### 去 AI 4 步法
1. 胶片颗粒: 0-5%
2. 柔光: 5%
3. 色彩校正: 饱和度+5~+10, 对比度+5, 色温暖白, 锐度-2~-3
4. 手持抖动: 3%

---

## 6. Stage 7: 最终审核门控

按 spec 7 个门控: 时长(30-45s), 节奏(节拍同步), 技术质量, A/B对比, 穿搭法则, CTA投票, 去AI验证, AI标识。
