# Export

One command turns the notebook session into a finished manuscript with formatted citations and
a reference list.

```python
%aexport paper.docx     # Word
%aexport paper.tex      # LaTeX
%aexport paper.md       # Markdown
```

Or from Python:

```python
from academicflow.export import export_document, export_notebook
from academicflow.magics.session import get_session

export_document(get_session(), "paper.docx", fmt="docx")   # "docx" | "latex" | "md"
```

## What the document contains

1. Title and authors (if set with `%%academic --title`)
2. Abstract (from `%aabstract` or an `abstract` section)
3. Sections in the order you wrote them, each with a heading
4. A **References** list in the chosen style

Sections named `section-<n>` (the automatic names) get no heading.

Citations are rendered in one pass over the whole paper, so IEEE and Nature number references in
order of first appearance across all sections.

## Formats

**DOCX.** Built with `pypandoc` (bundled pandoc). The reference document sets Times New Roman,
12 pt, 1.5 line spacing. To use your own styles, place a `reference.docx` in
`academicflow/export/templates/`. If pandoc fails, a simpler python-docx version is written and a
warning is shown.

**LaTeX.** The body is converted with pandoc and placed in `templates/article.tex`
(`article` class, title, author, abstract environment, sections). APA gets a hanging-indent
reference section, IEEE and Nature get `thebibliography`. The `.tex` file is written without TeX
installed, and compiles with `pdflatex`.

**Markdown.** Plain markdown. Nature citations use `<sup>n</sup>`.

## Export without Jupyter

```python
from academicflow.export import export_notebook

export_notebook("paper.ipynb", "paper.docx", fmt="docx", style="apa", bib_path="refs.bib")
```

or from a terminal:

```bash
python -m academicflow.export paper.ipynb paper.docx --style=ieee --bib refs.bib
```

The notebook is read like this:

- Cells starting with `%%academic` are used. `--section`, `--title`, `--authors` and `--style` are
  honoured.
- If there are none, all markdown cells are used: the first `# Heading` is the title and `##`
  headings name the sections.
- The bibliography is `bib_path`, or the first `%acite PATH` found in the notebook.
- A `style` argument other than `"apa"` overrides `--style` in the cells.

## Known limitations

- The pandoc-based DOCX uses pandoc's styles for headings and the title block, adjusted to Times
  New Roman. Journal-specific templates need a custom `reference.docx`.
- Figures and tables in cells are passed through pandoc but are not specially numbered.
- The python-docx fallback supports bold, italic and superscripts only.
