# 黑屏问题修复设计

> 日期：2026-05-04
> 状态：已批准，待实施
> 问题：v3 视频 48.6s 黑屏（画面总时长 55.5s vs 配音 104.1s）
> 约束：不做循环播放，用 Unsplash 新素材补充画面时长

---

## 问题根因

storyboard 中每个 clip 的 `duration` 硬编码值总和远小于配音时长：

| 段落 | 配音 | 当前画面 | 缺口 |
|------|------|---------|------|
| S01 | 16.7s | 10.0s | 6.7s |
| S02 | 34.1s | 17.0s | 17.1s |
| S03 | 38.5s | 17.0s | 21.5s |
| S04 | 14.8s | 11.5s | 3.3s |
| S05 | 4.8s | 7.0s | OK |
| **合计** | **104.1s** | **55.5s** | **48.6s** |

compose.py 的黑屏填充逻辑补了差额，导致近一半视频是黑屏。

## 修复方案：4 个改动

### 1. 新增 unsplash-download.py

独立脚本，读取 config JSON 的 `atmosphere` 数组，自动下载缺失图片。

- 输入：`--config config/xxx.json`
- API Key 从 `docs/content/.env` 读取（`UNSPLASH_ACCESS_KEY`）
- 下载到 `assets/unsplash/{video_id}/` 目录
- 幂等：已存在则跳过
- 调 Unsplash `/search/photos` API，用 `query` 字段搜索，取第一张 regular 尺寸

### 2. config JSON 扩展 atmosphere（+6 张新图）

```json
"atmosphere": [
  {"id": "AT01", "query": "empty warehouse industrial golden light", "output": "AT01-warehouse.jpg"},
  {"id": "AT02", "query": "desk lamp night workspace coffee phone", "output": "AT02-desk-night.jpg"},
  {"id": "AT03", "query": "building materials market tiles samples", "output": "AT03-market.jpg"},
  {"id": "AT04", "query": "coffee shop window phone typing natural light", "output": "AT04-coffee-shop.jpg"},
  {"id": "AT05", "query": "resume papers scattered on desk", "output": "AT05-resume-papers.jpg"},
  {"id": "AT06", "query": "empty office corridor fluorescent light", "output": "AT06-empty-office.jpg"},
  {"id": "AT07", "query": "man walking alone city street night", "output": "AT07-lonely-walk.jpg"},
  {"id": "AT08", "query": "smartphone screen glow dark room", "output": "AT08-phone-glow.jpg"},
  {"id": "AT09", "query": "tiles samples building materials showroom", "output": "AT09-tiles-showroom.jpg"},
  {"id": "AT10", "query": "sunrise through window hope morning", "output": "AT10-sunrise-hope.jpg"}
]
```

### 3. config JSON 重算 storyboard duration

每个 segment 的 clips 总时长 ≈ 配音时长：

- S01 (16.7s)：SS01(3.5) + video(5.5) + AT05-zoom(5.0) + TC01(3.0) = 17.0s
- S02 (34.1s)：video(8.0) + AT01-zoom(6.0) + AT06-zoom(6.0) + SS02(4.0) + AT07-zoom(6.0) + TC02(4.0) = 34.0s
- S03 (38.5s)：SS03(3.5) + AT02-zoom(7.0) + video(8.0) + AT08-zoom(6.0) + AT09-zoom(6.0) + AT03-zoom(5.0) + AT10-zoom(3.5) = 39.0s
- S04 (14.8s)：SS04(3.5) + video(7.5) + TC03(3.8) = 14.8s
- S05 (4.8s)：AT04(3.0) + video(2.0) = 5.0s

### 4. compose.py 删除黑屏填充

- 移除 `build_segment_clips()` 中的 black padding 逻辑
- 如果仍有微小缺口（<1s），冻结最后一帧而非纯黑

## 文件清单

| 文件 | 操作 |
|------|------|
| `docs/content/scripts/unsplash-download.py` | 新建 |
| `docs/content/config/unemploy-story-04-zhangwei-v3.json` | 修改 |
| `docs/content/scripts/medvi-compose.py` | 修改 |
