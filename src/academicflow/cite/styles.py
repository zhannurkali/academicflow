"""Reference formatters for APA 7, IEEE and Nature.

Owner: Member 3.
"""

from __future__ import annotations


def format_entry(entry: dict, style: str) -> str:
    """Format a normalised entry as a markdown reference string.

    TODO(member 3): real APA / IEEE / Nature formatting per entry type.
    """
    authors = ", ".join(last for _, last in entry.get("authors", []))
    return f"{authors} ({entry.get('year', 'n.d.')}). {entry.get('title', '')}."
