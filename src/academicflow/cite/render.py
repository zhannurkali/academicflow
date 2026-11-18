"""Inline citation rendering.

Owner: Member 3. Citation syntax is pandoc-style: ``[@key]``, ``[@a; @b]``, ``[@key, p. 12]``.
"""

from __future__ import annotations

from academicflow.cite.bib import Bibliography


def find_citations(text: str) -> list[tuple[str, int, int]]:
    """Find every cited key.

    Returns:
        ``(key, start, end)`` for each key occurrence.

    TODO(member 3).
    """
    return []


def render(
    text: str, bib: Bibliography, style: str, target: str = "markdown"
) -> tuple[str, list[str]]:
    """Replace citations with formatted inline citations.

    Args:
        text: Text containing ``[@key]`` citations.
        bib: The bibliography.
        style: ``"apa"``, ``"ieee"`` or ``"nature"``.
        target: ``"markdown"``, ``"pandoc"`` or ``"latex"``.

    Returns:
        ``(rendered_text, ordered_reference_list)``.

    TODO(member 3).
    """
    return text, []
