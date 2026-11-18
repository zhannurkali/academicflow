"""Text analysis core: readability, word count, reading time, keywords, passive voice.

Owner: Member 1.
"""

from __future__ import annotations

from academicflow.core.keywords import extract_keywords
from academicflow.core.passive import detect_passive
from academicflow.core.readability import analyze, count_syllables, readability
from academicflow.core.text import split_sentences, strip_markdown, tokenize

__all__ = [
    "split_sentences",
    "tokenize",
    "strip_markdown",
    "count_syllables",
    "readability",
    "extract_keywords",
    "detect_passive",
    "analyze",
]
