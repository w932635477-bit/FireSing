# B+ 重复暴击 "回去等通知吧" Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a 50-second Douyin unemployment video using interview stock footage + repeated phrase "回去等通知吧" with escalating emotional intensity.

**Architecture:** 5-stage pipeline: (1) prepare assets → (2) generate TTS voiceover (15 lines) → (3) create text cards (5 HTML→video) → (4) compose with FFmpeg → (5) post-process audio effects. Uses existing `gemini-tts-batch.py`, `text-card-renderer.py`, and a new `compose-repeat-blast.py` script.

**Tech Stack:** Python, FFmpeg, Playwright (HTML→PNG), Google Gemini TTS (Charon voice), Gemini API

**Design Doc:** `docs/plans/2026-05-04-unemploy-storyboard-repeat-blast.md`

---

## Task 1: Create Video Config JSON

**Files:**
- Create: `docs/content/config/unemploy-repeat-01-waitnotice.json`

**Step 1: Create config JSON**

```json
{
  "video_id": "unemploy-repeat-01-waitnotice",
  "version": "3.0",
  "series": "unemploy-repeat",
  "workflow_mode": "repeat-blast",
  "global": {
    "target_duration_sec": 50,
    "resolution": "1080x1920",
    "fps": 24,
    "voice": "Charon"
  },
  "repeated_phrase": "回去等通知吧",
  "voiceover": {
    "engine": "gemini-3.1-flash-tts",
    "voice": "Charon",
    "segments": [
      {"id": "LINE01", "emotion": "calm_corporate", "text": "回去等通知吧。"},
      {"id": "LINE02", "emotion": "polite_dismissive", "text": "嗯，你的情况我们了解了。回去等通知吧。"},
      {"id": "LINE03", "emotion": "impatient_dismissive", "text": "我们还有其他候选人，你先回去等通知吧。"},
      {"id": "LINE04", "emotion": "warm_then_cold", "text": "其实你条件不错，不过...回去等通知吧。"},
      {"id": "LINE05", "emotion": "rushed_muttering", "text": "好，就这样，回去等通知吧。"},
      {"id": "LINE06", "emotion": "whisper_haunting", "text": "回去等通知吧"},
      {"id": "LINE07", "emotion": "flat_robotic", "text": "回去等通知吧"},
      {"id": "LINE08", "emotion": "bitter_laugh_resigned", "text": "回去等通知吧"},
      {"id": "LINE09", "emotion": "slow_defeated", "text": "回去...等通知吧"},
      {"id": "LINE10", "emotion": "intense_rapid_shout", "text": "回去等通知吧回去等通知吧回去等通知吧回去等通知吧"},
      {"id": "LINE11", "emotion": "screaming_inside", "text": "回去等通知吧！！"},
      {"id": "LINE12", "emotion": "very_slow_heavy", "text": "半年了。"},
      {"id": "LINE13", "emotion": "vulnerable_trailing", "text": "你..."},
      {"id": "LINE14", "emotion": "quiet_trembling", "text": "还在等吗？"},
      {"id": "LINE15", "emotion": "warm_encouraging", "text": "你等了多久？"}
    ]
  },
  "stock_clips": {
    "clip1": {"file": "interview-clip-01.mp4", "duration": 24.7, "resolution": "2160x4096"},
    "clip2": {"file": "interview-clip-02.mp4", "duration": 16.6, "resolution": "2160x4096"},
    "clip3": {"file": "interview-clip-03.mp4", "duration": 8.3, "resolution": "1080x1920"},
    "clip4": {"file": "interview-clip-04.mp4", "duration": 12.1, "resolution": "720x1280"}
  },
  "storyboard": [
    {"shot": 1,  "time": "0-0.8s",    "type": "text_card", "ref": "TC01a", "duration": 0.8},
    {"shot": 2,  "time": "0.8-1.5s",  "type": "text_card", "ref": "TC01b", "duration": 0.7},
    {"shot": 3,  "time": "1.5-3s",    "type": "video_clip", "clip": "clip1", "seek": 0, "len": 1.5, "vo": "LINE01"},
    {"shot": 4,  "time": "3-7s",      "type": "video_clip", "clip": "clip1", "seek": 1.5, "len": 4.0, "overlay": "第1次", "vo": "LINE02"},
    {"shot": 5,  "time": "7-11s",     "type": "video_clip", "clip": "clip2", "seek": 0, "len": 4.0, "overlay": "第7次", "vo": "LINE03"},
    {"shot": 6,  "time": "11-14s",    "type": "video_clip", "clip": "clip3", "seek": 0, "len": 3.0, "overlay": "第23次", "vo": "LINE04"},
    {"shot": 7,  "time": "14-18s",    "type": "video_clip", "clip": "clip4", "seek": 0, "len": 4.0, "overlay": "第47次", "vo": "LINE05"},
    {"shot": 8,  "time": "18-20s",    "type": "text_card", "ref": "TC02-flash", "duration": 2.0},
    {"shot": 9,  "time": "20-22s",    "type": "video_clip", "clip": "clip1", "seek": 5.5, "len": 2.0, "text_center": "回去等通知吧", "vo": "LINE06"},
    {"shot": 10, "time": "22-24s",    "type": "video_clip", "clip": "clip2", "seek": 4.0, "len": 2.0, "text_center": "回去等通知吧", "vo": "LINE07"},
    {"shot": 11, "time": "24-26s",    "type": "video_clip", "clip": "clip4", "seek": 4.0, "len": 2.0, "text_center": "回去等通知吧", "vo": "LINE08"},
    {"shot": 12, "time": "26-28s",    "type": "video_clip", "clip": "clip3", "seek": 3.0, "len": 2.0, "text_center": "回去等通知吧", "vo": "LINE09"},
    {"shot": 13, "time": "28-31s",    "type": "video_clip", "clip": "clip1", "seek": 7.5, "len": 3.0, "text_rain": true, "vo": "LINE10"},
    {"shot": 14, "time": "31-33s",    "type": "video_clip", "clip": "clip2", "seek": 6.0, "len": 2.0, "text_rain": true, "vo": "LINE11"},
    {"shot": 15, "time": "33-35s",    "type": "text_card", "ref": "TC04-silence", "duration": 2.0},
    {"shot": 16, "time": "35-37s",    "type": "text_card", "ref": "TC04-dark", "duration": 2.0, "vo": "LINE12"},
    {"shot": 17, "time": "37-39s",    "type": "video_clip", "clip": "clip1", "seek": 10.5, "len": 2.0, "vo": "LINE13"},
    {"shot": 18, "time": "39-41s",    "type": "video_clip", "clip": "clip1", "seek": 12.5, "len": 1.5, "vo": "LINE14"},
    {"shot": 19, "time": "41-43s",    "type": "text_card", "ref": "TC04-full", "duration": 2.0},
    {"shot": 20, "time": "43-47s",    "type": "video_clip", "clip": "clip2", "seek": 8.0, "len": 2.0, "text_fade": "评论区说说", "vo": "LINE15"},
    {"shot": 21, "time": "47-50s",    "type": "text_card", "ref": "TC05-cta", "duration": 3.0}
  ],
  "bgm": {
    "heartbeat_60": {"file": "heartbeat-60bpm.mp3", "volume": 0.15},
    "heartbeat_120": {"file": "heartbeat-120bpm.mp3", "volume": 0.20},
    "heartbeat_140": {"file": "heartbeat-140bpm.mp3", "volume": 0.25},
    "heartbeat_160": {"file": "heartbeat-160bpm.mp3", "volume": 0.30},
    "piano_c": {"file": "piano-c-note.mp3", "volume": 0.10}
  },
  "upload_copy": {
    "platform": "douyin",
    "title_candidates": [
      "你已经听过这句话多少次了？",
      "回去等通知吧...半年了",
      "面试47次后我听懂了这句话"
    ],
    "tags": ["失业", "面试", "找工作", "裁员", "职场", "中年危机"]
  }
}
```

**Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('docs/content/config/unemploy-repeat-01-waitnotice.json'))"` 
Expected: No error

**Step 3: Commit**

```bash
git add docs/content/config/unemploy-repeat-01-waitnotice.json
git commit -m "feat: add B+ repeat blast video config (Episode 01)"
```

---

## Task 2: Prepare Stock Footage Assets

**Files:**
- Source: `docs/content/output/面试/*.mp4` (4 files)
- Target: `docs/content/assets/stock/interview-clip-01.mp4` through `04.mp4`

**Step 1: Create stock directory and copy clips**

```bash
mkdir -p docs/content/assets/stock
cp "docs/content/output/面试/7643444-uhd_2160_4096_25fps_副本.mp4" docs/content/assets/stock/interview-clip-01.mp4
cp "docs/content/output/面试/7644024-uhd_2160_4096_25fps_副本.mp4" docs/content/assets/stock/interview-clip-02.mp4
cp "docs/content/output/面试/7844862-hd_1080_1920_30fps_副本.mp4" docs/content/assets/stock/interview-clip-03.mp4
cp "docs/content/output/面试/7844951-hd_1080_1920_30fps_副本.mp4" docs/content/assets/stock/interview-clip-04.mp4
```

**Step 2: Verify clips**

Run: `for f in docs/content/assets/stock/interview-clip-*.mp4; do ffprobe -v error -show_entries format=duration -of csv=p=0 "$f"; done`
Expected: `24.720000`, `16.600000`, `8.333333`, `12.133333`

**Step 3: Commit**

```bash
git add docs/content/assets/stock/
git commit -m "chore: add interview stock footage for repeat blast video"
```

---

## Task 3: Add Emotion Arcs to TTS Script

**Files:**
- Modify: `docs/content/scripts/gemini-tts-batch.py:62-190` (add new emotions to `EMOTION_PROMPTS` and `AUDIO_TAGS`)

**Step 1: Add 15 new emotion arcs**

Add these entries to the `EMOTION_PROMPTS` dict after the existing unemployment emotions (after `"参与"`):

