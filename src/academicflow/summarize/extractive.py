"""Extractive summarisation with TextRank, and section-aware abstract generation.

Owner: Member 5.

The algorithm is deterministic and needs only numpy:

1. Split the text into sentences (``academicflow.core.split_sentences``).
2. Build a TF-IDF vector per sentence (stopwords removed).
3. Build a cosine-similarity graph between sentences.
4. Rank sentences with PageRank (power iteration, damping 0.85).
5. Boost sentences near the start/end of the text and sentences containing top keywords.
6. Pick the best sentences that fit in ``max_words`` and return them in original order.
"""

from __future__ import annotations

import math
import re
import warnings
from functools import lru_cache
from importlib import resources

import numpy as np

from academicflow.core.text import split_sentences, tokenize

DAMPING = 0.85
MAX_ITER = 100
TOLERANCE = 1e-6
POSITION_BOOST = 1.15  # sentences in the first or last 20% of a text
KEYWORD_BOOST = 1.10  # sentences containing one of the top keywords

# Canonical section names used by generate_abstract, in the order they appear in an abstract.
SECTION_ORDER = ("introduction", "methods", "results", "conclusion")
_SECTION_SYNONYMS = {
    "introduction": ("introduction", "intro", "background", "motivation", "overview"),
    "methods": (
        "methods",
        "method",
        "methodology",
        "materials and methods",
        "approach",
        "experimental setup",
        "experiments",
        "data and methods",
    ),
    "results": ("results", "result", "evaluation", "findings", "results and discussion"),
    "conclusion": ("conclusion", "conclusions", "discussion", "summary", "future work"),
}
_NUMBERING_RE = re.compile(r"^\s*(?:[ivxlc]+|\d+(?:\.\d+)*)[.)]?\s+", re.IGNORECASE)

_llm_warned = False


@lru_cache(maxsize=1)
def _stopwords() -> frozenset[str]:
    """Load the bundled stopword list (shared with academicflow.core)."""
    try:
        raw = resources.files("academicflow.core").joinpath("data/stopwords.txt").read_text("utf-8")
    except (FileNotFoundError, ModuleNotFoundError):  # pragma: no cover - defensive
        return frozenset()
    return frozenset(
        line.strip().lower()
        for line in raw.splitlines()
        if line.strip() and not line.startswith("#")
    )


