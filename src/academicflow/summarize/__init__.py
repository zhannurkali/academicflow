"""Abstract generator: extractive by default, optional LLM backend.

Owner: Member 5.
"""

from __future__ import annotations

from academicflow.summarize.extractive import generate_abstract, summarize

__all__ = ["summarize", "generate_abstract"]
