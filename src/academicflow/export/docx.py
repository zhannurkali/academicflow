"""DOCX export: pandoc first, python-docx as a fallback."""
from __future__ import annotations

import importlib.resources
import re
import subprocess
import tempfile
import warnings
from pathlib import Path
from typing import Any

from academicflow.export.common import Prepared, prepare, section_heading, to_pandoc_source

_FONT = "Times New Roman"
_reference_cache: str | None = None


def export_docx(session: Any, path: str) -> str:
    """Write the session as a Word document.

    Uses ``pypandoc`` (bundled pandoc) with a Times New Roman 12 pt, 1.5-spacing reference
    document. If pandoc fails for any reason a simpler python-docx rendering is written instead.

    Args:
        session: Session-like object (see :func:`academicflow.export.export_document`).
        path: Output ``.docx`` path.

    Returns:
        The path that was written.
    """
    prepared = prepare(session, "pandoc")
    try:
        import pypandoc

        extra: list[str] = []
        reference = _reference_doc()
        if reference:
            extra.append(f"--reference-doc={reference}")
        pypandoc.convert_text(
            to_pandoc_source(prepared),
            "docx",
            format="markdown",
            outputfile=path,
            extra_args=extra,
        )
    except Exception as exc:  # noqa: BLE001
        warnings.warn(
            f"pandoc conversion failed ({exc}); using python-docx fallback.", stacklevel=2
        )
        _write_fallback(prepared, path)
    return path


def _reference_doc() -> str | None:
    """Bundled ``templates/reference.docx`` if present, otherwise a generated one."""
    global _reference_cache
    try:
        bundled = importlib.resources.files("academicflow.export").joinpath(
            "templates", "reference.docx"
        )
        if bundled.is_file():
            return str(bundled)
    except Exception:  # noqa: BLE001
        pass
    if _reference_cache and Path(_reference_cache).exists():
        return _reference_cache
    _reference_cache = _generate_reference_docx()
    return _reference_cache


def _generate_reference_docx() -> str | None:
    """Create pandoc's default reference.docx and restyle it (Times New Roman 12, 1.5)."""
    try:
        import pypandoc
        from docx import Document
        from docx.enum.style import WD_STYLE_TYPE
        from docx.shared import Pt, RGBColor

        out = Path(tempfile.mkdtemp(prefix="academicflow-")) / "reference.docx"
        with open(out, "wb") as handle:
            subprocess.run(
                [pypandoc.get_pandoc_path(), "--print-default-data-file", "reference.docx"],
                stdout=handle,
                check=True,
            )
        doc = Document(str(out))
        body_styles = {"Normal", "Body Text", "First Paragraph", "Compact", "Block Text"}
        for style in doc.styles:
            if style.type != WD_STYLE_TYPE.PARAGRAPH:
                continue
            style.font.name = _FONT
            if style.name in body_styles:
                style.font.size = Pt(12)
                style.paragraph_format.line_spacing = 1.5
            else:
                style.font.color.rgb = RGBColor(0, 0, 0)
        doc.save(str(out))
        return str(out)
    except Exception:  # noqa: BLE001 - styling is optional
        return None


_INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^\s]+\^|<sup>.*?</sup>)")


def _add_inline(paragraph: Any, text: str) -> None:
    for token in _INLINE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**"):
            paragraph.add_run(token[2:-2]).bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            paragraph.add_run(token[1:-1]).italic = True
        elif token.startswith("^") and token.endswith("^"):
            paragraph.add_run(token[1:-1]).font.superscript = True
        elif token.startswith("<sup>"):
            paragraph.add_run(token[5:-6]).font.superscript = True
        else:
            paragraph.add_run(token)


def _write_fallback(p: Prepared, path: str) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt

    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = _FONT
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5

    def paragraphs(text: str) -> None:
        for block in re.split(r"\n\s*\n", text.strip()):
            block = block.strip()
            if not block:
                continue
            level = len(block) - len(block.lstrip("#"))
            if 0 < level <= 6 and block[level : level + 1] == " ":
                doc.add_heading(block[level + 1 :].strip(), level=min(level, 4))
            else:
                _add_inline(doc.add_paragraph(), " ".join(block.splitlines()))

    if p.title:
        doc.add_heading(p.title, level=0)
    if p.authors:
        line = doc.add_paragraph()
        line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        line.add_run(", ".join(p.authors)).italic = True
    if p.abstract:
        doc.add_heading("Abstract", level=1)
        paragraphs(p.abstract)
    for name, text in p.sections:
        heading = section_heading(name)
        if heading:
            doc.add_heading(heading, level=1)
        paragraphs(text)
    if p.references:
        doc.add_heading("References", level=1)
        for ref in p.references:
            _add_inline(doc.add_paragraph(), ref)
    doc.save(path)
