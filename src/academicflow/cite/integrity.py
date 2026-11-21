"""Citation integrity checks for academicflow.cite."""

from __future__ import annotations

import difflib
import re

from ..types import Issue
from .bib import Bibliography
from .render import find_citations

_REQUIRED = {
    "article": ("authors", "title", "year", "journal"),
    "inproceedings": ("authors", "title", "year", "booktitle"),
    "conference": ("authors", "title", "year", "booktitle"),
    "book": ("authors", "title", "year", "publisher"),
    "misc": ("title", "year"),
}
_DEFAULT_REQUIRED = ("authors", "title", "year")


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def check_integrity(text: str, bib: Bibliography) -> list[Issue]:
    """Check citations in the text against the bibliography.

    Rules:
        cite-missing-key (error): cited key not in the bibliography, with a "did you
            mean" suggestion when a similar key exists.
        cite-duplicate-doi (warning): an entry repeats another entry's DOI or title.
        cite-incomplete (warning): an entry lacks fields its type needs.
        cite-unused (info): an entry is never cited (start = end = 0).

    Args:
        text: Full text, with ``[@key]`` citations.
        bib: Loaded bibliography.

    Returns:
        A list of issues: missing keys in text order, then per-entry issues in file order.
    """
    issues: list[Issue] = []
    cited = set()
    keys = bib.keys()

    for key, start, end in find_citations(text):
        cited.add(key)
        if key in bib:
            continue
        match = difflib.get_close_matches(key, keys, n=1, cutoff=0.6)
        hint = f" Did you mean '{match[0]}'?" if match else ""
        issues.append(
            Issue(
                rule="cite-missing-key",
                message=f"Cited key '{key}' is not in the bibliography.{hint}",
                severity="error",
                start=start,
                end=end,
                suggestion=match[0] if match else None,
            )
        )

    seen_doi: dict[str, str] = {}
    seen_title: dict[str, str] = {}
    for key in keys:
        e = bib.get(key)
        doi = e["doi"].lower()
        title = _norm_title(e["title"])
        for table, value, what in ((seen_doi, doi, "DOI"), (seen_title, title, "title")):
            if value and value in table:
                issues.append(
                    Issue(
                        rule="cite-duplicate-doi",
                        message=f"'{key}' has the same {what} as '{table[value]}'.",
                        severity="warning",
                        suggestion=f"Keep only one of '{table[value]}' and '{key}'.",
                    )
                )
                break
            if value:
                table[value] = key

        missing = [f for f in _REQUIRED.get(e["type"], _DEFAULT_REQUIRED) if not e[f]]
        if missing:
            issues.append(
                Issue(
                    rule="cite-incomplete",
                    message=f"'{key}' ({e['type']}) is missing: {', '.join(missing)}.",
                    severity="warning",
                )
            )

    for key in keys:
        if key not in cited:
            issues.append(
                Issue(
                    rule="cite-unused",
                    message=f"'{key}' is in the bibliography but never cited.",
                    severity="info",
                )
            )
    return issues
