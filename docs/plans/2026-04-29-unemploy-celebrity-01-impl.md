# unemploy-celebrity-01 任正非 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 生产失业名人堂第1条视频——任正非43岁至暗时刻 × AI失业潮

**Architecture:** Medvi管线（Gemini TTS Charon + Seedream氛围空镜 + Kling视频 + FFmpeg粗剪 + 剪映后期）。Config-driven，复用现有脚本。

**Tech Stack:** Python, Gemini API, Seedream 4.5 (Evolink), Kling 3.0 (Evolink), FFmpeg

---

### Task 1: 创建 Config JSON

**Files:**
- Create: `docs/content/config/unemploy-celebrity-01.json`

**Step 1: 创建 config 文件**

```json
{
  "video_id": "unemploy-celebrity-01",
  "version": "2.0",
  "created": "2026-04-29",
  "status": "config_ready",
  "strategy": "unemployment-celebrity",
  "strategy_notes": "失业名人堂第1条：任正非43岁至暗时刻×AI失业潮。名人真实失败细节+AI失业现实+两派对立观点。氛围空镜+文字卡片+Charon男声旁白。",
  "review": {
    "score": 90,
    "dimensions": {
      "narrative": 23,
      "emotional_resonance": 23,
      "controversy_design": 18,
      "ai_connection": 13,
      "copy_quality": 13
    },
    "status": "pass"
  },
  "global": {
    "target_duration_sec": 100,
    "max_duration_sec": 180,
    "resolution": "1080x1920",
    "fps": 24,
    "codec": "h264",
    "aspect_ratio": "9:16",
    "workflow_version": "2.0",
    "style": "celebrity_atmosphere",
    "color_temperature": "cool_to_warm_shift",
    "accent_color": "#ffffff"
  },
  "script": {
    "topic": "任正非43岁被骗200万被开除离婚住棚屋，后来做了华为7000亿",
    "hook_type": "flashback_bomb",
    "cta_action": "评论站队",
    "cta_keyword": "你站哪边",
    "anti_ad_measures": [
      "不提AI Agent、代运营、智能体等业务关键词",
      "不引导私信、领取、关注",
      "CTA用开放式问题，激发评论互动",
      "绝不说'名人能行你也能'",
      "永远呈现两派观点，让观众吵架"
    ]
  },
  "character_anchor": null,
  "screenshots": [],
  "atmosphere_shots": [
    {
      "id": "AT01",
      "scene": "深圳夜景华为总部",
      "reference_prompt": "iPhone 15 snapshot, nighttime city skyline with a cluster of illuminated glass skyscrapers, blue-white light reflecting off glass facades, wet ground reflecting lights after rain, no people visible, no text, casual framing slightly off-center, untouched, vertical 9:16",
      "motion_prompt": "slow camera drift along the skyline, lights twinkle gently",
      "output_file": "unemploy-celebrity-01/AT01-shenzhen-night.png",
      "video_file": "unemploy-celebrity-01/AT01-shenzhen-night.mp4",
      "reference_file": "unemploy-celebrity-01/AT01-shenzhen-night.png",
      "segment": "S01"
    },
    {
      "id": "AT02",
      "scene": "深夜棚屋内部",
      "reference_prompt": "iPhone 15 snapshot, interior of a cramped shack at night, single bare yellow lightbulb hanging from corrugated metal ceiling, peeling walls stained with water damage, a folding table with scattered papers and cigarette butts, rainwater dripping from ceiling crack into a metal basin on floor, cramped humid atmosphere, no people visible, no text, casual framing, untouched, vertical 9:16",
      "motion_prompt": "rainwater drips steadily into basin, lightbulb sways gently, slow camera push inward",
      "output_file": "unemploy-celebrity-01/AT02-shack-interior.png",
      "video_file": "unemploy-celebrity-01/AT02-shack-interior.mp4",
      "reference_file": "unemploy-celebrity-01/AT02-shack-interior.png",
      "segment": "S02"
    },
    {
      "id": "AT03",
      "scene": "凌晨空办公室",
      "reference_prompt": "iPhone 15 snapshot, empty small office at 4am, single old CRT monitor glowing on a desk, instant noodle cup and full ashtray beside it, an old jacket draped over chair back, window shows sky transitioning from black to gray dawn light, lonely but persistent atmosphere, no people visible, no text, casual framing, untouched, vertical 9:16",
      "motion_prompt": "monitor screen flickers, dawn light slowly brightens through window, jacket sways slightly",
      "output_file": "unemploy-celebrity-01/AT03-dawn-office.png",
      "video_file": "unemploy-celebrity-01/AT03-dawn-office.mp4",
      "reference_file": "unemploy-celebrity-01/AT03-dawn-office.png",
      "segment": "S03"
    },
    {
      "id": "AT04",
      "scene": "现代办公室空工位",
      "reference_prompt": "iPhone 15 snapshot, modern open-plan office with rows of desks, most desks cleared out, a few monitors still on but chairs pushed aside, abandoned coffee mug on one desk, fluorescent overhead lights harsh and clinical, eerie abandoned feeling, no people visible, no text, casual framing, untouched, vertical 9:16",
      "motion_prompt": "slow horizontal pan across empty desks, one monitor flickers, fluorescent light hums",
      "output_file": "unemploy-celebrity-01/AT04-empty-modern-office.png",
      "video_file": "unemploy-celebrity-01/AT04-empty-modern-office.mp4",
      "reference_file": "unemploy-celebrity-01/AT04-empty-modern-office.png",
      "segment": "S04"
    },
    {
      "id": "AT05",
      "scene": "城市天台黄昏分裂",
      "reference_prompt": "iPhone 15 snapshot, rooftop view at dusk, left side shows modern glass office towers lit up brightly, right side shows old residential buildings with dark windows, golden hour light creating strong contrast between the two halves, divided cityscape, no people visible, no text, casual framing, untouched, vertical 9:16",
      "motion_prompt": "golden light slowly fading, office lights brighten on left while residential windows stay dark on right",
      "output_file": "unemploy-celebrity-01/AT05-rooftop-dusk-split.png",
      "video_file": "unemploy-celebrity-01/AT05-rooftop-dusk-split.mp4",
      "reference_file": "unemploy-celebrity-01/AT05-rooftop-dusk-split.png",
      "segment": "S05"
    },
    {
      "id": "AT06",
      "scene": "天台夜幕城市灯光",
      "reference_prompt": "iPhone 15 snapshot, same rooftop now at full night, city lights gradually turning on across the skyline, neon signs glowing in the distance, darkness in foreground with city illumination behind, contemplative open-ended atmosphere, no people visible, no text, casual framing, untouched, vertical 9:16",
      "motion_prompt": "city lights slowly brighten across the skyline, neon signs pulse gently, camera holds still",
      "output_file": "unemploy-celebrity-01/AT06-rooftop-night.png",
      "video_file": "unemploy-celebrity-01/AT06-rooftop-night.mp4",
      "reference_file": "unemploy-celebrity-01/AT06-rooftop-night.png",
      "segment": "S06"
    }
  ],
  "segments": [
    {
      "id": "S01",
      "type": "hook",
      "duration_sec": 20,
      "emotion_arc": "好奇",
      "subtitle_text": "华为营收8600亿 但他43岁被骗200万",
      "voiceover_text": "二零二四年，华为营收八千六百亿。全球十七万员工，一百七十个国家的订单源源不断。但一九八七年，这个男人四十三岁。他刚被国企开除。被骗走两百万。老婆签了离婚协议。父母弟妹六口人，挤在深圳一间棚屋里，夏天像蒸笼，雨天漏水。四十三岁。没有工作。没有存款。没有老婆。一家老小等着吃饭。那个站在楼顶往下看的人，和今天华为总部里那个掌舵的人，是同一个人。",
      "voiceover_pause_markers": "二零二四年<#0.3#>华为营收八千六百亿。<#0.8#>全球十七万员工<#0.2#>一百七十个国家的订单源源不断。<#1.0#>但一九八七年<#0.5#>这个男人四十三岁。<#0.8#>他刚被国企开除。<#0.3#>被骗走两百万。<#0.3#>老婆签了离婚协议。<#0.5#>父母弟妹六口人<#0.2#>挤在深圳一间棚屋里<#0.2#>夏天像蒸笼<#0.2#>雨天漏水。<#0.8#>四十三岁。<#0.3#>没有工作。<#0.3#>没有存款。<#0.3#>没有老婆。<#0.5#>一家老小等着吃饭。<#1.0#>那个站在楼顶往下看的人<#0.5#>和今天华为总部里那个掌舵的人<#0.5#>是同一个人。",
      "director_notes": "平静开场，像念数据一样报8600亿。到'但一九八七年'突然放慢。'四十三岁。没有工作。没有存款。没有老婆。'每个短句之间有停顿，节奏像心跳。最后一句是全篇第一个钩子，说完后留一秒空白。"
    },
    {
      "id": "S02",
      "type": "body",
      "duration_sec": 30,
      "emotion_arc": "压抑",
      "subtitle_text": "两万一千块起步 六口人挤棚屋",
      "voiceover_text": "两百万，八十年代的两百万。他在国企做基建，信了人，签了字，钱没了。公司说，你自己赔。赔不起？开除。他没地方去。深圳的棚户区，一个月房租几十块的铁皮屋。父母从贵州赶来，弟妹也来了。六口人，挤在十几平米的空间里。做饭是煤炉，洗澡是公共水龙头。他借了两万一千块创业。两万一。今天的华为，起步资金就是这两万一千块。创业第一年，他没什么像样的产品。到处跑客户，被人拒绝，被人嘲笑。有段时间发不出工资，他去借了高利贷。利息高到什么程度？员工后来回忆说，任总那段时间整夜整夜睡不着，烟一根接一根。最绝望的时候，他站在楼顶。不是想看风景。他在那里站了很久。后来有人问他，为什么没跳。他说，他想起棚屋里那六口人。父母从贵州来投奔他，弟妹指着他吃饭。他走了，他们怎么办。他从楼顶下来了。不是想通了，是没有资格死。他说过一句话：我这个人才是最没有水平的，我最没有水平了。",
      "voiceover_pause_markers": "两百万<#0.5#>八十年代的两百万。<#1.0#>他在国企做基建<#0.2#>信了人<#0.2#>签了字<#0.3#>钱没了。<#0.5#>公司说<#0.2#>你自己赔。<#0.3#>赔不起？<#0.5#>开除。<#0.8#>他没地方去。<#0.5#>深圳的棚户区<#0.2#>一个月房租几十块的铁皮屋。<#0.5#>父母从贵州赶来<#0.2#>弟妹也来了。<#0.5#>六口人<#0.3#>挤在十几平米的空间里。<#0.5#>做饭是煤炉<#0.2#>洗澡是公共水龙头。<#0.8#>他借了两万一千块创业。<#0.5#>两万一。<#0.8#>今天的华为<#0.3#>起步资金就是这两万一千块。<#1.0#>创业第一年<#0.2#>他没什么像样的产品。<#0.3#>到处跑客户<#0.2#>被人拒绝<#0.2#>被人嘲笑。<#0.5#>有段时间发不出工资<#0.2#>他去借了高利贷。<#0.5#>利息高到什么程度？<#0.5#>员工后来回忆说<#0.2#>任总那段时间整夜整夜睡不着<#0.2#>烟一根接一根。<#1.0#>最绝望的时候<#0.3#>他站在楼顶。<#0.5#>不是想看风景。<#1.0#>他在那里站了很久。<#0.5#>后来有人问他<#0.2#>为什么没跳。<#0.5#>他说<#0.3#>他想起棚屋里那六口人。<#0.5#>父母从贵州来投奔他<#0.2#>弟妹指着他吃饭。<#0.5#>他走了<#0.3#>他们怎么办。<#1.0#>他从楼顶下来了。<#0.5#>不是想通了<#0.3#>是没有资格死。<#0.8#>他说过一句话：<#0.3#>我这个人才是最没有水平的<#0.3#>我最没有水平了。",
      "director_notes": "压抑但克制的语气。不煽情，不夸张。'两百万，八十年代的两百万'用重复强调，像在确认一个不可思议的事实。'不是想看风景'说完后停顿，让这句话的重量落下来。'不是想通了，是没有资格死'是全篇情感核心，说完后声音低下去。"
    },
    {
      "id": "S03",
      "type": "body",
      "duration_sec": 20,
      "emotion_arc": "力量",
      "subtitle_text": "30年：棚屋→全球第一",
      "voiceover_text": "但他没有跳。棚屋里六口人的脸，把他从楼顶拉了回来。不是想通了，是没有资格死。第二天，他继续跑客户。没资源，他用人海战术——招应届毕业生，肯干。没技术，他去偷师——跑到国外运营商的展会上，一个产品一个产品地拆、看、学。没市场，他打农村包围城市——巨头不做的偏远地区，他做。早期华为的销售，背着一台交换机，坐大巴去县城。住最便宜的旅馆，请客户吃饭，喝到吐，拿到订单。三十年后，那个从棚屋出发的公司，成了全球通信设备第一。但这不是鸡汤。这不是说任正非行你也行。这是一个问题——那个年代的黑暗里，至少还能看到路。现在呢？",
      "voiceover_pause_markers": "但他没有跳。<#0.5#>棚屋里六口人的脸<#0.3#>把他从楼顶拉了回来。<#0.5#>不是想通了<#0.2#>是没有资格死。<#0.5#>第二天<#0.2#>他继续跑客户。<#0.8#>没资源<#0.2#>他用人海战术——招应届毕业生<#0.2#>肯干。<#0.5#>没技术<#0.2#>他去偷师——跑到国外运营商的展会上<#0.2#>一个产品一个产品地拆、看、学。<#0.5#>没市场<#0.2#>他打农村包围城市——巨头不做的偏远地区<#0.2#>他做。<#0.8#>早期华为的销售<#0.2#>背着一台交换机<#0.2#>坐大巴去县城。<#0.3#>住最便宜的旅馆<#0.2#>请客户吃饭<#0.2#>喝到吐<#0.2#>拿到订单。<#0.8#>三十年后<#0.3#>那个从棚屋出发的公司<#0.3#>成了全球通信设备第一。<#1.0#>但这不是鸡汤。<#0.5#>这不是说任正非行你也行。<#0.5#>这是一个问题——<#0.3#>那个年代的黑暗里<#0.2#>至少还能看到路。<#0.5#>现在呢？",
      "director_notes": "转折段。语速从慢到快。'没资源→他...没技术→他...没市场→他...'三组排比加速推进，带出力量感。'三十年后'突然放慢。'但这不是鸡汤'之后语气转冷，像在提问而不是回答。最后'现在呢？'轻声，留悬念。"
    },
    {
      "id": "S04",
      "type": "body",
      "duration_sec": 25,
      "emotion_arc": "尖锐",
      "subtitle_text": "9200万岗位被AI替代 35岁简历过不了筛选",
      "voiceover_text": "一九八七年，任正非被体制抛弃。没有工作，没有技能，连生存都成问题。二零二四年，轮到你了。世界经济论坛说，到二零三零年，全球九千两百万个岗位会被AI替代。高盛的报告说，每个月有一万六千个工作岗位在消失。斯坦福的研究更狠——AI渗透率最高的行业，二十二到二十五岁年轻人的就业率直接下降了百分之十三。任正非那个年代，被开除了还能摆地摊、做倒爷、搞基建。那个年代有粗放的红利，有野蛮生长的空间。现在？你的简历先被AI筛选一轮，不合格的连HR的面都见不到。你的技能，AI三个月就能学会。你的岗位，可能在你看到这条视频的时候已经被优化掉了。同样是被时代抛弃。四十三岁的任正非，和三十五岁的你，面对的是同一片黑暗。任正非后来翻盘，靠的是踩中了通信行业崛起的浪潮。每一次技术革命，砸碎一批饭碗的同时，确实会催生新的赛道。AI也不例外。但问题是——当年通信行业的门槛，是胆子和体力。今天AI赛道的门槛，是算力和算法。普通人够得着吗？",
      "voiceover_pause_markers": "一九八七年<#0.3#>任正非被体制抛弃。<#0.5#>没有工作<#0.2#>没有技能<#0.2#>连生存都成问题。<#1.0#>二零二四年<#0.5#>轮到你了。<#1.0#>世界经济论坛说<#0.2#>到二零三零年<#0.2#>全球九千两百万个岗位会被AI替代。<#0.5#>高盛的报告说<#0.2#>每个月有一万六千个工作岗位在消失。<#0.5#>斯坦福的研究更狠——<#0.3#>AI渗透率最高的行业<#0.2#>二十二到二十五岁年轻人的就业率直接下降了百分之十三。<#1.0#>任正非那个年代<#0.2#>被开除了还能摆地摊、做倒爷、搞基建。<#0.5#>那个年代有粗放的红利<#0.2#>有野蛮生长的空间。<#0.8#>现在？<#0.5#>你的简历先被AI筛选一轮<#0.2#>不合格的连HR的面都见不到。<#0.5#>你的技能<#0.2#>AI三个月就能学会。<#0.5#>你的岗位<#0.2#>可能在你看到这条视频的时候已经被优化掉了。<#1.0#>同样是被时代抛弃。<#0.5#>四十三岁的任正非<#0.2#>和三十五岁的你<#0.2#>面对的是同一片黑暗。<#1.0#>任正非后来翻盘<#0.2#>靠的是踩中了通信行业崛起的浪潮。<#0.5#>每一次技术革命<#0.2#>砸碎一批饭碗的同时<#0.2#>确实会催生新的赛道。<#0.5#>AI也不例外。<#0.8#>但问题是——<#0.3#>当年通信行业的门槛<#0.2#>是胆子和体力。<#0.5#>今天AI赛道的门槛<#0.2#>是算力和算法。<#0.5#>普通人够得着吗？",
      "director_notes": "冷静但尖锐。数据部分用事实陈述的语气，不渲染。'轮到你了'突然转向第二人称，语气要有刺入感。'现在？'之后每个'你的...'短句递进加速。'普通人够得着吗？'轻声但锋利，像手术刀。"
    },
    {
      "id": "S05",
      "type": "body",
      "duration_sec": 20,
      "emotion_arc": "对立",
      "subtitle_text": "时代红利吃完了 vs 越混乱越有机会",
      "voiceover_text": "有人说：别拿任正非骗自己了。那个年代是草莽年代，胆子大就行。四十三岁被骗两百万，借两万块钱就能翻身。现在呢？AI替代你的时候，你连两万块钱的生意都找不到。普通人没有资源、没有资本、没有信息差，拼有什么用？时代红利吃完了，别做梦了。也有人说：任正非当年哪有什么红利？他被开除的时候，体制是铁饭碗，他连饭碗都没了。他创业的时候，没人觉得通信行业有机会——行业老大哥是爱立信、诺基亚，一个中国小公司凭什么？凭什么就是答案。每次技术革命，淘汰一批人的同时确实会创造新赛道。当年进通信行业的门槛是胆子，今天进AI行业的门槛可能是会用工具。AI淘汰旧岗位的同时，也在创造会用AI的人这个新物种。越混乱的时候，越有重新洗牌的机会。跟年代没关系，跟你敢不敢重新定义自己有关系。",
      "voiceover_pause_markers": "有人说：<#0.5#>别拿任正非骗自己了。<#0.5#>那个年代是草莽年代<#0.2#>胆子大就行。<#0.5#>四十三岁被骗两百万<#0.2#>借两万块钱就能翻身。<#0.5#>现在呢？<#0.5#>AI替代你的时候<#0.2#>你连两万块钱的生意都找不到。<#0.5#>普通人没有资源<#0.2#>没有资本<#0.2#>没有信息差<#0.2#>拼有什么用？<#0.5#>时代红利吃完了<#0.2#>别做梦了。<#1.0#>也有人说：<#0.5#>任正非当年哪有什么红利？<#0.5#>他被开除的时候<#0.2#>体制是铁饭碗<#0.2#>他连饭碗都没了。<#0.5#>他创业的时候<#0.2#>没人觉得通信行业有机会——<#0.3#>行业老大哥是爱立信、诺基亚<#0.2#>一个中国小公司凭什么？<#0.5#>凭什么就是答案。<#0.5#>每次技术革命<#0.2#>淘汰一批人的同时确实会创造新赛道。<#0.5#>当年进通信行业的门槛是胆子<#0.2#>今天进AI行业的门槛可能是会用工具。<#0.5#>AI淘汰旧岗位的同时<#0.2#>也在创造会用AI的人这个新物种。<#0.5#>越混乱的时候<#0.2#>越有重新洗牌的机会。<#0.3#>跟年代没关系<#0.2#>跟你敢不敢重新定义自己有关系。",
      "director_notes": "两派观点有对比。A派略带嘲讽和无奈——像是在泼冷水。'别做梦了'说完后停顿。B派略带坚定和挑衅——像是在反驳。'凭什么就是答案'语调上扬。最后一句'跟你敢不敢重新定义自己有关系'收束有力。"
    },
    {
      "id": "S06",
      "type": "cta",
      "duration_sec": 10,
      "emotion_arc": "留白",
      "subtitle_text": "他的黑暗里有路 你的呢",
      "voiceover_text": "一九八七年的棚屋里，四十三岁的任正非不知道自己能不能活下去。二零二四年的出租屋里，你也不知道。区别是——他的黑暗里，好歹看得到路。你的黑暗里，连路都没有了。还是说……其实有，只是你还没看到？",
      "voiceover_pause_markers": "一九八七年的棚屋里<#0.3#>四十三岁的任正非不知道自己能不能活下去。<#1.0#>二零二四年的出租屋里<#0.3#>你也不知道。<#1.0#>区别是——<#0.5#>他的黑暗里<#0.2#>好歹看得到路。<#0.5#>你的黑暗里<#0.2#>连路都没有了。<#1.0#>还是说……<#0.5#>其实有<#0.3#>只是你还没看到？",
      "director_notes": "回归平静。前两句像在感叹。'区别是——'之后缓慢清晰地对比。最后'还是说……'停顿后声音放轻，'只是你还没看到？'带着一丝不确定和可能性。不要念成鸡汤，要念成一个真正的问号。说完后留两秒空白再结束。"
    }
  ]
}
```

