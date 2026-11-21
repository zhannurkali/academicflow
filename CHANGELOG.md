# Changelog

All notable changes to this project are documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-11-21

### Documentation
- Motivation, innovation and example use cases on the docs home page and in the README
  (shown on PyPI).
- New "Use cases" page with four step-by-step examples.
- Full citation guide: syntax, the three styles side by side, `render()` targets and the
  integrity checks.
- Screenshots of the magics and the exported Word document (#16).

### Fixed
- `python -m academicflow.export` failed with a circular import (#16).

## [1.0.0] - 2026-11-21

Every module from the project plan is complete.

### Added
- **Style checker** (`academicflow.style`, #4): informal words, contractions, first person,
  long sentences, repeated words and phrases, hedge words, section-aware rules (abstract
  length, citations in the abstract, tense in methods and results), and cross-section
  checks: terminology consistency (*data set* / *dataset*) and acronym rules.
- **Venue profiles** (#4): APA, IEEE and Nature YAML presets, plus custom profile files.
- **Citations** (#3, #12): reference formatting for conference papers, books and misc
  entries; `find_citations()`; inline citations in APA (author-date), IEEE (numbered) and
  Nature (superscript); integrity checks for missing keys (with "did you mean"), unused
  entries, duplicate DOIs and incomplete entries.
- **Text analysis** (#9, #10, #11, #13): Flesch reading ease and Flesch-Kincaid grade,
  RAKE-style keyword extraction, passive-voice detection, and both shown by `%astats`.
- **Docs**: pages for the core, style, citation, magics and export modules.


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
