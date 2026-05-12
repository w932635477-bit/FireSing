#!/usr/bin/env python3
"""
Gemini 3.1 Flash TTS Batch Voiceover Generator (config-driven)
Uses Google Gemini with advanced prompting (Director's Notes + audio tags).

Usage:
  source docs/content/.env
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json --shot S01 --dry-run
  python3 gemini-tts-batch.py --config config/day1-medvi-story.json --voice Charon
"""

import argparse
import json
import os
import struct
import subprocess
import sys
import time
import wave
from datetime import datetime
from pathlib import Path
import re

from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover"
DEFAULT_CONFIG_DIR = PROJECT_ROOT / "docs" / "content" / "config"

VOICES = [
    "Charon", "Orus", "Iapetus", "Sadaltager", "Sulafat",
    "Puck", "Fenrir", "Kore", "Aoede", "Ledas",
    "Enceladus", "Zephyr", "Vindemiatrix", "Leda", "Sadachbia",
]

# Unified narrator profile — same person throughout the whole video
NARRATOR_PROFILE_MALE = (
    "You are a Chinese male narrator telling a compelling story in a Douyin short video. "
    "Speak Mandarin naturally and warmly, as if sharing an amazing discovery with a friend. "
    "You have a confident, grounded voice with natural emotional range."
)

NARRATOR_PROFILE_FEMALE = (
    "You are a Chinese female narrator telling a compelling story in a Douyin short video. "
    "Speak Mandarin naturally and warmly, as if sharing an amazing discovery with a friend. "
    "You have a confident, clear voice with natural emotional range."
)

# Unemployment series narrator — first person, male, 38yo laid-off worker
NARRATOR_PROFILE_UNEMPLOY = (
    "你是一个38岁的中国男性，在外企工作了15年后被裁员。"
    "你在讲述自己的真实经历，不是旁白，是第一人称自述。"
    "语气自然，像跟老朋友聊天，不要播音腔。声音沉稳但带着真实情感。"
)

NARRATOR_PROFILE_QIDIAN = (
    "你是一个见过世面的中年男人，40多岁。"
    "你不是来安慰人的，你是来说实话的。"
    "你的语气像饭局上那个最敢说话的人——"
    "别人都客气，你直接掀桌子看底牌。"
    "不愤怒，不煽情，就是平实地把真相摆出来。"
    "语速适中偏快，30秒内必须出现第一个信息爆点。"
    "每条至少一句态度句——有立场、能截图、能当朋友圈文案的话。"
)

NARRATOR_PROFILE = NARRATOR_PROFILE_UNEMPLOY

NARRATOR_SCENE = "第一人称讲述被裁47天后靠翻通讯录赚到第一个5000块的经历。"

