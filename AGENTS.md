# PROJECT CONTEXT: academicflow

You are helping one member of a 5-person university team build "academicflow", a Python package published on PyPI. It is an academic-writing pipeline that runs inside Jupyter notebooks: text analysis, a style checker, a citation manager, an abstract generator, Jupyter magics, and export to LaTeX/Word.

Repo: https://github.com/zhannurkali/academicflow (public, MIT license)
PyPI name: academicflow
Deadline: 4 days total. Day 4 includes a live demo on JupyterHub where we run `pip install academicflow` in a fresh environment and walk through a full paper workflow.

## How we are graded (keep these in mind in every decision)
1. Published: public PyPI page + versioned releases (git tags v0.1.0 ... v1.0.0).
2. Documented: public docs site (MkDocs Material on GitHub Pages).
3. Functional: `pip install academicflow` must install with NO dependency conflicts and work on JupyterHub, ideally with no internet access after install and no API keys.
4. Innovative: features not easily replaced by existing packages. Our differentiators: section-aware style rules, terminology consistency across a whole notebook, venue profiles (APA/IEEE/Nature presets that control more than citation format), citation integrity checks, and one-command notebook-to-DOCX/LaTeX export with references already formatted.
5. Teamwork: regular small commits from every member, PRs reviewed by teammates.

## Hard technical rules
- Python >= 3.9. Use `from __future__ import annotations` in every module.
- Base dependencies ONLY: pybtex, pyyaml, ipython, nbformat, numpy, pypandoc_binary, python-docx. Do not add any other runtime dependency without a PR approved by Member 5.
- Optional extras: [nlp] = spacy; [llm] = openai. Code must work without them (import them lazily inside functions, fall back gracefully).
- NO runtime downloads (no nltk.download, no spacy model download, no fetching CSL files). Bundle any word lists or data as package files under the module's `data/` folder and load them with importlib.resources.
- Pure functions, type hints, docstrings (Google style) on every public function.
- Tests with pytest in tests/test_<module>.py. Every public function gets at least one test. Tests must not need network.
- Format/lint with ruff (line length 100).
- Never edit another member's folder. Shared files (types.py, pyproject.toml, __init__.py, AGENTS.md) change only through a PR that mentions the affected members.

## Repository layout
```
src/academicflow/
  __init__.py          # __version__, load_ipython_extension (re-exported from magics)
  types.py             # shared dataclasses (below) - owned by Member 5
  core/                # Member 1: text.py, readability.py, keywords.py, passive.py, data/stopwords.txt
  style/               # Member 2: rules.py, terminology.py, profiles.py, data/informal.yaml
  profiles/            # Member 2: apa.yaml, ieee.yaml, nature.yaml (package data)
  cite/                # Member 3: bib.py, styles.py, render.py, integrity.py
  summarize/           # Member 5: extractive.py, llm.py
  magics/              # Member 4: session.py, magics.py, display.py
  export/              # Member 4: docx.py, latex.py, templates/
tests/                 # one test file per module
examples/              # 01_quickstart.ipynb, 02_full_paper_workflow.ipynb, refs.bib, sample_draft.md
docs/ + mkdocs.yml     # one page per module, written by its owner
.github/workflows/     # test.yml (pytest on 3.9-3.12), publish.yml (trusted publishing on tag v*), docs.yml
```

## Shared types (src/academicflow/types.py)
```python
@dataclass
class Issue:
    rule: str                 # e.g. "informal-word", "passive-voice", "term-inconsistency", "cite-missing-key"
    message: str              # human-readable explanation
    severity: str = "warning" # "info" | "warning" | "error"
    start: int = 0            # character offset in the text that was checked
    end: int = 0
    suggestion: str | None = None
    section: str | None = None  # filled when checking a multi-section document

@dataclass
class TextStats:
    word_count: int
    sentence_count: int
    reading_time_min: float          # at 238 words per minute
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    avg_sentence_length: float
    keywords: list[tuple[str, float]]  # (keyword, score), best first
    passive_ratio: float             # passive sentences / all sentences
```

