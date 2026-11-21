from __future__ import annotations

import pytest

from academicflow.core import analyze, split_sentences, tokenize
from academicflow.core.keywords import extract_keywords
from academicflow.core.passive import detect_passive, passive_ratio
from academicflow.core.readability import basic_counts, count_syllables, readability
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


def test_split_sentences_offsets() -> None:
    text = "One. Two."
    assert split_sentences(text) == [(0, 4), (5, 9)]


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


def test_tokenize_drops_citations() -> None:
    assert tokenize("Water boils [@smith2020].") == ["water", "boils"]


def test_strip_markdown() -> None:
    assert strip_markdown("# Title\n- **bold** item") == "Title\nbold item"
    assert strip_markdown("See [the docs](http://x.org) now") == "See the docs now"
    assert strip_markdown("A [@k] b") == "A [@k] b"
    assert strip_markdown("A [@k] b", remove_citations=True) == "A  b"
    assert strip_markdown("Cost $5 or $10") == "Cost $5 or $10"
    assert strip_markdown("") == ""


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("the", 1),
        ("make", 1),
        ("table", 2),
        ("because", 2),
        ("analysed", 3),
        ("reading", 2),
        ("research", 2),
        ("paper", 2),
        ("samples", 2),
        ("hypothesis", 4),
        ("significant", 4),
        ("analysis", 4),
        ("methodology", 5),
        ("science", 2),
        ("queue", 1),
        ("state-of-the-art", 4),
        ("covid-19", 2),
        ("", 0),
        ("123", 0),
    ],
)
def test_count_syllables(word: str, expected: int) -> None:
    assert count_syllables(word) == expected


def test_readability_known_passage() -> None:
    result = readability("The cat sat on the mat.")
    assert result["flesch_reading_ease"] == pytest.approx(116.145, abs=0.01)
    assert result["flesch_kincaid_grade"] == pytest.approx(-1.45, abs=0.01)


def test_readability_harder_text_scores_lower() -> None:
    easy = readability("The cat sat on the mat. The dog ran to the park.")
    hard = readability(
        "Methodological considerations notwithstanding, interdisciplinary investigations "
        "necessitate comprehensive epistemological frameworks."
    )
    assert hard["flesch_reading_ease"] < easy["flesch_reading_ease"]
    assert hard["flesch_kincaid_grade"] > easy["flesch_kincaid_grade"]


def test_readability_empty() -> None:
    assert readability("") == {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}


def test_basic_counts() -> None:
    counts = basic_counts("The cat sat on the mat. It was happy.")
    assert counts["word_count"] == 9
    assert counts["sentence_count"] == 2
    assert counts["avg_sentence_length"] == pytest.approx(4.5)
    assert counts["reading_time_min"] == pytest.approx(9 / 238)


def test_basic_counts_empty() -> None:
    assert basic_counts("") == {
        "word_count": 0,
        "sentence_count": 0,
        "avg_sentence_length": 0.0,
        "reading_time_min": 0.0,
    }


def test_analyze_basic() -> None:
    stats = analyze("The cat sat on the mat. It was happy.")
    assert isinstance(stats, TextStats)
    assert stats.word_count == 9
    assert stats.sentence_count == 2
    assert stats.reading_time_min == pytest.approx(9 / 238)


def test_analyze_empty_text() -> None:
    stats = analyze("")
    assert stats.word_count == 0
    assert stats.sentence_count == 0
    assert stats.reading_time_min == 0.0
    assert stats.keywords == []
    assert stats.passive_ratio == 0.0


_KW_TEXT = "Deep learning is a method. Deep learning is useful for translation."


def test_extract_keywords_best_phrase() -> None:
    result = extract_keywords(_KW_TEXT, top_n=3)
    assert result[0] == ("deep learning", 1.0)
    assert all(0.0 <= score <= 1.0 for _, score in result)


def test_extract_keywords_deterministic() -> None:
    assert extract_keywords(_KW_TEXT) == extract_keywords(_KW_TEXT)


def test_extract_keywords_top_n() -> None:
    assert len(extract_keywords(_KW_TEXT, top_n=2)) == 2
    assert extract_keywords(_KW_TEXT, top_n=0) == []


def test_extract_keywords_empty_and_stopwords_only() -> None:
    assert extract_keywords("") == []
    assert extract_keywords("The of and.") == []
    assert extract_keywords("3.14 7") == []


@pytest.fixture(autouse=True)
def no_spacy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the heuristic detector so results do not depend on an installed spaCy."""
    monkeypatch.setattr("academicflow.core.passive._load_spacy", lambda: None)


def _passive_phrases(text: str) -> list[str]:
    return [text[i.start : i.end] for i in detect_passive(text)]


def test_detect_passive_true_positives() -> None:
    assert _passive_phrases("The samples were analysed.") == ["were analysed"]
    assert _passive_phrases("It has been shown that this works.") == ["has been shown"]
    assert _passive_phrases("The method will be tested later.") == ["will be tested"]
    assert _passive_phrases("The data were carefully checked.") == ["were carefully checked"]


def test_detect_passive_true_negatives() -> None:
    assert detect_passive("We analysed the samples.") == []
    assert detect_passive("The results are clear and we are here.") == []


def test_detect_passive_issue_fields() -> None:
    issue = detect_passive("The samples were analysed.")[0]
    assert issue.rule == "passive-voice"
    assert issue.severity == "info"
    assert issue.message == 'Passive voice: "were analysed".'
    assert issue.suggestion == "Consider active voice if the agent is important."
    assert (issue.start, issue.end) == (12, 25)


def test_detect_passive_empty() -> None:
    assert detect_passive("") == []
    assert passive_ratio("") == 0.0


def test_passive_ratio() -> None:
    assert passive_ratio("The samples were analysed. We tested them.") == pytest.approx(0.5)
    assert passive_ratio("The data were collected and were analysed.") == pytest.approx(1.0)


def test_analyze_uses_keywords_and_passive() -> None:
    stats = analyze("The samples were analysed. Deep learning is useful. Deep learning is fast.")
    assert stats.keywords[0][0] == "deep learning"
    assert stats.passive_ratio == pytest.approx(1 / 3)