# Emotion arc → Director's Notes only (same narrator, different emotional delivery)
EMOTION_PROMPTS = {
    "empathy": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Open with genuine amazement at the numbers. Use [amazed] at the key figure. Sound like you just discovered something incredible and can't wait to share it. Natural, conversational energy.",
    },
    "desire": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Shift to a more reflective, storytelling tone. Paint the humble beginnings vividly. Use [softly] to create intimacy. Slow down slightly. This is backstory, let it breathe.",
    },
    "hope": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Build momentum. List the AI capabilities with quiet excitement. Use [warmly] when describing the tools. This is the 'aha' moment where the listener sees the path forward.",
    },
    "shock": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Deliver the financial data with controlled impact. Use [confidently] for the numbers. Not shouting — let the data speak. A slight pause before each key figure adds weight.",
    },
    "contrast": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "This is the punchline. Use [serious] for the industry giants, then shift to subtle [impressed] satisfaction for the underdog's numbers. The contrast should feel earned, not forced.",
    },
    "joy": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Light, upbeat energy. Use [cheerfully] naturally. The daily revenue figure should land with a sense of 'can you believe this?' Don't oversell — let the number do the work.",
    },
    "trust": {
        "profile": NARRATOR_PROFILE,
        "scene": NARRATOR_SCENE,
        "director": "Warm, direct invitation. Use [warmly] and speak with quiet certainty. This is a friend making a genuine recommendation, not a sales pitch. End with natural conviction.",
    },
    # Yang Mun character emotions (Day4)
    "determined": {
        "profile": NARRATOR_PROFILE,
        "scene": "Narrating a business efficiency video exposing wasted human labor.",
        "director": "Speak with quiet anger and conviction. Use [confidently] to call out inefficiency. Not shouting, but firm. Each sentence should land like a fact, not an opinion. Slow down before the key insight.",
    },
    "power": {
        "profile": NARRATOR_PROFILE,
        "scene": "Delivering business rules that separate winners from losers.",
        "director": "Authority mode. Use [seriously] for the rule, then [impressed] for the result. Let numbers hit hard. Short pauses between statements. Sound like someone who has seen this truth firsthand.",
    },
    "contemplative": {
        "profile": NARRATOR_PROFILE,
        "scene": "Reflecting on what speed really means for survival.",
        "director": "Slow down. Use [thoughtfully] throughout. This is reflection, not attack. Each example should feel like turning a page. End with quiet certainty, not aggression.",
    },
    "warm": {
        "profile": NARRATOR_PROFILE,
        "scene": "Turning business lessons into a personal call to action.",
        "director": "Drop the authority. Use [warmly] and speak like a friend who genuinely cares. The shift from business data to 'you' should feel natural. End with gentle invitation, not pressure.",
    },
    # Day7 emotion arcs
    "tension": {
        "profile": NARRATOR_PROFILE,
        "scene": "Delivering an uncomfortable truth about busywork and wasted effort.",
        "director": "Build tension steadily. Use [seriously] to state the iron law. List examples with quiet intensity, each one sharper than the last. Not angry, but firm. End with the punchline landing like a verdict.",
    },
    "reversal": {
        "profile": NARRATOR_PROFILE,
        "scene": "Revealing a counterintuitive insight that changes the listener's perspective.",
        "director": "Start with the conventional wisdom, then flip it. Use [thoughtfully] for the setup, [impressed] for the reveal. The data point should feel like a plot twist. Slow down before the key figure.",
    },
    "fear": {
        "profile": NARRATOR_PROFILE,
        "scene": "Describing a vicious cycle that traps people in mediocrity.",
        "director": "Speak with controlled urgency. Use [seriously] for the cycle, then [softly] for the escape. Each repetition of the trap should feel heavier. End with quiet hope, not despair.",
    },
    # Unemployment series emotions (first-person male)
    "好奇": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "开场告诉朋友一个意外的结果。",
        "director": "像跟朋友说'你猜怎么着'一样开场。语气轻松带悬念，不要太沉重。说完数字后稍微停顿，让听众消化。结尾'翻通讯录'三个字稍微加重，制造好奇。",
    },
    "代入": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "开场跟朋友吐槽自己投简历的经历。",
        "director": "像跟老朋友聊天，不是演讲。开口要自然。念数字'847'的时候要慢，一个字一个字念，像在回忆一个自己都不敢相信的数字。'该去买彩票'要带一点苦笑，不是真的觉得好笑，是那种'我能怎么办呢'的笑。允许语气词：嗯、说实话、你知道吗、你说。偶尔停顿一下，像在想怎么说。",
    },
    "共鸣": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "自嘲自己连废纸都不如。",
        "director": "先正常叙述，到了'废纸'那句声音要轻。然后停顿。'嗯...说实话'之后转成自嘲语气。'五毛钱一斤'要说得漫不经心，'我连这个价都没有'要轻，像自言自语。不是愤怒，是那种苦笑到麻木的感觉。结尾不要收太干净，留一点余味。",
    },
    "希望": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "转折点，发现经验能卖钱。",
        "director": "前面讲群里的事要平淡，像回忆一件普通的事。'哥你太专业了'那句话可以稍微模仿一下对方语气。然后'那天晚上我睡不着'之后要明显停顿。'不是激动'稍顿。'是后悔'要重。最后一句'这玩意儿还能卖钱'要带一种不可思议的感觉，像突然发现了什么。",
    },
    "力量": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "从过来人的角度给同样处境的人力量。",
        "director": "安静笃定，不是说教，是确认。像一个已经走出来的人回头告诉你'你身上的东西比你以为的多'。不煽情，不反问，用陈述句传递力量。语速适中，每个短句之间有呼吸空间。",
    },
    "参与": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "放下故事，直接问听众。",
        "director": "从讲故事切换到直接对话。语气放松，像朋友问一句'你投了多少了？'。不要严肃，不要煽情，就一个自然的邀请。最后'评论区说说'要轻松，像随口一说。",
    },
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
    # Day1 v4 emotions: 40岁失业，我值几块钱？
    "anxious": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "失业第47天，每天醒来就数日子。",
        "director": "开口就带焦虑。'47天'三个字说得不快不慢，像在确认一个让人不安的事实。声音微微发紧，不是恐惧，是不安。结尾不要收太干净，留一点悬着的感觉。",
    },
    "bitter": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "投了两百封简历，石沉大海。",
        "director": "苦涩的自嘲。数字'两百'说得平淡，像在说别人的事。但语气底下是苦的，不是愤怒，是那种'我还能怎么办'的无奈。语速稍慢，每个字都带着疲惫。",
    },
    "desperate": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "零回复。所有的努力像被黑洞吞了。",
        "director": "声音要轻，像在说一个让自己绝望的事实。'零'字可以稍微拖一点，带着不敢相信。不是崩溃，是那种已经绝望到麻木的感觉。结尾声音往下走，像叹气。",
    },
    "hopeful": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "转机出现了。经验居然能变现。",
        "director": "语气从低谷开始往上走。开头还是平淡的叙述，到关键句时声音明显亮起来。不是兴奋，是那种'等等，这有可能？'的谨慎希望。语速比前面稍快，带着一丝急切。",
    },
    # Day3 AI portrait challenge emotions
    "pivot_attempt": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "第一次尝试失败，换了个方法再试。",
        "director": "语气从低落突然转成'等等，我换个思路'的感觉。不是兴奋，是冷静分析后的调整。说得干脆，像在说给自己听。语速稍快，句尾不要拖。",
    },
    # Override warm for Day1 unemployment context
    "warm_unemploy": {
        "profile": NARRATOR_PROFILE_UNEMPLOY,
        "scene": "发现经验有市场价值，从绝望中走出来。",
        "director": "像跟朋友说'你知道吗，原来我还有点用'。语气温暖但不煽情。'原来我值钱'五个字说得不快，每个字带着一种释然。不是得意，是松了一口气的感觉。结尾自然，不要刻意收束。",
    },
    # Qidian 启点系列 emotions (40+ 中年男人说实话)
    "calmly_qidian": {
        "profile": NARRATOR_PROFILE_QIDIAN,
        "scene": "饭局上那个最敢说话的人，平静地把真相摆出来。",
        "director": "平静陈述事实，不煽情不愤怒。像在饭局上随手翻开底牌。语速适中偏快，每句话都是确认不是疑问。关键数字说完稍微停顿，让数字自己说话。保持自然换气节奏，在逗号和句号处正常呼吸，不要憋气读完一整段。像真人说话一样有呼吸间隔。",
    },
    "shock_qidian": {
        "profile": NARRATOR_PROFILE_QIDIAN,
        "scene": "抛出对比数字，让观众自己感受差距。",
        "director": "语速要快，5秒内说完。两个数字做对比，不要停顿，一句接一句。前一个大数字说得干脆，后一个小数字说得轻快。整体节奏紧凑，像机关枪报数。",
    },
    "simply_qidian": {
        "profile": NARRATOR_PROFILE_QIDIAN,
        "scene": "一句话点破真相，态度句。",
        "director": "简单直接，不加修饰。这句话要说得像真理，不是观点。语速稍慢，每个字清楚。说完不要急，让这句话在空气里停一下。这句话要能截图、能当朋友圈文案。保持自然换气节奏，在逗号和句号处正常呼吸，不要憋气读完一整段。像真人说话一样有呼吸间隔。",
    },
    "confidently_qidian": {
        "profile": NARRATOR_PROFILE_QIDIAN,
        "scene": "笃定地给出承诺，从明天开始。",
        "director": "笃定有力，不犹豫。像在跟朋友约好明天见面一样自然。'从明天开始'要有节奏感，不是命令是邀请。结尾'变成自己的收入'说得稳，像已经看到结果了。",
    },
    "quietly_qidian": {
        "profile": NARRATOR_PROFILE_QIDIAN,
        "scene": "凑近说秘密，压低声音揭底。",
        "director": "压低声音，像凑近说的秘密。不是神秘，是认真。每个字都清楚但比正常说话轻。说完关键信息后停顿，让听众消化。结尾自然收束。保持自然换气节奏，在逗号和句号处正常呼吸，不要憋气读完一整段。像真人说话一样有呼吸间隔。",
    },
}

