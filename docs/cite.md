# Citations

`academicflow.cite` loads a BibTeX file, turns `[@key]` citations in your text into
APA, IEEE or Nature citations, builds the reference list, and checks the bibliography for
problems. It works offline: BibTeX is parsed with `pybtex`, and the three styles are
written by hand, so the output is deterministic and needs no style files or downloads.

## Quick start

In a notebook:

```python
%load_ext academicflow
%acite refs.bib
```

```
%%academic --style=apa --section=introduction
Deep learning has changed the field [@lecun2015].
```

`%acheck` then lists style problems and citation problems together. Use
`--style=ieee` or `--style=nature` to switch the format of the same text.

From Python:

```python
from academicflow.cite import Bibliography, render, check_integrity

source = "Deep learning has changed the field [@lecun2015]."
bib = Bibliography.from_file("refs.bib")
text, references = render(source, bib, "apa")
issues = check_integrity(source, bib)
```

## Citation syntax

Citations use the pandoc syntax inside square brackets.

| You write | Meaning |
|---|---|
| `[@lecun2015]` | one citation |
| `[@lecun2015; @vaswani2017]` | several citations in one group |
| `[@lecun2015, p. 437]` | citation with a locator (page, chapter, ...) |

Keys may contain letters, digits and `_ - : .`. A markdown link such as `[@a](http://x)`
is not treated as a citation. A key that is not in the `.bib` file stays in the text as
`[@key?]`, and `render()` never raises an error for it. The integrity check reports it.

## The three styles

The same text, rendered in each style:

```
Deep learning has changed the field [@lecun2015]. Transformers [@vaswani2017] led to
large language models [@brown2020; @bishop2006], see also [@lecun2015, p. 437].
```

**APA 7.** Author-year citations. Three or more authors become "et al.", several
citations in one group are sorted alphabetically, and the reference list is sorted by
first author.

```
Deep learning has changed the field (LeCun et al., 2015). Transformers (Vaswani et al.,
2017) led to large language models (Bishop, 2006; Brown et al., 2020), see also
(LeCun et al., 2015, p. 437).

Bishop, C. M. (2006). *Pattern recognition and machine learning*. Springer.
Brown, T. B., Mann, B., Ryder, N., Subbiah, M., et al. (2020). Language Models Are Few-Shot
Learners. In *Advances in Neural Information Processing Systems* (pp. 1877–1901).
LeCun, Y., Bengio, Y., & Hinton, G. (2015). Deep learning. *Nature*, *521*(7553), 436–444.
https://doi.org/10.1038/nature14539
Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L.,
& Polosukhin, I. (2017). Attention is all you need. In *Advances in Neural Information
Processing Systems*.
```

Two cited works with the same author label and year get letters: `(Smith, 2020a)` and
`(Smith, 2020b)`, ordered by title. Up to 20 authors are listed; longer lists use the
APA 7 `. . .` form. A missing year is printed as `n.d.`.

**IEEE.** Numbers follow the order of first citation. Three or more consecutive numbers
in a group become a range (`[1]-[3]`); two stay separate (`[1], [2]`). More than six
authors become "et al.".

```
Deep learning has changed the field [1]. Transformers [2] led to large language models
[3], [4], see also [1, p. 437].

[1] Y. LeCun, Y. Bengio, and G. Hinton, "Deep Learning," *Nature*, vol. 521, no. 7553,
pp. 436–444, 2015, doi: 10.1038/nature14539.
[2] A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information
Processing Systems*, 2017.
[3] T. B. Brown et al., "Language Models Are Few-Shot Learners," in *Advances in Neural
Information Processing Systems*, 2020, pp. 1877–1901.
[4] C. M. Bishop, *Pattern Recognition and Machine Learning*. Springer, 2006.
```

**Nature.** Superscript numbers in order of first citation, attached to the word before
them. Three or more consecutive numbers become a range (`1–3`). More than five authors
become "et al.". Locators are not shown.

```
Deep learning has changed the field<sup>1</sup>. Transformers<sup>2</sup> led to large
language models<sup>3,4</sup>, see also<sup>1</sup>.

1. LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. *Nature* **521**, 436–444 (2015).
2. Vaswani, A. et al. Attention is all you need. in *Advances in Neural Information
   Processing Systems* (2017).
3. Brown, T. B. et al. Language Models Are Few-Shot Learners. in *Advances in Neural
   Information Processing Systems* 1877–1901 (2020).
4. Bishop, C. M. *Pattern Recognition and Machine Learning* (Springer, 2006).
```

## Render targets

`render(text, bib, style, target)` takes a `target` for where the text is going:

| Target | APA / IEEE | Nature |
|---|---|---|
| `"markdown"` (default, notebook display) | as shown above | `<sup>1,2</sup>` |
| `"pandoc"` (export through pandoc) | as shown above | `^1,2^` |
| `"latex"` | `&` is escaped (`Smith \& Lee`) | `\textsuperscript{1,2}` |

