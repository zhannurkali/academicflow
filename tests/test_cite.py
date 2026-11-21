from __future__ import annotations

import pytest

from academicflow.cite.bib import Bibliography, clean_latex
from academicflow.cite.integrity import check_integrity
from academicflow.cite.render import find_citations, render
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


def paper(**kw):
    base = make(
        type="inproceedings",
        title="Neural Citation Parsing",
        year="2021",
        journal="",
        volume="",
        number="",
        pages="45\u201352",
        booktitle="Proceedings of the Writing Tools Workshop",
        publisher="ACL",
        doi="10.1000/abc",
    )
    base.update(kw)
    return base


def book(**kw):
    base = make(
        type="book",
        authors=[("Kim", "Lee")],
        title="Writing Science",
        year="2019",
        journal="",
        volume="",
        number="",
        pages="",
        publisher="Oxford University Press",
        doi="",
    )
    base.update(kw)
    return base


def web(**kw):
    base = make(
        type="misc",
        authors=[],
        title="Citation Style Guide",
        year="2022",
        journal="",
        volume="",
        number="",
        pages="",
        publisher="Example University",
        doi="",
        url="https://example.org/guide",
    )
    base.update(kw)
    return base


def test_apa_inproceedings():
    assert format_reference(paper(), "apa") == (
        "Smith, J. A., & Müller, H. (2021). Neural citation parsing. "
        "In *Proceedings of the Writing Tools Workshop* (pp. 45\u201352). ACL. "
        "https://doi.org/10.1000/abc"
    )


def test_ieee_inproceedings():
    assert format_reference(paper(), "ieee") == (
        'J. A. Smith and H. Müller, "Neural Citation Parsing," '
        "in *Proceedings of the Writing Tools Workshop*, 2021, pp. 45\u201352, "
        "doi: 10.1000/abc."
    )


def test_nature_inproceedings():
    assert format_reference(paper(), "nature") == (
        "Smith, J. A. & Müller, H. Neural citation parsing. "
        "in *Proceedings of the Writing Tools Workshop* 45\u201352 (ACL, 2021)."
    )


def test_conference_is_alias_of_inproceedings():
    assert format_reference(paper(type="conference"), "apa") == format_reference(paper(), "apa")


def test_inproceedings_single_page_and_missing_fields():
    assert "(p. 7)." in format_reference(paper(pages="7"), "apa")
    out = format_reference(paper(booktitle="", pages="", publisher="", doi=""), "apa")
    assert out == "Smith, J. A., & Müller, H. (2021). Neural citation parsing."


def test_apa_book():
    assert format_reference(book(), "apa") == (
        "Lee, K. (2019). *Writing science*. Oxford University Press."
    )


def test_ieee_book():
    assert format_reference(book(), "ieee") == (
        "K. Lee, *Writing Science*. Oxford University Press, 2019."
    )


def test_nature_book():
    assert format_reference(book(), "nature") == (
        "Lee, K. *Writing Science* (Oxford University Press, 2019)."
    )


def test_book_with_doi_and_no_publisher():
    assert format_reference(book(publisher="", doi="10.1/b"), "apa").endswith(
        "*Writing science*. https://doi.org/10.1/b"
    )


def test_apa_misc_without_authors():
    assert format_reference(web(), "apa") == (
        "*Citation style guide*. (2022). Example University. https://example.org/guide"
    )


def test_ieee_misc_online():
    assert format_reference(web(), "ieee") == (
        '"Citation Style Guide," Example University, 2022. [Online]. '
        "Available: https://example.org/guide"
    )


def test_nature_misc():
    assert format_reference(web(), "nature") == (
        "Citation style guide. Example University https://example.org/guide (2022)."
    )


def test_unsupported_type_uses_article_layout():
    thesis = web(type="phdthesis", publisher="MIT", url="")
    assert "MIT" in format_reference(thesis, "ieee")


def lib(*entries):
    return Bibliography({e["key"]: e for e in entries})


def smith(key="smith2020", **kw):
    return make(key=key, **kw)


def lee(key="lee2019", **kw):
    base = {
        "authors": [("Kim", "Lee")],
        "year": "2019",
        "title": "Writing Science",
        "doi": "10.1/b",
    }
    base.update(kw)
    return make(key=key, **base)


def numbered(n):
    return lib(*(make(key=f"k{i}") for i in range(1, n + 1)))


def test_find_citations_offsets():
    text = "See [@smith2020] and [@lee2019; @park2021, p. 3]."
    found = find_citations(text)
    assert [k for k, _, _ in found] == ["smith2020", "lee2019", "park2021"]
    assert all(text[s:e] == k for k, s, e in found)


def test_find_citations_ignores_non_citations():
    assert find_citations("[link](x) [@a](http://x) [plain] [@] [@a;]") == []


def test_render_apa_markdown():
    bib = lib(smith(), lee())
    text = "As shown [@smith2020], and [@lee2019; @smith2020, p. 12]."
    out, refs = render(text, bib, "apa")
    assert out == (
        "As shown (Smith & Müller, 2020), and (Lee, 2019; Smith & Müller, 2020, p. 12)."
    )
    assert refs == [format_reference(lee(), "apa"), format_reference(smith(), "apa")]


def test_render_apa_et_al_for_three_authors():
    park = make(key="park2021", year="2021", authors=[("S", "Park"), ("A", "Kim"), ("B", "Lee")])
    assert render("[@park2021]", lib(park), "apa")[0] == "(Park et al., 2021)"


