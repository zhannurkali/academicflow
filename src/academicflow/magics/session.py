"""Shared notebook session state for the academicflow magics.

This module is plain Python (no IPython import) so it can be tested and reused by the export
code. The session is a module-level singleton: every magic reads and writes the same object.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Any

_AUTO_NAME = re.compile(r"^section-(\d+)$")
SECTION_SEPARATOR = "\n\n"


@dataclass
class Session:
    """State collected while the user writes a paper in a notebook.

    Attributes:
        profile: Venue profile name or YAML path (``"apa"``, ``"ieee"``, ``"nature"``).
        bib: Loaded ``academicflow.cite.Bibliography`` or ``None``.
        bib_path: Path the bibliography was loaded from.
        sections: Ordered mapping of section name to raw markdown. Replacing a key keeps
            its original position.
        title: Paper title.
        authors: Author names, in order.
        abstract: Abstract text, if one was written or generated.
    """

    profile: str = "apa"
    bib: Any = None
    bib_path: str | None = None
    sections: dict[str, str] = field(default_factory=dict)
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None

    def set_section(self, name: str, text: str) -> None:
        """Store ``text`` under ``name``; an existing section keeps its position."""
        self.sections[name] = text

    def auto_section_name(self, text: str) -> str:
        """Return a default section name for a cell without ``--section``.

        Re-running a cell with identical text reuses its earlier auto name, so the section is
        replaced instead of duplicated. Otherwise the next free ``section-<n>`` is returned.

        Args:
            text: Raw cell text.

        Returns:
            A name such as ``"section-3"``.
        """
        used = []
        for name, existing in self.sections.items():
            match = _AUTO_NAME.match(name)
            if match:
                if existing == text:
                    return name
                used.append(int(match.group(1)))
        return f"section-{max(used, default=0) + 1}"

    def body_sections(self) -> dict[str, str]:
        """Return all sections except the abstract, in order."""
        return {k: v for k, v in self.sections.items() if k.strip().lower() != "abstract"}

    def full_text(self, include_abstract: bool = True) -> str:
        """Join the section texts with blank lines."""
        source = self.sections if include_abstract else self.body_sections()
        return SECTION_SEPARATOR.join(source.values())

    def is_empty(self) -> bool:
        """Whether nothing exportable has been stored yet."""
        return not self.sections and not self.abstract

    def reset(self) -> None:
        """Restore every field to its default value (in place)."""
        self.profile = "apa"
        self.bib = None
        self.bib_path = None
        self.sections = {}
        self.title = None
        self.authors = []
        self.abstract = None


_SESSION = Session()


def get_session() -> Session:
    """Return the singleton :class:`Session`."""
    return _SESSION


def reset_session() -> Session:
    """Clear the singleton and return it."""
    _SESSION.reset()
    return _SESSION


def join_with_offsets(sections: dict[str, str]) -> tuple[str, list[tuple[str, int, int]]]:
    """Join sections into one text and remember where each one lives.

    Args:
        sections: Ordered mapping of section name to text.

    Returns:
        ``(full_text, spans)`` where each span is ``(name, start, end)`` in ``full_text``.
    """
    pieces: list[str] = []
    spans: list[tuple[str, int, int]] = []
    pos = 0
    for name, text in sections.items():
        spans.append((name, pos, pos + len(text)))
        pieces.append(text)
        pos += len(text) + len(SECTION_SEPARATOR)
    return SECTION_SEPARATOR.join(pieces), spans


def locate_issues(issues: list, spans: list[tuple[str, int, int]]) -> list:
    """Assign issues from a joined text back to their section.

    Issues with a real character range get ``section`` set and their offsets rebased to the
    section text. Issues without a range (for example ``cite-unused``) are returned unchanged.

    Args:
        issues: ``Issue`` objects whose offsets refer to the joined text.
        spans: Output of :func:`join_with_offsets`.

    Returns:
        New list of issues (copies where changed).
    """
    located = []
    for issue in issues:
        has_range = getattr(issue, "end", 0) > getattr(issue, "start", 0)
        if has_range and getattr(issue, "section", None) is None:
            for name, start, end in spans:
                if start <= issue.start < end:
                    issue = replace(
                        issue, section=name, start=issue.start - start, end=issue.end - start
                    )
                    break
        located.append(issue)
    return located
