# Changelog

All notable changes to this project are documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.0] - 2026-11-20

First public release.

### Added
- **Text analysis** (`academicflow.core`): sentence splitter that handles abbreviations,
  decimals and citations; tokenizer; markdown stripper.
- **Citations** (`academicflow.cite`): BibTeX parsing with LaTeX accent clean-up and clear
  error messages; APA 7, IEEE and Nature reference formatting for journal articles.
- **Abstract generator** (`academicflow.summarize`): TextRank extractive summaries,
  section-aware abstracts, and an optional OpenAI-compatible LLM backend (works with
  Ollama) that falls back to TextRank.
- **Jupyter magics** (`academicflow.magics`): `%load_ext academicflow`, `%acite`,
  `%%academic`, `%astats`, `%acheck`, `%aabstract`, `%aexport`, with a notebook session.
- **Export** (`academicflow.export`): Word (.docx), LaTeX (.tex) and Markdown export,
  `export_notebook()` and a command-line entry point.
- **Examples**: quickstart notebook, full paper workflow notebook, and a sample draft with
  deliberate mistakes and an answer key.
- **Docs**: MkDocs site with one page per module.
- **Infrastructure**: CI on Python 3.10-3.13, PyPI trusted publishing on tags, docs
  deployment to GitHub Pages.

### Changed
- Python 3.10 or newer is required (3.9 reached end of life).

### Coming next
- Style checker with section-aware rules, terminology consistency and venue profiles.
- Reference formatting for conference papers, books and other entry types.
- Citation integrity checks and inline citation rendering.
