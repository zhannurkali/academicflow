"""Citation manager: BibTeX parsing, APA/IEEE/Nature formatting, integrity checks.

Owner: Member 3.
"""

from __future__ import annotations

from academicflow.cite.bib import Bibliography
from academicflow.cite.integrity import check_integrity
from academicflow.cite.render import find_citations, render

STYLES = ("apa", "ieee", "nature")

__all__ = ["Bibliography", "find_citations", "render", "check_integrity", "STYLES"]
