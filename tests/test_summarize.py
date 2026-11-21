import sys
import types
import warnings

import pytest

from academicflow.core import tokenize
from academicflow.summarize import (
    extractive,
    generate_abstract,
    normalize_section_name,
    rank_sentences,
    summarize,
)
from academicflow.summarize.llm import llm_summarize, truncate_words

TEXT = (
    "Transformers are neural networks built on attention. "
    "Attention lets transformers weigh every word in a sentence. "
    "The weather was pleasant on the day of the conference. "
    "Transformers with attention now dominate language modelling. "
    "Many attention-based transformers are trained on large text corpora."
)

PAPER = {
    "Abstract": "OLD ABSTRACT that must be ignored.",
    "1. Introduction": (
        "Reading scientific papers takes a long time. "
        "Automatic summarisation can help researchers read papers faster. "
        "We study extractive summarisation of scientific papers."
    ),
    "2. Materials and Methods": (
        "We implemented TextRank over TF-IDF sentence vectors. "
        "Sentences were ranked with PageRank on a similarity graph."
    ),
    "Results": (
        "TextRank selected the most central sentences of each paper. "
        "Summaries stayed within the word limit in every test."
    ),
    "Conclusion": "Extractive summarisation is a fast, offline baseline for abstracts.",
}


@pytest.fixture(autouse=True)
def _reset_llm_warning():
    extractive._llm_warned = False
    yield
    extractive._llm_warned = False


# ---------- extractive ----------


def test_empty_text_returns_empty_string():
    assert summarize("") == ""
    assert summarize("   \n ") == ""
    assert rank_sentences("") == []


def test_word_limit_is_respected():
    for limit in (5, 12, 20, 40):
        assert len(tokenize(summarize(TEXT, max_words=limit))) <= limit


def test_short_text_is_kept_whole():
    assert summarize("One short sentence.", max_words=50) == "One short sentence."


def test_off_topic_sentence_is_dropped():
    summary = summarize(TEXT, max_words=30)
    assert "weather" not in summary
    assert "attention" in summary.lower()


def test_output_keeps_original_order():
    summary = summarize(TEXT, max_words=40)
    sentences = [TEXT[s:e] for s, e, _ in rank_sentences(TEXT)]
    positions = [TEXT.index(s) for s in sentences if s in summary]
    assert positions == sorted(positions)


def test_summarize_is_deterministic():
    assert summarize(TEXT, max_words=25) == summarize(TEXT, max_words=25)


def test_invalid_arguments():
    with pytest.raises(ValueError):
        summarize(TEXT, method="magic")
    with pytest.raises(ValueError):
        summarize(TEXT, max_words=0)
    with pytest.raises(ValueError):
        generate_abstract(PAPER, method="magic")


# ---------- section names and abstracts ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1. Introduction", "introduction"),
        ("Background", "introduction"),
        ("2. Materials and Methods", "methods"),
        ("III. Methodology", "methods"),
        ("Evaluation", "results"),
        ("5 Discussion", "conclusion"),
        ("Abstract", "abstract"),
        ("Related Work", "related work"),
    ],
)
def test_normalize_section_name(raw, expected):
    assert normalize_section_name(raw) == expected


def test_abstract_ignores_existing_abstract_and_respects_limit():
    abstract = generate_abstract(PAPER, max_words=60)
    assert "OLD ABSTRACT" not in abstract
    assert 0 < len(tokenize(abstract)) <= 60


def test_abstract_follows_section_order():
    abstract = generate_abstract(PAPER, max_words=80)
    assert abstract.index("TextRank") < abstract.index("offline baseline")


def test_abstract_without_standard_sections_summarises_everything():
    sections = {"Part A": TEXT, "Part B": "Another sentence about transformers."}
    assert generate_abstract(sections, max_words=30)


def test_abstract_of_empty_document():
    assert generate_abstract({}) == ""
    assert generate_abstract({"abstract": "only an abstract"}) == ""


# ---------- LLM backend ----------


def _install_fake_openai(monkeypatch, answer="A generated summary.", calls=None):
    class _Completions:
        def create(self, **kwargs):
            if calls is not None:
                calls.append(kwargs)
            message = types.SimpleNamespace(content=answer)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])

    class OpenAI:
        def __init__(self, **kwargs):
            if calls is not None:
                calls.append(kwargs)
            self.chat = types.SimpleNamespace(completions=_Completions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=OpenAI))


def test_llm_falls_back_when_openai_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", None)  # makes "import openai" fail
    with pytest.warns(RuntimeWarning, match="extractive"):
        result = summarize(TEXT, max_words=25, method="llm")
    assert result == summarize(TEXT, max_words=25)


def test_llm_falls_back_without_model(monkeypatch):
    _install_fake_openai(monkeypatch)
    monkeypatch.delenv("ACADEMICFLOW_LLM_MODEL", raising=False)
    with pytest.warns(RuntimeWarning):
        assert summarize(TEXT, max_words=25, method="llm") == summarize(TEXT, max_words=25)


def test_llm_warns_only_once(monkeypatch):
    monkeypatch.setitem(sys.modules, "openai", None)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        summarize(TEXT, method="llm")
        summarize(TEXT, method="llm")
    assert len([w for w in caught if issubclass(w.category, RuntimeWarning)]) == 1


def test_llm_used_when_configured(monkeypatch):
    calls = []
    _install_fake_openai(monkeypatch, calls=calls)
    monkeypatch.setenv("ACADEMICFLOW_LLM_MODEL", "llama3.2")
    monkeypatch.setenv("ACADEMICFLOW_LLM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert summarize(TEXT, method="llm") == "A generated summary."
    client_kwargs, request = calls
    assert client_kwargs["base_url"] == "http://localhost:11434/v1"
    assert request["model"] == "llama3.2"


def test_llm_abstract_prompt(monkeypatch):
    calls = []
    _install_fake_openai(monkeypatch, answer="An abstract.", calls=calls)
    result = generate_abstract(PAPER, max_words=100, method="llm", model="m", api_key="k")
    assert result == "An abstract."
    prompt = calls[1]["messages"][1]["content"]
    assert "abstract" in prompt.lower() and "OLD ABSTRACT" not in prompt


def test_llm_answer_is_truncated(monkeypatch):
    long_answer = "First sentence here. " + "Second sentence is much longer than allowed. " * 5
    _install_fake_openai(monkeypatch, answer=long_answer)
    assert llm_summarize(TEXT, max_words=5, model="m", api_key="k") == "First sentence here."


def test_truncate_words_without_sentence_boundary():
    assert truncate_words("one two three four five six", 3) == "one two three…"
