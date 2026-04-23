# Day 8 Yangmun: "不合群才是你的超能力" Design

## 选题定位

- **video_id**: day8-yangmun
- **主题**: 不合群才是你的超能力
- **策略**: yangmun-emotion-ip, 铁律三段式, 流量优先
- **情绪弧线**: shock → tension → reversal → empowerment → participation
- **与 Day 4-7 关系**: 零主题重叠（效率/逆袭/坚持/努力→不合群）

## 选题评分: 88-90/100

- Hook 个人化（"你装合群"起手）
- 马斯克原话已确认（"我的童年非常孤独"）
- 粘性细节（"推下楼梯打到住院"）
- 每段"你"起手，观众代入快
- CTA 可参与（"最不合群的那件事"）

## 配音文案 (V3 终稿)

### S01 Hook (7s) — shock

> 你装合群，装了多少年？马斯克说过：我的童年非常孤独。他小学被推下楼梯打到住院。但不合群的人，看到的和你不一样。

- 字幕: "你装合群 装了多少年？"
- story_images: 被推下楼梯的场景 + 不合群的人看到的世界

### S02 铁律一 (10s) — tension

> 铁律一：你为了合群放弃了什么。马斯克从来不合群，他把别人社交的时间全用在了思考上。而你呢？笑脸、应酬、群聊、陪笑。换来一张好人卡，丢掉了你唯一的优势。

- 字幕: "铁律一：你为了合群放弃了什么"
- story_images: 社交场景 + 被消耗的自己

### S03 铁律二 (9s) — reversal

> 铁律二：孤独的人看到别人看不到的。2018年特斯拉差点破产，所有分析师都说他完了。但他看到的是燃油车的终局。不是他更聪明，是他不用同意人群的结论。

- 字幕: "铁律二：孤独的人看到别人看不到的"
- story_images: 2018特斯拉破产危机 + 燃油车终局

### S04 铁律三 (10s) — empowerment

> 铁律三：世界是被不合群的人改变的。乔布斯被自己公司赶走，回来做了iPhone。马斯克被嘲笑20年，公司值万亿。你不敢不合群，不是你弱，是你还没找到值得你坚持的那件事。

- 字幕: "铁律三：世界是被不合群的人改变的"
- story_images: 乔布斯被赶走 + 马斯克被嘲笑

### S05 CTA (5s) — warm

> 杨梦问你：评论区打出你最不合群的那件事。不合群，不是你的错，是你的开始。

- 字幕: "不合群不是你的错 是你的开始"

## 总时长: 41s

在 30-50s 目标区间内，与 Day 7 结构一致。

## Config JSON

完整 config 将在实现计划中生成，关键参数:

- character_anchor: 杨梦（短发波波头，米白亚麻衫）
- voiceover: doubao_tts, claire, shock emotion
- reference_images: seedream_4.5, evolink
- video_generation: kling_v3, image_to_video
- style: yangmun_minimalist_portrait
- color_temperature: warm
- accent_color: #c9a96e
