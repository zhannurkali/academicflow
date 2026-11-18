"""Single-text style rules.

Owner: Member 2.
"""

from __future__ import annotations

from academicflow.types import Issue


def check(text: str, profile: str = "apa", section: str | None = None) -> list[Issue]:
    """Check one piece of text against a venue profile.

    Args:
        text: Text to check.
        profile: Profile name or YAML path.
        section: Optional section name, enables section-aware rules.

    Returns:
        Issues sorted by offset.

    TODO(member 2): informal-word, contraction, first-person, long-sentence,
    repeated-word, repeated-phrase, hedge words, section rules.
    """
    return []
