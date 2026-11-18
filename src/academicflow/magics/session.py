"""Notebook-wide state shared by all magics. Plain Python, no IPython import.

Owner: Member 4.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from academicflow.cite.bib import Bibliography


@dataclass
class Session:
    """State of the paper being written in the current notebook."""

    profile: str = "apa"
    bib: Bibliography | None = None
    bib_path: str | None = None
    sections: dict[str, str] = field(default_factory=dict)  # insertion-ordered
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""

    def set_section(self, name: str, text: str) -> None:
        """Store a section; re-running a cell replaces it and keeps its position."""
        self.sections[name] = text

    def full_text(self) -> str:
        """All sections joined in order."""
        return "\n\n".join(self.sections.values())


_SESSION: Session | None = None


def get_session() -> Session:
    """Return the singleton session, creating it on first use."""
    global _SESSION
    if _SESSION is None:
        _SESSION = Session()
    return _SESSION


def reset_session() -> Session:
    """Discard all state and return a fresh session."""
    global _SESSION
    _SESSION = Session()
    return _SESSION
