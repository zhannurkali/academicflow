"""Reference formatters (APA 7, IEEE, Nature) for academicflow.cite.

Output is markdown (``*italic*``, ``**bold**``). The reference number ("[1]", "1.") is NOT
included: ``render()`` adds it, because numbering depends on order of first citation.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

_INITIALS_TOKEN = re.compile(r"(?:[^\W\d_]\.)+")


def _initials(first: str) -> str:
    """Turn "John Alan" into "J. A." and "Jean-Paul" into "J.-P."."""
    out: list[str] = []
    for token in first.split():
        if _INITIALS_TOKEN.fullmatch(token):  # already initials, e.g. "J." or "J.A."
            out.extend(token[i : i + 2] for i in range(0, len(token), 2))
        else:
            out.append("-".join(p[0].upper() + "." for p in token.split("-") if p))
    return " ".join(out)


def _end(text: str) -> str:
    """Add a final period unless the text already ends with . ? or !."""
    return text if not text or text[-1] in ".?!" else text + "."


def _sentence_case(title: str) -> str:
    """Convert a Title Case title to sentence case; leave other titles untouched.

    Conservative: only converts when every longer word (4+ letters, after the first word
    and after a colon) is capitalised. Acronyms and mixed-case words (BERT, iPhone) are
    kept. Known limitation: proper nouns in a Title Case title (e.g. "Python") are
    lowercased, because the BibTeX braces that protect them are already stripped.
    """
    words = title.split(" ")
    positions = [
        i
        for i, w in enumerate(words)
        if i > 0 and not words[i - 1].endswith(":") and len(w) > 3 and not w.isupper()
    ]

    def is_cap(w: str) -> bool:
        return w[:1].isupper() and w[1:].islower()

    if not positions or not all(is_cap(words[i]) for i in positions):
        return title
    for i in range(1, len(words)):
        if not words[i - 1].endswith(":") and is_cap(words[i]):
            words[i] = words[i].lower()
    return " ".join(words)


# ---------------------------------------------------------------- APA 7


def _apa_authors(e: dict[str, Any]) -> str:
    names = []
    for first, last in e["authors"]:
        ini = _initials(first)
        names.append(f"{last}, {ini}" if ini else last)
    if not names:
        return ""
    if e.get("et_al"):
        return ", ".join(names) + ", et al."
    if len(names) == 1:
        return names[0]
    if len(names) <= 20:
        return ", ".join(names[:-1]) + ", & " + names[-1]
    return ", ".join(names[:19]) + ", . . . " + names[-1]


def _apa(e: dict[str, Any]) -> str:
    authors = _apa_authors(e)
    year = e["year"] or "n.d."
    title = _end(_sentence_case(e["title"]))
    out = f"{_end(authors)} ({year}). {title}" if authors else f"{title} ({year})."

    vol = f"*{e['volume']}*" if e["volume"] else ""
    if e["number"]:
        vol += f"({e['number']})"
    journal = f"*{e['journal']}*" if e["journal"] else ""
    source = ", ".join(p for p in (journal, vol, e["pages"]) if p)
    if source:
        out += f" {source}."
    link = f"https://doi.org/{e['doi']}" if e["doi"] else e["url"]
    if link:
        out += f" {link}"
    return out


# ---------------------------------------------------------------- IEEE


def _ieee_authors(e: dict[str, Any]) -> str:
    names = [f"{_initials(f)} {last}".strip() for f, last in e["authors"]]
    if not names:
        return ""
    if e.get("et_al") or len(names) > 6:
        return f"{names[0]} et al."
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def _ieee(e: dict[str, Any]) -> str:
    authors = _ieee_authors(e)
    title = e["title"]
    pages = ""
    if e["pages"]:
        pages = ("pp. " if "\u2013" in e["pages"] else "p. ") + e["pages"]
    rest = [
        f"*{e['journal']}*" if e["journal"] else "",
        f"vol. {e['volume']}" if e["volume"] else "",
        f"no. {e['number']}" if e["number"] else "",
        pages,
        e["year"],
        f"doi: {e['doi']}" if e["doi"] else "",
    ]
    rest = [p for p in rest if p]
    head = f'{authors}, "{title},"' if authors else f'"{title},"'
    if not rest:
        return head[:-2] + '."'
    return f"{head} {', '.join(rest)}."


# ---------------------------------------------------------------- Nature


def _nature_authors(e: dict[str, Any]) -> str:
    names = []
    for first, last in e["authors"]:
        ini = _initials(first)
        names.append(f"{last}, {ini}" if ini else last)
    if not names:
        return ""
    if e.get("et_al") or len(names) > 5:
        return f"{names[0]} et al."
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} & {names[1]}"
    return ", ".join(names[:-1]) + " & " + names[-1]


def _nature(e: dict[str, Any]) -> str:
    authors = _nature_authors(e)
    out = f"{_end(authors)} " if authors else ""
    out += _end(_sentence_case(e["title"]))
    source = f"*{e['journal']}*" if e["journal"] else ""
    if e["volume"]:
        source += f" **{e['volume']}**"
    if e["pages"]:
        source += f", {e['pages']}" if source else e["pages"]
    if e["year"]:
        source += f" ({e['year']})"
    return f"{out} {source.strip()}." if source.strip() else out


_FORMATTERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "apa": _apa,
    "ieee": _ieee,
    "nature": _nature,
}


def format_reference(entry: dict[str, Any], style: str) -> str:
    """Format one normalised bibliography entry as a markdown reference.

    Articles are fully supported. Other entry types use the article layout with the
    booktitle or publisher in the journal slot (temporary fallback until Day 2).

    Args:
        entry: Normalised entry dict from ``Bibliography.get``.
        style: "apa", "ieee" or "nature".

    Returns:
        The reference as markdown, without a number prefix.

    Raises:
        ValueError: If the style is unknown.
    """
    key = style.lower()
    if key not in _FORMATTERS:
        raise ValueError(f"Unknown citation style '{style}' (use apa, ieee or nature)")
    if entry["type"] != "article":
        container = entry["journal"] or entry["booktitle"] or entry["publisher"]
        entry = {**entry, "journal": container}
    return _FORMATTERS[key](entry)


def to_latex(markdown_ref: str) -> str:
    """Convert a markdown reference to LaTeX.

    Escapes ``& % _ #``, then turns ``**bold**`` into ``\\textbf{}`` and ``*italic*`` into
    ``\\textit{}``.

    Args:
        markdown_ref: Reference produced by ``format_reference``.

    Returns:
        LaTeX source text.
    """
    out = re.sub(r"([&%_#])", r"\\\1", markdown_ref)
    out = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", out)
    return re.sub(r"\*(.+?)\*", r"\\textit{\1}", out)