AUDIO_TAGS = {
    "empathy": ["[amazed]", "[curious]"],
    "desire": ["[softly]", "[thoughtfully]"],
    "hope": ["[warmly]", "[gently]"],
    "shock": ["[gasps]", "[excitedly]"],
    "contrast": ["[serious]", "[impressed]"],
    "joy": ["[cheerfully]", "[laughing]"],
    "trust": ["[warmly]", "[confidently]"],
    "determined": ["[confidently]", "[seriously]"],
    "power": ["[seriously]", "[impressed]"],
    "contemplative": ["[thoughtfully]", "[softly]"],
    "warm": ["[warmly]", "[gently]"],
    "tension": ["[seriously]", "[confidently]"],
    "reversal": ["[thoughtfully]", "[impressed]"],
    "fear": ["[seriously]", "[softly]"],
    "好奇": ["[curious]", "[gently]"],
    "代入": ["[softly]", "[thoughtfully]"],
    "共鸣": ["[seriously]", "[softly]"],
    "希望": ["[warmly]", "[gently]"],
    "力量": ["[confidently]", "[warmly]"],
    "参与": ["[cheerfully]", "[warmly]"],
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
    "anxious": ["[nervously]", "[tense]"],
    "bitter": ["[resigned]", "[bitter]"],
    "desperate": ["[softly]", "[defeated]"],
    "hopeful": ["[warmly]", "[hopefully]"],
    "warm_unemploy": ["[warmly]", "[relieved]"],
    "pivot_attempt": ["[calmly]", "[analytical]"],
    "calmly_qidian": ["[calmly]", "[steadily]"],
    "shock_qidian": ["[calmly]", "[firmly]"],
    "simply_qidian": ["[simply]", "[directly]"],
    "confidently_qidian": ["[confidently]", "[warmly]"],
    "quietly_qidian": ["[quietly]", "[intimately]"],
}


