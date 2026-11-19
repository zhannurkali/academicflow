"""Shared helpers for the exporters: citation rendering and document assembly."""
from __future__ import annotations

import json
import re
import warnings
from dataclasses import dataclass, field
from typing import Any

KNOWN_STYLES = ("apa", "ieee", "nature")
_BREAK = "\n\n%%AF-SECTION-BREAK%%\n\n"
_NUMBERED = re.compile(r"^\s*(\[\d+\]|\d+\.)\s+")
_CITATION = re.compile(r"\[@[^\]]+\]")
_AUTO_NAME = re.compile(r"^section-\d+$")


@dataclass
class Prepared:
    """A document ready to be written: citations already rendered."""

    title: str | None
    authors: list[str]
    abstract: str | None
    sections: list[tuple[str, str]]
    references: list[str] = field(default_factory=list)
    style: str = "apa"


def citation_style(profile: str | None) -> str:
    """Map a venue profile (name or YAML path) to a citation style.

    Args:
        profile: ``"apa"``, ``"ieee"``, ``"nature"`` or a path to a custom profile.

    Returns:
        One of ``"apa"``, ``"ieee"``, ``"nature"``.
    """
    name = (profile or "apa").strip()
    if name.lower() in KNOWN_STYLES:
        return name.lower()
    try:
        from academicflow.style import load_profile

        value = load_profile(name).get("citation_style")
    except Exception:  # noqa: BLE001 - fall back to a safe default
        value = None
    return value if value in KNOWN_STYLES else "apa"


def section_heading(name: str) -> str | None:
    """Human heading for a section name, or ``None`` for auto names like ``section-2``."""
    clean = name.replace("_", " ").strip()
    if not clean or _AUTO_NAME.match(clean):
        return None
    return clean[0].upper() + clean[1:]


def strip_number(ref: str) -> str:
    """Remove a leading ``[1]`` or ``1.`` marker from a formatted reference."""
    return _NUMBERED.sub("", ref, count=1).strip()


def format_reference_list(refs: list[str], style: str) -> list[str]:
    """Make sure numbered styles carry their number; APA entries are returned unchanged.

    ``cite.render`` returns the ordered reference list. If the formatter already numbered the
    entries nothing is added, otherwise ``[n]`` (IEEE) or ``n.`` (Nature) is prefixed.
    """
    out = []
    for i, ref in enumerate(refs, 1):
        if style == "ieee" and not _NUMBERED.match(ref):
            ref = f"[{i}] {ref}"
        elif style == "nature" and not _NUMBERED.match(ref):
            ref = f"{i}. {ref}"
        out.append(ref)
    return out


def prepare(session: Any, target: str) -> Prepared:
    """Render citations over the whole document and collect the parts.

    Citations are rendered in one pass over ``abstract + sections`` so numbered styles
    (IEEE, Nature) number references by order of first appearance in the full paper.

    Args:
        session: Object with ``profile, bib, sections, title, authors, abstract``.
        target: ``"markdown"``, ``"pandoc"`` or ``"latex"`` (passed to ``cite.render``).

    Returns:
        A :class:`Prepared` document.

    Raises:
        ValueError: If there is nothing to export.
    """
    style = citation_style(session.profile)
    abstract = session.abstract or session.sections.get("abstract")
    parts: list[tuple[str, str]] = []
    if abstract:
        parts.append(("abstract", abstract))
    parts += [(n, t) for n, t in session.sections.items() if n.strip().lower() != "abstract"]
    if not parts:
        raise ValueError("Nothing to export: add sections with %%academic first.")

    references: list[str] = []
    texts = [t for _, t in parts]
    if session.bib is not None:
        from academicflow import cite

        rendered, refs = cite.render(_BREAK.join(texts), session.bib, style, target)
        pieces = rendered.split(_BREAK)
        if len(pieces) != len(parts):
            raise RuntimeError("Citation rendering changed the section structure.")
        texts = pieces
        references = format_reference_list(list(refs), style)
    elif any(_CITATION.search(t) for t in texts):
        warnings.warn(
            "Citations found but no bibliography is loaded (use %acite); "
            "they are exported as written.",
            stacklevel=3,
        )

    rendered_parts = [(parts[i][0], texts[i]) for i in range(len(parts))]
    abstract_out = None
    if abstract:
        abstract_out = rendered_parts.pop(0)[1]
    return Prepared(
        title=session.title,
        authors=list(session.authors or []),
        abstract=abstract_out,
        sections=rendered_parts,
        references=references,
        style=style,
    )


def _yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def to_markdown(p: Prepared) -> str:
    """Plain markdown version of the paper (``fmt="md"``)."""
    lines: list[str] = []
    if p.title:
        lines += [f"# {p.title}", ""]
    if p.authors:
        lines += ["*" + ", ".join(p.authors) + "*", ""]
    if p.abstract:
        lines += ["## Abstract", "", p.abstract.strip(), ""]
    for name, text in p.sections:
        heading = section_heading(name)
        if heading:
            lines += [f"## {heading}", ""]
        lines += [text.strip(), ""]
    if p.references:
        lines += ["## References", ""]
        for ref in p.references:
            lines += [ref, ""]
    return "\n".join(lines).rstrip() + "\n"


def to_pandoc_source(p: Prepared) -> str:
    """Pandoc markdown with a YAML metadata block, used for DOCX conversion."""
    meta = ["---"]
    if p.title:
        meta.append(f"title: {_yaml_str(p.title)}")
    if p.authors:
        meta.append("author:")
        meta += [f"  - {_yaml_str(a)}" for a in p.authors]
    if p.abstract:
        meta.append("abstract: |")
        meta += [("  " + line) if line.strip() else "" for line in p.abstract.strip().splitlines()]
    meta += ["---", ""]
    body: list[str] = []
    for name, text in p.sections:
        heading = section_heading(name)
        if heading:
            body += [f"# {heading}", ""]
        body += [text.strip(), ""]
    if p.references:
        body += ["# References", ""]
        for ref in p.references:
            body += [ref, ""]
    return "\n".join(meta + body)
