"""LaTeX export: our own article template, body converted with pandoc."""
from __future__ import annotations

import importlib.resources
from typing import Any

from academicflow.export.common import Prepared, prepare, section_heading, strip_number

_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def latex_escape(text: str) -> str:
    """Escape LaTeX special characters in plain text (titles, author names, headings)."""
    return "".join(_ESCAPES.get(ch, ch) for ch in text)


def _md_to_tex(text: str) -> str:
    import pypandoc

    return pypandoc.convert_text(text, "latex", format="markdown").strip()


def _template() -> str:
    return (
        importlib.resources.files("academicflow.export")
        .joinpath("templates", "article.tex")
        .read_text(encoding="utf-8")
    )


def _references(p: Prepared) -> tuple[str, str]:
    """Return ``(latex_block, biblabel_preamble)`` for the reference list."""
    if not p.references:
        return "", ""
    if p.style == "apa":
        items = [
            "\\noindent\\hangindent=2em\\hangafter=1 " + _md_to_tex(ref) + "\\par\\vspace{4pt}"
            for ref in p.references
        ]
        return "\\section*{References}\n" + "\n".join(items), ""
    items = [
        f"\\bibitem{{ref{i}}} {_md_to_tex(strip_number(ref))}"
        for i, ref in enumerate(p.references, 1)
    ]
    block = "\\begin{thebibliography}{99}\n" + "\n".join(items) + "\n\\end{thebibliography}"
    label = ""
    if p.style == "nature":
        label = "\\makeatletter\\renewcommand\\@biblabel[1]{#1.}\\makeatother"
    return block, label


def render_latex(p: Prepared) -> str:
    """Fill the article template with a prepared document."""
    abstract = (
        "\\begin{abstract}\n" + _md_to_tex(p.abstract) + "\n\\end{abstract}" if p.abstract else ""
    )
    body = []
    for name, text in p.sections:
        heading = section_heading(name)
        if heading:
            body.append(f"\\section{{{latex_escape(heading)}}}")
        body.append(_md_to_tex(text))
    refs, biblabel = _references(p)
    values = {
        "<<BIBLABEL>>": biblabel,
        "<<TITLE>>": latex_escape(p.title or ""),
        "<<AUTHOR>>": " \\and ".join(latex_escape(a) for a in p.authors),
        "<<MAKETITLE>>": "\\maketitle" if p.title else "",
        "<<ABSTRACT>>": abstract,
        "<<BODY>>": "\n\n".join(body),
        "<<REFERENCES>>": refs,
    }
    out = _template()
    for key, value in values.items():
        out = out.replace(key, value)
    return out


def export_latex(session: Any, path: str) -> str:
    """Write the session as a ``.tex`` file that compiles with pdflatex.

    TeX does not need to be installed to produce the file.

    Args:
        session: Session-like object.
        path: Output ``.tex`` path.

    Returns:
        The path that was written.
    """
    prepared = prepare(session, "latex")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render_latex(prepared))
    return path
