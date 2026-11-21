"""Keyword extraction with a RAKE-style scorer."""

from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache
from importlib import resources

from academicflow.core.text import strip_markdown

__all__ = ["extract_keywords"]

_MAX_PHRASE_WORDS = 3
_BREAKS = re.compile(r"[,;:!?()\[\]\"\u201c\u201d\u2014\u2013\n]+|\.(?=\s|$)")
_WORD = re.compile(r"[^\W_]+(?:[-'\u2019][^\W_]+)*")


def extract_keywords(text: str, top_n: int = 10) -> list[tuple[str, float]]:
    """Extract the most important phrases (1-3 words) from a text.

    Uses RAKE-style scoring: the text is split into candidate phrases at stopwords and
    punctuation, each word is scored by degree / frequency, and a phrase scores the sum of
    its words. Phrases that occur several times get a logarithmic bonus. Scores are
    normalised so the best phrase has score 1.0. The output is deterministic.

    Args:
        text: Plain or Markdown text. Citations like ``[@key]`` are ignored.
        top_n: Maximum number of keywords to return.

    Returns:
        ``(phrase, score)`` pairs, best first, scores in 0-1. Empty list for empty text,
        text with only stopwords, or ``top_n <= 0``.

    Example:
        >>> extract_keywords("Deep learning is a method. Deep learning is useful.", 1)
        [('deep learning', 1.0)]
    """
    phrases = _candidates(text)
    if not phrases or top_n <= 0:
        return []
    freq: Counter[str] = Counter()
    degree: Counter[str] = Counter()
    for phrase in phrases:
        for word in phrase:
            freq[word] += 1
            degree[word] += len(phrase)
    raw: dict[tuple[str, ...], float] = {}
    for phrase, count in Counter(phrases).items():
        rake = sum(degree[w] / freq[w] for w in phrase)
        raw[phrase] = rake * (1 + math.log(count))
    best = max(raw.values())
    ranked = sorted(raw.items(), key=lambda item: (-item[1], item[0]))
    return [(" ".join(p), round(score / best, 4)) for p, score in ranked[:top_n]]


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    """Load the bundled stopword list (no network, no downloads)."""
    data = resources.files("academicflow.core").joinpath("data").joinpath("stopwords.txt")
    words = data.read_text(encoding="utf-8").split()
    return frozenset(w.lower() for w in words)


def _candidates(text: str) -> list[tuple[str, ...]]:
    cleaned = strip_markdown(text, remove_citations=True).lower()
    stop = _stopwords()
    phrases: list[tuple[str, ...]] = []
    for segment in _BREAKS.split(cleaned):
        current: list[str] = []
        for match in _WORD.finditer(segment):
            word = match.group()
            if word in stop or len(word) < 2 or not any(c.isalpha() for c in word):
                _flush(current, phrases)
                current = []
            else:
                current.append(word)
        _flush(current, phrases)
    return phrases


def _flush(words: list[str], out: list[tuple[str, ...]]) -> None:
    for i in range(0, len(words), _MAX_PHRASE_WORDS):
        out.append(tuple(words[i : i + _MAX_PHRASE_WORDS]))