def normalize_section_name(name: str) -> str:
    """Map a section heading to a canonical name.

    ``"2. Materials and Methods"`` becomes ``"methods"``. Unknown names are returned
    lower-cased with numbering removed.

    Args:
        name: Section name as written by the user.

    Returns:
        ``"introduction"``, ``"methods"``, ``"results"``, ``"conclusion"``, ``"abstract"``
        or the cleaned original name.
    """
    cleaned = _NUMBERING_RE.sub("", name.strip().lower()).replace("-", " ").replace("_", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if cleaned == "abstract":
        return "abstract"
    for canonical, synonyms in _SECTION_SYNONYMS.items():
        if cleaned in synonyms:
            return canonical
    return cleaned


def _content_tokens(sentence: str) -> list[str]:
    stop = _stopwords()
    return [t for t in tokenize(sentence) if t not in stop and len(t) > 1]


def _tfidf_matrix(token_lists: list[list[str]]) -> np.ndarray:
    """Row-normalised TF-IDF matrix (sentences x vocabulary)."""
    vocab: dict[str, int] = {}
    for tokens in token_lists:
        for t in tokens:
            vocab.setdefault(t, len(vocab))
    n = len(token_lists)
    if not vocab:
        return np.zeros((n, 0))
    tf = np.zeros((n, len(vocab)))
    for i, tokens in enumerate(token_lists):
        for t in tokens:
            tf[i, vocab[t]] += 1.0
    df = (tf > 0).sum(axis=0)
    idf = np.log((1.0 + n) / (1.0 + df)) + 1.0
    mat = tf * idf
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def _pagerank(sim: np.ndarray) -> np.ndarray:
    """PageRank scores for a weighted, undirected similarity graph."""
    n = sim.shape[0]
    row_sums = sim.sum(axis=1, keepdims=True)
    # Sentences with no similar neighbours link uniformly to everyone (dangling nodes).
    transition = np.where(row_sums > 0, sim / np.where(row_sums == 0, 1.0, row_sums), 1.0 / n)
    scores = np.full(n, 1.0 / n)
    for _ in range(MAX_ITER):
        new = (1.0 - DAMPING) / n + DAMPING * transition.T @ scores
        if np.abs(new - scores).sum() < TOLERANCE:
            return new
        scores = new
    return scores


def rank_sentences(text: str) -> list[tuple[int, int, float]]:
    """Score every sentence of ``text`` with TextRank.

    Args:
        text: Input text.

    Returns:
        ``(start, end, score)`` per sentence, in original order. Scores sum to roughly 1
        before boosts are applied.
    """
    spans = split_sentences(text)
    if not spans:
        return []
    if len(spans) == 1:
        return [(spans[0][0], spans[0][1], 1.0)]

    token_lists = [_content_tokens(text[s:e]) for s, e in spans]
    mat = _tfidf_matrix(token_lists)
    sim = mat @ mat.T if mat.shape[1] else np.zeros((len(spans), len(spans)))
    np.fill_diagonal(sim, 0.0)
    scores = _pagerank(sim)

    n = len(spans)
    edge = max(1, math.ceil(0.2 * n))
    top_keywords = _top_keywords(text)
    ranked = []
    for i, ((s, e), score) in enumerate(zip(spans, scores, strict=True)):
        if i < edge or i >= n - edge:
            score *= POSITION_BOOST
        if top_keywords and top_keywords & set(token_lists[i]):
            score *= KEYWORD_BOOST
        ranked.append((s, e, float(score)))
    return ranked


def _top_keywords(text: str, n: int = 5) -> set[str]:
    """Single words from academicflow.core.extract_keywords (empty if not implemented yet)."""
    try:
        from academicflow.core import extract_keywords

        words: set[str] = set()
        for phrase, _ in extract_keywords(text, top_n=n):
            words.update(tokenize(phrase))
        return words
    except Exception:  # keywords are a bonus; never let them break summarisation
        return set()


def _select(
    text: str, ranked: list[tuple[int, int, float]], max_words: int
) -> list[tuple[int, int]]:
    """Greedily pick the best sentences that fit in ``max_words``; return them in text order."""
    order = sorted(range(len(ranked)), key=lambda i: (-ranked[i][2], i))
    chosen: list[int] = []
    used = 0
    for i in order:
        s, e, _ = ranked[i]
        n_words = len(tokenize(text[s:e]))
        if n_words == 0 or used + n_words > max_words:
            continue
        chosen.append(i)
        used += n_words
    return [(ranked[i][0], ranked[i][1]) for i in sorted(chosen)]


def _extractive(text: str, max_words: int) -> str:
    ranked = rank_sentences(text)
    return " ".join(text[s:e].strip() for s, e in _select(text, ranked, max_words))


def _try_llm(text: str, max_words: int, kind: str, **kwargs) -> str | None:
    """Run the LLM backend; on any failure warn once and return None."""
    global _llm_warned
    try:
        from academicflow.summarize.llm import llm_summarize

        return llm_summarize(text, max_words=max_words, kind=kind, **kwargs)
    except Exception as exc:  # noqa: BLE001 - any failure falls back to extractive
        if not _llm_warned:
            warnings.warn(
                f"LLM summarisation unavailable ({exc}); using extractive TextRank instead.",
                RuntimeWarning,
                stacklevel=3,
            )
            _llm_warned = True
        return None


def summarize(text: str, max_words: int = 200, method: str = "extractive", **kwargs) -> str:
    """Summarise ``text`` in at most ``max_words`` words.

    Args:
        text: Input text (markdown allowed).
        max_words: Word limit for the summary.
        method: ``"extractive"`` (TextRank, offline, deterministic) or ``"llm"``
            (OpenAI-compatible API; falls back to extractive on any error).
        **kwargs: Passed to the LLM backend (``model``, ``base_url``, ``api_key``).

    Returns:
        The summary. Extractive summaries keep the original sentence order.

    Raises:
        ValueError: If ``method`` is unknown or ``max_words`` is not positive.
    """
    if method not in ("extractive", "llm"):
        raise ValueError(f"method must be 'extractive' or 'llm', got {method!r}")
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if not text.strip():
        return ""
    if method == "llm":
        result = _try_llm(text, max_words, kind="summary", **kwargs)
        if result:
            return result
    return _extractive(text, max_words)


def generate_abstract(
    sections: dict[str, str], max_words: int = 200, method: str = "extractive", **kwargs
) -> str:
    """Generate an abstract from a paper's sections.

    The extractive method takes the best sentences from each of the introduction,
    methods, results and conclusion (in that order), sharing the word budget between
    the sections that exist. Section names are normalised, so ``"2. Materials and Methods"``
    counts as methods. Any existing ``abstract`` section is ignored. If none of the four
    standard sections exist, the whole text is summarised instead.

    Args:
        sections: Ordered mapping of section name to text.
        max_words: Word limit for the abstract.
        method: ``"extractive"`` or ``"llm"`` (falls back to extractive on any error).
        **kwargs: Passed to the LLM backend.

    Returns:
        The abstract as one paragraph.
    """
    if method not in ("extractive", "llm"):
        raise ValueError(f"method must be 'extractive' or 'llm', got {method!r}")
    if max_words <= 0:
        raise ValueError("max_words must be positive")

    body = {
        name: text for name, text in sections.items() if normalize_section_name(name) != "abstract"
    }
    if not any(t.strip() for t in body.values()):
        return ""

    if method == "llm":
        joined = "\n\n".join(f"## {name}\n{text}" for name, text in body.items())
        result = _try_llm(joined, max_words, kind="abstract", **kwargs)
        if result:
            return result

    grouped: dict[str, list[str]] = {}
    for name, text in body.items():
        canonical = normalize_section_name(name)
        if canonical in SECTION_ORDER and text.strip():
            grouped.setdefault(canonical, []).append(text)

    if not grouped:
        return _extractive("\n\n".join(body.values()), max_words)

    present = [s for s in SECTION_ORDER if s in grouped]
    budget = max_words // len(present)
    parts = []
    for i, section in enumerate(present):
        # The last section may use whatever budget earlier sections left unused.
        used = sum(len(tokenize(p)) for p in parts)
        limit = max_words - used if i == len(present) - 1 else budget
        text = "\n\n".join(grouped[section])
        ranked = rank_sentences(text)
        picked = (
            _select(text, ranked, limit)[:2] if len(present) > 1 else _select(text, ranked, limit)
        )
        parts.extend(text[s:e].strip() for s, e in picked)
    return " ".join(p for p in parts if p)
