"""Text utilities: sentence splitting, tokenisation and Markdown stripping."""

from __future__ import annotations

import re
from bisect import bisect_right

__all__ = ["split_sentences", "tokenize", "strip_markdown"]

# --- shared patterns -------------------------------------------------------------------
_CITATION = re.compile(r"\[@[^\]]*\]")
_HEADING_LINE = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+\S")
_TERMINATOR = re.compile(r"""[.!?]+["'\u201d\u2019)\]]*(?=\s|$)""")
_LAST_WORD = re.compile(r"([A-Za-z][A-Za-z.]*)$")
_CLOSERS = "\"'\u201d\u2019)]"

# Abbreviations (lowercase, without the final dot) that do not end a sentence.
_ABBREVIATIONS = frozenset(
    {
        "e.g",
        "i.e",
        "al",
        "fig",
        "figs",
        "eq",
        "eqs",
        "dr",
        "prof",
        "mr",
        "mrs",
        "ms",
        "vs",
        "cf",
        "ca",
        "approx",
        "sec",
        "secs",
        "ch",
        "ref",
        "refs",
        "tab",
        "vol",
        "pp",
        "p",
        "inc",
        "ltd",
        "jr",
        "sr",
        "resp",
        "viz",
        "ph.d",
    }
)

# --- markdown patterns -----------------------------------------------------------------
_FENCE = re.compile(r"(```|~~~).*?\1", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_DISPLAY_MATH = re.compile(r"\$\$.*?\$\$", re.DOTALL)
_INLINE_MATH = re.compile(r"(?<![\\$])\$(?=\S)[^$\n]*?(?<=\S)\$(?!\d)")
_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HEADING = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+")
_QUOTE = re.compile(r"(?m)^[ \t]*>+[ \t]?")
_LIST = re.compile(r"(?m)^[ \t]*(?:[-*+]|\d+[.)])[ \t]+")
_BOLD_STAR = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_BOLD_UNDER = re.compile(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)")
_ITALIC_STAR = re.compile(r"\*(?=\S)([^*\n]+?)(?<=\S)\*")
_ITALIC_UNDER = re.compile(r"(?<!\w)_(?=\S)([^_\n]+?)(?<=\S)_(?!\w)")

# Numbers like 3.14 stay whole; words keep inner hyphens/apostrophes (covid-19, state-of-the-art).
_TOKEN = re.compile(r"\d+(?:[.,]\d+)+|[^\W_]+(?:[-'\u2019][^\W_]+)*")


def strip_markdown(text: str, remove_citations: bool = False) -> str:
    """Remove Markdown and LaTeX syntax so only readable prose remains.

    Removes fenced and inline code, ``$...$`` / ``$$...$$`` math, heading hashes, list and
    quote markers, emphasis markers, and turns ``[text](url)`` into ``text``.

    Args:
        text: Markdown source.
        remove_citations: If True, also delete ``[@key]`` citation markers.

    Returns:
        The text without Markdown syntax. Offsets are NOT preserved.

    Example:
        >>> strip_markdown("# Title\\n- **bold** item")
        'Title\\nbold item'
    """
    if not text:
        return ""
    text = _FENCE.sub(" ", text)
    text = _DISPLAY_MATH.sub(" ", text)
    text = _INLINE_CODE.sub(" ", text)
    text = _INLINE_MATH.sub(" ", text)
    if remove_citations:
        text = _CITATION.sub("", text)
    text = _LINK.sub(r"\1", text)
    text = _HEADING.sub("", text)
    text = _QUOTE.sub("", text)
    text = _LIST.sub("", text)
    for pattern in (_BOLD_STAR, _BOLD_UNDER, _ITALIC_STAR, _ITALIC_UNDER):
        text = pattern.sub(r"\1", text)
    return text


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens.

    Keeps hyphenated words (``state-of-the-art``), words with digits (``covid-19``) and
    decimals (``3.14``). Drops punctuation, Markdown syntax, LaTeX math, code and
    ``[@key]`` citation markers.

    Args:
        text: Input text (plain or Markdown).

    Returns:
        List of lowercase tokens; empty list for empty input.

    Example:
        >>> tokenize("COVID-19 results [@smith2020] improved.")
        ['covid-19', 'results', 'improved']
    """
    cleaned = strip_markdown(text, remove_citations=True)
    return [m.group().lower() for m in _TOKEN.finditer(cleaned)]


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Split text into sentences and return their character offsets.

    Does not split after common abbreviations (e.g., i.e., et al., Fig., Eq., Dr., vs.),
    single-letter initials, decimals (3.14), or inside ``[@key]`` citations. Blank lines and
    Markdown heading lines always end a sentence.

    Args:
        text: Input text. Offsets refer to this exact string.

    Returns:
        List of ``(start, end)`` offsets such that ``text[start:end]`` is the sentence
        without surrounding whitespace. Empty list for empty or blank input.

    Example:
        >>> t = "We did this, e.g. twice. It worked."
        >>> [t[s:e] for s, e in split_sentences(t)]
        ['We did this, e.g. twice.', 'It worked.']
    """
    if not text or not text.strip():
        return []
    starts, ends = _citation_spans(text)
    spans: list[tuple[int, int]] = []
    for block_start, block_end in _iter_blocks(text):
        spans.extend(_split_block(text, block_start, block_end, starts, ends))
    return spans


# --- private helpers -------------------------------------------------------------------
def _citation_spans(text: str) -> tuple[list[int], list[int]]:
    spans = [(m.start(), m.end()) for m in _CITATION.finditer(text)]
    return [s for s, _ in spans], [e for _, e in spans]


def _inside(pos: int, starts: list[int], ends: list[int]) -> bool:
    i = bisect_right(starts, pos) - 1
    return i >= 0 and pos < ends[i]


def _iter_blocks(text: str):
    """Yield (start, end) of paragraphs; a heading line is its own block."""
    block_start: int | None = None
    block_end = 0
    pos = 0
    for line in text.splitlines(keepends=True):
        line_start, pos = pos, pos + len(line)
        line_end = line_start + len(line.rstrip())
        if not line.strip():
            if block_start is not None:
                yield block_start, block_end
                block_start = None
            continue
        if _HEADING_LINE.match(line):
            if block_start is not None:
                yield block_start, block_end
                block_start = None
            yield line_start, line_end
            continue
        if block_start is None:
            block_start = line_start
        block_end = line_end
    if block_start is not None:
        yield block_start, block_end


def _split_block(
    text: str, start: int, end: int, starts: list[int], ends: list[int]
) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    sent_start = start
    for m in _TERMINATOR.finditer(text, start, end):
        if _inside(m.start(), starts, ends):
            continue
        j = m.end()
        while j < end and text[j].isspace():
            j += 1
        if j < end and text[j].islower():
            continue  # "...vs. the ..." -> same sentence
        if m.group().rstrip(_CLOSERS) == ".":
            word = _LAST_WORD.search(text[max(start, m.start() - 20) : m.start()])
            if word:
                w = word.group(1)
                if w.lower() in _ABBREVIATIONS or (len(w) == 1 and w.isupper()):
                    continue
        first = sent_start
        while first < m.end() and text[first].isspace():
            first += 1
        spans.append((first, m.end()))
        sent_start = m.end()
    tail = sent_start
    while tail < end and text[tail].isspace():
        tail += 1
    if tail < end:
        spans.append((tail, end))
    return spans