```python
    # B+ Repeat Blast emotions (Episode 01: 回去等通知吧)
    "calm_corporate": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "HR说'回去等通知吧'，像读一句标准话术。",
        "director": "短促、官方、不带感情。越是客气越刺痛。像公司前台念一条通知，不是跟人说话。语速正常，句尾不要拖。",
    },
    "polite_dismissive": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "HR客套地拒绝你，先说'了解情况'再说不合适。",
        "director": "礼貌但敷衍。'你的情况我们了解了'是废话铺垫，说完赶紧进正题。句尾'回去等通知吧'说得特别顺，像说了一万遍。",
    },
    "impatient_dismissive": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "HR开始不耐烦，暗示你只是备胎。",
        "director": "语速比上一句快。'其他候选人'说得很自然，'先'字稍微加重，潜台词是'你排后面'。结尾'回去等通知吧'说得更快，像赶人。",
    },
    "warm_then_cold": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "HR先夸你再拒绝，给你希望再拿走。",
        "director": "前半句'其实你条件不错'说得真诚，像真的在夸你。'不过'之后语速突然加快，草草收尾。'回去等通知吧'像附赠的，不是重点。重点在'不过'的转折。",
    },
    "rushed_muttering": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "HR连客套都不演了，赶紧结束面试。",
        "director": "含糊、匆忙、自言自语的感觉。'好就这样'说很快，像在划掉一个待办事项。'回去等通知吧'说得特别轻特别快，像已经在看手机了。",
    },
    "whisper_haunting": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "这句话在你脑子里回响，不是别人在说，是你自己在想。",
        "director": "气声，贴近话筒，像耳语。非常轻但每个字都清楚。不是在跟谁说，是这句话自己冒出来的。句尾不要完全消失，留一点余音。",
    },
    "flat_robotic": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "机械式重复，像自动回复短信。",
        "director": "平直，无感情，每个字等间隔。不是人在说话，是系统在播报。去掉所有语气词和呼吸。像TTS默认输出。",
    },
    "bitter_laugh_resigned": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "先苦笑一声，再说出来。已经麻木了。",
        "director": "开头先轻轻'哼'一声苦笑，不是大笑，是从鼻子里出气的笑。然后说这句话的时候嘴角是歪的。不是愤怒，是那种'得了吧'的无奈。",
    },
    "slow_defeated": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "最后一次了，没力气了，像在说给自己听。",
        "director": "极慢，比所有前面都慢。每个字之间有明显停顿。'回去'和'等'之间停一下，'等'和'通知吧'之间再停一下。句尾声音往下走，像叹气。",
    },
    "intense_rapid_shout": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "四句话叠在一起，越来越快越来越响。",
        "director": "开头正常语速，每重复一遍加快一点加大声一点。最后一句几乎是喊出来的但不是真喊，是压抑到极限突然爆发。中间不要停。",
    },
    "screaming_inside": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "内心在尖叫，咬牙切齿地说出来。",
        "director": "压抑的嘶吼，不是真的喊。咬牙切齿，像牙齿咬着说出来。'回去等通知吧'五个字每个都带着恨意。最后'吧'字要爆破出来。",
    },
    "very_slow_heavy": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "所有噪音消失后，唯一的一句话。半年了。",
        "director": "极慢，几乎听不见。像对自己说，不是对别人说。'半年了'三个字每个字之间有一秒停顿。声音很沉很重，像一个很大的石头慢慢放下来。",
    },
    "vulnerable_trailing": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "最脆弱的一个字，不敢问完。",
        "director": "'你'字拖长，像在犹豫要不要说。后面停顿0.5秒，像鼓起勇气但没鼓够。声音在句尾消散，不是说完是没力气说完。",
    },
    "quiet_trembling": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "问题终于问完，不需要回答。",
        "director": "轻微颤抖，像嘴唇在抖。'还在等吗'四个字说得轻但清楚。句尾'吗'字往上走但很微弱，不是疑问，是自问。说完后留一秒呼吸声。",
    },
    "warm_encouraging": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "从黑暗中拉出来，像朋友在问你。",
        "director": "语气突然转变，从压抑变成温暖。像朋友拍拍你肩膀问一句'你等了多久'。不是同情，是关心。语速正常，声音明亮，跟前面形成强烈反差。",
    },
```

**Step 2: Add audio tags for new emotions**

Add to `AUDIO_TAGS` dict:

```python
    "calm_corporate": ["[calm]", "[detached]"],
    "polite_dismissive": ["[calm]", "[rushed]"],
    "impatient_dismissive": ["[firmly]", "[quickly]"],
    "warm_then_cold": ["[warmly]", "[coldly]"],
    "rushed_muttering": ["[quickly]", "[muttering]"],
    "whisper_haunting": ["[whisper]", "[haunting]"],
    "flat_robotic": ["[monotone]", "[flat]"],
    "bitter_laugh_resigned": ["[laughing]", "[resigned]"],
    "slow_defeated": ["[slowly]", "[defeated]"],
    "intense_rapid_shout": ["[intensely]", "[shouting]"],
    "screaming_inside": ["[angrily]", "[clenched]"],
    "very_slow_heavy": ["[slowly]", "[heavily]"],
    "vulnerable_trailing": ["[softly]", "[vulnerable]"],
    "quiet_trembling": ["[trembling]", "[quietly]"],
    "warm_encouraging": ["[warmly]", "[encouraging]"],
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('docs/content/scripts/gemini-tts-batch.py').read()); print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add docs/content/scripts/gemini-tts-batch.py
git commit -m "feat: add 15 emotion arcs for B+ repeat blast TTS"
```

---

## Task 4: Generate TTS Voiceover (15 Lines)

**Files:**
- Create: `docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/LINE01.mp3` through `LINE15.mp3`
- Uses: `docs/content/scripts/gemini-tts-batch.py`

