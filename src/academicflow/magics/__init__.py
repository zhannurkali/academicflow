"""Jupyter magics for academicflow."""
from __future__ import annotations

from academicflow.magics.magics import (
    AcademicMagics,
    load_ipython_extension,
    unload_ipython_extension,
)
from academicflow.magics.session import Session, get_session, reset_session

__all__ = [
    "AcademicMagics",
    "Session",
    "get_session",
    "load_ipython_extension",
    "reset_session",
    "unload_ipython_extension",
]
