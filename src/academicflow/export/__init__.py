"""Export a paper to DOCX, LaTeX or Markdown.

Owner: Member 4.
"""

from __future__ import annotations

from pathlib import Path


def _assemble_markdown(session) -> str:
    parts = []
    if session.title:
        parts.append(f"# {session.title}")
    if session.abstract:
        parts.append(f"## Abstract\n\n{session.abstract}")
    for name, text in session.sections.items():
        if name.lower() != "abstract":
            parts.append(f"## {name.replace('-', ' ').title()}\n\n{text}")
    return "\n\n".join(parts) + "\n"


def export_document(session, path: str, fmt: str | None = None) -> str:
    """Export the session's paper.

    Args:
        session: An :class:`academicflow.magics.Session`.
        path: Output path.
        fmt: ``"docx"``, ``"latex"`` or ``"md"``; inferred from the extension if omitted.

    Returns:
        The absolute output path.

    TODO(member 4): citations via cite.render(target="pandoc"), docx and latex output.
    """
    out = Path(path)
    fmt = fmt or {".docx": "docx", ".tex": "latex"}.get(out.suffix.lower(), "md")
    if fmt != "md":
        raise NotImplementedError(f"Export to {fmt} is not implemented yet (member 4)")
    out.write_text(_assemble_markdown(session), encoding="utf-8")
    return str(out.resolve())


def export_notebook(
    nb_path: str,
    out_path: str,
    fmt: str = "docx",
    style: str = "apa",
    bib_path: str | None = None,
) -> str:
    """Export a notebook file directly (no running kernel needed).

    TODO(member 4).
    """
    raise NotImplementedError("export_notebook is not implemented yet (member 4)")


__all__ = ["export_document", "export_notebook"]
