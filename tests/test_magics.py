from IPython.core.interactiveshell import InteractiveShell

from academicflow.magics import get_session, reset_session


def test_session_replaces_section_in_place():
    s = reset_session()
    s.set_section("intro", "a")
    s.set_section("methods", "b")
    s.set_section("intro", "c")
    assert list(s.sections) == ["intro", "methods"]
    assert s.sections["intro"] == "c"


def test_load_ext_and_academic_cell_magic():
    reset_session()
    ip = InteractiveShell.instance()
    ip.extension_manager.load_extension("academicflow")
    ip.run_cell_magic("academic", "--style=ieee --section=introduction", "Hello world.")
    session = get_session()
    assert session.profile == "ieee"
    assert session.sections["introduction"] == "Hello world."
