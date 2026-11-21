# Text analysis (`academicflow.core`)

The core module turns raw text (plain or Markdown) into numbers and highlights: sentences,
tokens, readability, keywords and passive voice. It needs no internet, no API key and no
downloaded data.

```python
from academicflow.core import analyze, detect_passive
```

## Functions

| Function | What it does |
|---|---|
| `split_sentences(text)` | Returns `(start, end)` character offsets of each sentence. |
| `tokenize(text)` | Returns lowercase word tokens. |
| `strip_markdown(text)` | Removes Markdown, code and LaTeX syntax. |
| `count_syllables(word)` | Estimates syllables in one word. |
| `readability(text)` | Flesch Reading Ease and Flesch-Kincaid Grade. |
| `basic_counts(text)` | Word count, sentence count, average sentence length, reading time. |
| `extract_keywords(text, top_n=10)` | RAKE-style keyword phrases, scores 0-1. |
| `detect_passive(text)` | Passive-voice constructions as `Issue` objects. |
| `passive_ratio(text)` | Share of sentences that contain a passive construction. |
| `analyze(text)` | Everything above in one `TextStats`. |

## Sentences and tokens

`split_sentences` does not split after `e.g.`, `i.e.`, `et al.`, `Fig.`, `Eq.`, `Dr.`, `vs.`,
inside decimals such as `3.14`, or inside `[@key]` citations. Headings and blank lines
always end a sentence.

```python
>>> t = "We did this, e.g. twice. It worked."
>>> [t[s:e] for s, e in split_sentences(t)]
['We did this, e.g. twice.', 'It worked.']
>>> tokenize("COVID-19 results [@smith2020] improved.")
['covid-19', 'results', 'improved']
```

Hyphenated words and words with digits stay whole. Citations, Markdown syntax, inline code
and `$...$` math are ignored when counting.

## Readability

```python
>>> readability("The cat sat on the mat.")["flesch_kincaid_grade"]
-1.45
```

Both formulas are the standard Flesch formulas. Syllables are counted with a heuristic
(vowel groups, silent final e, `-le` endings, small exceptions table).
Reading time uses 238 words per minute.

## Keywords

Keywords are scored with RAKE: the text is split into phrases (1-3 words) at stopwords
and punctuation, and each phrase is scored from its words. Scores are normalised so the
best phrase is 1.0. The result is deterministic.

```python
>>> extract_keywords("Deep learning is a method. Deep learning is useful.", 1)
[('deep learning', 1.0)]
```

## Passive voice

A form of "to be" (optionally after has/have/will/can..., optionally followed by an
adverb) plus a past participle (regular `-ed` or a bundled list of irregular participles).
If spaCy and `en_core_web_sm` are installed, dependency labels are used instead. This is
detected automatically and falls back silently.

```python
>>> issue = detect_passive("The samples were analysed.")[0]
>>> issue.message
'Passive voice: "were analysed".'
>>> (issue.start, issue.end)
(12, 25)
```

`start` and `end` are offsets in the text you passed in, so they can be used for
highlighting.

## Full example

```python
>>> t = ("Transformers changed NLP [@vaswani2017]. The models were trained on large corpora. "
...      "It has been shown that attention improves translation quality. "
...      "We evaluated the results on three benchmarks.")
>>> analyze(t)
TextStats(word_count=26, sentence_count=4, reading_time_min=0.1092436974789916,
flesch_reading_ease=60.32, flesch_kincaid_grade=6.46, avg_sentence_length=6.5,
keywords=[('attention improves translation', 1.0), ('transformers changed nlp', 1.0),
('large corpora', 0.4444), ('three benchmarks', 0.4444), ('evaluated', 0.1111),
('models', 0.1111), ('quality', 0.1111), ('trained', 0.1111)], passive_ratio=0.5)
```

## Empty input

Every function accepts an empty string and returns zeros or an empty list.

## Known limitations

- **Passive voice:** adjectival participles ("is interested", "was located") are flagged as
  passive. Participles shorter than 5 letters ending in `-ed` are only found if they are
  in the irregular list. Passive detection with spaCy is more accurate but optional.
- **Keywords:** there is no part-of-speech tagging, so verbs can appear inside key
  phrases ("improves translation"). Single words that occur once score low.
- **Long phrases:** phrases longer than 3 words are cut into chunks, so a term like
  "optional large language model" can appear as "optional large language".
- **Sentences:** a single capital letter followed by a dot is treated as an initial
  (`J. Smith`), so `Plan B. We ...` is not split.
- **Headings:** Markdown heading lines count as one sentence each.
- **Syllables:** a heuristic, not a dictionary. Rare words can be off by one, which moves
  the readability scores slightly.
- **English only.**