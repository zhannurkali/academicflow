# Changelog

All notable changes to this project are documented here. Versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Project skeleton: package layout, shared types (`Issue`, `TextStats`), stub API for every module.
- `%load_ext academicflow` with `%acite`, `%%academic`, `%astats`, `%acheck`, `%aabstract`, `%aexport`.
- APA, IEEE and Nature venue profiles (initial).
- CI (tests on Python 3.10-3.13), PyPI trusted publishing on tags, docs deployment to GitHub Pages.
- `summarize()` and `generate_abstract()`: TextRank extractive summaries with section-aware abstracts,
  and an optional OpenAI-compatible LLM backend (works with Ollama) that falls back to TextRank.
