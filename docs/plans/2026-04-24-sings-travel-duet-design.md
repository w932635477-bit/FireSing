# Sings Travel Duet Design: 城市对唱

**Date**: 2026-04-24
**Status**: Approved
**Direction**: Sings workflow pivot from outfit comparison to city travel edu-duet

## Overview

A new content series using the Sings pipeline to produce 30-60 second "city edu-duet" videos. Yang Mun (AI character) introduces one city per episode through male-female duet singing, mixing official tourism footage with AI character visuals.

## Content Format

**Name**: 城市对唱 (working title)

**Structure per episode (30-60s)**:
- 0-3s: Opening hook — Yang Mun announces the city + a striking visual
- 3-45s: Duet body — Yang Mun (female, experiential perspective) + male vocal (knowledge perspective) sing about 2 city highlights
- 45-60s: Ending — next city teaser + engagement prompt ("下一站去哪？评论区告诉我！")

**Lyric structure**:
- 8-16 lines per episode, BPM 120-130
- Yang Mun lines: experiential/emotional ("火锅的辣让我尖叫")
- Male vocal lines: factual/historical ("轻轨穿楼是因为8D地形")
- Duet chorus: summary/emotional peak ("重庆，一座让你上瘾的城市")

**Visual composition**:
- 70% official tourism board footage (real footage, high quality, free)
- 30% Yang Mun AI visuals (Seedream + Kling, 2-4 scenes per episode)
- CapCut post-production: lyrics subtitles, info cards, transitions, AI content labels

## Technical Pipeline

```
Step 1: Topic & Lyrics
  └─ Select city → research 2 highlights → write duet lyrics (8-16 lines)

Step 2: Music Generation
  └─ Suno API → male-female duet → select best version

Step 3: Footage Preparation
  ├─ Download official tourism board footage for the city
  └─ Seedream generates Yang Mun "check-in" photos at city landmarks (2-4 images)

Step 4: AI Video Generation
  └─ Kling converts Yang Mun photos to 5-second video clips

Step 5: FFmpeg Compositing
  └─ Real footage + Yang Mun clips → assembled to match lyric beats

Step 6: CapCut Post-Production
  ├─ Dynamic lyric subtitles (K-style)
  ├─ Info cards (city name, highlight names)
  ├─ Transitions and effects
  └─ AI content labeling (compliance)
```

**Cost estimate**: ~$0.20-0.30/video (Suno + 2-4 Seedream images + 2-4 Kling clips)

**Comparison with existing Sings pipeline**:

| Component | Current Sings | Travel Duet |
|-----------|--------------|-------------|
| Visual source | 100% Seedream | 70% real footage + 30% Seedream |
| Kling usage | Every segment | Yang Mun scenes only (2-4 clips) |
| API cost | ~$0.50/video | ~$0.20-0.30/video |
| Footage source | None | Tourism board official footage |
| Character | Yang Mun + male (planned) | Yang Mun only (male = voice only) |
| Lyric style | Outfit/rap | City edu-duet |

## Character Design

**Yang Mun** (existing): Young Chinese woman, late 20s, round face, short black bob haircut, cream-colored linen shirt. Only visual character.

**Male role**: Voice only (Suno male vocal). No visual character design needed. Functions as accompaniment and knowledge perspective.

## Config Structure (Draft)

```json
{
  "video_id": "city-chongqing",
  "title": "重庆：8D魔幻城市",
  "platform": ["douyin", "xiaohongshu"],
  "duration_target": 45,
  "series": "sings-travel",
  "city": "重庆",
  "highlights": [
    {"name": "轻轨穿楼", "type": "attraction"},
    {"name": "九宫格火锅", "type": "food"}
  ],
  "official_footage": [
    {"description": "Chongqing monorail passing through building", "source_url": "..."}
  ],
  "ai_characters": {
    "yangmun": [
      {"scene": "standing on Chongqing hillside overlooking city at night"}
    ]
  },
  "music": {
    "style": "catchy upbeat pop duet, Chinese city pop, 125 bpm",
    "lyrics": "..."
  }
}
```

## Monetization Plan

### Phase 1: Content Accumulation (Days 0-30)
- Publish 15-20 episodes (1 per day or every other day)
- Dual platform: Douyin + Xiaohongshu
- Start with popular tourist cities
- Observe data: which cities, highlight types, music styles get best engagement
- Revenue: ¥0

### Phase 2: Commercial Partnership (Days 30-90)
- **Tourism board custom content** (primary): Use existing city content as portfolio, approach tourism boards. Pricing: ¥500-2000/episode
- **OTA affiliate commissions**: Ctrip/Fliggy affiliate links in video descriptions. Commission: 3-8% per booking
- **Knowledge products**: "AI travel music video production tutorial" at ¥99-299

### Phase 3: Scale (Days 90+)
- Standardize city content template library (lyric templates, music style templates)
- Batch production: scale from 1 to 2-3 episodes/day
- Expand to international cities (Pexels/Pixabay footage for international destinations)
- Develop B2B clients (travel agencies, OTAs, destination marketing companies)

## First Batch Cities

1. 重庆 (8D city, hotpot, monorail)
2. 成都 (pandas, mahjong, hotpot)
3. 西安 (terracotta warriors, city wall, street food)
4. 长沙 (spicy food, nightlife, Orange Isle)
5. 大理 (Erhai Lake, ancient town, wind/flower/snow/moon)
6. 厦门 (Gulangyu, seafood, Minnan culture)
7. 青岛 (beer, ocean, German architecture)
8. 杭州 (West Lake, Longjing tea, Song dynasty culture)

## Footage Sourcing Strategy

| City type | Source | Cost |
|-----------|--------|------|
| Domestic cities | Official tourism board promotional footage | Free |
| Yang Mun visuals | Seedream + Kling | $0.05-0.15/clip |
| International cities (future) | Pexels/Pixabay | Free |

Sources for tourism board footage:
- City tourism bureau official websites (各地文旅局官网)
- Douyin official accounts of tourism boards
- Government public media libraries
- Open media kits for content creators

## Key Decisions

1. **Format**: City edu-duet (not pure MV, not story, not pure documentary)
2. **Platform**: Douyin + Xiaohongshu dual publishing
3. **Character**: Yang Mun only visually; male is voice-only accompaniment
4. **Visuals**: Real tourism footage (70%) + AI Yang Mun (30%)
5. **Duration**: 30-60 seconds
6. **Content strategy**: One city per episode, 2 highlights per city
7. **Monetization**: Tourism board partnerships as primary revenue