def get_audio_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, timeout=10,
    )
    return float(result.stdout.strip())


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def strip_pause_markers(text: str) -> str:
    return re.sub(r"<#\d+\.?\d*#>", "", text)


def save_pcm_as_wav(pcm_data: bytes, output_path: Path, sample_rate: int = 24000,
                    sample_width: int = 2, channels: int = 1) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)


def build_prompt(seg: dict, emotion: str) -> str:
    """Build advanced prompt with Profile + Scene + Director's Notes."""
    text = strip_pause_markers(seg.get("voiceover_pause_markers", seg.get("voiceover_text", "")))
    tags = AUDIO_TAGS.get(emotion, [])
    tagged_text = f"{tags[0]} {text}" if tags else text

    ep = EMOTION_PROMPTS.get(emotion, {})
    profile = ep.get("profile", "You are a Chinese male narrator. Speak Mandarin naturally.")
    scene = ep.get("scene", "Narrating a short video segment.")
    director = ep.get("director", "Speak naturally and clearly.")

    return f"""Audio Profile: {profile}

Scene: {scene}

Director's Notes: {director}

Transcript: {tagged_text}"""


def synthesize(client: genai.Client, text_prompt: str, voice: str,
               output_path: Path) -> dict:
    response = client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=text_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )

    audio_part = response.candidates[0].content.parts[0]
    pcm_data = audio_part.inline_data.data

    wav_path = output_path.with_suffix(".wav")
    save_pcm_as_wav(pcm_data, wav_path)

    mp3_path = output_path.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-ar", "44100",
         "-ac", "1", "-b:a", "192k", str(mp3_path)],
        capture_output=True, timeout=30,
    )
    # Keep WAV source file (don't delete)

    duration_s = get_audio_duration(mp3_path)
    return {"duration_s": duration_s, "file_size": mp3_path.stat().st_size}


def generate_srt(segments: list[dict], output_path: Path) -> None:
    entries = []
    cumulative = 0.0
    for i, seg in enumerate(segments):
        duration = seg["actual_duration_s"]
        start = cumulative
        end = cumulative + duration
        text = seg.get("voiceover_text", "")
        entries.append(f"{i + 1}\n{format_srt_time(start)} --> {format_srt_time(end)}\n{text}\n")
        cumulative = end
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))


