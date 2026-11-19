"""Tests for DOCX / LaTeX / Markdown export (cite.render is faked, so no network or bib needed)."""
from __future__ import annotations

import json
import re

import pytest

from academicflow import cite
from academicflow.export import export_document, export_notebook, infer_format
from academicflow.export.common import (
    citation_style,
    format_reference_list,
    prepare,
    section_heading,
    strip_number,
)
from academicflow.export.latex import latex_escape
from academicflow.magics.session import Session

_CITE = re.compile(r"\[@([^\]]+)\]")


def fake_render(text, bib, style_name, target="markdown"):
    order = []

    def sub(match):
        key = match.group(1)
        if key not in order:
            order.append(key)
        return f"(Cited, {key})"

    return _CITE.sub(sub, text), [f"Author, A. ({k}). *Title of {k}*." for k in order]


def pandoc_available():
    try:
        import pypandoc

        pypandoc.get_pandoc_version()
        return True
    except Exception:  # noqa: BLE001
        return False


needs_pandoc = pytest.mark.skipif(not pandoc_available(), reason="pandoc not available")


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr(cite, "render", fake_render)
    s = Session(profile="apa", bib=object())
    s.title = "A Study of R&D_costs"
    s.authors = ["Ada Lovelace", "Alan Turing"]
    s.abstract = "We study things."
    s.set_section("introduction", "Prior work [@smith2020] matters.")
    s.set_section("methods", "We did it & more.")
    return s


def test_helpers():
    assert citation_style("IEEE") == "ieee"
    assert section_heading("introduction") == "Introduction"
    assert section_heading("section-3") is None
    assert strip_number("[12] Foo") == "Foo" and strip_number("3. Foo") == "Foo"
    assert format_reference_list(["A"], "ieee") == ["[1] A"]
    assert format_reference_list(["A"], "nature") == ["1. A"]
    assert format_reference_list(["[1] A"], "ieee") == ["[1] A"]
    assert format_reference_list(["A"], "apa") == ["A"]
    assert latex_escape("R&D_50%") == r"R\&D\_50\%"
    assert infer_format("x.tex") == "latex" and infer_format("x.md") == "md"
    assert infer_format("x.docx") == "docx" and infer_format("x.bin") == "docx"


def test_prepare_renders_once_and_splits(session):
    p = prepare(session, "pandoc")
    assert p.abstract == "We study things."
    assert [n for n, _ in p.sections] == ["introduction", "methods"]
    assert "(Cited, smith2020)" in p.sections[0][1]
    assert p.references == ["Author, A. (smith2020). *Title of smith2020*."]


def test_export_md(session, tmp_path):
    path = export_document(session, str(tmp_path / "paper.md"), "md")
    text = open(path, encoding="utf-8").read()
    assert text.startswith("# A Study of R&D_costs")
    assert "## Abstract" in text and "## Introduction" in text and "## References" in text
    assert text.index("## Abstract") < text.index("## Introduction") < text.index("## References")
    assert "(Cited, smith2020)" in text and "Title of smith2020" in text


def test_abstract_section_is_not_duplicated(session, tmp_path):
    session.set_section("abstract", "Section abstract")
    session.abstract = "Stored abstract"
    text = open(export_document(session, str(tmp_path / "p.md"), "md"), encoding="utf-8").read()
    assert text.count("## Abstract") == 1 and "Stored abstract" in text
    assert "Section abstract" not in text


def test_unknown_format_and_empty_session(session, tmp_path):
    with pytest.raises(ValueError):
        export_document(session, str(tmp_path / "x.pdf"), "pdf")
    with pytest.raises(ValueError):
        export_document(Session(), str(tmp_path / "x.md"), "md")


def test_citations_without_bib_warn(tmp_path):
    s = Session()
    s.set_section("intro", "See [@key].")
    with pytest.warns(UserWarning):
        path = export_document(s, str(tmp_path / "p.md"), "md")
    assert "[@key]" in open(path, encoding="utf-8").read()