**Step 1: Source env and generate all lines**

```bash
source docs/content/.env
python3 docs/content/scripts/gemini-tts-batch.py \
  --config docs/content/config/unemploy-repeat-01-waitnotice.json \
  --voice Charon
```

Expected: 15 MP3 files in `docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/`

**Step 2: Check durations match storyboard targets**

```bash
for f in docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/LINE*.mp3; do
  name=$(basename "$f" .mp3)
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  echo "$name: ${dur}s"
done
```

Expected approximate durations:
- LINE01: ~1.5s, LINE02: ~4s, LINE03: ~4s, LINE04: ~3s, LINE05: ~4s
- LINE06-09: ~2s each, LINE10: ~3s, LINE11: ~2s
- LINE12: ~2s, LINE13: ~1.5s, LINE14: ~2s, LINE15: ~3s

**Step 3: Generate backup versions for LINE06-09 (ESCALATION critical lines)**

For each of LINE06-09, generate 2 additional versions with alternative Director's Notes:

```bash
# Repeat for LINE06, LINE07, LINE08, LINE09 with --shot flag
python3 docs/content/scripts/gemini-tts-batch.py \
  --config docs/content/config/unemploy-repeat-01-waitnotice.json \
  --voice Charon --shot LINE06
```

Select the most distinct-sounding version for each line.

**Step 4: Commit voiceover assets**

```bash
git add docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/
git commit -m "feat: generate TTS voiceover for B+ repeat blast (15 lines)"
```

---

## Task 5: Generate BGM/SFX Audio

**Files:**
- Create: `docs/content/assets/bgm/heartbeat-60bpm.mp3`
- Create: `docs/content/assets/bgm/heartbeat-120bpm.mp3`
- Create: `docs/content/assets/bgm/heartbeat-140bpm.mp3`
- Create: `docs/content/assets/bgm/heartbeat-160bpm.mp3`
- Create: `docs/content/assets/bgm/piano-c-note.mp3`
- Create: `docs/content/assets/bgm/40hz-drone.mp3`
- Create: `docs/content/assets/bgm/silence-2s.mp3`

**Step 1: Generate heartbeat sounds with FFmpeg**

```bash
cd docs/content/assets/bgm

# Heartbeat 60bpm (1 beat/sec, 20s loop)
ffmpeg -y -f lavfi -i "sine=frequency=40:duration=0.15" \
  -af "afade=t=in:st=0:d=0.02,afade=t=out:st=0.1:d=0.05,volume=0.6" \
  heartbeat-single.mp3

# Create loop by concatenating with silence gaps
python3 -c "
import subprocess
for bpm, name in [(60,'60'), (120,'120'), (140,'140'), (160,'160')]:
    gap = 60.0 / bpm - 0.15
    beats = int(bpm * 0.3)  # ~18 seconds
    with open(f'hb_{name}_list.txt', 'w') as f:
        for i in range(beats):
            f.write(f\"file 'heartbeat-single.mp3'\n\")
            if i < beats - 1:
                f.write(f\"file 'silence-{gap:.3f}.mp3'\n\")
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=44100:cl=mono',
                    '-t', str(gap), '-b:a', '192k', f'silence-{gap:.3f}.mp3'],
                   capture_output=True)
    subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', f'hb_{name}_list.txt', '-c:a', 'aac', '-b:a', '192k',
                    f'heartbeat-{bpm}bpm.mp3'], capture_output=True)
print('Done')
"

# 40Hz drone for HOOK
ffmpeg -y -f lavfi -i "sine=frequency=40:duration=3" \
  -af "volume=0.3,afade=t=in:st=0:d=2" \
  40hz-drone.mp3

# Piano C note for TRAP
ffmpeg -y -f lavfi -i "sine=frequency=261.63:duration=5" \
  -af "volume=0.2,afade=t=in:st=0:d=0.5,afade=t=out:st=3:d=2" \
  piano-c-note.mp3

# Silence for BREAK
ffmpeg -y -f lavfi -i "anullsrc=r=44100:cl=mono" -t 2 -b:a 192k silence-2s.mp3
```

**Step 2: Verify BGM files exist**

Run: `ls -la docs/content/assets/bgm/heartbeat-*.mp3 docs/content/assets/bgm/piano-c-note.mp3`
Expected: All files present

**Step 3: Commit**

```bash
git add docs/content/assets/bgm/heartbeat-*.mp3 docs/content/assets/bgm/piano-c-note.mp3 docs/content/assets/bgm/40hz-drone.mp3
git commit -m "feat: generate BGM/SFX for B+ repeat blast video"
```

---

## Task 6: Create Text Card HTML Templates

**Files:**
- Create: `docs/content/templates/tc-repeat-01-hook.html` (TC01a + TC01b)
- Create: `docs/content/templates/tc-repeat-02-flash.html` (red blink)
- Create: `docs/content/templates/tc-repeat-03-escalation.html` (center text)
- Create: `docs/content/templates/tc-repeat-04-break.html` (silence text)
- Create: `docs/content/templates/tc-repeat-05-cta.html` (final CTA)

**Step 1: Create TC01 — HOOK counter**

