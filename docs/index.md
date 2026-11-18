# academicflow

**Write, check, cite and export scientific papers without leaving Jupyter.**

```bash
pip install academicflow
```

## Features

- **Text analysis**: word count, reading time, readability grade, keywords, passive voice.
- **Style checker**: informal language, repeated phrases, and section-aware rules such as tense in Methods and abstract length.
- **Terminology consistency**: catches "data set" vs "dataset" and undefined acronyms across the whole paper.
- **Venue profiles**: `apa`, `ieee` and `nature` presets control citation format, word limits and style rules together.
- **Citations**: load a `.bib` file, write `[@key]`, and get APA, IEEE or Nature formatting, plus checks for missing keys and duplicate DOIs.
- **Abstract generator**: extractive by default, with an optional LLM backend.
- **Export**: one command to `.docx` or `.tex`, with references already formatted.

## How it differs from existing tools

| Tool | Does | academicflow adds |
| --- | --- | --- |
| textstat | Readability scores | Section-aware rules, notebook integration |
| proselint | Generic prose linting | Academic and venue-specific rules, cross-section terminology |
| pybtex | BibTeX parsing | Inline citation rendering in notebooks, integrity checks |
| nbconvert | Notebook conversion | Paper-structured export with formatted references |
