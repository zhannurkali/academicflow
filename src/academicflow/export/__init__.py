"""Export an academicflow session or notebook to DOCX, LaTeX or Markdown."""
from __future__ import annotations

import os
from typing import Any

from academicflow.export.common import prepare, to_markdown

_ALIASES = {"docx": "docx", "word": "docx", "latex": "latex", "tex": "latex", "md": "md",
            "markdown": "md"}
_EXTENSIONS = {".docx": "docx", ".tex": "latex", ".latex": "latex", ".md": "md",
               ".markdown": "md"}


def infer_format(path: str, default: str = "docx") -> str:
    """Pick an export format from a file extension (``default`` if unknown)."""
    return _EXTENSIONS.get(os.path.splitext(path)[1].lower(), default)


def export_document(session: Any, path: str, fmt: str = "docx") -> str:
    """Export the session's paper.

    The document contains the title, authors, abstract, the sections in order and a formatted
    reference list. Citations are rendered over the whole paper, so numbered styles number
    references by first appearance.

    Args:
        session: Object with ``profile, bib, sections, title, authors, abstract``
            (normally ``academicflow.magics.session.get_session()``).
        path: Output file path.
        fmt: ``"docx"``, ``"latex"`` or ``"md"``.

    Returns:
        Absolute path of the written file.

    Raises:
        ValueError: For an unknown format or an empty session.
    """
    key = _ALIASES.get(str(fmt).lower())
    if key is None:
        raise ValueError(f"Unknown export format {fmt!r}; use 'docx', 'latex' or 'md'.")
    out = os.path.abspath(os.path.expanduser(path))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if key == "md":
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(to_markdown(prepare(session, "markdown")))
    elif key == "latex":
        from academicflow.export.latex import export_latex

        export_latex(session, out)
    else:
        from academicflow.export.docx import export_docx

        export_docx(session, out)
    return out


def export_notebook(
    nb_path: str,
    out_path: str,
    fmt: str = "docx",
    style: str = "apa",
    bib_path: str | None = None,
) -> str:
    """Export a notebook without opening Jupyter.

    Reads ``%%academic`` cells (or all markdown cells if there are none) and reuses
    :func:`export_document`.

    Args:
        nb_path: Input ``.ipynb`` path.
        out_path: Output path.
        fmt: ``"docx"``, ``"latex"`` or ``"md"``.
        style: Citation style. A non-default value overrides ``--style`` in the notebook.
        bib_path: ``.bib`` file; defaults to the notebook's ``%acite`` path.

    Returns:
        Absolute path of the written file.
    """
    from academicflow.export.notebook import session_from_notebook

    session = session_from_notebook(nb_path, style=style, bib_path=bib_path)
    return export_document(session, out_path, fmt)


__all__ = ["export_document", "export_notebook", "infer_format"]