**Step 2: 验证 JSON 合法性**

Run: `python3 -c "import json; json.load(open('docs/content/config/unemploy-celebrity-01.json')); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add docs/content/config/unemploy-celebrity-01.json
git commit -m "feat: add unemploy-celebrity-01 config (任正非, 6 segments, Charon voice)"
```

---

### Task 2: 生成 Gemini TTS 配音

**Prerequisites:** Task 1 完成, `source docs/content/.env`

**Step 1: 创建输出目录**

```bash
mkdir -p docs/content/assets/voiceover/unemploy-celebrity-01
```

**Step 2: 运行 TTS 批量生成**

```bash
cd docs/content/scripts
source ../.env
python3 gemini-tts-batch.py --config config/unemploy-celebrity-01.json --voice Charon
```

Expected: 6个MP3文件生成到 `docs/content/assets/voiceover/unemploy-celebrity-01/`

**Step 3: 验证输出**

```bash
ls -la docs/content/assets/voiceover/unemploy-celebrity-01/
```

Expected: S01.mp3 ~ S06.mp3, 每个文件大小 > 50KB

**Step 4: Commit**

```bash
git add docs/content/assets/voiceover/unemploy-celebrity-01/
git commit -m "feat: generate Gemini TTS Charon voiceover for unemploy-celebrity-01"
```

