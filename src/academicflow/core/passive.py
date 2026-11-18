"""Passive-voice detection.

Owner: Member 1.
"""

from __future__ import annotations

from academicflow.types import Issue


def detect_passive(text: str) -> list[Issue]:
    """Find passive-voice constructions.

    Returns:
        Issues with ``rule="passive-voice"`` and ``severity="info"``.

    TODO(member 1): be-verb + past participle heuristic, spaCy when installed.
    """
    return []