The reference list is always returned as markdown strings (`*italic*`, `**bold**`).
IEEE references start with `[n]`, Nature references with `n.`, and APA references have
no number. For LaTeX output, convert each reference with `to_latex`:

```python
from academicflow.cite.styles import to_latex

to_latex(references[0])
# 'LeCun, Y., Bengio, Y., \& Hinton, G. (2015). Deep learning. \textit{Nature}, ...'
```

`to_latex` escapes `& % _ #` and turns `*x*` into `\textit{x}` and `**x**` into
`\textbf{x}`.

## Supported entry types

| BibTeX type | APA | IEEE | Nature |
|---|---|---|---|
| `article` | Author (Year). Title. *Journal*, *vol*(no), pages. DOI | Authors, "Title," *Journal*, vol., no., pp., year, doi: | Authors. Title. *Journal* **vol**, pages (year). |
| `inproceedings` (also `conference`) | Author (Year). Title. In *Proceedings* (pp.). Publisher. DOI | Authors, "Title," in *Proceedings*, year, pp., doi: | Authors. Title. in *Proceedings* pages (publisher, year). |
| `book` | Author (Year). *Title*. Publisher. | Authors, *Title*. Publisher, year. | Authors. *Title* (Publisher, year). |
| `misc` | like `book`, with the URL at the end | Authors, "Title," publisher, year. [Online]. Available: URL | Authors. Title. Publisher URL (year). |

Other types (for example `phdthesis` or `techreport`) use the article layout, with the
booktitle or publisher in place of the journal, so they never fail.

## Integrity checks

`check_integrity(text, bib)` returns a list of `Issue` objects. Pass the full text of
your paper (all sections joined), so that "unused" entries are detected correctly.

| Rule | Severity | What it flags |
|---|---|---|
| `cite-missing-key` | error | a cited key that is not in the bibliography; suggests the closest key if there is one |
| `cite-duplicate-doi` | warning | an entry with the same DOI, or the same title, as an earlier entry |
| `cite-incomplete` | warning | an entry missing fields its type needs |
| `cite-unused` | info | an entry that is never cited |

Required fields: `article` needs authors, title, year and journal; `inproceedings` needs
authors, title, year and booktitle; `book` needs authors, title, year and publisher;
`misc` needs title and year; every other type needs authors, title and year.

Example output for a text with a misspelled key, a duplicated paper and an incomplete
entry:

```
error   cite-missing-key    Cited key 'vaswni2017' is not in the bibliography. Did you mean 'vaswani2017'?
warning cite-duplicate-doi  'lecun2015nature' has the same DOI as 'lecun2015'.
warning cite-incomplete     'bengio2013' (article) is missing: year, journal.
```

`cite-missing-key` issues point at the key in the text (`start` and `end` are character
offsets). The other three rules describe a bibliography entry, so their offsets are 0.

## Python API

| Function | Description |
|---|---|
| `Bibliography.from_file(path)` | load a `.bib` file; raises `ValueError` with the line number if it is malformed |
| `Bibliography.from_string(text)` | the same, from a string |
| `bib.keys()`, `bib.get(key)`, `key in bib`, `len(bib)` | inspect the entries; `get` raises `KeyError` for unknown keys |
| `bib.format_reference(key, style)` | one formatted reference (markdown) |
| `find_citations(text)` | list of `(key, start, end)`; `text[start:end]` is the key |
| `render(text, bib, style, target="markdown")` | returns `(new_text, references)` |
| `check_integrity(text, bib)` | returns a list of `Issue` |

`style` is `"apa"`, `"ieee"` or `"nature"`. An unknown style or target raises
`ValueError`.

## Known limitations

- **Sentence case.** APA and Nature want sentence-case titles. Titles that look like
  Title Case are converted, and acronyms are kept. Proper nouns are lowercased, and
  titles with hyphenated words (such as "Few-Shot") are left as they are, because the
  braces that protect capitals in BibTeX are removed while loading. Write titles in
  sentence case in the `.bib` file if exact capitalisation matters.
- **Editors, cities and edition** are not read, so `In E. Editor (Ed.),` (APA) and the
  city before the publisher (IEEE) are left out.
- **Inline forms.** Narrative citations such as "Smith (2020)", prefixes such as
  `[see @key]` and the merging of several works by one author, `(Smith, 2019, 2020)`, are
  not supported.
- **Duplicate titles.** Two entries with the same title (ignoring case and punctuation)
  are reported as duplicates, even when the authors differ.
- **Offline only.** No style files or web lookups are used, so nothing is downloaded.

## Tips for a clean `.bib` file

- Give every entry authors, title, year and the container field for its type (journal,
  booktitle or publisher). `%acheck` lists what is missing.
- Add the DOI when you have it. It is used for the reference and for finding duplicates.
- Use keys without spaces, for example `smith2020`.
- Use `and others` after the authors you want to list if the full list is very long.
