"""IPython magics for academicflow: %acite, %%academic, %astats, %acheck, %aabstract, %aexport.

Every magic calls the public API of the other modules (core, style, cite, summarize, export)
and catches exceptions so the user sees one short red message instead of a traceback
(pass ``--debug`` to get the traceback).
"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import HTML, FileLink, Markdown
from IPython.display import display as ipy_display

from academicflow.export import export_document, infer_format
from academicflow.export.common import citation_style, format_reference_list
from academicflow.export.notebook import apply_title_cell
from academicflow.magics import display as ui
from academicflow.magics.session import (
    get_session,
    join_with_offsets,
    locate_issues,
)

_NO_SECTIONS = "No sections yet. Write one with %%academic --section=introduction."


def _html(markup: str) -> None:
    ipy_display(HTML(markup))


@magics_class
class AcademicMagics(Magics):
    """The academicflow magic commands."""

    # ------------------------------------------------------------------ plumbing
    def _guard(self, func: Callable, line: str, impl: Callable, *extra: Any) -> Any:
        """Parse ``line`` with ``func``'s argument parser and run ``impl`` safely."""
        debug = "--debug" in line.split()
        try:
            args = parse_argstring(func, line)
            return impl(args, *extra)
        except Exception as exc:  # noqa: BLE001 - shown to the user, traceback with --debug
            if debug:
                raise
            if isinstance(exc, KeyError) and exc.args:
                text = str(exc.args[0])
            else:
                text = str(exc) or type(exc).__name__
            _html(ui.error_html(text))
            return None

    # ------------------------------------------------------------------ %acite
    @magic_arguments()
    @argument("path", help="Path to a BibTeX file.")
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @line_magic
    def acite(self, line: str = "") -> None:
        """Load a BibTeX file into the session: ``%acite refs.bib``."""
        return self._guard(self.acite, line, self._acite)

    def _acite(self, args: Any) -> None:
        from academicflow import cite

        session = get_session()
        path = os.path.expanduser(args.path)
        bib = cite.Bibliography.from_file(path)
        session.bib, session.bib_path = bib, path
        print(f"Loaded {len(bib.keys())} references from {args.path}")

    # ------------------------------------------------------------------ %%academic
    @magic_arguments()
    @argument("--style", help="Venue profile: apa, ieee, nature (or a YAML path).")
    @argument("--section", help="Section name (default: section-<n>).")
    @argument("--title", action="store_true",
              help="Cell is the title (first line) followed by one author per line.")
    @argument("--authors", help='Authors separated by ";" (with --title).')
    @argument("--no-check", dest="no_check", action="store_true", help="Hide the issue panel.")
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @cell_magic
    def academic(self, line: str = "", cell: str = "") -> None:
        """Render, store and check one section of the paper."""
        return self._guard(self.academic, line, self._academic, cell)

    def _academic(self, args: Any, cell: str) -> None:
        from academicflow import cite, style

        session = get_session()
        if args.style:
            style.load_profile(args.style)  # raises ValueError for unknown profiles
            session.profile = args.style

        text = cell.strip("\n")
        if args.title:
            apply_title_cell(session, text, args.authors)
            shown = f"# {session.title}" if session.title else ""
            if session.authors:
                shown += "\n\n*" + ", ".join(session.authors) + "*"
            ipy_display(Markdown(shown))
            return

        name = args.section or session.auto_section_name(text)
        session.set_section(name, text)

        rendered, refs = text, []
        if session.bib is not None:
            rendered, refs = cite.render(
                text, session.bib, citation_style(session.profile), target="markdown"
            )
        shown = rendered
        if refs:
            shown += "\n\n**References**\n\n" + "\n\n".join(
                format_reference_list(list(refs), citation_style(session.profile))
            )
        ipy_display(Markdown(shown))

        if session.bib is None and cite.find_citations(text):
            _html(ui.message("Citations found but no bibliography is loaded. "
                             "Run %acite refs.bib first.", "warning"))
        if not args.no_check:
            issues = style.check(text, session.profile, name)
            _html(ui.issue_panel(list(issues), text, title=f"Style issues ({name})"))

    # ------------------------------------------------------------------ %astats
    @magic_arguments()
    @argument("section", nargs="?", help="Section name (default: whole document).")
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @line_magic
    def astats(self, line: str = "") -> None:
        """Show text statistics for one section or the whole document."""
        return self._guard(self.astats, line, self._astats)

    def _astats(self, args: Any) -> None:
        from academicflow import core

        session = get_session()
        if args.section:
            if args.section not in session.sections:
                known = ", ".join(session.sections) or "none"
                raise KeyError(f"Unknown section {args.section!r}. Available: {known}")
            text, label = session.sections[args.section], f"Statistics: {args.section}"
        else:
            body = session.body_sections()
            if not body:
                _html(ui.message(_NO_SECTIONS, "warning"))
                return
            text, label = session.full_text(include_abstract=False), "Statistics: whole document"
        stats = core.analyze(text)
        passive = list(core.detect_passive(text))
        _html(ui.stats_table(stats, label) + ui.keyword_chips(list(stats.keywords)))
        if passive:
            _html(
                f"<b>Passive voice ({len(passive)})</b>"
                + ui.highlight_passive(text, passive)
            )

    # ------------------------------------------------------------------ %acheck
    @magic_arguments()
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @line_magic
    def acheck(self, line: str = "") -> None:
        """Check the whole document: style, cross-section rules and citation integrity."""
        return self._guard(self.acheck, line, self._acheck)

    def _acheck(self, args: Any) -> None:
        from academicflow import cite, style

        session = get_session()
        sections = dict(session.sections)
        if not sections:
            _html(ui.message(_NO_SECTIONS, "warning"))
            return
        issues = list(style.check_document(sections, session.profile))
        full, spans = join_with_offsets(sections)
        if session.bib is not None:
            issues += locate_issues(list(cite.check_integrity(full, session.bib)), spans)
        elif cite.find_citations(full):
            _html(ui.message("Citations found but no bibliography is loaded; "
                             "run %acite refs.bib to check them.", "warning"))

        groups: list[tuple[str, list, str | None]] = []
        for name, text in sections.items():
            groups.append((name, [i for i in issues if i.section == name], text))
        known = set(sections)
        general = [i for i in issues if i.section not in known]
        groups.append(("Document / bibliography", general, None))
        _html(ui.grouped_issue_panel(groups))

    # ------------------------------------------------------------------ %aabstract
    @magic_arguments()
    @argument("--words", type=int, default=200, help="Maximum abstract length in words.")
    @argument("--llm", action="store_true", help="Use the optional LLM backend.")
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @line_magic
    def aabstract(self, line: str = "") -> None:
        """Generate an abstract from the stored sections and store it."""
        return self._guard(self.aabstract, line, self._aabstract)

    def _aabstract(self, args: Any) -> None:
        import importlib

        # "from academicflow import summarize" can return the summarize() function
        summarize = importlib.import_module("academicflow.summarize")

        session = get_session()
        body = session.body_sections()
        if not body:
            _html(ui.message(_NO_SECTIONS, "warning"))
            return
        abstract = summarize.generate_abstract(
            body, max_words=args.words, method="llm" if args.llm else "extractive"
        )
        session.abstract = abstract
        session.set_section("abstract", abstract)
        ipy_display(Markdown(f"**Abstract** ({len(abstract.split())} words)\n\n{abstract}"))

    # ------------------------------------------------------------------ %aexport
    @magic_arguments()
    @argument("path", help="Output file, e.g. paper.docx or paper.tex.")
    @argument("--format", choices=["docx", "latex", "md"], help="Default: from the extension.")
    @argument("--debug", action="store_true", help="Show full tracebacks.")
    @line_magic
    def aexport(self, line: str = "") -> None:
        """Export the paper: ``%aexport paper.docx`` / ``--format=latex`` / ``--format=md``."""
        return self._guard(self.aexport, line, self._aexport)

    def _aexport(self, args: Any) -> None:
        session = get_session()
        fmt = args.format or infer_format(args.path)
        written = export_document(session, args.path, fmt)
        print(f"Exported to {written}")
        rel = os.path.relpath(written)
        ipy_display(FileLink(written if rel.startswith("..") else rel))


def load_ipython_extension(ipython: Any) -> None:
    """Entry point for ``%load_ext academicflow``."""
    ipython.register_magics(AcademicMagics)
    print("academicflow loaded: %acite, %%academic, %astats, %acheck, %aabstract, %aexport")


def unload_ipython_extension(ipython: Any) -> None:  # noqa: ARG001
    """Nothing to clean up; the session is kept in memory only."""
