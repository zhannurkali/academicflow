# Abstract generator (`academicflow.summarize`)

Generate a summary of any text, or a full abstract from a paper's sections. The default
method is **extractive TextRank**: it runs offline, needs no API key and gives the same
result every time. An optional **LLM backend** writes new sentences instead, and falls
back to TextRank automatically if anything goes wrong.

## In a notebook

```python
%load_ext academicflow

%%academic --section=introduction
...

%aabstract              # TextRank abstract, 200 words
%aabstract --words=150  # shorter
%aabstract --llm        # LLM abstract (see configuration below)
```

## From Python

```python
from academicflow.summarize import summarize, generate_abstract

summarize(long_text, max_words=100)

generate_abstract({
    "1. Introduction": "...",
    "2. Materials and Methods": "...",
    "Results": "...",
    "Conclusion": "...",
}, max_words=200)
```

## How the extractive method works

1. The text is split into sentences, and each sentence becomes a TF-IDF vector (stopwords removed).
2. Sentences are linked by cosine similarity, and **PageRank** scores how central each sentence is.
3. Sentences in the first or last 20% of the text get a small boost (×1.15), as do sentences
   containing the text's top keywords (×1.10).
4. The best sentences that fit in `max_words` are returned **in their original order**.

`generate_abstract` is section-aware. It takes up to two of the best sentences from the
introduction, methods, results and conclusion, in that order, and shares the word budget
between the sections that exist. Section names are normalised:

| You write | Treated as |
| --- | --- |
| Introduction, Background, Motivation | introduction |
| Methods, Methodology, Materials and Methods, Approach, Experiments | methods |
| Results, Evaluation, Findings | results |
| Conclusion, Discussion, Summary, Future work | conclusion |

Numbering such as `2.` or `III.` is ignored, and any existing `Abstract` section is skipped.
If none of the four standard sections exist, the whole text is summarised.

## LLM backend (optional)

```bash
pip install "academicflow[llm]"
```

Any OpenAI-compatible API works. Configure it with environment variables or with
arguments (`model=`, `base_url=`, `api_key=`):

| Variable | Meaning | Example |
| --- | --- | --- |
| `ACADEMICFLOW_LLM_MODEL` | Model name (required) | `llama3.2` |
| `ACADEMICFLOW_LLM_BASE_URL` | API URL; leave unset for OpenAI | `http://localhost:11434/v1` |
| `OPENAI_API_KEY` | API key; not needed for local servers | |

**Local and free, with Ollama:**

```bash
ollama pull llama3.2
export ACADEMICFLOW_LLM_MODEL=llama3.2
export ACADEMICFLOW_LLM_BASE_URL=http://localhost:11434/v1
```

```python
summarize(text, method="llm")
generate_abstract(sections, method="llm")
```

The model is told to use only facts from the text and never to invent results or
citations. Answers longer than `max_words` are cut at a sentence boundary.

If the `openai` package, the model name or the key is missing, or the request fails, you
get one warning and the TextRank result instead, so a demo never breaks.

## Limitations

- Extractive summaries reuse the author's sentences, so they can read less smoothly than
  a hand-written abstract.
- Sentence splitting quality depends on `academicflow.core.split_sentences`.
- LLM output should always be checked by the authors before submission.
