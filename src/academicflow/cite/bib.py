"""BibTeX loading.

Owner: Member 3.
"""

from __future__ import annotations

from pathlib import Path


class Bibliography:
    """A collection of BibTeX entries, keyed by citation key."""

    def __init__(self, entries: dict[str, dict] | None = None) -> None:
        self.entries: dict[str, dict] = entries or {}

    @classmethod
    def from_string(cls, bibtex: str) -> Bibliography:
        """Parse BibTeX source text.

        TODO(member 3): normalise authors/fields, LaTeX accents, clear errors.
        """
        from pybtex.database import parse_string

        data = parse_string(bibtex, "bibtex")
        entries = {}
        for key, entry in data.entries.items():
            fields = {k.lower(): str(v) for k, v in entry.fields.items()}
            authors = [
                (" ".join(p.first_names + p.middle_names), " ".join(p.last_names))
                for p in entry.persons.get("author", [])
            ]
            entries[key] = {"type": entry.type, "authors": authors, **fields}
        return cls(entries)

    @classmethod
    def from_file(cls, path: str | Path) -> Bibliography:
        """Load a ``.bib`` file."""
        return cls.from_string(Path(path).read_text(encoding="utf-8"))

    def keys(self) -> list[str]:
        """Return all citation keys in file order."""
        return list(self.entries)

    def get(self, key: str) -> dict:
        """Return the normalised entry for ``key``."""
        if key not in self.entries:
            raise KeyError(f"Citation key {key!r} not found in bibliography")
        return self.entries[key]

    def format_reference(self, key: str, style: str) -> str:
        """Format one reference in ``"apa"``, ``"ieee"`` or ``"nature"`` style.

        TODO(member 3): implement in styles.py.
        """
        from academicflow.cite.styles import format_entry

        return format_entry(self.get(key), style)

    def __contains__(self, key: object) -> bool:
        return key in self.entries

    def __len__(self) -> int:
        return len(self.entries)
