"""Extractive summarisation.

Owner: Member 5.
"""

from __future__ import annotations

from academicflow.core.text import split_sentences, tokenize


def summarize(text: str, max_words: int = 200, method: str = "extractive", **kwargs) -> str:
    """Summarise ``text`` in at most ``max_words`` words.

    Args:
        text: Input text.
        max_words: Word limit.
        method: ``"extractive"`` or ``"llm"``.

    TODO(member 5): TextRank, LLM backend with fallback. Placeholder: leading sentences.
    """
    out: list[str] = []
    count = 0
    for start, end in split_sentences(text):
        sentence = text[start:end]
        n = len(tokenize(sentence))
        if count + n > max_words:
            break
        out.append(sentence)
        count += n
    return " ".join(out)


def generate_abstract(
    sections: dict[str, str], max_words: int = 200, method: str = "extractive"
) -> str:
    """Generate an abstract from a document's sections (ignoring any ``abstract`` section)."""
    body = "\n\n".join(t for name, t in sections.items() if name.lower() != "abstract")
    return summarize(body, max_words=max_words, method=method)
