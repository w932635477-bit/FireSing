"""Chorus detection — identify chorus sections by lyric repetition."""

import logging
from collections import Counter

logger = logging.getLogger(__name__)


def detect(segments: list) -> list[str]:
    """Detect chorus segments by finding repeated lyric text.

    A segment is chorus if its text appears >= 2 times across all segments.

    Returns list of segment IDs identified as chorus.
    """
    if not segments:
        return []

    # Count text occurrences
    text_counts = Counter(seg.text for seg in segments)
    repeated_texts = {text for text, count in text_counts.items() if count >= 2}

    chorus_ids = []
    for seg in segments:
        if seg.text in repeated_texts:
            chorus_ids.append(seg.id)

    if chorus_ids:
        logger.info(f"Detected {len(chorus_ids)} chorus segments out of {len(segments)}")

    return chorus_ids
