"""Build a session from a ``.ipynb`` file so papers can be exported from the command line."""
from __future__ import annotations

import os
import re
import shlex
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from academicflow.magics.session import Session

_ACITE = re.compile(r"^%acite\s+(\S+)", re.MULTILINE)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def parse_academic_args(argline: str) -> dict[str, Any]:
    """Parse the options after ``%%academic`` without importing IPython.

    Args:
        argline: Text after ``%%academic`` on the first cell line.

    Returns:
        Dict with ``style``, ``section``, ``authors`` (str or None) and ``title`` (bool).
    """
    result: dict[str, Any] = {"style": None, "section": None, "authors": None, "title": False}
    tokens = shlex.split(argline)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--title":
            result["title"] = True
        elif tok.startswith("--") and tok[2:].split("=", 1)[0] in ("style", "section", "authors"):
            key, _, value = tok[2:].partition("=")
            if not value and i + 1 < len(tokens):
                i += 1
                value = tokens[i]
            result[key] = value or None
        i += 1
    return result


def apply_title_cell(session: Session, body: str, authors_opt: str | None = None) -> None:
    """First non-empty line is the title; further non-empty lines are authors."""
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if lines:
        session.title = lines[0].lstrip("#").strip()
    if authors_opt:
        session.authors = [a.strip() for a in authors_opt.split(";") if a.strip()]
    elif len(lines) > 1:
        session.authors = lines[1:]


def _resolve(path: str, nb_dir: str) -> str:
    path = os.path.expanduser(path)
    if os.path.isabs(path) or os.path.exists(path):
        return path
    return os.path.join(nb_dir, path)


def session_from_notebook(nb_path: str, style: str = "apa", bib_path: str | None = None) -> Session:
    """Collect the paper from a notebook.

    Cells starting with ``%%academic`` are used (``--section``, ``--title``, ``--authors`` and
    ``--style`` are honoured). If there are none, all markdown cells are used in order: the first
    ``# Heading`` becomes the title and ``##`` headings name sections.

    Args:
        nb_path: Notebook path.
        style: Citation style / profile. A non-default value wins over ``--style`` in cells.
        bib_path: ``.bib`` file. If omitted, the first ``%acite PATH`` line in the notebook is used.

    Returns:
        A new (non-singleton) :class:`Session`.

    Raises:
        ValueError: If the notebook contains no usable text.
    """
    import nbformat

    # imported here, not at the top: magics.magics imports this module (circular otherwise)
    from academicflow.magics.session import Session as SessionClass

    nb = nbformat.read(nb_path, as_version=4)
    nb_dir = os.path.dirname(os.path.abspath(nb_path))
    session = SessionClass(profile=style)
    cell_style: str | None = None
    found_academic = False
    detected_bib: str | None = None

    for cell in nb.cells:
        source = cell.source if isinstance(cell.source, str) else "".join(cell.source)
        if cell.cell_type == "code":
            match = _ACITE.search(source)
            if match and detected_bib is None:
                detected_bib = match.group(1)
            first, _, body = source.partition("\n")
            if first.startswith("%%academic"):
                found_academic = True
                opts = parse_academic_args(first[len("%%academic") :])
                cell_style = opts["style"] or cell_style
                if opts["title"]:
                    apply_title_cell(session, body, opts["authors"])
                    continue
                body = body.strip("\n")
                name = opts["section"] or session.auto_section_name(body)
                session.set_section(name, body)

    if not found_academic:
        for cell in nb.cells:
            if cell.cell_type != "markdown":
                continue
            text = (cell.source if isinstance(cell.source, str) else "".join(cell.source)).strip()
            if not text:
                continue
            first, _, rest = text.partition("\n")
            heading = _HEADING.match(first)
            if heading and len(heading.group(1)) == 1 and session.title is None:
                session.title = heading.group(2)
                text = rest.strip()
                if not text:
                    continue
                session.set_section(session.auto_section_name(text), text)
            elif heading:
                body = rest.strip()
                if body:
                    session.set_section(heading.group(2), body)
            else:
                session.set_section(session.auto_section_name(text), text)

    if style == "apa" and cell_style:
        session.profile = cell_style
    chosen = bib_path or detected_bib
    if chosen:
        from academicflow import cite

        session.bib_path = _resolve(chosen, nb_dir)
        session.bib = cite.Bibliography.from_file(session.bib_path)
    if session.is_empty():
        raise ValueError(f"No %%academic or markdown cells with text found in {nb_path}.")
    return session
