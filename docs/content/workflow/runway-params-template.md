# Runway Gen-4 图生视频参数模板

> 适用于 Runway Gen-4 / Gen-4 Turbo Image to Video
> Gen-4 必须上传参考图，提示词只写运动描述
> 最后更新：2026-04-17

---

## 全局参数

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| Model | Gen-4 Turbo | 迭代阶段用（5 credits/s，速度快 2.5x） |
| Model | Gen-4 | 最终输出用（12 credits/s，质量更高） |
| Duration | 5s | 大多数镜头 |
| Duration | 10s | 需要复杂运动的镜头（慎用，翻车概率更高） |
| Resolution | 9:16 — 720x1280 | 抖音/小红书竖版原生 |
| Fixed Seed | 开启 | 选定一个 seed 保持全片风格一致 |
| FPS | 24fps | Gen-4 固定输出 |

### 推荐流程

1. **Gen-4 Turbo 迭代**：每个镜头生成 3-5 个候选，选最佳（成本低，速度快）
2. **Gen-4 最终生成**：用选好的参考图 + 参数，Gen-4 重新生成（质量最高）
3. **4K Upscale**：最终选中的片段一键升到 4K
4. **Retime**：调整速度 + 添加内置手持抖动

---

## 分辨率选择

| 格式 | 比例 | 像素 | 用途 |
|------|------|------|------|
| 竖版 | 9:16 | 720x1280 | 抖音/小红书（**默认用这个**） |
| 横版 | 16:9 | 1280x720 | B站/YouTube |
| 方形 | 1:1 | 960x960 | Instagram |
| 竖版肖像 | 3:4 | 832x1104 | 小红书图文 |

---

## 提示词规则（Gen-4）

### 核心原则：只写运动，不写画面

参考图已经定义了画面内容（主体、构图、色调、光影）。提示词只需描述**运动**。

**好的提示词：**
```
slow zoom in on the golden numbers, subtle particle movement
```

**坏的提示词：**
```
a dramatic cinematic scene with golden numbers floating in a dark space with volumetric lighting and particles and lens flare...
```

### 提示词模板

| 镜头类型 | 提示词 |
|---------|--------|
| 数据展示 | `slow zoom in, numbers glowing subtly` |
| 人物场景 | `subtle head movement, natural breathing, ambient light shift` |
| 环境展示 | `slow pan left, leaves swaying gently, ambient atmosphere` |
| 对比画面 | `slow zoom out, revealing the scale contrast` |
| 高潮数字 | `dramatic zoom in, numbers pulsing with energy` |
| 文字卡片 | `gentle fade in, slight parallax on text elements` |

### 提示词增强技巧

- 加 `cinematic motion` 增加电影感
- 加 `smooth camera movement` 避免抖动
- 加 `shallow depth of field` 保持景深
- 不要写超过 2 句话
- 不要描述画面中已经有的内容

---

## Day 1 各镜头参数

| 镜头 | Duration | Resolution | Fixed Seed | Prompt |
|------|----------|-----------|------------|--------|
| S01 数字浮现 | 5s | 9:16 | ✅ | slow zoom in on golden numbers, subtle glow pulsing, cinematic motion |
| S02 空办公室 | 5s | 9:16 | ✅ | slow pan right across empty office, single lamp flickering slightly, cinematic |
| S03 拖车公园 | 5s | 9:16 | ✅ | slow push in, warm golden hour light shifting, subtle wind movement |
| S04 编程场景 | 5s | 9:16 | ✅ | subtle screen glow changing, focused stillness, cinematic mood |
| S05 数据展示 | 5s | 9:16 | ✅ | slow zoom in, data numbers appearing sequentially, golden glow |
| S06 公司对比 | 5s | 9:16 | ✅ | slow pan right revealing office scale, cinematic contrast |
| S07 利润率对比 | 5s | 9:16 | ✅ | slow zoom in on comparison bars, subtle animation, minimal movement |
| S08 工具展示 | 录屏 | — | — | 用真实截图，不需 Runway |
| S09 日营收 | 5s | 9:16 | ✅ | dramatic zoom out revealing revenue number, rising energy |
| S10 转化 | 5s | 9:16 | ✅ | gentle fade in, clean text appearing, warm cinematic |

---

## Retime 后处理（生成后）

对选中的片段用 Runway Retime 工具：

| 操作 | 说明 |
|------|------|
| Trim | 裁掉开头/结尾不稳定的帧 |
| Speed | 调整速度（0.8x-1.2x） |
| Handheld Shake | **强度 10-15%**，模拟手持拍摄（替代剪映手动加） |
| Reverse | 特殊效果用 |

> Retime 不消耗 credits，可以反复调整。

---

## 质量检查

生成后检查每个片段：

- [ ] 无人物变形（手指、脸、肢体）
- [ ] 无文字乱码（AI 生成的文字通常不对，后期加字幕覆盖）
- [ ] 运动流畅不卡顿
- [ ] 色调与参考图一致
- [ ] 无明显 AI 痕迹（塑料感、过度光滑、完美对称）
- [ ] Fixed Seed 保持全片风格一致
