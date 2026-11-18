"""Optional LLM backend for summaries and abstracts.

Owner: Member 5. Requires ``pip install "academicflow[llm]"``.

Works with any OpenAI-compatible API, including a local Ollama server. Configure it with
arguments or environment variables:

* ``ACADEMICFLOW_LLM_MODEL``: model name (required), e.g. ``llama3.2`` for Ollama.
* ``ACADEMICFLOW_LLM_BASE_URL``: API URL, e.g. ``http://localhost:11434/v1`` for Ollama.
  Leave unset for OpenAI.
* ``OPENAI_API_KEY``: API key (not needed for Ollama).

Callers in :mod:`academicflow.summarize.extractive` catch every error raised here and
fall back to TextRank, so the notebook never breaks because of a missing key or network.
"""

from __future__ import annotations

import os

from academicflow.core.text import split_sentences, tokenize

_SYSTEM_PROMPT = (
    "You are an expert academic editor. You write concise, formal summaries of "
    "scientific papers. Use only information present in the text. Never invent results, "
    "numbers or citations. Do not include citation markers."
)

_TASKS = {
    "summary": "Summarise the following text in one paragraph of at most {n} words.",
    "abstract": (
        "Write the abstract for the following paper in one paragraph of at most {n} words. "
        "Cover the problem, the method, the main results and the conclusion, in that order."
    ),
}


def truncate_words(text: str, max_words: int) -> str:
    """Cut ``text`` to at most ``max_words`` words, preferring a sentence boundary.

    Args:
        text: Text to shorten.
        max_words: Word limit.

    Returns:
        Whole sentences that fit; if even the first sentence is too long, its first
        ``max_words`` words followed by an ellipsis.
    """
    if len(tokenize(text)) <= max_words:
        return text.strip()
    kept: list[str] = []
    used = 0
    for s, e in split_sentences(text):
        n = len(tokenize(text[s:e]))
        if used + n > max_words:
            break
        kept.append(text[s:e].strip())
        used += n
    if kept:
        return " ".join(kept)
    return " ".join(text.split()[:max_words]) + "…"


def llm_summarize(
    text: str,
    max_words: int = 200,
    kind: str = "summary",
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 60.0,
) -> str:
    """Summarise ``text`` with an OpenAI-compatible chat model.

    Args:
        text: Text to summarise.
        max_words: Word limit; longer answers are truncated at a sentence boundary.
        kind: ``"summary"`` or ``"abstract"``.
        model: Model name; defaults to ``$ACADEMICFLOW_LLM_MODEL``.
        base_url: API base URL; defaults to ``$ACADEMICFLOW_LLM_BASE_URL`` (OpenAI if unset).
        api_key: API key; defaults to ``$OPENAI_API_KEY`` (a placeholder is used when a
            ``base_url`` is set, since local servers such as Ollama ignore it).
        timeout: Request timeout in seconds.

    Returns:
        The generated summary.

    Raises:
        RuntimeError: If ``openai`` is not installed, or the model or key is not configured,
            or the API returns an empty answer.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError('install the LLM extra: pip install "academicflow[llm]"') from exc

    if kind not in _TASKS:
        raise ValueError(f"kind must be one of {tuple(_TASKS)}, got {kind!r}")
    model = model or os.environ.get("ACADEMICFLOW_LLM_MODEL")
    if not model:
        raise RuntimeError("no model configured; set ACADEMICFLOW_LLM_MODEL or pass model=")
    base_url = base_url or os.environ.get("ACADEMICFLOW_LLM_BASE_URL") or None
    api_key = api_key or os.environ.get("OPENAI_API_KEY") or ("not-needed" if base_url else None)
    if not api_key:
        raise RuntimeError("no API key; set OPENAI_API_KEY or ACADEMICFLOW_LLM_BASE_URL")

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _TASKS[kind].format(n=max_words) + "\n\n" + text},
        ],
    )
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("the model returned an empty answer")
    return truncate_words(content, max_words)
