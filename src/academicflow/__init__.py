"""academicflow: an academic-writing pipeline for Jupyter notebooks.

Quick start in a notebook::

    %load_ext academicflow
    %acite refs.bib
    %%academic --style=apa --section=introduction
    Transformers changed NLP [@vaswani2017].
"""

from __future__ import annotations

__version__ = "0.1.0.dev0"

from academicflow.cite import Bibliography, check_integrity, find_citations, render
from academicflow.core import analyze
from academicflow.style import check, check_document, load_profile
from academicflow.summarize import generate_abstract, summarize
from academicflow.types import Issue, TextStats

__all__ = [
    "__version__",
    "Issue",
    "TextStats",
    "analyze",
    "check",
    "check_document",
    "load_profile",
    "Bibliography",
    "find_citations",
    "render",
    "check_integrity",
    "summarize",
    "generate_abstract",
    "load_ipython_extension",
]


def load_ipython_extension(ipython):  # pragma: no cover - thin wrapper
    """Enable ``%load_ext academicflow`` (implemented in academicflow.magics)."""
    from academicflow.magics import load_ipython_extension as _load

    _load(ipython)
