"""Jupyter magics for academicflow.

Owner: Member 4.
"""

from __future__ import annotations

from academicflow.magics.session import Session, get_session, reset_session


def load_ipython_extension(ipython) -> None:
    """Register the magics; called by ``%load_ext academicflow``."""
    from academicflow.magics.magics import AcademicMagics

    ipython.register_magics(AcademicMagics)


__all__ = ["Session", "get_session", "reset_session", "load_ipython_extension"]
