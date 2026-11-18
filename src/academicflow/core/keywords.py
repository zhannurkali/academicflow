"""Keyword extraction.

Owner: Member 1.
"""

from __future__ import annotations


def extract_keywords(text: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Extract the most important phrases.

    Args:
        text: Input text.
        top_n: Maximum number of keywords.

    Returns:
        ``(phrase, score)`` pairs, best first, scores in 0-1.

    TODO(member 1): RAKE/TF scoring with the bundled stopword list.
    """
    return []
