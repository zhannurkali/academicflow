# Citations (`academicflow.cite`)

Load a BibTeX file, cite with `[@key]` while you write, and get correctly formatted
citations and a reference list in **APA 7**, **IEEE** or **Nature** style. Citations are
also checked: a typo in a key, an entry you never cite, two entries for the same paper or
an entry with missing fields are all reported.

## In a notebook

```python
%load_ext academicflow
%acite refs.bib
```

```python
%%academic --style=apa --section=introduction
Deep learning [@lecun2015] builds on attention [@vaswani2017, p. 5; @lecun2015].
```

The cell is shown with formatted citations and its reference list. Change `--style` to
`ieee` or `nature` and everything is reformatted. `%acheck` runs the integrity checks on
the whole paper.

## Citation syntax

The syntax is the same as pandoc's, so the text also works with other Markdown tools.

| Write | Meaning |
| --- | --- |
| `[@lecun2015]` | one source |
| `[@lecun2015; @vaswani2017]` | several sources |
| `[@vaswani2017, p. 5]` | a source with a page or other locator |

A key that is not in the bibliography never stops rendering. It is shown as
`[@key?]`, and `check_integrity` reports it.

## The three styles side by side

Input: `Deep learning [@lecun2015] builds on attention [@vaswani2017, p. 5; @lecun2015].`

| Style | Inline citations | Reference list |
| --- | --- | --- |
| APA | Deep learning (LeCun et al., 2015) builds on attention (LeCun et al., 2015; Vaswani et al., 2017, p. 5). | alphabetical, no numbers |
| IEEE | Deep learning [1] builds on attention [1], [2, p. 5]. | `[1]`, `[2]`, in order of first citation |
| Nature | Deep learning<sup>1</sup> builds on attention<sup>1,2</sup>. | `1.`, `2.`, in order of first citation |

The reference for `lecun2015` in each style:

- **APA:** LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. *Nature*, *521*(7553), 436–444. https://doi.org/10.1038/nature14539
- **IEEE:** [1] Y. LeCun, Y. Bengio, and G. Hinton, "Deep Learning," *Nature*, vol. 521, no. 7553, pp. 436–444, 2015, doi: 10.1038/nature14539.
- **Nature:** 1. LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. *Nature* **521**, 436–444 (2015).

Supported entry types: `article`, `inproceedings` (and `conference`), `book` and `misc`
(for example web pages). Other types fall back to the article layout.

## From Python

```python
from academicflow.cite import Bibliography, render, find_citations, check_integrity

bib = Bibliography.from_file("refs.bib")      # or Bibliography.from_string(text)
bib.keys()                                    # ['vaswani2017', 'lecun2015']

text = "Deep learning [@lecun2015] builds on attention [@vaswani2017, p. 5]."
new_text, references = render(text, bib, style="ieee")
# new_text   -> 'Deep learning [1] builds on attention [2, p. 5].'
# references -> ['[1] Y. LeCun, ...', '[2] A. Vaswani et al., ...']

find_citations(text)                          # [('lecun2015', 16, 25), ('vaswani2017', 49, 60)]
```

`render(text, bib, style, target)` returns the text with citations replaced and the
reference list as Markdown strings. `target` changes only how Nature superscripts are
written:

| `target` | Nature superscript | Used by |
| --- | --- | --- |
| `"markdown"` (default) | `<sup>1</sup>` | notebook display |
| `"pandoc"` | `^1^` | Word export |
| `"latex"` | `\textsuperscript{1}` | LaTeX export |

## Integrity checks

`check_integrity(text, bib)` compares the citations in the whole document with the
bibliography. Pass it the full text of all sections, not one section, or every entry
looks unused.

| Rule | Severity | Finds |
| --- | --- | --- |
| `cite-missing-key` | error | a cited key that is not in the `.bib` file, with a "did you mean" suggestion |
| `cite-unused` | info | an entry in the `.bib` file that is never cited |
| `cite-duplicate-doi` | warning | two entries with the same DOI or the same title |
| `cite-incomplete` | warning | an entry missing fields its type needs, such as an article without a journal |

Example:

```python
for issue in check_integrity("[@vaswani2071] and [@lecun2015]", bib):
    print(issue.severity, issue.message)
# error  Cited key 'vaswani2071' is not in the bibliography. Did you mean 'vaswani2017'?
# info   'vaswani2017' is in the bibliography but never cited.
```

## Known limitations

- Formatting covers the most common entry types and fields. Unusual BibTeX fields are
  ignored.
- APA titles are converted to sentence case automatically. Proper nouns inside a Title Case
  title (for example "Python") are lowercased, because BibTeX braces that protect them are
  removed when the file is parsed.
