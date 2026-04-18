# Day 1 参考图提示词（Gen-4 优化版）

> Midjourney 提示词，统一风格：电影感 / 深色调 / 纪录片
> **已优化为 9:16 竖版**（匹配 Runway Gen-4 原生输出）
> 视频优先设计：构图考虑运动空间，避免边缘裁剪
> 全部使用 --ar 9:16 --style raw --s 250 --v 6.1

---

## 提示词优化要点

| 优化 | 原因 |
|------|------|
| 9:16 竖版构图 | Runway Gen-4 原生支持 9:16，避免裁剪损失 |
| 主体居中偏下 | 留出上方空间给运动（zoom in）和字幕 |
| 避免边缘元素 | Runway 生成时边缘可能变形 |
| 加入光影层次 | AI 视频质量 = 参考图光影质量 |
| 控制复杂度 | 画面越简洁，视频生成越稳定 |

---

## S01: 数字浮现（3-4s）

**候选 1：**
```
giant golden numbers 401000000 glowing in center of dark void, financial data visualization, dramatic top-down amber light, deep navy black background, warm gold accent, ultra realistic, shallow depth of field, numbers positioned in lower two-thirds of frame --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
holographic golden financial numbers floating in darkness, matrix-like data stream falling downward, amber gold light particles centered, dark void background, cinematic depth, numbers in lower center frame --ar 9:16 --style raw --s 250 --v 6.1
```

## S02: 空办公室（2-3s）

**候选 1：**
```
empty modern startup office at night viewed from above, only two desks with monitors visible in center, single warm desk lamp glow, deep dark shadows surrounding, lonely atmosphere, overhead shot, cinematic, minimal --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
aerial view of dark open plan office, two lit workstations in vast empty space, contrast between warm light and cold darkness, documentary photography, minimalist composition --ar 9:16 --style raw --s 250 --v 6.1
```

## S03: 拖车公园（4-5s）

**候选 1：**
```
american suburban trailer park at golden hour, warm sunset light, young man sitting outside on steps with laptop, centered composition, intimate documentary moment, 35mm film grain, warm amber tones --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
mobile home community evening scene, warm amber lighting from window, silhouette of person visible through window working on computer, nostalgic warm atmosphere, terrence malick cinematography style, centered subject --ar 9:16 --style raw --s 250 --v 6.1
```

## S04: 编程场景（3s）

**候选 1：**
```
close up of hands typing on macbook keyboard in dark room centered in frame, code on screen reflecting soft blue and amber glow on face, focused concentration, shallow depth of field, moody atmosphere --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
over-the-shoulder shot of programmer at night, single monitor showing code in dark room, warm coffee cup on desk, only screen illumination, atmospheric tech startup aesthetic, centered composition --ar 9:16 --style raw --s 250 --v 6.1
```

## S05: 数据展示（5-6s）

**候选 1：**
```
financial dashboard on dark screen centered in frame, large gold numbers $401M prominently displayed, revenue chart rising upward, minimalist data visualization, dark background, premium business aesthetic, vertical layout --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
abstract financial data visualization, floating golden numbers $401000000 and rising graphs centered, dark void environment, subtle particle effects, premium corporate presentation style, vertical composition --ar 9:16 --style raw --s 250 --v 6.1
```

## S06: 公司对比（4-5s）

**候选 1：**
```
vertical split composition, top half small intimate office with two people at desks, bottom half massive corporate open floor with rows of desks, dramatic contrast in scale, warm vs cold lighting, cinematic aerial perspective --ar 9:16 --style raw --s 250 --v 6.1
```

**候选 2：**
```
tiny startup team of two in warm-lit garage space top of frame, massive corporate office floor with hundreds of cold-lit desks bottom of frame, visual scale contrast, documentary photography style --ar 9:16 --style raw --s 250 --v 6.1
```

## S07: 利润率对比（3s）

**候选 1：**
```
minimal data comparison bars on dark background centered, tall gold bar labeled 16.2% next to short gray bar labeled 5.5%, clean geometric design, premium financial aesthetic, dark slate background, vertical bar chart layout --ar 9:16 --style raw --s 250 --v 6.1
```

## S08: AI 工具展示（5-7s）

用实际工具截图代替 AI 生成图（更真实可信），不需要参考图提示词。

**改为：截屏拼接**
- ChatGPT 界面截图（深色模式）
- Claude 界面截图（深色模式）
- Midjourney 生成过程截图
- AI 客服对话截图

> 这一段用真实界面比 AI 生成更有说服力。截图用 Canva 排版成 9:16 竖版拼贴。

## S09: 日营收（3s）

**候选 1：**
```
dramatic revenue counter showing $3000000 per day in large golden LED numbers centered in frame, dark environment, rising line chart in background, financial news aesthetic, amber glow emanating from numbers --ar 9:16 --style raw --s 250 --v 6.1
```

## S10: 转化卡片（5-7s）

用 Canva 制作文字卡片，不需要 AI 生成图。

设计要素：
- 黑色背景（#000000）
- 金色文字「私信回复 AI获客」（#c9a96e）
- 简洁的抖音/小红书图标
- 9:16 竖版

---

## 统一风格检查清单

- [ ] 所有图片色调：深色背景 + 暖金点缀
- [ ] 所有图片构图：9:16 竖版，主体居中偏下
- [ ] 人物场景：自然光，不做作
- [ ] 数据场景：极简设计，不要花哨
- [ ] 边缘干净无重要元素（避免 Runway 变形）
- [ ] 每张图都能单独作为"电影截图"看

---

## Midjourney → Runway 最佳实践

1. **生成 4 张候选**，选构图最干净、光影最立体的 1 张
2. **避免选择**：边缘有人/物的图、文字太多的图、过于对称的图
3. **在 Runway 里**：参考图是第一帧，所以构图必须考虑运动方向
4. **Zoom in 场景**：主体放中下，上方留空间
5. **Pan 场景**：主体偏一侧，另一侧留空间给平移
