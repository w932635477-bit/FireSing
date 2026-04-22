# 穿搭对比 Seedream Prompt 模板

> 适用：小红书 Sings 穿搭对比视频的参考图生成
> 引擎：Seedream 4.5 (Evolink API)
> 最后更新：2026-04-22

## 基础角色锚定（每条 prompt 必须包含）

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
```

## Prompt 结构（6 层）

```
[1. 角色锚定], [2. 服装描述], [3. 场景/背景], [4. 姿势], [5. 光影],
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16
```

## 穿搭 A 套模板

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing [A套服装: 面料+颜色+版型+配件],
[场景: bright modern office lobby / cozy cafe / city street etc.],
[姿势: confident posture / relaxed stance / walking etc.],
soft natural daylight from the left, cream white walls, bright airy atmosphere,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16
```

## 穿搭 B 套模板

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
wearing [B套服装: 面料+颜色+版型+配件],
[同一场景],
[不同姿势],
soft natural daylight from the left, cream white walls, bright airy atmosphere,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16
```

## CTA 镜头模板

```
Candid photograph of a young Chinese woman, mid-twenties, warm complexion,
subtle freckles, shoulder-length black hair with soft waves, wearing minimal jewelry,
natural makeup, warm and approachable expression, shot on Kodak Portra 400,
natural skin texture, visible pores, fine hair strands, slight asymmetry,
authentic beauty, NOT perfect, NOT retouched,
looking directly at camera with warm inviting smile,
wearing [该期推荐的穿搭],
bright cream-colored background, soft diffused lighting,
close-up from chest up,
natural skin texture, visible noise, fashion lookbook style,
vertical composition 9:16
```

## 负面 Prompt

```
airbrushed, smooth plastic skin, perfect symmetry, HDR, overprocessed,
studio lighting, stock photo, 3D render, illustration, cartoon, anime,
watermark, text, logo, oversaturated, mannequin, flawless, magazine cover,
retouched, poreless skin, dark, moody, cinematic, film grain
```

## 场景库

| 场景 | 背景描述 |
|------|---------|
| 面试/办公 | bright modern office lobby with floor-to-ceiling windows |
| 约会 | cozy restaurant with warm pendant lighting, evening |
| 闺蜜聚会 | bright minimalist cafe with green plants |
| 通勤 | city street in soft morning light, blurred pedestrians |
| 户外/公园 | open park with dappled sunlight through trees |
| 商场购物 | modern shopping mall, glass ceiling, natural light |
| 居家 | bright living room with large windows, white walls |

## 注意事项

- 每条 prompt 必须包含完整的角色锚定段落
- 穿搭描述要具体到面料和版型（ribbed texture, slim-fit, oversized 等）
- 背景必须明亮（bright, airy, natural daylight），不要暗色调
- 同一集 A/B 两套 prompt 只改服装和姿势，角色锚定和背景保持一致
- 避免手部特写（AI 手部常见问题），用 mid-body 或 chest-up 景别
