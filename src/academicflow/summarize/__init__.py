"""Abstract generator: extractive TextRank by default, optional LLM backend.

Owner: Member 5.
"""

from __future__ import annotations

from academicflow.summarize.extractive import (
    generate_abstract,
    normalize_section_name,
    rank_sentences,
    summarize,
)

__all__ = ["summarize", "generate_abstract", "rank_sentences", "normalize_section_name"]
