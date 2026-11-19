"""Tests for session state, HTML helpers and the magics (other modules are faked)."""
from __future__ import annotations

import importlib
import re

import pytest

from academicflow import cite, core, style
from academicflow.magics import display as ui
from academicflow.magics import magics as mg
from academicflow.magics.session import (
    Session,
    get_session,
    join_with_offsets,
    locate_issues,
    reset_session,
)
from academicflow.types import Issue, TextStats

summarize = importlib.import_module("academicflow.summarize")
_CITE = re.compile(r"\[@([^\]]+)\]")


class FakeBib:
    def __init__(self, keys):
        self._keys = list(keys)

    @classmethod
    def from_file(cls, path):
        return cls(["smith2020", "lee2019"])

    def keys(self):
        return list(self._keys)


def fake_find(text):
    return [(m.group(1), m.start(), m.end()) for m in _CITE.finditer(text)]


def fake_render(text, bib, style_name, target="markdown"):
    order = []

    def sub(match):
        key = match.group(1)
        if key not in order:
            order.append(key)
        return f"(cited {key})"

    return _CITE.sub(sub, text), [f"Reference {k}" for k in order]


def fake_stats():
    return TextStats(
        word_count=1234, sentence_count=60, reading_time_min=5.2, flesch_reading_ease=41.0,
        flesch_kincaid_grade=12.3, avg_sentence_length=20.5, keywords=[("deep learning", 1.0)],
        passive_ratio=0.25,
    )


@pytest.fixture(autouse=True)
def env(monkeypatch):
    reset_session()
    shown = []
    monkeypatch.setattr(mg, "ipy_display", shown.append)
    monkeypatch.setattr(cite, "Bibliography", FakeBib)
    monkeypatch.setattr(cite, "render", fake_render)
    monkeypatch.setattr(cite, "find_citations", fake_find)
    monkeypatch.setattr(cite, "check_integrity", lambda text, bib: [])
    monkeypatch.setattr(style, "load_profile", lambda name: {})
    monkeypatch.setattr(style, "check", lambda text, profile="apa", section=None: [])
    monkeypatch.setattr(style, "check_document", lambda sections, profile="apa": [])
    yield shown
    reset_session()


def out(shown):
    return "\n".join(str(getattr(o, "data", o)) for o in shown)


@pytest.fixture
def magics():
    return mg.AcademicMagics(None)


# ---------------------------------------------------------------- session
def test_session_replace_keeps_order():
    s = Session()
    s.set_section("a", "1")
    s.set_section("b", "2")
    s.set_section("a", "new")
    assert list(s.sections) == ["a", "b"]
    assert s.sections["a"] == "new"


def test_auto_section_name_reuses_identical_text():
    s = Session()
    first = s.auto_section_name("hello")
    s.set_section(first, "hello")
    assert first == "section-1"
    assert s.auto_section_name("hello") == "section-1"
    assert s.auto_section_name("other") == "section-2"


def test_singleton_and_reset():
    get_session().title = "T"
    assert get_session().title == "T"
    reset_session()
    assert get_session().title is None and get_session().profile == "apa"


def test_body_sections_and_full_text():
    s = Session()
    s.set_section("abstract", "A")
    s.set_section("intro", "B")
    assert list(s.body_sections()) == ["intro"]
    assert s.full_text(include_abstract=False) == "B"
    assert s.full_text() == "A\n\nB"
    assert not s.is_empty()


def test_join_with_offsets_and_locate_issues():
    text, spans = join_with_offsets({"a": "hello", "b": "world"})
    assert text == "hello\n\nworld"
    assert spans == [("a", 0, 5), ("b", 7, 12)]
    issue = Issue(rule="r", message="m", start=7, end=10)
    unranged = Issue(rule="cite-unused", message="m")
    result = locate_issues([issue, unranged], spans)
    assert (result[0].section, result[0].start, result[0].end) == ("b", 0, 3)
    assert result[1].section is None


# ---------------------------------------------------------------- display
def test_display_escapes_user_text():
    issue = Issue(rule="x", message="<script>alert(1)</script>", start=0, end=3)
    html_out = ui.issue_panel([issue], "<b>abc</b>")
    assert "<script>" not in html_out and "&lt;script&gt;" in html_out
    assert "&lt;b&gt;" in html_out


def test_issue_panel_empty_and_counts():
    assert "no issues" in ui.issue_panel([], title="Style").lower()
    issues = [Issue("a", "m", severity="error"), Issue("b", "m", severity="info")]
    assert ui.severity_counts(issues) == {"error": 1, "warning": 0, "info": 1}


def test_stats_table_and_highlight():
    assert "1,234" in ui.stats_table(fake_stats())
    marked = ui.highlight_passive("It was done.", [Issue("p", "m", start=3, end=11)])
    assert "<mark" in marked and "was done" in marked


# ---------------------------------------------------------------- magics
def test_acite_loads_bibliography(magics, capsys):
    magics.acite("refs.bib")
    assert get_session().bib is not None and get_session().bib_path == "refs.bib"
    assert "Loaded 2 references from refs.bib" in capsys.readouterr().out