Write `docs/content/templates/tc-repeat-01-hook.html`:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; background: #000; display: flex;
       align-items: center; justify-content: center; flex-direction: column;
       font-family: "PingFang SC", "Noto Sans SC", sans-serif; overflow: hidden; }
.text1 { color: #fff; font-size: 48px; font-weight: 300; letter-spacing: 4px;
         opacity: 0; animation: fadeIn 0.3s ease-out 0.1s forwards; }
.text2 { color: #FF2D2D; font-size: 64px; font-weight: 700; letter-spacing: 8px;
         opacity: 0; animation: blink 0.1s step-end 3 0s forwards; margin-top: 20px; }
@keyframes fadeIn { to { opacity: 1; } }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
</style></head>
<body>
<div class="text1">你已经听过这句话</div>
<div class="text2">____次了</div>
</body></html>
```

**Step 2: Create TC02 — Red flash (18-20s)**

Write `docs/content/templates/tc-repeat-02-flash.html`:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; background: #000; display: flex;
       align-items: center; justify-content: center;
       font-family: "PingFang SC", "Noto Sans SC", sans-serif; overflow: hidden; }
.text { color: #FF2D2D; font-size: 96px; font-weight: 900; letter-spacing: 8px;
        animation: blink 0.3s step-end 3; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
</style></head>
<body>
<div class="text">回去等通知吧</div>
</body></html>
```

**Step 3: Create TC04 — Break silence text**

Write `docs/content/templates/tc-repeat-04-break.html` (variant A: "你还在等吗"):

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; background: #000; display: flex;
       align-items: center; justify-content: center; flex-direction: column; gap: 40px;
       font-family: "PingFang SC", "Noto Sans SC", sans-serif; overflow: hidden; }
.sub { font-size: 40px; font-weight: 300; color: #888; letter-spacing: 4px;
       opacity: 0; animation: fadeIn 2s ease-out forwards; }
.main { font-size: 48px; font-weight: 300; color: #fff; letter-spacing: 6px;
        opacity: 0; animation: fadeIn 2s ease-out 0.5s forwards; }
@keyframes fadeIn { to { opacity: 1; } }
</style></head>
<body>
<div class="sub">半年了。</div>
<div class="main">你还在等吗？</div>
</body></html>
```

**Step 4: Create TC05 — CTA final**

Write `docs/content/templates/tc-repeat-05-cta.html`:

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: 1080px; height: 1920px; background: #000; display: flex;
       align-items: center; justify-content: center; flex-direction: column; gap: 24px;
       font-family: "PingFang SC", "Noto Sans SC", sans-serif; overflow: hidden; }
.main { font-size: 72px; font-weight: 600; color: #fff; letter-spacing: 4px;
        opacity: 0; animation: fadeIn 0.5s ease-out forwards; }
.sub { font-size: 32px; font-weight: 300; color: #888; letter-spacing: 2px;
       opacity: 0; animation: fadeIn 0.5s ease-out 0.3s forwards; }
@keyframes fadeIn { to { opacity: 1; } }
</style></head>
<body>
<div class="main">你等了多久？</div>
<div class="sub">评论区</div>
</body></html>
```

**Step 5: Commit**

```bash
git add docs/content/templates/tc-repeat-*.html
git commit -m "feat: add HTML text card templates for B+ repeat blast video"
```

---

## Task 7: Render Text Cards to Video

**Files:**
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC01-hook.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC02-flash.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC04-silence.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC04-dark.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC04-full.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/TC05-cta.mp4`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/badge-1.png`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/badge-7.png`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/badge-23.png`
- Create: `docs/content/assets/textcards/unemploy-repeat-01-waitnotice/badge-47.png`

**Step 1: Render text card videos with Playwright**

Use `text-card-renderer.py` for each card:

```bash
source docs/content/.env

# TC01 - HOOK (1.5s)
python3 docs/content/scripts/text-card-renderer.py \
  --config docs/content/config/unemploy-repeat-01-waitnotice.json \
  --style medvi --duration 1.5

# TC02 - Red flash (2s)
# TC04 variants - dark/silence/full (2s each)
# TC05 - CTA (3s)
```

If text-card-renderer doesn't support direct template input, render manually:

```bash
mkdir -p docs/content/assets/textcards/unemploy-repeat-01-waitnotice

# For each text card template:
for template in tc-repeat-01-hook tc-repeat-02-flash tc-repeat-04-break tc-repeat-05-cta; do
  # Playwright screenshot
  python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1080, 'height': 1920})
    page.goto('file://$(pwd)/docs/content/templates/${template}.html')
    page.wait_for_timeout(500)
    page.screenshot(path='docs/content/assets/textcards/unemploy-repeat-01-waitnotice/${template}.png', full_page=False)
    browser.close()
"
done
```

**Step 2: Convert PNGs to video clips**

