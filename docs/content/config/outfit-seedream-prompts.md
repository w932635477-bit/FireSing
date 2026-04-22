# 穿搭对比 Seedream Prompt 模板 v2.0

> 适用：小红书 Sings 穿搭对比视频的参考图生成
> 引擎：Seedream 4.5 (Evolink API)
> 框架：The Fabricant 7 元素时尚 Prompt 结构
> 最后更新：2026-04-22

---

## 7 元素 Prompt 结构

基于 The Fabricant（AI 时尚先锋）的 7 元素框架，适配 Seedream 4.5：

```
[1. 美学与氛围]  — 整体调性（lookbook, editorial, candid）
[2. 人物与姿势]  — 角色锚定 + 肢体语言 + 凝视方向
[3. 服装与造型]  — 面料+颜色+版型+配件（最详细的部分）
[4. 环境与背景]  — 场景空间 + 颜色/纹理
[5. 光线]        — 光源类型 + 方向 + 色温
[6. 相机与技术]  — 相机型号 + 镜头 + 光圈 + 焦距
[7. 色调与品质]  — 胶片模拟 + 质感关键词 + 构图
```

---

## 角色锚定（每条 prompt 的 [2. 人物] 部分）

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
```

---

## 完整 Prompt 模板

### 穿搭全身照（S02/S03 用）

```
[1. A clean lookbook style photograph]
[2. 角色锚定,
    [姿势: standing with arms relaxed at sides / one hand in pocket / arms crossed etc.],
    [凝视: looking slightly off-camera / direct gaze with gentle smile etc.],]
[3. wearing [服装: 面料+颜色+版型+剪裁细节+配件],
    [配件细节: delicate gold necklace / leather watch / small stud earrings etc.],]
[4. [场景: standing in a bright modern office lobby with floor-to-ceiling windows / etc.],]
[5. soft natural daylight from the left, bright and airy atmosphere, no harsh shadows,]
[6. shot on Nikon D850 with 85mm f/2.8 prime lens, slightly below eye level,]
[7. natural skin texture, visible pores, fine hair strands, Kodak Portra 400 film simulation,
    fashion lookbook style, sharp details, vertical composition 9:16]
```

### 穿搭中景特写（展示服装细节）

```
[1. A detailed fashion editorial photograph]
[2. 角色锚定,
    [姿势: mid-body shot, slight turn to show garment drape],
    gentle confident expression,]
[3. wearing [服装: 面料纹理+颜色+版型+具体剪裁如single-breasted/ribbed/structured等],]
[4. [场景: clean background with subtle texture, cream white walls],]
[5. diffused soft box lighting from 45 degrees, wrapping around subject evenly,]
[6. shot on Phase One XF with 85mm lens, shallow depth of field, f/2.8,]
[7. natural skin texture, visible noise, Kodak Portra 400 colors,
    editorial quality, vertical composition 9:16]
```

### CTA 特写镜头（S05 用）

```
[1. An intimate, warm portrait photograph]
[2. 角色锚定,
    looking directly at camera with warm inviting smile,
    close-up from chest up,]
[3. wearing [该期推荐的穿搭简述],]
[4. bright cream-colored seamless paper background, no distractions,]
[5. soft diffused beauty lighting, even illumination, warm tone,]
[6. shot on Hasselblad H6D with 100mm lens, f/4, eye-level,]
[7. natural skin texture, visible noise, Kodak Portra 400 film simulation,
    fashion lookbook style, vertical composition 9:16]