def test_academic_stores_renders_and_checks(magics, env, monkeypatch):
    seen = {}

    def fake_check(text, profile="apa", section=None):
        seen.update(text=text, profile=profile, section=section)
        return [Issue("informal-word", "Avoid 'big'", start=0, end=3, suggestion="large")]

    monkeypatch.setattr(style, "check", fake_check)
    magics.acite("refs.bib")
    magics.academic("--style=ieee --section=introduction", "Big results [@smith2020].")
    session = get_session()
    assert session.profile == "ieee"
    assert session.sections["introduction"] == "Big results [@smith2020]."
    assert seen["section"] == "introduction" and seen["profile"] == "ieee"
    shown = out(env)
    assert "(cited smith2020)" in shown and "Reference smith2020" in shown
    assert "informal-word" in shown


def test_academic_rerun_replaces_and_no_check(magics, env, monkeypatch):
    monkeypatch.setattr(style, "check", lambda *a, **k: pytest.fail("check must not run"))
    magics.academic("--section=methods --no-check", "First version.")
    magics.academic("--section=results --no-check", "Results.")
    magics.academic("--section=methods --no-check", "Second version.")
    assert list(get_session().sections) == ["methods", "results"]
    assert get_session().sections["methods"] == "Second version."


def test_academic_default_names_and_hint_without_bib(magics, env):
    magics.academic("--no-check", "See [@smith2020].")
    assert "section-1" in get_session().sections
    assert "%acite" in out(env)


def test_academic_title_cell(magics, env):
    magics.academic("--title", "# My Paper\nAda Lovelace\nAlan Turing")
    session = get_session()
    assert session.title == "My Paper"
    assert session.authors == ["Ada Lovelace", "Alan Turing"]
    assert session.sections == {}


def test_unknown_profile_shows_message_not_traceback(magics, env, monkeypatch):
    def bad(name):
        raise ValueError("Unknown profile 'zzz'")

    monkeypatch.setattr(style, "load_profile", bad)
    magics.academic("--style=zzz", "text")
    assert "Unknown profile" in out(env)
    assert get_session().sections == {}


def test_astats_section_and_whole(magics, env, monkeypatch):
    monkeypatch.setattr(core, "analyze", lambda text: fake_stats())
    monkeypatch.setattr(
        core, "detect_passive", lambda text: [Issue("passive-voice", "m", "info", 3, 11)]
    )
    magics.academic("--section=intro --no-check", "It was done.")
    magics.astats("intro")
    shown = out(env)
    assert "Words" in shown and "deep learning" in shown and "<mark" in shown
    env.clear()
    magics.astats("")
    assert "whole document" in out(env)


def test_astats_unknown_section_message_and_debug(magics, env):
    magics.astats("nope")
    assert "Unknown section" in out(env) and "nope" in out(env)
    with pytest.raises(KeyError):
        magics.astats("nope --debug")


def test_acheck_groups_by_section_and_integrity(magics, env, monkeypatch):
    magics.academic("--section=intro --no-check", "Intro text.")
    magics.academic("--section=methods --no-check", "We cite [@oops].")
    monkeypatch.setattr(
        style, "check_document",
        lambda sections, profile="apa": [
            Issue("informal-word", "m", "warning", 0, 5, section="intro")
        ],
    )
    text, _ = join_with_offsets(get_session().sections)
    start = text.index("[@oops]")
    monkeypatch.setattr(
        cite, "check_integrity",
        lambda t, bib: [
            Issue("cite-missing-key", "missing", "error", start, start + 7),
            Issue("cite-unused", "unused", "info"),
        ],
    )
    magics.acite("refs.bib")
    magics.acheck("")
    shown = out(env)
    assert "3 issues" in shown
    assert "informal-word" in shown and "cite-missing-key" in shown
    assert "Document / bibliography" in shown and "methods" in shown


def test_acheck_clean_and_empty(magics, env):
    magics.acheck("")
    assert "No sections yet" in out(env)
    env.clear()
    magics.academic("--section=intro --no-check", "Fine.")
    magics.acheck("")
    assert "No issues found" in out(env)


def test_aabstract_stores_abstract(magics, env, monkeypatch):
    captured = {}

    def fake_abstract(sections, max_words=200, method="extractive"):
        captured.update(sections=dict(sections), words=max_words, method=method)
        return "A short abstract."

    monkeypatch.setattr(summarize, "generate_abstract", fake_abstract)
    magics.academic("--section=abstract --no-check", "Old abstract")
    magics.academic("--section=intro --no-check", "Intro.")
    magics.aabstract("--words=50 --llm")
    session = get_session()
    assert session.abstract == "A short abstract."
    assert session.sections["abstract"] == "A short abstract."
    assert "abstract" not in captured["sections"]
    assert captured["words"] == 50 and captured["method"] == "llm"
    assert "A short abstract." in out(env)


def test_aexport_infers_format_and_links(magics, env, monkeypatch, tmp_path):
    calls = []

    def fake_export(session, path, fmt="docx"):
        calls.append((path, fmt))
        target = tmp_path / "paper.tex"
        target.write_text("x")
        return str(target)

    monkeypatch.setattr(mg, "export_document", fake_export)
    magics.aexport("paper.tex")
    assert calls == [("paper.tex", "latex")]
    magics.aexport("paper.tex --format=md")
    assert calls[-1] == ("paper.tex", "md")
    assert len(env) == 2  # one FileLink per call


def test_load_extension_registers_magics():
    class Shell:
        registered = None

        def register_magics(self, cls):
            self.registered = cls

    shell = Shell()
    mg.load_ipython_extension(shell)
    assert shell.registered is mg.AcademicMagics