```bash
cd docs/content/assets/textcards/unemploy-repeat-01-waitnotice

# TC01-hook: 1.5s
ffmpeg -y -loop 1 -i tc-repeat-01-hook.png -c:v libx264 -t 1.5 -pix_fmt yuv420p -r 24 -vf "scale=1080:1920" TC01-hook.mp4

# TC02-flash: 2s
ffmpeg -y -loop 1 -i tc-repeat-02-flash.png -c:v libx264 -t 2.0 -pix_fmt yuv420p -r 24 -vf "scale=1080:1920" TC02-flash.mp4

# TC04-break: 2s
ffmpeg -y -loop 1 -i tc-repeat-04-break.png -c:v libx264 -t 2.0 -pix_fmt yuv420p -r 24 -vf "scale=1080:1920" TC04-full.mp4

# TC05-cta: 3s
ffmpeg -y -loop 1 -i tc-repeat-05-cta.png -c:v libx264 -t 3.0 -pix_fmt yuv420p -r 24 -vf "scale=1080:1920" TC05-cta.mp4

# Black cards for dark segments
ffmpeg -y -f lavfi -i color=c=black:s=1080x1920:d=2 -c:v libx264 -pix_fmt yuv420p -r 24 TC04-dark.mp4
ffmpeg -y -f lavfi -i color=c=black:s=1080x1920:d=2 -c:v libx264 -pix_fmt yuv420p -r 24 TC04-silence.mp4
```

**Step 3: Create badge overlays (count badges for PATTERN segment)**

```bash
for num in 1 7 23 47; do
  python3 -c "
from playwright.sync_api import sync_playwright
html = '''<!DOCTYPE html><html><head><style>
* { margin: 0; padding: 0; }
body { width: 300px; height: 80px; display: flex; align-items: center; justify-content: center;
       background: rgba(0,0,0,0.6); border-radius: 12px; }
span { font-family: PingFang SC, sans-serif; font-size: 36px; color: #AAA; letter-spacing: 2px; }
</style></head><body><span>第${num}次</span></body></html>'''
with open('/tmp/badge-${num}.html', 'w') as f: f.write(html)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 300, 'height': 80})
    page.goto('file:///tmp/badge-${num}.html')
    page.wait_for_timeout(200)
    page.screenshot(path='docs/content/assets/textcards/unemploy-repeat-01-waitnotice/badge-${num}.png', transparent=True)
    browser.close()
"
done
```

**Step 4: Commit**

```bash
git add docs/content/assets/textcards/unemploy-repeat-01-waitnotice/
git commit -m "feat: render text cards and badge overlays for B+ repeat blast"
```

---

## Task 8: Post-Process TTS Audio (ESCALATION Pitch Effects)

**Files:**
- Modify: `docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/LINE06.mp3` through `LINE09.mp3`

**Step 1: Apply pitch shifting and spatial effects**

```bash
cd docs/content/assets/voiceover/unemploy-repeat-01-waitnotice

# LINE06: pitch up 1.5 semitones (more tense) + heavy reverb
ffmpeg -y -i LINE06.mp3 -af "asetrate=44100*1.09,aresample=44100,aecho=0.8:0.3:40:0.3,volume=0.5" LINE06-processed.mp3 && mv LINE06-processed.mp3 LINE06.mp3

# LINE07: pitch down 2 semitones (mechanical, low)
ffmpeg -y -i LINE07.mp3 -af "asetrate=44100*0.89,aresample=44100,volume=0.7" LINE07-processed.mp3 && mv LINE07-processed.mp3 LINE07.mp3

# LINE08: pitch up 0.5 semitones + slight echo (spacious)
ffmpeg -y -i LINE08.mp3 -af "asetrate=44100*1.03,aresample=44100,aecho=0.8:0.88:60:0.4,volume=0.8" LINE08-processed.mp3 && mv LINE08-processed.mp3 LINE08.mp3

# LINE09: pitch down 1 semitone + slow down 15% (more desperate)
ffmpeg -y -i LINE09.mp3 -af "asetrate=44100*0.94,aresample=44100,atempo=0.85,volume=0.4" LINE09-processed.mp3 && mv LINE09-processed.mp3 LINE09.mp3
```

**Step 2: Verify processed files sound different**

Listen to LINE06 through LINE09 and confirm each has distinct tonal character.

**Step 3: Commit**

```bash
git add docs/content/assets/voiceover/unemploy-repeat-01-waitnotice/
git commit -m "feat: apply pitch/space post-processing to ESCALATION voice lines"
```

---

## Task 9: Write Compose Script

**Files:**
- Create: `docs/content/scripts/compose-repeat-blast.py`

This is the core script that assembles all 21 shots into the final video. It reads the config JSON, extracts stock footage segments, overlays text cards, merges voiceover, and adds BGM.

**Step 1: Write the compose script**

The script must:
1. Read config JSON from Task 1
2. For each storyboard shot:
   - `text_card` type: use pre-rendered TC video
   - `video_clip` type: extract segment from stock footage with `-ss` and `-t`, scale to 1080x1920
   - If `overlay` key exists: burn in count badge at bottom
   - If `text_center` key exists: burn in centered text
   - If `text_rain` key exists: skip (handled in post in 剪映)
   - If `vo` key exists: merge voiceover audio
3. Concatenate all shots
4. Mix BGM segments (heartbeat for PATTERN/ESCALATION, piano for TRAP)
5. Output final MP4