def concatenate_audio(segment_files: list[Path], output_path: Path) -> None:
    concat_list = output_path.parent / "_concat.txt"
    with open(concat_list, "w") as f:
        for path in segment_files:
            f.write(f"file '{path}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_list), "-c:a", "libmp3lame", "-b:a", "192k", str(output_path)],
        capture_output=True, timeout=60,
    )
    concat_list.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Gemini TTS (config-driven)")
    parser.add_argument("--config", type=str, required=True, help="Video config JSON file")
    parser.add_argument("--voice", type=str, default="Charon",
                        help=f"Voice name ({', '.join(VOICES[:5])} recommended)")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--shot", type=str, help="Generate only this segment (e.g., S01)")
    parser.add_argument("--delay", type=float, default=25.0,
                        help="Delay between requests in seconds (free tier: 25s)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--female", action="store_true", help="Use female narrator profile")
    parser.add_argument("--yunwu-only", action="store_true", help="Skip Google, use yunwu.ai directly")
    parser.add_argument("--no-doubao", action="store_true", help="Disable Doubao fallback (fail instead)")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = DEFAULT_CONFIG_DIR / config_path
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    video_id = config["video_id"]
    segments = config.get("segments", [])
    if not segments:
        print("ERROR: No segments in config")
        sys.exit(1)

    voice = args.voice
    output_dir = Path(args.output_dir) / video_id

    if args.female:
        print(f"  Note: Using female narrator profile (Aoede voice)")
        global NARRATOR_PROFILE
        NARRATOR_PROFILE = NARRATOR_PROFILE_FEMALE
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.shot:
        segments = [s for s in segments if s["id"] == args.shot.upper()]
        if not segments:
            print(f"Shot {args.shot} not found")
            sys.exit(1)

    print(f"Gemini TTS — {video_id}")
    print("=" * 50)
    print(f"Model: gemini-3.1-flash-tts-preview")
    print(f"Voice: {voice}")
    print(f"Output: {output_dir}")
    print(f"Channel priority: Google → 云雾AI → Doubao")
    print()

    if args.dry_run:
        print("DRY RUN")
        for seg in segments:
            emotion = seg.get("emotion", "")
            prompt = build_prompt(seg, emotion)
            print(f"  {seg['id']} [{emotion}]:")
            print(f"    Text: {seg.get('voiceover_text', '')[:60]}...")
            ep = EMOTION_PROMPTS.get(emotion, {})
            print(f"    Profile: {ep.get('profile', '')[:60]}...")
            print(f"    Director: {ep.get('director', '')[:60]}...")
            print()
        return

    google_key = os.environ.get("GEMINI_API_KEY")
    yunwu_key = os.environ.get("YUNWU_API_KEY")
    yunwu_base = os.environ.get("YUNWU_BASE_URL", "https://yunwu.ai")

    if not google_key and not yunwu_key:
        print("ERROR: No API key set (GEMINI_API_KEY or YUNWU_API_KEY)")
        print("Get Google key: https://aistudio.google.com/apikey")
        sys.exit(1)

    google_client = None if args.yunwu_only else (genai.Client(api_key=google_key) if google_key else None)
    yunwu_client = (
        genai.Client(api_key=yunwu_key, http_options={"base_url": yunwu_base})
        if yunwu_key else None
    )
    client = yunwu_client if args.yunwu_only else (google_client or yunwu_client)
    active_channel = "yunwu" if args.yunwu_only else "google"
    print(f"Channel: Google (direct) → 云雾AI (fallback) → Doubao (last resort)")
    if yunwu_client:
        print(f"  云雾AI ready: {yunwu_base}")
    else:
        print("  云雾AI: not configured (no YUNWU_API_KEY)")

    def _is_quota_error(error: Exception) -> bool:
        msg = str(error).lower()
        return any(kw in msg for kw in ["429", "quota", "resource_exhausted", "403", "permission", "503", "unavailable", "high demand"])

    no_doubao = args.no_doubao

    def _synthesize_doubao(seg: dict, dest: Path) -> dict:
        """Fallback: synthesize via Doubao TTS. Returns {duration_s, file_size}."""
        import base64
        import importlib.util
        # Import from sibling script
        spec = importlib.util.spec_from_file_location(
            "doubao_tts_batch",
            str(Path(__file__).resolve().parent / "doubao-tts-batch.py"),
        )
        dtb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dtb)
        doubao_key = os.environ.get("MODEL_SPEECH_API_KEY")
        if not doubao_key:
            raise RuntimeError("MODEL_SPEECH_API_KEY not set for Doubao fallback")
        voice_id = dtb.resolve_voice("default_female")
        emotion = seg.get("emotion", seg.get("emotion_arc", "shock"))
        raw_text = seg.get("voiceover_pause_markers", seg.get("voiceover_text", ""))
        ref_audio_b64 = None
        voiceover_cfg = config.get("voiceover", {})
        if voiceover_cfg.get("ref_audio") == "claire":
            ref_path = PROJECT_ROOT / "docs" / "content" / "assets" / "voiceover" / "_ref_audio" / "day4-gemini.mp3"
            if ref_path.exists():
                with open(ref_path, "rb") as f:
                    ref_audio_b64 = base64.b64encode(f.read()).decode()
        return dtb.synthesize_segment(doubao_key, raw_text, voice_id, emotion, dest, ref_audio_b64=ref_audio_b64)

    use_doubao = False
    use_yunwu = args.yunwu_only
    results = []
    total_duration = 0.0

    for i, seg in enumerate(segments):
        text = seg.get("voiceover_text", "")
        emotion = seg.get("emotion", seg.get("emotion_arc", ""))
        if not text:
            print(f"  [{seg['id']}] SKIPPED — no text")
            continue

        if i > 0 and not use_doubao and not use_yunwu:
            print(f"  Waiting {args.delay}s (rate limit)...", flush=True)
            time.sleep(args.delay)

        dest = output_dir / f"{seg['id']}.mp3"
        prompt = build_prompt(seg, emotion)

        print(f"[{seg['id']}] [{seg.get('emotion_arc', '')}] {text[:50]}...")

        if use_doubao:
            print("  Synthesizing (Doubao)... ", end="", flush=True)
            try:
                info = _synthesize_doubao(seg, dest)
                total_duration += info["duration_s"]
                print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                results.append({
                    "segment": seg["id"], "file": str(dest),
                    "duration_s": info["duration_s"], "status": "success",
                    "actual_duration_s": info["duration_s"],
                    "voiceover_text": text, "engine": "doubao_fallback",
                })
            except Exception as e:
                print(f"failed: {e}")
                results.append({"segment": seg["id"], "status": "error", "error": str(e)})
            continue

        if use_yunwu:
            print("  Synthesizing (云雾AI)... ", end="", flush=True)
            try:
                info = synthesize(yunwu_client, prompt, voice, dest)
                total_duration += info["duration_s"]
                print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                results.append({
                    "segment": seg["id"], "file": str(dest),
                    "duration_s": info["duration_s"], "status": "success",
                    "actual_duration_s": info["duration_s"],
                    "voiceover_text": text, "engine": "yunwu_gemini",
                })
            except Exception as e:
                if _is_quota_error(e) or "503" in str(e):
                    print(f"云雾AI failed: {e}")
                    if no_doubao:
                        print("  Doubao disabled (--no-doubao). Waiting 60s and retrying yunwu...")
                        time.sleep(60)
                        try:
                            info = synthesize(yunwu_client, prompt, voice, dest)
                            total_duration += info["duration_s"]
                            print(f"  Retry done ({info['duration_s']:.1f}s)")
                            results.append({
                                "segment": seg["id"], "file": str(dest),
                                "duration_s": info["duration_s"], "status": "success",
                                "actual_duration_s": info["duration_s"],
                                "voiceover_text": text, "engine": "yunwu_gemini_retry",
                            })
                            continue
                        except Exception as e_retry:
                            print(f"  Retry also failed: {e_retry}")
                            results.append({"segment": seg["id"], "status": "error", "error": str(e_retry)})
                            continue
                    print(f"  Falling back to Doubao TTS")
                    use_doubao = True
                    try:
                        info = _synthesize_doubao(seg, dest)
                        total_duration += info["duration_s"]
                        print(f"  Doubao done ({info['duration_s']:.1f}s)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "doubao_fallback",
                        })
                    except Exception as e2:
                        print(f"  Doubao also failed: {e2}")
                        results.append({"segment": seg["id"], "status": "error", "error": str(e2)})
                else:
                    print(f"failed: {e}")
                    results.append({"segment": seg["id"], "status": "error", "error": str(e)})
            continue

        print(f"  Synthesizing (Google direct)... ", end="", flush=True)

        try:
            info = synthesize(google_client, prompt, voice, dest)
            total_duration += info["duration_s"]
            print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
            ep = EMOTION_PROMPTS.get(emotion, {})
            print(f"    director: {ep.get('director', '')[:50]}...")
            results.append({
                "segment": seg["id"], "file": str(dest),
                "duration_s": info["duration_s"], "status": "success",
                "actual_duration_s": info["duration_s"],
                "voiceover_text": text,
                "director_notes": ep.get("director", ""),
            })
        except Exception as e:
            if _is_quota_error(e):
                print(f"\n  Google quota exceeded!")
                if yunwu_client:
                    use_yunwu = True
                    print(f"  Retrying {seg['id']} with 云雾AI... ", end="", flush=True)
                    try:
                        info = synthesize(yunwu_client, prompt, voice, dest)
                        total_duration += info["duration_s"]
                        print(f"done ({info['duration_s']:.1f}s, {info['file_size'] // 1024}KB)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "yunwu_gemini",
                        })
                    except Exception as e2:
                        print(f"云雾AI failed: {e2}")
                        if no_doubao:
                            print("  Doubao disabled (--no-doubao). Waiting 60s and retrying yunwu...")
                            time.sleep(60)
                            try:
                                info = synthesize(yunwu_client, prompt, voice, dest)
                                total_duration += info["duration_s"]
                                print(f"  Retry done ({info['duration_s']:.1f}s)")
                                results.append({
                                    "segment": seg["id"], "file": str(dest),
                                    "duration_s": info["duration_s"], "status": "success",
                                    "actual_duration_s": info["duration_s"],
                                    "voiceover_text": text, "engine": "yunwu_gemini_retry",
                                })
                            except Exception as e_retry:
                                print(f"  Retry also failed: {e_retry}")
                                results.append({"segment": seg["id"], "status": "error", "error": str(e_retry)})
                            continue
                        print(f"  Falling back to Doubao TTS")
                        use_doubao = True
                        try:
                            info = _synthesize_doubao(seg, dest)
                            total_duration += info["duration_s"]
                            print(f"  Doubao done ({info['duration_s']:.1f}s)")
                            results.append({
                                "segment": seg["id"], "file": str(dest),
                                "duration_s": info["duration_s"], "status": "success",
                                "actual_duration_s": info["duration_s"],
                                "voiceover_text": text, "engine": "doubao_fallback",
                            })
                        except Exception as e3:
                            print(f"  Doubao also failed: {e3}")
                            results.append({"segment": seg["id"], "status": "error", "error": str(e3)})
                else:
                    if no_doubao:
                        print("  No 云雾AI configured and Doubao disabled. Giving up.")
                        results.append({"segment": seg["id"], "status": "error", "error": "No Gemini channel available"})
                        continue
                    print(f"  No 云雾AI configured, falling back to Doubao TTS")
                    use_doubao = True
                    try:
                        info = _synthesize_doubao(seg, dest)
                        total_duration += info["duration_s"]
                        print(f"  Doubao done ({info['duration_s']:.1f}s)")
                        results.append({
                            "segment": seg["id"], "file": str(dest),
                            "duration_s": info["duration_s"], "status": "success",
                            "actual_duration_s": info["duration_s"],
                            "voiceover_text": text, "engine": "doubao_fallback",
                        })
                    except Exception as e2:
                        print(f"  Doubao also failed: {e2}")
                        results.append({"segment": seg["id"], "status": "error", "error": str(e2)})
            else:
                print(f"failed: {e}")
                results.append({"segment": seg["id"], "status": "error", "error": str(e)})

    successful = [r for r in results if r["status"] == "success"]

    if successful:
        srt_path = output_dir / f"{video_id}-subtitles-gemini.srt"
        generate_srt(successful, srt_path)
        print(f"\nSRT saved: {srt_path}")

        full_path = output_dir / f"{video_id}-full-narration-gemini.mp3"
        seg_files = [Path(r["file"]) for r in successful]
        concatenate_audio(seg_files, full_path)
        print(f"Full narration: {full_path}")

    log_path = output_dir / f"gemini-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "engine": "gemini-3.1-flash-tts-preview",
            "voice_id": voice,
            "video_id": video_id,
            "total_duration_s": round(total_duration, 2),
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 50}")
    print(f"Done: {len(successful)} succeeded, {len(results) - len(successful)} failed")
    print(f"Total: {total_duration:.1f}s")
    if total_duration > 60:
        print("WARNING: Exceeds 60s limit!")
    elif total_duration < 30:
        print("WARNING: Below 30s minimum!")


if __name__ == "__main__":
    main()
