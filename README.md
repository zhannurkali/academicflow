# academicflow

[![PyPI](https://img.shields.io/pypi/v/academicflow)](https://pypi.org/project/academicflow/)
[![Python](https://img.shields.io/pypi/pyversions/academicflow)](https://pypi.org/project/academicflow/)
[![Tests](https://github.com/zhannurkali/academicflow/actions/workflows/test.yml/badge.svg)](https://github.com/zhannurkali/academicflow/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://zhannurkali.github.io/academicflow/)

An academic-writing pipeline for Jupyter notebooks: text analysis, section-aware style checks,
terminology consistency, BibTeX citations in APA / IEEE / Nature style, abstract generation,
and one-command export to Word or LaTeX.

> Status: stable (1.0.0).

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
