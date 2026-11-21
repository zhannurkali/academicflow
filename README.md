# academicflow

[![PyPI](https://img.shields.io/pypi/v/academicflow)](https://pypi.org/project/academicflow/)
[![Python](https://img.shields.io/pypi/pyversions/academicflow)](https://pypi.org/project/academicflow/)
[![Tests](https://github.com/zhannurkali/academicflow/actions/workflows/test.yml/badge.svg)](https://github.com/zhannurkali/academicflow/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://zhannurkali.github.io/academicflow/)

An academic-writing pipeline for Jupyter notebooks: text analysis, section-aware style checks,
terminology consistency, BibTeX citations in APA / IEEE / Nature style, abstract generation,
and one-command export to Word or LaTeX.

> Status: stable (1.0.1).

## Why

Students and researchers analyse data in Jupyter, but write the paper somewhere else:
a grammar checker for each section, a reference manager for citations, Word or LaTeX for
the final format. Problems slip through the gaps: the same term spelled three ways across
sections, acronyms used before they are defined, a typo in a citation key, references
reformatted by hand for a new journal. academicflow brings writing, checking, citing and
exporting into the notebook, next to the analysis.

## What's new compared with existing tools

Libraries such as textstat, proselint, pybtex and nbconvert each handle one text or one
step. academicflow understands the structure of a paper:

- **Checks across sections**: inconsistent terminology (*data set* / *dataset*) and
  acronym problems that a single-text checker cannot see.
- **Section-aware rules**: past tense in Methods, the abstract word limit, no citations in
  the abstract.
- **Venue profiles**: one YAML preset (`apa`, `ieee`, `nature` or your own) sets the
  citation style, word limits and rules together.
- **Live citations with integrity checks**: `[@key]` is formatted as you write; typos get a
  "did you mean" suggestion.
- **One-command export** of only the paper's sections to Word or LaTeX, with formatted
  references.

Everything runs offline: no API key or model download is needed.

## Example use cases

- Check a thesis chapter for terminology, acronym and tense problems before submission.
- Move a paper from an IEEE conference to a Nature journal by changing one flag.
- Keep a five-person group report consistent in terminology and citations.
- Turn an analysis notebook into a Word draft with formatted references.

Step-by-step versions: [Use cases](https://zhannurkali.github.io/academicflow/use-cases/).

## Install

```bash
pip install academicflow
```

## Quick start

```python
%load_ext academicflow
%acite refs.bib
```

```python
%%academic --style=apa --section=introduction
Transformers changed natural language processing [@vaswani2017].
```

```python
%astats              # word count, reading time, readability, keywords, passive voice
%acheck              # style + terminology + citation integrity across all sections
%aabstract           # generate an abstract
%aexport paper.docx  # or paper.tex
```

## Documentation

https://zhannurkali.github.io/academicflow/

## Development

```bash
git clone https://github.com/zhannurkali/academicflow.git
cd academicflow
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && pytest
```

Contributors should read [AGENTS.md](AGENTS.md) for the module ownership, API contract and git workflow.

## License

MIT
