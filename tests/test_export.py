from academicflow.export import export_document
from academicflow.magics import reset_session


def test_export_markdown(tmp_path):
    s = reset_session()
    s.title = "My Paper"
    s.set_section("introduction", "Intro text.")
    out = export_document(s, str(tmp_path / "paper.md"))
    content = open(out, encoding="utf-8").read()
    assert "# My Paper" in content
    assert "## Introduction" in content
