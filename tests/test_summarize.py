from academicflow.summarize import generate_abstract, summarize


def test_summarize_respects_word_limit():
    text = "One two three four. Five six seven eight. Nine ten eleven twelve."
    assert len(summarize(text, max_words=8).split()) <= 8


def test_generate_abstract_ignores_abstract_section():
    sections = {"abstract": "OLD ABSTRACT.", "introduction": "New intro sentence."}
    assert "OLD" not in generate_abstract(sections)
