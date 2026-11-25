# academicflow

**Write, check, cite and export scientific papers without leaving Jupyter.**

```bash
pip install academicflow
```

```python
%load_ext academicflow
%acite refs.bib
```

## Demo

<video src="assets/academicflow_30s.mp4" controls muted playsinline width="100%"></video>

A longer [60-second version](assets/academicflow_60s.mp4) is also available.

## Motivation

Many students and researchers already do their analysis in Jupyter notebooks, but writing
the paper still happens elsewhere. A typical workflow uses four tools: the notebook for
results, a grammar checker for each section, a reference manager for citations, and Word
or LaTeX for the final format. Text is copied between them by hand, and the common
problems of academic writing slip through:

- the same term written three ways across sections (*data set*, *dataset*, *data-set*)
- acronyms used before they are defined, or defined twice
- present tense in the Methods section, or an abstract over the journal's word limit
- a typo in a citation key that only shows up as "[?]" in the final PDF
- references reformatted by hand when the paper moves from one journal to another

academicflow brings writing, checking, citing and exporting into the notebook, so the
paper lives next to the analysis it describes.

## What it does

- **Text analysis**: word count, reading time, Flesch reading ease and grade level,
  keywords and passive voice.
- **Style checker**: informal words, contractions, long sentences, repeated words and
  phrases, and rules that depend on the section, such as tense in Methods and the
  abstract word limit.
- **Terminology and acronyms across the whole paper**: inconsistent spellings of a term
  and acronym problems, found by comparing all sections.
- **Venue profiles**: `apa`, `ieee` and `nature` presets set the citation style, word
  limits and style rules together. Custom profiles are plain YAML files.
- **Citations**: write `[@key]`, load a `.bib` file, and get APA, IEEE or Nature
  formatting, plus checks for missing keys, unused and duplicate entries.
- **Abstract generator**: TextRank picks the most central sentences of each section;
  an optional LLM backend (OpenAI or a local Ollama model) can write one instead.
- **Export**: one command to Word (`.docx`) or LaTeX (`.tex`), with citations and the
  reference list already formatted.

Everything runs offline after `pip install`. No API key and no model download is needed.

## Innovation

Each part has a library already. What they don't do is understand the structure of a
paper: which section a sentence is in, whether a term is spelled the same way in every
section, or what a particular journal expects.

| Existing tool | What it does | What academicflow adds |
| --- | --- | --- |
| textstat | readability scores for one text | statistics per section and for the whole paper, inside the notebook |
| proselint, LanguageTool | generic style and grammar checks on one text | academic rules that depend on the section and the venue, and checks **across** sections (terminology, acronyms) |
| pybtex, citeproc | parse BibTeX, format references | `[@key]` citations rendered live in notebook cells, and integrity checks (typos with "did you mean", unused and duplicate entries) |
| nbconvert, pandoc | convert a whole notebook | export only the paper's sections, in order, with an abstract and a formatted reference list |

The reusable pieces are the **venue profiles** (one YAML file sets citation style, word
limits and style rules) and the **document-level checks** that look at all sections
together.

## Example use cases

See [Use cases](use-cases.md) for step-by-step examples:

1. **Checking a thesis chapter before submission**: find terminology, acronym and tense
   problems across all sections at once.
2. **Moving a paper to another journal**: switch from IEEE to Nature with one flag.
3. **A group project report**: keep five authors' terminology and citations consistent.
4. **From analysis notebook to Word draft**: write the paper next to the code and export
   it with formatted references.

## Where to go next

- [Getting started](getting-started.md): install and a five-minute tour
- Module guides: [text analysis](core.md), [style checker](style.md),
  [citations](cite.md), [abstract generator](summarize.md), [Jupyter magics](magics.md),
  [export](export.md)
- Example notebooks: [`examples/`](https://github.com/zhannurkali/academicflow/tree/main/examples)
  in the repository