```python
#!/usr/bin/env python3
"""
B+ Repeat Blast video composer.
Assembles interview stock footage + text cards + voiceover + BGM.

Usage:
  python3 compose-repeat-blast.py --config config/unemploy-repeat-01-waitnotice.json
  python3 compose-repeat-blast.py --config config/unemploy-repeat-01-waitnotice.json --dry-run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE / "config"
STOCK_DIR = BASE / "assets" / "stock"
TC_DIR = BASE / "assets" / "textcards"
VO_DIR = BASE / "assets" / "voiceover"
BGM_DIR = BASE / "assets" / "bgm"
OUTPUT_DIR = BASE / "output"


def run(cmd: list[str], label: str = "") -> None:
    print(f"  [{label}] {' '.join(cmd[:5])}...")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR: {r.stderr[:500]}")
        sys.exit(1)


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())


def extract_stock_clip(
    source: Path, seek: float, length: float, output: Path,
) -> None:
    run([
        "ffmpeg", "-y", "-ss", f"{seek:.3f}", "-i", str(source),
        "-t", f"{length:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-an", str(output),
    ], f"extract {output.name}")


def overlay_badge(video: Path, badge: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(badge),
        "-filter_complex",
        "[1:v]scale=300:80[badge];"
        "[0:v][badge]overlay=(W-w)/2:H*88/100:enable='between(t,0,999)'",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-an", str(output),
    ], f"badge {output.name}")


def overlay_center_text(video: Path, text: str, output: Path) -> None:
    escaped = text.replace("'", "'\\''").replace(":", "\\:")
    run([
        "ffmpeg", "-y", "-i", str(video),
        "-vf",
        f"drawtext=text='{escaped}':fontsize=72:fontcolor=white:"
        f"borderw=2:bordercolor=0xFF2D2D@0.8:"
        f"x=(w-text_w)/2:y=(h-text_h)/2:"
        f"fontfile=/System/Library/Fonts/PingFang.ttc",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
        "-an", str(output),
    ], f"text {output.name}")


def merge_vo(video: Path, vo: Path, output: Path) -> None:
    run([
        "ffmpeg", "-y", "-i", str(video), "-i", str(vo),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        str(output),
    ], f"vo {output.name}")


def build_shot(
    shot: dict, config: dict, temp_dir: Path, video_id: str,
) -> Path:
    shot_num = shot["shot"]
    out = temp_dir / f"shot_{shot_num:02d}.mp4"
    shot_type = shot["type"]

    if shot_type == "text_card":
        tc_ref = shot["ref"]
        tc_dir = TC_DIR / video_id
        tc_file = tc_dir / f"{tc_ref}.mp4"
        if not tc_file.exists():
            # Try PNG → video
            tc_png = tc_dir / f"{tc_ref}.png"
            if tc_png.exists():
                run([
                    "ffmpeg", "-y", "-loop", "1", "-i", str(tc_png),
                    "-c:v", "libx264", "-t", f"{shot['duration']:.3f}",
                    "-pix_fmt", "yuv420p", "-r", "24",
                    "-vf", "scale=1080:1920", str(out),
                ], f"tc-png {tc_ref}")
            else:
                # Generate black frame
                run([
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", f"color=c=black:s=1080x1920:d={shot['duration']:.3f}",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                    str(out),
                ], f"black {shot_num}")
        else:
            run([
                "ffmpeg", "-y", "-i", str(tc_file),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24",
                "-vf", "scale=1080:1920", "-t", f"{shot['duration']:.3f}",
                str(out),
            ], f"tc {tc_ref}")

    elif shot_type == "video_clip":
        clip_key = shot["clip"]
        clip_cfg = config["stock_clips"][clip_key]
        source = STOCK_DIR / clip_cfg["file"]
        seek = shot["seek"]
        length = shot["len"]
        raw = temp_dir / f"shot_{shot_num:02d}_raw.mp4"
        extract_stock_clip(source, seek, length, raw)

        current = raw

        # Overlay badge (count)
        if "overlay" in shot:
            badge_num = {"第1次": 1, "第7次": 7, "第23次": 23, "第47次": 47}.get(shot["overlay"], 1)
            badge_file = TC_DIR / video_id / f"badge-{badge_num}.png"
            if badge_file.exists():
                badged = temp_dir / f"shot_{shot_num:02d}_badge.mp4"
                overlay_badge(current, badge_file, badged)
                current = badged

        # Overlay center text (ESCALATION)
        if "text_center" in shot:
            texted = temp_dir / f"shot_{shot_num:02d}_text.mp4"
            overlay_center_text(current, shot["text_center"], texted)
            current = texted

        # Merge voiceover
        if "vo" in shot:
            vo_ref = shot["vo"]
            vo_file = VO_DIR / video_id / f"{vo_ref}.mp3"
            if vo_file.exists():
                voiced = temp_dir / f"shot_{shot_num:02d}_vo.mp4"
                merge_vo(current, vo_file, voiced)
                current = voiced

        # Rename final
        if current != out:
            run(["mv", str(current), str(out)], f"final {shot_num}")

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="B+ Repeat Blast composer")
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--dry-run", action="store=True")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = CONFIG_DIR / config_path.name
    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    out_dir = OUTPUT_DIR / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = out_dir / "temp_shots"
    temp_dir.mkdir(parents=True, exist_ok=True)

    storyboard = config["storyboard"]

    if args.dry_run:
        print(f"Dry run: {video_id} ({len(storyboard)} shots)")
        for s in storyboard:
            print(f"  Shot {s['shot']:2d} ({s['time']:10s}): {s['type']} "
                  f"{'vo='+s['vo'] if 'vo' in s else ''} "
                  f"{'overlay='+s['overlay'] if 'overlay' in s else ''}")
        return

    print(f"Composing: {video_id} ({len(storyboard)} shots)")

    shot_files: list[Path] = []
    for shot in storyboard:
        print(f"\n--- Shot {shot['shot']} ({shot['time']}) ---")
        sf = build_shot(shot, config, temp_dir, video_id)
        shot_files.append(sf)

    # Concat all shots
    concat_list = temp_dir / "shot_list.txt"
    concat_list.write_text("".join(f"file '{sf}'\n" for sf in shot_files))
    no_bgm = out_dir / f"{video_id}-no-bgm.mp4"
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p", "-r", "24",
        str(no_bgm),
    ], "CONCAT all shots")

    # BGM mixing
    final = out_dir / f"{video_id}-rough-cut.mp4"
    heartbeat = BGM_DIR / "heartbeat-60bpm.mp3"
    if heartbeat.exists():
        video_dur = get_duration(no_bgm)
        run([
            "ffmpeg", "-y",
            "-i", str(no_bgm),
            "-stream_loop", "-1", "-i", str(heartbeat),
            "-filter_complex",
            f"[1:a]volume=0.08,afade=t=in:st=0:d=2,afade=t=out:st={video_dur-3:.3f}:d=3[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(final),
        ], "FINAL+bgm")
    else:
        import shutil
        shutil.copy2(str(no_bgm), str(final))

    dur = get_duration(final)
    size = final.stat().st_size // (1024 * 1024)
    print(f"\nDONE: {final}")
    print(f"  Duration: {dur:.1f}s (target: 50s)")
    print(f"  Size: {size}MB")


if __name__ == "__main__":
    main()
```

