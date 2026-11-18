from academicflow.cite import Bibliography, check_integrity, render

BIB = """
@article{smith2020,
  author = {Smith, John and Lee, Anna},
  title = {A Study of Things},
  journal = {Journal of Studies},
  year = {2020}
}
"""


def test_bibliography_parses():
    bib = Bibliography.from_string(BIB)
    assert bib.keys() == ["smith2020"]
    assert "smith2020" in bib
    assert bib.get("smith2020")["authors"] == [("John", "Smith"), ("Anna", "Lee")]


def test_render_and_integrity_do_not_crash():
    bib = Bibliography.from_string(BIB)
    text, refs = render("As shown [@smith2020].", bib, "apa")
    assert isinstance(text, str) and isinstance(refs, list)
    assert isinstance(check_integrity(text, bib), list)
