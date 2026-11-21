"""Passive-voice detection (be-verb + past participle heuristic, spaCy when available)."""

from __future__ import annotations

import re
from functools import lru_cache
from importlib import resources
from typing import Any

from academicflow.core.text import split_sentences
from academicflow.types import Issue

__all__ = ["detect_passive", "passive_ratio"]

_SUGGESTION = "Consider active voice if the agent is important."

_AUX = r"(?:(?:has|have|had|will|would|can|could|may|might|must|shall|should)\s+(?:not\s+)?)?"
_BE = r"(?:am|is|are|was|were|be|been|being)"
_MID = r"(?:\s+(?:not|also|being|been|\w+ly))*"
_PATTERN = re.compile(rf"\b{_AUX}{_BE}{_MID}\s+(?P<part>[A-Za-z]+)\b", re.IGNORECASE)

# Words ending in -ed that are not past participles.
_NOT_PARTICIPLES = frozenset({"indeed", "speed", "proceed", "exceed", "succeed", "hundred"})


def detect_passive(text: str) -> list[Issue]:
    """Find passive-voice constructions.

    Uses spaCy dependency labels when spaCy and ``en_core_web_sm`` are installed. Otherwise
    uses a heuristic: a form of "to be" (optionally preceded by has/have/will/can...,
    optionally followed by an adverb) and then a past participle (regular ``-ed`` or from a
    bundled list of irregular participles).

    Args:
        text: Plain or Markdown text.

    Returns:
        Issues with ``rule="passive-voice"`` and ``severity="info"``. ``start`` and ``end``
        are offsets of the matched phrase in ``text``. Empty list for empty text.

    Example:
        >>> issue = detect_passive("The samples were analysed.")[0]
        >>> issue.message
        'Passive voice: "were analysed".'
    """
    if not text or not text.strip():
        return []
    nlp = _load_spacy()
    if nlp is not None:
        spans = _spans_spacy(nlp, text)
    else:
        spans = _spans_heuristic(text)
    return [_make_issue(text, start, end) for start, end in spans]


def passive_ratio(text: str) -> float:
    """Compute the share of sentences that contain at least one passive construction.

    Args:
        text: Plain or Markdown text.

    Returns:
        Passive sentences divided by all sentences, between 0.0 and 1.0. 0.0 for empty text.

    Example:
        >>> passive_ratio("The samples were analysed. We tested them.")
        0.5
    """
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    hit: set[int] = set()
    for issue in detect_passive(text):
        for index, (start, end) in enumerate(sentences):
            if start <= issue.start < end:
                hit.add(index)
                break
    return len(hit) / len(sentences)


def _make_issue(text: str, start: int, end: int) -> Issue:
    phrase = " ".join(text[start:end].split())
    return Issue(
        rule="passive-voice",
        message=f'Passive voice: "{phrase}".',
        severity="info",
        start=start,
        end=end,
        suggestion=_SUGGESTION,
    )


@lru_cache(maxsize=1)
def _participles() -> frozenset[str]:
    """Load the bundled irregular participles (no network, no downloads)."""
    data = resources.files("academicflow.core").joinpath("data")
    words = data.joinpath("irregular_participles.txt").read_text(encoding="utf-8").split()
    return frozenset(w.lower() for w in words)


def _is_participle(word: str) -> bool:
    w = word.lower()
    if w in _participles():
        return True
    return len(w) >= 5 and w.endswith("ed") and w not in _NOT_PARTICIPLES


def _spans_heuristic(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    pos = 0
    while True:
        match = _PATTERN.search(text, pos)
        if match is None:
            break
        if _is_participle(match.group("part")):
            spans.append((match.start(), match.end()))
            pos = match.end()
        else:
            pos = match.start() + 1
    return spans


@lru_cache(maxsize=1)
def _load_spacy() -> Any:
    """Return the spaCy English pipeline, or None if spaCy or the model is missing."""
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _spans_spacy(nlp: Any, text: str) -> list[tuple[int, int]]:
    spans: set[tuple[int, int]] = set()
    for token in nlp(text):
        if token.dep_ != "auxpass":
            continue
        head = token.head
        parts = [token, head]
        parts += [
            child
            for child in head.children
            if child.dep_ in {"aux", "auxpass", "neg", "advmod"} and child.i < head.i
        ]
        spans.add((min(t.idx for t in parts), head.idx + len(head.text)))
    return sorted(spans)
