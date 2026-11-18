"""Readability scores and the combined ``analyze`` function.

Owner: Member 1.
"""

from __future__ import annotations

import re

from academicflow.core.keywords import extract_keywords
from academicflow.core.passive import detect_passive
from academicflow.core.text import split_sentences, tokenize
from academicflow.types import TextStats

WORDS_PER_MINUTE = 238


def count_syllables(word: str) -> int:
    """Estimate the number of syllables in a word.

    TODO(member 1): silent final e, -le endings, exceptions list.
    """
    return max(1, len(re.findall(r"[aeiouy]+", word.lower())))


def readability(text: str) -> dict[str, float]:
    """Compute Flesch Reading Ease and Flesch-Kincaid Grade.

    TODO(member 1): implement the standard formulas.
    """
    return {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}


def analyze(text: str) -> TextStats:
    """Compute all statistics for ``text``.

    Args:
        text: Input text (markdown allowed).

    Returns:
        A :class:`~academicflow.types.TextStats`.
    """
    words = tokenize(text)
    sentences = split_sentences(text)
    n_words, n_sents = len(words), len(sentences)
    scores = readability(text)
    passive = detect_passive(text)
    return TextStats(
        word_count=n_words,
        sentence_count=n_sents,
        reading_time_min=round(n_words / WORDS_PER_MINUTE, 2),
        flesch_reading_ease=scores["flesch_reading_ease"],
        flesch_kincaid_grade=scores["flesch_kincaid_grade"],
        avg_sentence_length=round(n_words / n_sents, 2) if n_sents else 0.0,
        keywords=extract_keywords(text),
        passive_ratio=round(len(passive) / n_sents, 3) if n_sents else 0.0,
    )
