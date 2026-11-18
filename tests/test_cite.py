from __future__ import annotations

import pytest

from academicflow.cite.bib import Bibliography, clean_latex
from academicflow.cite.styles import _initials, _sentence_case, format_reference, to_latex

SAMPLE = r"""
@article{smith2020,
  author  = {Smith, John A. and M{\"u}ller, Hans and Garc{\'\i}a, Ana},
  title   = {Deep {Learning} for \& Text},
  journal = {Journal of {AI} Research},
  year    = {2020},
  volume  = {12},
  number  = {3},
  pages   = {101--110},
  doi     = {https://doi.org/10.1000/xyz123}
}
@book{lee2019,
  author    = {Lee, Kim and others},
  title     = {Writing Science},
  publisher = {Oxford University Press},
  year      = {2019}
}
"""


def test_clean_latex_accents_and_escapes():
    assert clean_latex(r"M{\"u}ller") == "Müller"
    assert clean_latex(r"Garc{\'\i}a") == "García"
    assert clean_latex(r"{\c{c}}a va \& co") == "ça va & co"
    assert clean_latex("A  {Protected}\n title") == "A Protected title"


def test_from_string_normalises_entry():
    bib = Bibliography.from_string(SAMPLE)
    e = bib.get("smith2020")
    assert e["type"] == "article"
    assert e["authors"][0] == ("John A.", "Smith")
    assert e["authors"][1] == ("Hans", "Müller")
    assert e["title"] == "Deep Learning for & Text"
    assert e["pages"] == "101\u2013110"
    assert e["doi"] == "10.1000/xyz123"


def test_and_others_sets_et_al():
    e = Bibliography.from_string(SAMPLE).get("lee2019")
    assert e["et_al"] is True
    assert len(e["authors"]) == 1


def test_keys_contains_len():
    bib = Bibliography.from_string(SAMPLE)
    assert bib.keys() == ["smith2020", "lee2019"]
    assert "smith2020" in bib and "nope" not in bib
    assert len(bib) == 2


def test_unknown_key_message():
    with pytest.raises(KeyError, match="Unknown citation key: 'nope'"):
        Bibliography.from_string(SAMPLE).get("nope")


def test_malformed_bib_raises_value_error():
    with pytest.raises(ValueError, match="Invalid BibTeX"):
        Bibliography.from_string("@article{broken, title = {unclosed")


def test_from_file(tmp_path):
    p = tmp_path / "refs.bib"
    p.write_text(SAMPLE, encoding="utf-8")
    assert len(Bibliography.from_file(p)) == 2
    with pytest.raises(FileNotFoundError):
        Bibliography.from_file(tmp_path / "missing.bib")


def make(**kw):
    base = {
        "key": "smith2020",
        "type": "article",
        "authors": [("John A.", "Smith"), ("Hans", "Müller")],
        "et_al": False,
        "title": "Deep Learning for Text",
        "year": "2020",
        "journal": "Journal of AI Research",
        "booktitle": "",
        "volume": "12",
        "number": "3",
        "pages": "101\u2013110",
        "publisher": "",
        "doi": "10.1000/xyz123",
        "url": "",
    }
    base.update(kw)
    return base


def people(n):
    return [(f"A{i}", f"Last{i}") for i in range(1, n + 1)]


def test_initials():
    assert _initials("John Alan") == "J. A."
    assert _initials("Jean-Paul") == "J.-P."
    assert _initials("J.A.") == "J. A."
    assert _initials("") == ""


def test_sentence_case():
    assert _sentence_case("Deep Learning for Text") == "Deep learning for text"
    title = "Attention: A Survey of BERT Models"
    assert _sentence_case(title) == "Attention: A survey of BERT models"
    assert _sentence_case("Already sentence case here") == "Already sentence case here"


def test_apa_article():
    assert format_reference(make(), "apa") == (
        "Smith, J. A., & Müller, H. (2020). Deep learning for text. "
        "*Journal of AI Research*, *12*(3), 101\u2013110. https://doi.org/10.1000/xyz123"
    )


def test_apa_one_and_three_authors():
    one = format_reference(make(authors=[("John A.", "Smith")], doi=""), "apa")
    assert one.startswith("Smith, J. A. (2020). ")
    three = format_reference(make(authors=people(3)), "apa")
    assert three.startswith("Last1, A. Last2, A. ") is False
    assert three.startswith("Last1, A., Last2, A., & Last3, A. (2020). ")


def test_apa_missing_year_and_url_fallback():
    out = format_reference(make(year="", doi="", url="https://example.org/x"), "apa")
    assert "(n.d.)" in out and out.endswith("https://example.org/x")


def test_ieee_article():
    assert format_reference(make(), "ieee") == (
        'J. A. Smith and H. Müller, "Deep Learning for Text," *Journal of AI Research*, '
        "vol. 12, no. 3, pp. 101\u2013110, 2020, doi: 10.1000/xyz123."
    )


def test_ieee_et_al_after_six_authors():
    assert format_reference(make(authors=people(6)), "ieee").startswith(
        "A. Last1, A. Last2, A. Last3, A. Last4, A. Last5, and A. Last6, "
    )
    assert format_reference(make(authors=people(7)), "ieee").startswith('A. Last1 et al., "')


def test_nature_article():
    assert format_reference(make(), "nature") == (
        "Smith, J. A. & Müller, H. Deep learning for text. "
        "*Journal of AI Research* **12**, 101\u2013110 (2020)."
    )


def test_nature_et_al_after_five_authors():
    assert format_reference(make(authors=people(5)), "nature").startswith(
        "Last1, A., Last2, A., Last3, A., Last4, A. & Last5, A. "
    )
    assert format_reference(make(authors=people(6)), "nature").startswith("Last1, A. et al. ")


def test_unknown_style_raises():
    with pytest.raises(ValueError, match="Unknown citation style"):
        format_reference(make(), "chicago")


def test_non_article_does_not_crash():
    book = make(type="book", journal="", publisher="Oxford University Press", pages="", doi="")
    assert "Oxford University Press" in format_reference(book, "apa")


def test_to_latex():
    md = "*Journal of AI Research*, *12*(3). https://doi.org/10.1/x_1 & **bold** 50%"
    assert to_latex(md) == (
        "\\textit{Journal of AI Research}, \\textit{12}(3). https://doi.org/10.1/x\\_1 "
        "\\& \\textbf{bold} 50\\%"
    )