---

### Task 3: 生成 Seedream 氛围参考图

**Prerequisites:** Task 1 完成, `source docs/content/.env`

**Step 1: 创建输出目录**

```bash
mkdir -p docs/content/assets/references/unemploy-celebrity-01
```

**Step 2: 运行 Seedream 批量生图**

```bash
cd docs/content/scripts
source ../.env
python3 seedream-batch.py --config config/unemploy-celebrity-01.json
```

Expected: 6张PNG生成到 `docs/content/assets/references/unemploy-celebrity-01/`

**Step 3: 验证输出**

```bash
ls -la docs/content/assets/references/unemploy-celebrity-01/
```

Expected: AT01 ~ AT06 的PNG文件, 每个文件 > 100KB

**Step 4: 人工审核图片质量**

检查每张图是否符合场景描述，无AI味（不用人像）。

**Step 5: Commit**

```bash
git add docs/content/assets/references/unemploy-celebrity-01/
git commit -m "feat: generate 6 Seedream atmosphere shots for unemploy-celebrity-01"
```

---

### Task 4: 生成 Kling 视频

**Prerequisites:** Task 3 完成（参考图已审核）

**Step 1: 运行 Kling 批量视频生成**

```bash
cd docs/content/scripts
source ../.env
python3 kling-gen-batch.py --config config/unemploy-celebrity-01.json
```

