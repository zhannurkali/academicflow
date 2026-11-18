"""IPython magics: %acite, %%academic, %astats, %acheck, %aabstract, %aexport.

Owner: Member 4.
"""

from __future__ import annotations

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import HTML, Markdown, display

from academicflow import cite, core, style, summarize
from academicflow.magics.display import issues_html
from academicflow.magics.session import get_session


@magics_class
class AcademicMagics(Magics):
    """Magics registered by ``%load_ext academicflow``."""

    @line_magic
    def acite(self, line: str) -> None:
        """%acite PATH - load a BibTeX file into the session."""
        path = line.strip()
        if not path:
            print("Usage: %acite refs.bib")
            return
        session = get_session()
        session.bib = cite.Bibliography.from_file(path)
        session.bib_path = path
        print(f"Loaded {len(session.bib)} references from {path}")

    @magic_arguments()
    @argument("--style", default=None, help="apa | ieee | nature (persists)")
    @argument("--section", default=None, help="section name, e.g. introduction")
    @argument("--no-check", action="store_true", help="hide style issues")
    @cell_magic
    def academic(self, line: str, cell: str) -> None:
        """%%academic [--style=apa] [--section=NAME] [--no-check]"""
        args = parse_argstring(self.academic, line)
        session = get_session()
        if args.style:
            session.profile = args.style.lower()
        name = args.section or f"section-{len(session.sections) + 1}"
        session.set_section(name, cell)

        text, refs = cell, []
        if session.bib is not None:
            text, refs = cite.render(cell, session.bib, session.profile, target="markdown")
        elif cite.find_citations(cell):
            print("Hint: run %acite refs.bib to format citations.")
        md = text + ("\n\n**References**\n\n" + "\n".join(f"- {r}" for r in refs) if refs else "")
        display(Markdown(md))
        if not args.no_check:
            display(HTML(issues_html(style.check(cell, session.profile, section=name))))

    @line_magic
    def astats(self, line: str) -> None:
        """%astats [SECTION] - text statistics (TODO(member 4): HTML table)."""
        session = get_session()
        text = session.sections.get(line.strip(), "") if line.strip() else session.full_text()
        print(core.analyze(text))

    @line_magic
    def acheck(self, line: str) -> None:
        """%acheck - check the whole document and its citations."""
        session = get_session()
        issues = style.check_document(session.sections, session.profile)
        if session.bib is not None:
            issues += cite.check_integrity(session.full_text(), session.bib)
        display(HTML(issues_html(issues, title="Document issues")))

    @line_magic
    def aabstract(self, line: str) -> None:
        """%aabstract - generate an abstract (TODO(member 4): --words, --llm)."""
        session = get_session()
        session.abstract = summarize.generate_abstract(session.sections)
        display(Markdown(f"**Abstract.** {session.abstract}"))

    @line_magic
    def aexport(self, line: str) -> None:
        """%aexport PATH [--format=docx|latex|md] (TODO(member 4))."""
        from academicflow.export import export_document

        path = line.split()[0] if line.strip() else "paper.md"
        print(f"Exported to {export_document(get_session(), path)}")
