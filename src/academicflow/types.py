"""Shared data types used by every academicflow module.

Owned by Member 5. Change only through a PR that mentions all affected members.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEVERITIES = ("info", "warning", "error")


@dataclass
class Issue:
    """A single problem found in a text.

    Attributes:
        rule: Machine-readable rule id, e.g. ``"informal-word"`` or ``"cite-missing-key"``.
        message: Human-readable explanation.
        severity: ``"info"``, ``"warning"`` or ``"error"``.
        start: Character offset (inclusive) in the text that was checked.
        end: Character offset (exclusive).
        suggestion: Optional replacement or advice.
        section: Section name, filled when checking a multi-section document.
    """

    rule: str
    message: str
    severity: str = "warning"
    start: int = 0
    end: int = 0
    suggestion: str | None = None
    section: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")


@dataclass
class TextStats:
    """Summary statistics for a text, returned by :func:`academicflow.core.analyze`."""

    word_count: int = 0
    sentence_count: int = 0
    reading_time_min: float = 0.0  # at 238 words per minute
    flesch_reading_ease: float = 0.0
    flesch_kincaid_grade: float = 0.0
    avg_sentence_length: float = 0.0
    keywords: list[tuple[str, float]] = field(default_factory=list)
    passive_ratio: float = 0.0
