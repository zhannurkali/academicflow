"""Syllable counting, readability formulas and basic text counts."""

from __future__ import annotations

import re

from academicflow.core.text import split_sentences, tokenize
from academicflow.types import TextStats

__all__ = ["WORDS_PER_MINUTE", "analyze", "basic_counts", "count_syllables", "readability"]

WORDS_PER_MINUTE = 238

_VOWELS = "aeiouy"
_VOWEL_GROUP = re.compile(r"[aeiouy]+")
_HYPHENS = re.compile(r"[-\u2010\u2011\u2013]")

# Words the vowel-group heuristic gets wrong (common in academic writing).
_EXCEPTIONS = {
    "science": 2,
    "scientific": 4,
    "scientist": 3,
    "create": 2,
    "creative": 3,
    "area": 3,
    "idea": 3,
    "media": 3,
    "various": 3,
    "variable": 4,
    "variables": 4,
    "variance": 3,
    "variation": 4,
    "theory": 3,
    "quiet": 2,
    "being": 2,
    "individual": 5,
    "usually": 4,
    "layer": 2,
    "player": 2,
    "poem": 2,
    "trial": 2,
    "dual": 2,
    "bias": 2,
    "client": 2,
    "coefficient": 4,
}


def count_syllables(word: str) -> int:
    """Estimate the number of syllables in a word.

    Uses vowel groups, a silent-e rule (also for -ed and -es endings), keeps -le endings
    after a consonant, and a small table of exceptions. Hyphenated words are counted
    part by part.

    Args:
        word: A single word (may contain hyphens, digits or apostrophes).

    Returns:
        Syllable count, at least 1 for any word containing letters. Returns 0 for an empty
        string or a token without letters (for example ``"123"``).

    Example:
        >>> count_syllables("analysed")
        3
    """
    parts = [p for p in _HYPHENS.split(word.lower()) if p]
    return sum(_syllables_in_part(p) for p in parts)


def readability(text: str) -> dict[str, float]:
    """Compute Flesch Reading Ease and Flesch-Kincaid Grade Level.

    Args:
        text: Plain or Markdown text.

    Returns:
        Dict with keys ``"flesch_reading_ease"`` and ``"flesch_kincaid_grade"``, rounded to
        two decimals. Both are 0.0 for empty text.

    Example:
        >>> readability("The cat sat on the mat.")["flesch_kincaid_grade"]
        -1.45
    """
    tokens = tokenize(text)
    if not tokens:
        return {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}
    sentences = max(1, len(split_sentences(text)))
    syllables = sum(max(1, count_syllables(t)) for t in tokens)
    words_per_sentence = len(tokens) / sentences
    syllables_per_word = syllables / len(tokens)
    ease = 206.835 - 1.015 * words_per_sentence - 84.6 * syllables_per_word
    grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
    return {
        "flesch_reading_ease": round(ease, 2),
        "flesch_kincaid_grade": round(grade, 2),
    }


def basic_counts(text: str) -> dict[str, float]:
    """Count words and sentences and estimate reading time.

    Args:
        text: Plain or Markdown text.

    Returns:
        Dict with ``word_count``, ``sentence_count``, ``avg_sentence_length`` (words per
        sentence) and ``reading_time_min`` (at 238 words per minute). All zeros for empty
        text.

    Example:
        >>> basic_counts("The cat sat. It was happy.")["word_count"]
        6
    """
    words = len(tokenize(text))
    sentences = len(split_sentences(text)) if words else 0
    return {
        "word_count": words,
        "sentence_count": sentences,
        "avg_sentence_length": words / sentences if sentences else 0.0,
        "reading_time_min": words / WORDS_PER_MINUTE,
    }


def analyze(text: str) -> TextStats:
    """Combine all text metrics into one TextStats object.

    Keywords and passive ratio are placeholders until the keywords and passive modules
    are implemented (Day 2).

    Args:
        text: Plain or Markdown text.

    Returns:
        A TextStats with word and sentence counts, reading time, readability scores and
        average sentence length. All numeric fields are zero and keywords is empty for
        empty text.

    Example:
        >>> analyze("The cat sat. It was happy.").word_count
        6
    """
    counts = basic_counts(text)
    scores = readability(text)
    return TextStats(
        word_count=int(counts["word_count"]),
        sentence_count=int(counts["sentence_count"]),
        reading_time_min=counts["reading_time_min"],
        flesch_reading_ease=scores["flesch_reading_ease"],
        flesch_kincaid_grade=scores["flesch_kincaid_grade"],
        avg_sentence_length=counts["avg_sentence_length"],
        keywords=[],
        passive_ratio=0.0,
    )


def _syllables_in_part(part: str) -> int:
    w = re.sub(r"[^a-z]", "", part)
    if not w:
        return 0
    if w in _EXCEPTIONS:
        return _EXCEPTIONS[w]
    count = len(_VOWEL_GROUP.findall(w))
    if count > 1 and _has_silent_e(w):
        count -= 1
    return max(count, 1)


def _has_silent_e(w: str) -> bool:
    """True if a trailing -e, -ed or -es is a silent vowel group of its own."""
    if w.endswith("e"):
        e_idx = len(w) - 1
    elif w.endswith(("ed", "es")):
        e_idx = len(w) - 2
    else:
        return False
    if e_idx < 1 or w[e_idx - 1] in _VOWELS:
        return False
    before = w[e_idx - 1]
    consonant_le = before == "l" and e_idx >= 2 and w[e_idx - 2] not in _VOWELS
    if w.endswith("e"):
        return not consonant_le  # table, example: the final e is pronounced
    if w.endswith("ed") and before in "td":
        return False  # wanted, needed
    if w.endswith("es") and (before in "sxzcg" or w[e_idx - 2 : e_idx] in ("ch", "sh")):
        return False  # uses, boxes, places, watches
    return not consonant_le  # handled, samples keep the vowel
