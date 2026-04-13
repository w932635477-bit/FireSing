"""Voice profile presets — 8 built-in voice profiles seeded on startup."""

import logging

from sqlalchemy.orm import Session

from ..models import VoiceModel

logger = logging.getLogger(__name__)

VOICE_PROFILES = [
    {
        "name": "原声女",
        "pitch_shift": 0.0,
        "formant_shift": 0.0,
        "eq_profile": "natural",
        "color": "#FF69B4",
    },
    {
        "name": "高亮女声",
        "pitch_shift": 2.0,
        "formant_shift": 1.5,
        "eq_profile": "bright",
        "color": "#FF6347",
    },
    {
        "name": "温柔女声",
        "pitch_shift": 1.0,
        "formant_shift": -0.5,
        "eq_profile": "dark",
        "color": "#DDA0DD",
    },
    {
        "name": "原声男",
        "pitch_shift": 0.0,
        "formant_shift": 0.0,
        "eq_profile": "natural",
        "color": "#4169E1",
    },
    {
        "name": "浑厚男声",
        "pitch_shift": -2.0,
        "formant_shift": -1.5,
        "eq_profile": "deep",
        "color": "#8B4513",
    },
    {
        "name": "清亮男声",
        "pitch_shift": 1.0,
        "formant_shift": 1.0,
        "eq_profile": "bright",
        "color": "#00CED1",
    },
    {
        "name": "鼻音歌手",
        "pitch_shift": 0.5,
        "formant_shift": 2.0,
        "eq_profile": "nasal",
        "color": "#FF8C00",
    },
    {
        "name": "低沉男声",
        "pitch_shift": -3.0,
        "formant_shift": -2.0,
        "eq_profile": "dark",
        "color": "#2F4F4F",
    },
]


def seed_presets(db: Session) -> int:
    """Seed voice profile presets if they don't exist.

    Returns number of new presets created.
    """
    existing = db.query(VoiceModel).filter(VoiceModel.is_preset == True).count()
    if existing >= len(VOICE_PROFILES):
        logger.info(f"Presets already seeded ({existing} profiles)")
        return 0

    # Clear any partial presets and re-seed
    db.query(VoiceModel).filter(VoiceModel.is_preset == True).delete()

    count = 0
    for preset in VOICE_PROFILES:
        vm = VoiceModel(
            is_preset=True,
            **preset,
        )
        db.add(vm)
        count += 1

    db.commit()
    logger.info(f"Seeded {count} voice profile presets")
    return count
