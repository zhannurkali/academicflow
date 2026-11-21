"""Inline citation parsing and rendering for academicflow.cite.

Citation syntax (pandoc style): ``[@key]``, ``[@a; @b]`` and ``[@key, p. 12]``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .bib import Bibliography
from .styles import format_reference

_STYLES = ("apa", "ieee", "nature")
_TARGETS = ("markdown", "pandoc", "latex")
_GROUP = re.compile(r"\[\s*@[^\[\]]*\]")
_ITEM = re.compile(r"\s*@([\w:.\-]+)\s*(?:,\s*(.*?))?\s*")


@dataclass(frozen=True)
class _Item:
    key: str
    locator: str
    start: int  # offsets of the key text itself (without "@")
    end: int


@dataclass(frozen=True)
class _Group:
    start: int
    end: int
    items: tuple[_Item, ...]


def _parse(text: str) -> list[_Group]:
    """Find every citation group such as ``[@a; @b, p. 3]`` in the text."""
    groups: list[_Group] = []
    for m in _GROUP.finditer(text):
        if text[m.end() : m.end() + 1] == "(":  # markdown link like [@x](url), not a citation
            continue
        inner_start = m.start() + 1
        items: list[_Item] = []
        offset = 0
        for part in m.group()[1:-1].split(";"):
            im = _ITEM.fullmatch(part)
            if im is None:
                items = []
                break
            key_start = inner_start + offset + im.start(1)
            locator = (im.group(2) or "").strip()
            items.append(_Item(im.group(1), locator, key_start, key_start + len(im.group(1))))
            offset += len(part) + 1
        if items:
            groups.append(_Group(m.start(), m.end(), tuple(items)))
    return groups


def find_citations(text: str) -> list[tuple[str, int, int]]:
    """Find every cited key in the text.

    Args:
        text: Text containing ``[@key]`` or ``[@a; @b]`` citations.

    Returns:
        A list of ``(key, start, end)`` in text order, one per key occurrence.
        ``text[start:end] == key`` (the "@" is not included).
    """
    return [(it.key, it.start, it.end) for g in _parse(text) for it in g.items]


# ------------------------------------------------------------ helpers


def _runs(nums: list[int]) -> list[tuple[int, int]]:
    """Group sorted unique integers into (first, last) runs of consecutive numbers."""
    runs: list[tuple[int, int]] = []
    for n in nums:
        if runs and n == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], n)
        else:
            runs.append((n, n))
    return runs


def _apa_label(e: dict[str, Any]) -> str:
    authors = e["authors"]
    if not authors:
        return e["title"]
    if e.get("et_al") or len(authors) >= 3:
        return f"{authors[0][1]} et al."
    if len(authors) == 2:
        return f"{authors[0][1]} & {authors[1][1]}"
    return authors[0][1]


def _apa_letters(order: list[str], bib: Bibliography) -> dict[str, str]:
    """Letters (a, b, ...) for cited entries sharing the same author label and year."""
    clusters: dict[tuple[str, str], list[str]] = {}
    for key in order:
        e = bib.get(key)
        clusters.setdefault((_apa_label(e), e["year"]), []).append(key)
    letters: dict[str, str] = {}
    for keys in clusters.values():
        if len(keys) > 1:
            for i, key in enumerate(sorted(keys, key=lambda k: bib.get(k)["title"].casefold())):
                letters[key] = chr(ord("a") + i)
    return letters


def _render_group(
    group: _Group,
    style: str,
    target: str,
    bib: Bibliography,
    numbers: dict[str, int],
    letters: dict[str, str],
) -> str:
    known = [it for it in group.items if it.key in bib]
    unknown = [f"[@{it.key}?]" for it in group.items if it.key not in bib]
    parts: list[str] = []

    if known and style == "apa":
        cites = set()
        for it in known:
            e = bib.get(it.key)
            year = (e["year"] or "n.d.") + letters.get(it.key, "")
            cite = f"{_apa_label(e)}, {year}"
            cites.add((cite, f"{cite}, {it.locator}" if it.locator else cite))
        text = "(" + "; ".join(c[1] for c in sorted(cites, key=lambda c: c[0].casefold())) + ")"
        parts.append(text.replace("&", r"\&") if target == "latex" else text)
    elif known and style == "ieee":
        plain = sorted({numbers[it.key] for it in known if not it.locator})
        tokens: list[tuple[int, str]] = []
        for a, b in _runs(plain):
            if b - a >= 2:
                tokens.append((a, f"[{a}]-[{b}]"))
            else:
                tokens.extend((n, f"[{n}]") for n in range(a, b + 1))
        tokens.extend(
            (numbers[it.key], f"[{numbers[it.key]}, {it.locator}]") for it in known if it.locator
        )
        parts.append(", ".join(t for _, t in sorted(tokens, key=lambda t: t[0])))
    elif known:  # nature
        nums = sorted({numbers[it.key] for it in known})
        pieces = []
        for a, b in _runs(nums):
            if b - a >= 2:
                pieces.append(f"{a}\u2013{b}")
            else:
                pieces.extend(str(n) for n in range(a, b + 1))
        body = ",".join(pieces)
        wrap = {
            "markdown": f"<sup>{body}</sup>",
            "pandoc": f"^{body}^",
            "latex": f"\\textsuperscript{{{body}}}",
        }
        parts.append(wrap[target])
    return " ".join(parts + unknown)


def render(
    text: str, bib: Bibliography, style: str, target: str = "markdown"
) -> tuple[str, list[str]]:
    """Replace ``[@key]`` citations with formatted inline citations.

    Unknown keys are left as ``[@key?]``; this function never raises for them
    (``check_integrity`` reports them).

    Args:
        text: Text containing pandoc-style citations.
        bib: Loaded bibliography.
        style: "apa", "ieee" or "nature".
        target: "markdown" (Nature uses ``<sup>n</sup>``), "pandoc" (Nature uses ``^n^``)
            or "latex" (Nature uses ``\\textsuperscript{n}``; "&" is escaped).

    Returns:
        ``(new_text, references)``. References are markdown strings for the cited entries
        only: sorted by first author for APA, in order of first citation for IEEE
        ("[n] ...") and Nature ("n. ..."). Convert with ``to_latex`` for LaTeX output.

    Raises:
        ValueError: If the style or target is unknown.
    """
    style = style.lower()
    if style not in _STYLES:
        raise ValueError(f"Unknown citation style '{style}' (use apa, ieee or nature)")
    if target not in _TARGETS:
        raise ValueError(f"Unknown render target '{target}' (use markdown, pandoc or latex)")

    groups = _parse(text)
    order: list[str] = []
    for g in groups:
        for it in g.items:
            if it.key in bib and it.key not in order:
                order.append(it.key)
    numbers = {key: i for i, key in enumerate(order, start=1)}
    letters = _apa_letters(order, bib) if style == "apa" else {}

    out: list[str] = []
    pos = 0
    for g in groups:
        start = g.start
        if style == "nature":  # superscripts attach directly to the preceding word
            while start > pos and text[start - 1] in " \t":
                start -= 1
        out.append(text[pos:start])
        out.append(_render_group(g, style, target, bib, numbers, letters))
        pos = g.end
    out.append(text[pos:])

    if style == "apa":
        def sort_key(key: str) -> tuple[str, str, str]:
            e = bib.get(key)
            name = e["authors"][0][1] if e["authors"] else e["title"]
            return (name.casefold(), e["year"] + letters.get(key, ""), e["title"].casefold())

        refs = []
        for key in sorted(order, key=sort_key):
            e = bib.get(key)
            if key in letters:
                e = {**e, "year": e["year"] + letters[key]}
            refs.append(format_reference(e, "apa"))
    elif style == "ieee":
        refs = [f"[{numbers[k]}] {format_reference(bib.get(k), 'ieee')}" for k in order]
    else:
        refs = [f"{numbers[k]}. {format_reference(bib.get(k), 'nature')}" for k in order]
    return "".join(out), refs
