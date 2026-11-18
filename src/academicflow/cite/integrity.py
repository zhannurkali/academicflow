"""Citation integrity checks.

Owner: Member 3.
"""

from __future__ import annotations

from academicflow.cite.bib import Bibliography
from academicflow.types import Issue


def check_integrity(text: str, bib: Bibliography) -> list[Issue]:
    """Check citations against the bibliography.

    TODO(member 3): cite-missing-key, cite-unused, cite-duplicate-doi, cite-incomplete.
    """
    return []