@needs_pandoc
def test_export_latex_apa(session, tmp_path):
    tex = open(export_document(session, str(tmp_path / "p.tex"), "latex"), encoding="utf-8").read()
    assert "\\begin{document}" in tex and "\\end{document}" in tex
    assert "\\section{Introduction}" in tex and "\\begin{abstract}" in tex
    assert "R\\&D\\_costs" in tex and "\\maketitle" in tex
    assert "\\section*{References}" in tex and "\\hangindent" in tex
    assert "<<" not in tex


@needs_pandoc
def test_export_latex_ieee_uses_thebibliography(session, tmp_path):
    session.profile = "ieee"
    tex = open(export_document(session, str(tmp_path / "p.tex"), "latex"), encoding="utf-8").read()
    assert "\\begin{thebibliography}" in tex and "\\bibitem{ref1}" in tex


@needs_pandoc
def test_export_docx(session, tmp_path):
    from docx import Document

    path = export_document(session, str(tmp_path / "paper.docx"), "docx")
    doc = Document(path)
    texts = [p.text for p in doc.paragraphs]
    headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
    assert "Introduction" in headings and "References" in headings
    assert any("Title of smith2020" in t for t in texts)
    assert any("A Study of R&D_costs" in t for t in texts)


def test_docx_fallback_without_pandoc(session, tmp_path, monkeypatch):
    from docx import Document

    from academicflow.export import docx as docx_mod

    def boom(*a, **k):
        raise RuntimeError("no pandoc")

    monkeypatch.setattr(docx_mod, "_reference_doc", boom)
    with pytest.warns(UserWarning):
        path = export_document(session, str(tmp_path / "fallback.docx"), "docx")
    texts = [p.text for p in Document(path).paragraphs]
    assert "Introduction" in texts and any("Title of smith2020" in t for t in texts)


def _write_notebook(path, cells):
    nb = {
        "nbformat": 4, "nbformat_minor": 5, "metadata": {},
        "cells": [
            {"cell_type": kind, "metadata": {}, "source": src, "id": f"cell{i}",
             **({"outputs": [], "execution_count": None} if kind == "code" else {})}
            for i, (kind, src) in enumerate(cells)
        ],
    }
    path.write_text(json.dumps(nb), encoding="utf-8")


def test_export_notebook_from_academic_cells(tmp_path, monkeypatch):
    monkeypatch.setattr(cite, "render", fake_render)
    monkeypatch.setattr(cite.Bibliography, "from_file", classmethod(lambda cls, p: object()),
                        raising=False)
    nb = tmp_path / "paper.ipynb"
    _write_notebook(nb, [
        ("code", "%load_ext academicflow"),
        ("code", "%acite refs.bib"),
        ("code", "%%academic --title\nMy Paper\nAda Lovelace"),
        ("code", "%%academic --section=introduction --style=ieee\nHello [@smith2020]."),
        ("markdown", "ignored when %%academic cells exist"),
    ])
    out = export_notebook(str(nb), str(tmp_path / "out.md"), "md")
    text = open(out, encoding="utf-8").read()
    assert "# My Paper" in text and "## Introduction" in text and "ignored" not in text
    assert "[1] " in text  # ieee picked up from the cell and numbered


def test_export_notebook_markdown_fallback(tmp_path):
    nb = tmp_path / "plain.ipynb"
    _write_notebook(nb, [
        ("markdown", "# Plain Title"),
        ("markdown", "## Introduction\nSome intro."),
        ("markdown", "Loose paragraph."),
    ])
    text = open(export_notebook(str(nb), str(tmp_path / "o.md"), "md"), encoding="utf-8").read()
    assert text.startswith("# Plain Title")
    assert "## Introduction" in text and "Some intro." in text and "Loose paragraph." in text


def test_export_notebook_empty_raises(tmp_path):
    nb = tmp_path / "empty.ipynb"
    _write_notebook(nb, [("code", "print(1)")])
    with pytest.raises(ValueError):
        export_notebook(str(nb), str(tmp_path / "o.md"), "md")