Expected: 6个MP4生成到 `docs/content/output/unemploy-celebrity-01/`

**Step 2: 验证输出**

```bash
ls -la docs/content/output/unemploy-celebrity-01/
```

Expected: AT01 ~ AT06 的MP4文件, 每个文件 > 500KB

**Step 3: Commit**

```bash
git add docs/content/output/unemploy-celebrity-01/
git commit -m "feat: generate 6 Kling atmosphere videos for unemploy-celebrity-01"
```

---

### Task 5: FFmpeg 粗剪合成

**Prerequisites:** Task 2 (配音) + Task 4 (视频) 完成

**Step 1: 适配 compose 脚本或新建**

参考 `compose-unemploy-01.py`，根据新config格式调整输入路径和段落映射。

**Step 2: 运行 FFmpeg 粗剪**

```bash
cd docs/content/scripts
python3 compose-unemploy-celebrity-01.py --config config/unemploy-celebrity-01.json
```

Expected: 粗剪MP4输出到 `docs/content/output/unemploy-celebrity-01/rough-cut.mp4`

**Step 3: 验证输出**

```bash
ffprobe docs/content/output/unemploy-celebrity-01/rough-cut.mp4
```

Expected: 1080x1920, H.264, 时长与配音总时长大致匹配

**Step 4: Commit**