def test_render_apa_same_author_year_gets_letters():
    first = smith()
    second = make(key="smith2020b", title="Another Study")
    out, refs = render("[@smith2020] [@smith2020b]", lib(first, second), "apa")
    assert out == "(Smith & Müller, 2020b) (Smith & Müller, 2020a)"
    assert refs[0] == format_reference({**second, "year": "2020a"}, "apa")
    assert refs[1] == format_reference({**first, "year": "2020b"}, "apa")


def test_render_apa_latex_escapes_ampersand():
    assert render("[@smith2020]", lib(smith()), "apa", "latex")[0] == r"(Smith \& Müller, 2020)"


def test_render_ieee_numbers_by_first_appearance():
    bib = lib(smith(), lee())
    out, refs = render("A [@smith2020] B [@lee2019] C [@smith2020]", bib, "ieee")
    assert out == "A [1] B [2] C [1]"
    assert refs == [
        f"[1] {format_reference(smith(), 'ieee')}",
        f"[2] {format_reference(lee(), 'ieee')}",
    ]


def test_render_ieee_ranges_pairs_and_locator():
    bib = numbered(4)
    assert render("[@k1; @k2; @k3; @k4]", bib, "ieee")[0] == "[1]-[4]"
    assert render("[@k1; @k2]", bib, "ieee")[0] == "[1], [2]"
    assert render("[@k1; @k2; @k3] [@k4; @k1]", bib, "ieee")[0] == "[1]-[3] [1], [4]"
    assert render("[@k1, p. 12]", bib, "ieee")[0] == "[1, p. 12]"


def test_render_nature_targets():
    bib = numbered(3)
    assert render("Text [@k1; @k2].", bib, "nature")[0] == "Text<sup>1,2</sup>."
    assert render("Text [@k1; @k2].", bib, "nature", "pandoc")[0] == "Text^1,2^."
    latex = render("Text [@k1; @k2].", bib, "nature", "latex")[0]
    assert latex == "Text\\textsuperscript{1,2}."
    assert render("[@k1; @k2; @k3]", bib, "nature")[0] == "<sup>1\u20133</sup>"


def test_render_nature_reference_list_is_numbered():
    bib = lib(smith(), lee())
    _, refs = render("[@lee2019] [@smith2020]", bib, "nature")
    assert refs == [
        f"1. {format_reference(lee(), 'nature')}",
        f"2. {format_reference(smith(), 'nature')}",
    ]


def test_render_unknown_key_left_in_place():
    bib = lib(smith())
    out, refs = render("See [@nope] and [@smith2020].", bib, "apa")
    assert out == "See [@nope?] and (Smith & Müller, 2020)."
    assert refs == [format_reference(smith(), "apa")]
    assert render("[@smith2020; @nope]", bib, "apa")[0] == "(Smith & Müller, 2020) [@nope?]"
    assert render("[@nope]", lib(), "ieee") == ("[@nope?]", [])


def test_render_without_citations_and_bad_arguments():
    assert render("plain text", lib(smith()), "apa") == ("plain text", [])
    assert render("", lib(), "nature") == ("", [])
    with pytest.raises(ValueError, match="Unknown citation style"):
        render("x", lib(), "chicago")
    with pytest.raises(ValueError, match="Unknown render target"):
        render("x", lib(), "apa", "html")


def test_integrity_missing_key_with_suggestion():
    bib = lib(smith(), lee())
    text = "[@smith2020] [@smth2020] [@lee2019]"
    issues = [i for i in check_integrity(text, bib) if i.rule == "cite-missing-key"]
    assert len(issues) == 1
    issue = issues[0]
    assert issue.severity == "error" and issue.suggestion == "smith2020"
    assert text[issue.start : issue.end] == "smth2020"
    assert "Did you mean 'smith2020'?" in issue.message


def test_integrity_missing_key_without_match():
    issues = check_integrity("[@zzzzzz]", lib(smith()))
    missing = [i for i in issues if i.rule == "cite-missing-key"]
    assert missing[0].suggestion is None and "Did you mean" not in missing[0].message


def test_integrity_duplicate_doi_and_title():
    dup_doi = make(key="smith2020dup", title="Something else")
    dup_title = lee(key="lee2019b", doi="10.1/other", title="WRITING science!")
    bib = lib(smith(), lee(), dup_doi, dup_title)
    issues = [i for i in check_integrity("", bib) if i.rule == "cite-duplicate-doi"]
    assert [i.message for i in issues] == [
        "'smith2020dup' has the same DOI as 'smith2020'.",
        "'lee2019b' has the same title as 'lee2019'.",
    ]
    assert all(i.severity == "warning" for i in issues)


def test_integrity_incomplete_entries():
    bad = make(key="bad2018", authors=[], year="", journal="")
    talk = make(key="talk", type="inproceedings", booktitle="")
    issues = [i for i in check_integrity("", lib(bad, talk)) if i.rule == "cite-incomplete"]
    assert issues[0].message == "'bad2018' (article) is missing: authors, year, journal."
    assert issues[1].message == "'talk' (inproceedings) is missing: booktitle."


def test_integrity_unused_entry_and_clean_case():
    bib = lib(smith(), lee())
    unused = [i for i in check_integrity("[@smith2020]", bib) if i.rule == "cite-unused"]
    assert [(i.severity, i.start, i.end) for i in unused] == [("info", 0, 0)]
    assert "lee2019" in unused[0].message
    assert check_integrity("[@smith2020] [@lee2019]", bib) == []
