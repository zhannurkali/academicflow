"""Reference formatters (APA 7, IEEE, Nature) for academicflow.cite.

Output is markdown (``*italic*``, ``**bold**``). The reference number ("[1]", "1.") is NOT
included: ``render()`` adds it, because numbering depends on order of first citation.

Supported entry types: article, inproceedings (alias: conference), book, misc.
Other types use the article layout with the booktitle or publisher in the journal slot.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

_INITIALS_TOKEN = re.compile(r"(?:[^\W\d_]\.)+")
_Formatter = Callable[[dict[str, Any]], str]


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


def _italic_title(title: str) -> str:
    """Wrap a title in markdown italics and end the sentence."""
    return f"*{title}*" if title[-1:] in (".", "?", "!") else f"*{title}*."


def _pp(pages: str) -> str:
    """Return "pp. 1\u201310" for a range and "p. 5" for a single page."""
    return ("pp. " if "\u2013" in pages else "p. ") + pages


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


def _apa_lead(e: dict[str, Any], italic: bool = False) -> str:
    """Return "Authors (Year). Title." (title in italics for books and similar)."""
    authors = _apa_authors(e)
    year = e["year"] or "n.d."
    title = _sentence_case(e["title"])
    title = _italic_title(title) if italic else _end(title)
    return f"{_end(authors)} ({year}). {title}" if authors else f"{title} ({year})."


def _apa_link(e: dict[str, Any]) -> str:
    return f"https://doi.org/{e['doi']}" if e["doi"] else e["url"]


def _apa_article(e: dict[str, Any]) -> str:
    out = _apa_lead(e)
    vol = f"*{e['volume']}*" if e["volume"] else ""
    if e["number"]:
        vol += f"({e['number']})"
    journal = f"*{e['journal']}*" if e["journal"] else ""
    source = ", ".join(p for p in (journal, vol, e["pages"]) if p)
    if source:
        out += f" {source}."
    link = _apa_link(e)
    return f"{out} {link}" if link else out


def _apa_inproceedings(e: dict[str, Any]) -> str:
    out = _apa_lead(e)
    if e["booktitle"]:
        out += f" In *{e['booktitle']}*"
        out += f" ({_pp(e['pages'])})." if e["pages"] else "."
    if e["publisher"]:
        out += f" {_end(e['publisher'])}"
    link = _apa_link(e)
    return f"{out} {link}" if link else out


def _apa_book(e: dict[str, Any]) -> str:
    out = _apa_lead(e, italic=True)
    if e["publisher"]:
        out += f" {_end(e['publisher'])}"
    link = _apa_link(e)
    return f"{out} {link}" if link else out


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


def _ieee_quoted(e: dict[str, Any], rest: list[str]) -> str:
    """Return 'Authors, "Title," part, part.' (IEEE layout for articles and papers)."""
    authors = _ieee_authors(e)
    head = f'{authors}, "{e["title"]},"' if authors else f'"{e["title"]},"'
    rest = [p for p in rest if p]
    if not rest:
        return head[:-2] + '."'
    return f"{head} {', '.join(rest)}."


def _ieee_article(e: dict[str, Any]) -> str:
    return _ieee_quoted(
        e,
        [
            f"*{e['journal']}*" if e["journal"] else "",
            f"vol. {e['volume']}" if e["volume"] else "",
            f"no. {e['number']}" if e["number"] else "",
            _pp(e["pages"]) if e["pages"] else "",
            e["year"],
            f"doi: {e['doi']}" if e["doi"] else "",
        ],
    )


def _ieee_inproceedings(e: dict[str, Any]) -> str:
    return _ieee_quoted(
        e,
        [
            f"in *{e['booktitle']}*" if e["booktitle"] else "",
            e["year"],
            _pp(e["pages"]) if e["pages"] else "",
            f"doi: {e['doi']}" if e["doi"] else "",
        ],
    )


def _ieee_book(e: dict[str, Any]) -> str:
    authors = _ieee_authors(e)
    head = f"{authors}, *{e['title']}*" if authors else f"*{e['title']}*"
    rest = [p for p in (e["publisher"], e["year"], f"doi: {e['doi']}" if e["doi"] else "") if p]
    return f"{head}. {', '.join(rest)}." if rest else f"{head}."


def _ieee_misc(e: dict[str, Any]) -> str:
    out = _ieee_quoted(e, [e["publisher"], e["year"], f"doi: {e['doi']}" if e["doi"] else ""])
    if e["url"] and not e["doi"]:
        out += f" [Online]. Available: {e['url']}"
    return out


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


def _nature_head(e: dict[str, Any]) -> str:
    """Return "Authors. Title." with the title in sentence case."""
    authors = _nature_authors(e)
    prefix = f"{_end(authors)} " if authors else ""
    return prefix + _end(_sentence_case(e["title"]))


def _nature_article(e: dict[str, Any]) -> str:
    head = _nature_head(e)
    source = f"*{e['journal']}*" if e["journal"] else ""
    if e["volume"]:
        source += f" **{e['volume']}**"
    if e["pages"]:
        source += f", {e['pages']}" if source else e["pages"]
    if e["year"]:
        source += f" ({e['year']})"
    return f"{head} {source.strip()}." if source.strip() else head


def _nature_inproceedings(e: dict[str, Any]) -> str:
    head = _nature_head(e)
    parts = [f"in *{e['booktitle']}*" if e["booktitle"] else "", e["pages"]]
    venue = ", ".join(p for p in (e["publisher"], e["year"]) if p)
    parts.append(f"({venue})" if venue else "")
    tail = " ".join(p for p in parts if p)
    return f"{head} {tail}." if tail else head


def _nature_book(e: dict[str, Any]) -> str:
    authors = _nature_authors(e)
    out = f"{_end(authors)} " if authors else ""
    out += f"*{e['title']}*"
    imprint = ", ".join(p for p in (e["publisher"], e["year"]) if p)
    if imprint:
        out += f" ({imprint})"
    return out + "."


def _nature_misc(e: dict[str, Any]) -> str:
    out = _nature_head(e)
    extra = " ".join(p for p in (e["publisher"], e["url"]) if p)
    if extra:
        out += f" {extra}"
    if e["year"]:
        out += f" ({e['year']})"
    return _end(out)


_FORMATTERS: dict[str, dict[str, _Formatter]] = {
    "apa": {
        "article": _apa_article,
        "inproceedings": _apa_inproceedings,
        "book": _apa_book,
        "misc": _apa_book,
    },
    "ieee": {
        "article": _ieee_article,
        "inproceedings": _ieee_inproceedings,
        "book": _ieee_book,
        "misc": _ieee_misc,
    },
    "nature": {
        "article": _nature_article,
        "inproceedings": _nature_inproceedings,
        "book": _nature_book,
        "misc": _nature_misc,
    },
}
_TYPE_ALIASES = {"conference": "inproceedings"}


def format_reference(entry: dict[str, Any], style: str) -> str:
    """Format one normalised bibliography entry as a markdown reference.

    Supports article, inproceedings (alias conference), book and misc. Other entry types
    use the article layout, with the booktitle or publisher in the journal slot.

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
    kind = _TYPE_ALIASES.get(entry["type"], entry["type"])
    formatter = _FORMATTERS[key].get(kind)
    if formatter is None:
        container = entry["journal"] or entry["booktitle"] or entry["publisher"]
        entry = {**entry, "journal": container}
        formatter = _FORMATTERS[key]["article"]
    return formatter(entry)


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
