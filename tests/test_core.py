from academicflow.core import analyze, split_sentences, tokenize
from academicflow.types import TextStats


def test_split_sentences_offsets():
    text = "First sentence. Second one!"
    assert [text[s:e] for s, e in split_sentences(text)] == ["First sentence.", "Second one!"]


def test_tokenize_drops_citations():
    assert tokenize("Results improved [@smith2020].") == ["results", "improved"]


def test_analyze_empty_text():
    stats = analyze("")
    assert isinstance(stats, TextStats)
    assert stats.word_count == 0