```

---

## 面料/纹理词库

Prompt [3. 服装] 部分必须使用具体的面料和纹理词汇：

| 类别 | 英文关键词 | 中文含义 |
|------|-----------|---------|
| 梭织 | tailored, structured, single-breasted, double-breasted | 剪裁合身，单/双排扣 |
| 针织 | ribbed texture, cable knit, fine gauge, chunky knit | 罗纹纹理，绞花，细针距，粗针织 |
| 面料 | cotton, linen, silk, wool, cashmere, denim, tweed | 棉，亚麻，丝，羊毛，羊绒，牛仔，粗花呢 |
| 版型 | slim-fit, relaxed-fit, oversized, form-fitting, A-line | 修身，宽松，超大号，贴身，A字 |
| 垂坠 | flowing, draped, structured, crisp, soft drape | 飘逸，垂褶，挺括，利落，柔垂 |
| 裤型 | straight-leg, wide-leg, tapered, cropped, high-waisted | 直筒，阔腿，锥形，九分，高腰 |
| 质感 | matte, glossy, sheer, opaque, textured, smooth | 哑光，光泽，半透，不透，纹理，光滑 |

---

## 相机参数对照表

Prompt [6. 相机] 部分根据镜头类型选择：

| 镜头类型 | 相机+镜头 | 光圈 | 用途 |
|---------|----------|------|------|
| 全身 lookbook | Nikon D850, 35mm f/2.8 | f/4 | 展示完整穿搭 |
| 半身 editorial | Phase One XF, 85mm | f/2.8 | 服装细节+人物 |
| 特写 portrait | Hasselblad H6D, 100mm | f/4 | CTA 面部特写 |
| 街拍风格 | Leica M11, 50mm Summilux | f/2 | 通勤/户外场景 |

---

## 光线模板

Prompt [5. 光线] 部分根据场景选择：

| 场景类型 | 光线描述 |
|---------|---------|
| 室内办公 | soft natural daylight from large windows, bright and airy, no harsh shadows |
| 室内简约 | diffused soft box lighting from 45 degrees, wrapping around subject evenly |
| 室内温暖 | warm ambient lighting with gentle fill, golden undertones |
| 户外自然 | soft overcast daylight, even illumination, no direct sun |
| 户外黄金 | golden hour side lighting, warm tones, long soft shadows |

---

## 负面 Prompt

```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain,
wrinkled clothing, unnatural fabric folds, distorted patterns, unrealistic texture,
deformed, bad anatomy, disfigured, poorly drawn face, extra limb, ugly,
poorly drawn hands, missing limb, floating limbs, disconnected limbs,
malformed hands, blur, out of focus, long neck, long body, lowres
```

---

## 场景库

| 场景 | [4. 环境] 描述 |
|------|---------------|
| 面试/办公 | bright modern office lobby with floor-to-ceiling windows, cream white walls |
| 入职 | open-plan office with warm wood accents, large windows, natural light |
| 约会 | cozy restaurant corner booth, warm pendant lighting, soft bokeh background |
| 闺蜜聚会 | bright minimalist cafe with green plants, white marble table, large windows |
| 通勤 | city sidewalk in soft morning light, blurred pedestrians, modern buildings |
| 户外/公园 | open grassy area with dappled sunlight through large trees |
| 商场购物 | modern shopping atrium, glass ceiling, clean white floors, natural light |
| 居家 | bright living room, white walls, large window, minimal furniture |
| 晚宴 | elegant restaurant interior, soft candlelight, dark wood accents |
| 运动健身 | bright gym with large mirrors, natural light, clean modern equipment |

---

## 注意事项

- 每条 prompt 必须包含完整的 7 元素，不可省略
- [3. 服装] 是最重要的元素，必须具体到面料、纹理、版型（不是"深蓝西装"，而是"well-fitted navy blue blazer with structured shoulders, single-breasted two-button closure, woven wool blend"）
- 背景必须明亮（bright, airy, natural daylight），不要暗色调
- 同一集 A/B 两套 prompt 只改 [2. 姿势] 和 [3. 服装]，其他元素保持一致
- 避免手部特写（AI 手部常见问题），用 mid-body 或 chest-up 景别
- 相机参数对 Seedream 不一定生效，但能引导模型理解"专业时尚摄影"的意图

---

## 修订记录

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-04-22 | 1.0 | 初始版本（6 层结构） |
| 2026-04-22 | 2.0 | 全面升级为 The Fabricant 7 元素框架，增加面料词库+相机参数+光线模板+场景库 |
