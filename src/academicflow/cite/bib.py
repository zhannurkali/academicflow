"""BibTeX loading and normalisation for academicflow.cite."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from pybtex.database import BibliographyData, parse_file, parse_string
from pybtex.exceptions import PybtexError

# Combining marks for LaTeX accent commands such as \" \' \` \^ \~ \= \. \c \v \u \H \k
_ACCENTS = {
    '"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302", "~": "\u0303",
    "=": "\u0304", ".": "\u0307", "c": "\u0327", "v": "\u030c", "u": "\u0306",
    "H": "\u030b", "k": "\u0328",
}  # fmt: skip

_SPECIALS = {
    r"\ss": "ß", r"\o": "ø", r"\O": "Ø", r"\aa": "å", r"\AA": "Å",
    r"\ae": "æ", r"\AE": "Æ", r"\l": "ł", r"\L": "Ł",
}  # fmt: skip

_ESCAPES = {r"\&": "&", r"\%": "%", r"\_": "_", r"\#": "#", r"\$": "$"}

_PUNCT_ACCENT = re.compile(r"\\([`'^\"~=.])\s*(?:\{\s*([A-Za-z])\s*\}|([A-Za-z]))")
_LETTER_ACCENT = re.compile(r"\\([cvuHk])\s*(?:\{\s*([A-Za-z])\s*\}|\s([A-Za-z]))")
_DOTLESS_I = re.compile(r"\\i(?![A-Za-z])")


def clean_latex(text: str) -> str:
    """Convert a BibTeX field value to plain Unicode text.

    Handles common LaTeX accents (``{\\"o}`` -> ``ö``), escaped symbols (``\\&``),
    and removes protective braces.

    Args:
        text: Raw BibTeX field value.

    Returns:
        Cleaned text with collapsed whitespace.
    """
    out = _DOTLESS_I.sub("i", text)
    out = _PUNCT_ACCENT.sub(lambda m: (m.group(2) or m.group(3)) + _ACCENTS[m.group(1)], out)
    out = _LETTER_ACCENT.sub(lambda m: (m.group(2) or m.group(3)) + _ACCENTS[m.group(1)], out)
    for src, dst in _SPECIALS.items():
        out = re.sub(re.escape(src) + r"(?![A-Za-z])", dst, out)
    for src, dst in _ESCAPES.items():
        out = out.replace(src, dst)
    out = out.replace("{", "").replace("}", "").replace("~", " ")
    out = unicodedata.normalize("NFC", out)
    return re.sub(r"\s+", " ", out).strip()


def _normalise_pages(pages: str) -> str:
    return re.sub(r"\s*(?:--|-|\u2013|\u2014)\s*", "\u2013", pages)


def _normalise_entry(key: str, entry: Any) -> dict[str, Any]:
    fields = entry.fields
    authors: list[tuple[str, str]] = []
    et_al = False
    for person in entry.persons.get("author", []):
        if str(person).strip() == "others":
            et_al = True
            continue
        first = clean_latex(" ".join(person.first_names + person.middle_names))
        last = clean_latex(" ".join(person.prelast_names + person.last_names))
        if person.lineage_names:
            last = f"{last} {clean_latex(' '.join(person.lineage_names))}"
        authors.append((first, last))

    def get(name: str) -> str:
        return clean_latex(fields.get(name, ""))

    doi = get("doi")
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return {
        "key": key,
        "type": entry.type.lower(),
        "authors": authors,
        "et_al": et_al,
        "title": get("title"),
        "year": get("year"),
        "journal": get("journal") or get("journaltitle"),
        "booktitle": get("booktitle"),
        "volume": get("volume"),
        "number": get("number") or get("issue"),
        "pages": _normalise_pages(get("pages")),
        "publisher": get("publisher"),
        "doi": doi,
        "url": get("url"),
    }


class Bibliography:
    """A set of normalised BibTeX entries.

    Each entry is a dict with keys: key, type, authors [(first, last)], et_al, title,
    year, journal, booktitle, volume, number, pages, publisher, doi, url.
    Missing fields are empty strings.
    """

    def __init__(self, entries: dict[str, dict[str, Any]] | None = None) -> None:
        self._entries: dict[str, dict[str, Any]] = dict(entries or {})

    @classmethod
    def from_string(cls, bibtex: str) -> Bibliography:
        """Parse BibTeX text.

        Args:
            bibtex: BibTeX source.

        Returns:
            A Bibliography.

        Raises:
            ValueError: If the BibTeX is malformed (message includes the line number).
        """
        try:
            data = parse_string(bibtex, "bibtex")
        except PybtexError as exc:
            raise cls._parse_error(exc, None) from exc
        return cls._from_data(data)

    @classmethod
    def from_file(cls, path: str | Path) -> Bibliography:
        """Parse a .bib file.

        Args:
            path: Path to the file.

        Returns:
            A Bibliography.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the BibTeX is malformed (message includes the line number).
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"BibTeX file not found: {p}")
        try:
            data = parse_file(str(p), "bibtex")
        except PybtexError as exc:
            raise cls._parse_error(exc, p.name) from exc
        return cls._from_data(data)

    @staticmethod
    def _parse_error(exc: Exception, name: str | None) -> ValueError:
        line = getattr(exc, "lineno", None)
        where = f"{name}, " if name else ""
        where += f"line {line}" if line else "unknown line"
        return ValueError(f"Invalid BibTeX ({where}): {getattr(exc, 'message', exc)}")

    @classmethod
    def _from_data(cls, data: BibliographyData) -> Bibliography:
        return cls({key: _normalise_entry(key, e) for key, e in data.entries.items()})

    def keys(self) -> list[str]:
        """Return entry keys in file order."""
        return list(self._entries)

    def get(self, key: str) -> dict[str, Any]:
        """Return the normalised entry for ``key``.

        Raises:
            KeyError: With a readable message if the key is unknown.
        """
        try:
            return self._entries[key]
        except KeyError:
            raise KeyError(f"Unknown citation key: '{key}' (not in the loaded .bib)") from None

    def __contains__(self, key: object) -> bool:
        return key in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def format_reference(self, key: str, style: str) -> str:
        """Format one reference as markdown.

        Args:
            key: Citation key.
            style: "apa", "ieee" or "nature".

        Returns:
            The formatted reference (markdown italics/bold).
        """
        from .styles import format_reference  # lazy: styles.py is written after bib.py

        return format_reference(self.get(key), style)
