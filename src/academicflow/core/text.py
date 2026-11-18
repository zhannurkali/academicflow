"""Low-level text utilities shared by every module.

Owner: Member 1. Other members import ``split_sentences`` and ``tokenize``, so keep the
signatures stable. The versions below are simple placeholders that already work well
enough for integration.
"""

from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
_CITE_RE = re.compile(r"\[@[^\]]*\]")
_SENT_END_RE = re.compile(r"[.!?]+(?=\s|$)")


def strip_markdown(text: str) -> str:
    """Remove markdown/LaTeX syntax so it is not counted as words.

    TODO(member 1): strip headings, emphasis, inline code, $...$ math, links.
    """
    return text


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Split text into sentences.

    Args:
        text: Input text.

    Returns:
        ``(start, end)`` character offsets of each sentence, whitespace trimmed.

    TODO(member 1): handle abbreviations (e.g., i.e., et al., Fig.), decimals and
    citations such as ``[@smith2020]``.
    """
    spans: list[tuple[int, int]] = []

    def _add(s: int, e: int) -> None:
        while s < e and text[s].isspace():
            s += 1
        while e > s and text[e - 1].isspace():
            e -= 1
        if s < e:
            spans.append((s, e))

    start = 0
    for m in _SENT_END_RE.finditer(text):
        _add(start, m.end())
        start = m.end()
    _add(start, len(text))
    return spans


def tokenize(text: str) -> list[str]:
    """Return lowercase word tokens, ignoring punctuation and ``[@key]`` citations.

    TODO(member 1): refine (hyphenated words, numbers, markdown).
    """
    return [w.lower() for w in _WORD_RE.findall(_CITE_RE.sub(" ", text))]
