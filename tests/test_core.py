from __future__ import annotations

from academicflow.core import analyze, split_sentences, tokenize
from academicflow.core.text import strip_markdown
from academicflow.types import TextStats


def _sents(text: str) -> list[str]:
    return [text[s:e] for s, e in split_sentences(text)]


def test_split_basic() -> None:
    assert _sents("This is one. This is two! Is this three? Yes.") == [
        "This is one.",
        "This is two!",
        "Is this three?",
        "Yes.",
    ]


def test_split_abbreviations() -> None:
    text = (
        "We used several tools, e.g. Python and Julia. Results were good (see Fig. 3). "
        "Smith et al. showed this. Dr. Lee agreed."
    )
    sents = _sents(text)
    assert len(sents) == 4
    assert sents[2] == "Smith et al. showed this."
    assert sents[3] == "Dr. Lee agreed."


def test_split_decimals() -> None:
    assert _sents("The value was 3.14 for all runs. The p-value was 0.05.") == [
        "The value was 3.14 for all runs.",
        "The p-value was 0.05.",
    ]


def test_split_not_inside_citations() -> None:
    text = "See [@smith2020]. Another one [@lee2021, p. 4] follows. Done."
    assert _sents(text) == [
        "See [@smith2020].",
        "Another one [@lee2021, p. 4] follows.",
        "Done.",
    ]


def test_split_headings_and_paragraphs() -> None:
    text = "# Title\nFirst sentence. Second one.\n\nNew paragraph without period"
    assert _sents(text) == [
        "# Title",
        "First sentence.",
        "Second one.",
        "New paragraph without period",
    ]


def test_split_empty() -> None:
    assert split_sentences("") == []
    assert split_sentences("  \n ") == []


def test_tokenize_hyphen_digits() -> None:
    assert tokenize("State-of-the-art models improved COVID-19 detection.") == [
        "state-of-the-art",
        "models",
        "improved",
        "covid-19",
        "detection",
    ]


def test_tokenize_drops_citations_and_markdown() -> None:
    assert tokenize("Results hold [@smith2020; @lee2021] here.") == ["results", "hold", "here"]
    assert tokenize("## Heading\n**Bold** and *italic* with `code` and $x^2$.") == [
        "heading",
        "bold",
        "and",
        "italic",
        "with",
        "and",
    ]


def test_tokenize_decimal_and_empty() -> None:
    assert tokenize("pH 7.4") == ["ph", "7.4"]
    assert tokenize("") == []


def test_strip_markdown() -> None:
    assert strip_markdown("# Title\n- **bold** item") == "Title\nbold item"
    assert strip_markdown("See [the docs](http://x.org) now") == "See the docs now"
    assert strip_markdown("A [@k] b") == "A [@k] b"
    assert strip_markdown("A [@k] b", remove_citations=True) == "A  b"
    assert strip_markdown("Cost $5 or $10") == "Cost $5 or $10"
    assert strip_markdown("") == ""


def test_split_sentences_offsets():
    text = "First sentence. Second one!"
    assert [text[s:e] for s, e in split_sentences(text)] == ["First sentence.", "Second one!"]


def test_tokenize_drops_citations():
    assert tokenize("Results improved [@smith2020].") == ["results", "improved"]


def test_analyze_empty_text():
    stats = analyze("")
    assert isinstance(stats, TextStats)
    assert stats.word_count == 0
