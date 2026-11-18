"""Optional LLM backend (OpenAI-compatible, also works with Ollama).

Owner: Member 5. Requires ``pip install academicflow[llm]``.
"""

from __future__ import annotations


def llm_summarize(text: str, max_words: int = 200, **kwargs) -> str:
    """Summarise with an LLM.

    TODO(member 5): lazy ``openai`` import, env config, fallback to extractive.
    """
    raise NotImplementedError("LLM backend not implemented yet (member 5)")
