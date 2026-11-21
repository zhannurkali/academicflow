# Example use cases

Four situations where academicflow saves time. Each one runs in a Jupyter notebook after
`pip install academicflow`. The full worked example, with a sample paper and bibliography, is
[`examples/02_full_paper_workflow.ipynb`](https://github.com/zhannurkali/academicflow/blob/main/examples/02_full_paper_workflow.ipynb).

## 1. Checking a thesis chapter before submission

A student has finished a chapter and wants to catch the problems a supervisor would mark,
before sending it.

```python
%load_ext academicflow
%acite thesis.bib
```

Paste each section into its own cell:

```python
%%academic --style=apa --section=introduction
...
```

```python
%%academic --section=methods
...
```

Then check the whole chapter at once:

```python
%acheck
```

`%acheck` reports, per section:

- a term spelled differently in different sections, such as *data set* in the introduction
  and *data-set* in the results
- acronyms used before they are defined, defined twice, or defined and never used again
- present tense in Methods or Results, where the profile expects past tense
- informal words and contractions, each with a formal alternative
- citation keys that are not in `thesis.bib`, with a "did you mean" suggestion

`%astats` adds reading time, readability grade and the share of passive sentences, so
the student can see whether a section is much harder to read than the others.

## 2. Moving a paper to another journal

A paper written for an IEEE conference is rejected and will be submitted to a Nature
journal instead. Normally every citation and every reference has to be reformatted by
hand.

Change the style flag on the first cell and re-run the notebook:

```python
%%academic --style=nature --section=abstract
...
```

- `[1]`-style citations become superscripts, and the reference list switches to Nature's
  format.
- The venue profile also changes the checks: `%acheck` now reports that the abstract is
  over Nature's 200-word limit.
- `%aabstract --words=150` drafts a shorter abstract from the introduction, methods,
  results and conclusion, as a starting point for the rewrite.
- `%aexport paper.docx` writes the new version.

A journal with its own rules can get its own profile: a short YAML file with the citation
style, word limits and rule settings. See [Style checker](style.md#custom-profile).

## 3. A group project report

Five students each write one section of a report. Each person's section reads well on its
own, but together they use different terms and cite the same paper with different keys.

Collect the sections and check them as one document:

```python
from academicflow import check_document, check_integrity, Bibliography

sections = {
    "introduction": open("intro.md").read(),
    "methods": open("methods.md").read(),
    "results": open("results.md").read(),
    "discussion": open("discussion.md").read(),
}
for issue in check_document(sections, profile="ieee"):
    print(issue.section, issue.rule, issue.message)

bib = Bibliography.from_file("refs.bib")
for issue in check_integrity("\n\n".join(sections.values()), bib):
    print(issue.rule, issue.message)
```

The terminology and acronym checks only make sense across sections, which is exactly
what a single-file grammar checker cannot see. The integrity check finds the misspelled
keys and two `.bib` entries for the same paper (same DOI).

## 4. From an analysis notebook to a Word draft

A researcher keeps the analysis and the paper in the same notebook. Code cells produce
the figures and numbers; `%%academic` cells hold the text.

```python
%%academic --title
Effect of X on Y
A. Researcher
B. Researcher
```

```python
%%academic --style=apa --section=results
The treatment group improved by 12% compared with the control [@smith2020].
```

When the draft is ready:

```python
%aexport paper.docx      # for co-authors who edit in Word
%aexport paper.tex       # for the journal's LaTeX template
```

Only the `%%academic` sections are exported, in order, with the abstract and a formatted
reference list. The code cells stay in the notebook. The same export works from a terminal,
without opening Jupyter:

```bash
python -m academicflow.export paper.ipynb paper.docx --style=apa --bib refs.bib
```