```bash
git add docs/content/output/unemploy-celebrity-01/rough-cut.mp4
git commit -m "feat: FFmpeg rough-cut composite for unemploy-celebrity-01"
```

---

### Task 6: 剪映后期（手动）

**Prerequisites:** Task 5 完成（粗剪MP4）

**人工步骤：**
1. 导入粗剪MP4到剪映
2. 添加文字卡片（大号黑体/粗体，白色+描边）
   - S01: 「华为营收 8600亿」/ 「43岁 被骗200万 被开除 离婚」
   - S02: 「起步资金：2.1万」/ 「六口人 挤棚屋」/ 「"我这个人才是最没有水平的"」
   - S03: 「30年：棚屋 → 全球第一」/ 「这不是鸡汤，这是一个问题」
   - S04: 「9200万岗位 → 2030年被AI替代」/ 「35岁 简历过不了AI筛选」/ 「他那个年代的黑暗里，还有路。现在呢？」
   - S05: 「A派：时代红利吃完了 别做梦」/ 「B派：越混乱越有机会 跟年代没关系」
   - S06: 「他的黑暗里有路。你的呢？」/ 「评论区 → 你站哪边？」
3. 数字用红色/金色高亮
4. 转场用闪白或黑屏
5. 去AI滤镜处理
6. 导出 1080x1920 H.264

---

### Task 7: 更新 Config 状态

**Step 1: 更新 status 字段**

```json
"status": "materials_ready_for_editing"
```

**Step 2: Commit**

```bash
git add docs/content/config/unemploy-celebrity-01.json
git commit -m "docs(config): update unemploy-celebrity-01 status to materials_ready_for_editing"
```