## Public API contract (stubs exist from Day 1; owners replace them with real code)
```
# Member 1 - academicflow.core
split_sentences(text: str) -> list[tuple[int, int]]      # (start, end) offsets
tokenize(text: str) -> list[str]                          # lowercase word tokens
count_syllables(word: str) -> int
readability(text: str) -> dict[str, float]               # flesch_reading_ease, flesch_kincaid_grade
extract_keywords(text: str, top_n: int = 10) -> list[tuple[str, float]]
detect_passive(text: str) -> list[Issue]                  # rule="passive-voice", severity="info"
analyze(text: str) -> TextStats

# Member 2 - academicflow.style
load_profile(name_or_path: str) -> dict                   # "apa" | "ieee" | "nature" | path to a YAML file
check(text: str, profile: str = "apa", section: str | None = None) -> list[Issue]
check_document(sections: dict[str, str], profile: str = "apa") -> list[Issue]   # cross-section rules

# Member 3 - academicflow.cite
class Bibliography:
    @classmethod from_file(cls, path) -> Bibliography
    @classmethod from_string(cls, bibtex: str) -> Bibliography
    keys() -> list[str]
    format_reference(key: str, style: str) -> str        # style: "apa" | "ieee" | "nature"
find_citations(text: str) -> list[tuple[str, int, int]]  # (key, start, end); syntax [@key] and [@a; @b]
render(text: str, bib: Bibliography, style: str, target: str = "markdown") -> tuple[str, list[str]]
    # returns (text with inline citations replaced, ordered reference list)
    # target: "markdown" (for notebook display, Nature uses <sup>n</sup>) | "pandoc" (Nature uses ^n^) | "latex"
check_integrity(text: str, bib: Bibliography) -> list[Issue]

# Member 5 - academicflow.summarize
summarize(text: str, max_words: int = 200, method: str = "extractive", **kwargs) -> str
generate_abstract(sections: dict[str, str], max_words: int = 200, method: str = "extractive") -> str

# Member 4 - academicflow.magics / academicflow.export
load_ipython_extension(ipython)                           # enables %load_ext academicflow
Session (singleton): profile name, Bibliography | None, ordered sections dict[str, str], title, authors
export_document(session, path: str, fmt: str = "docx") -> str     # fmt: "docx" | "latex" | "md"
export_notebook(nb_path: str, out_path: str, fmt: str = "docx", style: str = "apa", bib_path: str | None = None) -> str
```

## Magics (user-facing, Member 4 implements by calling everyone's API)
```
%load_ext academicflow
%acite refs.bib                       # load bibliography into the session
%%academic --style=apa --section=introduction [--no-check]
    <markdown text with [@key] citations>
    -> renders formatted text + references, stores the section, shows style issues
%astats [section]                     # TextStats table
%acheck                               # check_document over all sections + citation integrity
%aabstract [--words=200] [--llm]      # generate and store the abstract
%aexport paper.docx [--format=docx|latex|md]
```

## Git workflow
- Branch per task: feature/m<N>-<short-name> (e.g. feature/m3-ieee-format). Never push to main.
- Small commits, conventional messages: feat(cite): add IEEE formatter / test(core): ... / docs(style): ...
- Open a PR at least twice a day. One teammate reviews. CI must pass before merge.
- Only Member 5 bumps __version__ and creates tags.

## Timeline (4 days)
- Day 1: skeleton + stubs (Member 5, by 11:00), basic version of every module, v0.1.0 on PyPI in the evening.
- Day 2: full features + tests, v0.2.0.
- Day 3: integration through magics, export, innovation features, docs pages, example notebooks, v0.3.0.
- Day 4: fresh-install test on JupyterHub, bug fixes only after 14:00, v1.0.0, rehearsal.