**Step 2: Test with dry-run**

```bash
python3 docs/content/scripts/compose-repeat-blast.py \
  --config docs/content/config/unemploy-repeat-01-waitnotice.json --dry-run
```

Expected: Prints 21 shots without errors.

**Step 3: Commit**

```bash
git add docs/content/scripts/compose-repeat-blast.py
git commit -m "feat: add B+ repeat blast video composer script"
```

---

## Task 10: Run Full Composition

**Files:**
- Create: `docs/content/output/unemploy-repeat-01-waitnotice/unemploy-repeat-01-waitnotice-rough-cut.mp4`

**Step 1: Run the compose script**

```bash
python3 docs/content/scripts/compose-repeat-blast.py \
  --config docs/content/config/unemploy-repeat-01-waitnotice.json
```

Expected: ~50s MP4 at `docs/content/output/unemploy-repeat-01-waitnotice/`

**Step 2: Verify output**

```bash
ffprobe docs/content/output/unemploy-repeat-01-waitnotice/unemploy-repeat-01-waitnotice-rough-cut.mp4
```

Check: duration ~50s, resolution 1080x1920, has audio track.

**Step 3: Watch and check storyboard timing**

Play the rough cut and verify:
- [ ] 0-3s: Black screen with text, first "回去等通知吧"
- [ ] 3-18s: 4 interview clips with count badges, distinct voice tones
- [ ] 18-20s: Red flash
- [ ] 20-33s: Fast cuts with center text overlay
- [ ] 33-43s: Black silence, then "半年了。你...还在等吗？"
- [ ] 43-50s: "你等了多久？评论区"

**Step 4: Commit**

```bash
git add docs/content/output/unemploy-repeat-01-waitnotice/
git commit -m "feat: produce B+ repeat blast rough cut (Episode 01)"
```

---

## Task 11: Quality Check + Risk Checklist

**Step 1: Run the storyboard risk checklist**

- [ ] Any 2 "回去等通知吧" lines sound different (play LINE01 vs LINE06 vs LINE09)
- [ ] ESCALATION lines have distinct spatial character (pitch up/down/echo/slow)
- [ ] BREAK "半年了" sounds nothing like any PATTERN line
- [ ] No static frames > 3s (every segment has visual change)
- [ ] HOOK has ≥2 visual changes in first 3s (black→white text→red text→footage)

**Step 2: Note any issues for 剪映 post-production**

The following items are handled in 剪映 (not FFmpeg):
- Text rain effect (shot 13-14)
- Smoother transitions (flash white, flash red)
- Color grading (darken ESCALATION, warm up TRAP)
- Subtitle styling
- Final audio levels balancing

**Step 3: Document results**

Record findings in a brief note. If any major issues found, fix in compose script and re-run.

---

## Task 12: Generate Upload Copy

**Files:**
- Create: `docs/content/assets/upload-copy/unemploy-repeat-01-douyin.md`

**Step 1: Generate Douyin upload copy**

```markdown
# 抖音上传文案 — B+ 重复暴击 Episode 01

## 标题候选
1. 你已经听过这句话多少次了？
2. 回去等通知吧...半年了
3. 面试47次后我听懂了这句话

## 正文
回去等通知吧。
回去等通知吧。
回去等通知吧。

半年了。
你，还在等吗？

## 标签
#失业 #面试 #找工作 #裁员 #职场 #中年危机 #求职 #打工人

## 引导评论
你等了多久？评论区说说👇
```

**Step 2: Commit**

```bash
git add docs/content/assets/upload-copy/unemploy-repeat-01-douyin.md
git commit -m "feat: add Douyin upload copy for B+ repeat blast Episode 01"
```
