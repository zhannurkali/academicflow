# Examples

| File | What it shows |
| --- | --- |
| `01_quickstart.ipynb` | Every feature through the Python API, in a few cells |
| `03_one_minute_demo.ipynb` | The one-minute presentation version: install, write, check, export |
| `02_full_paper_workflow.ipynb` | The full demo: write a paper with magics, check it, generate an abstract, export it |
| `sample_draft.md` | The same paper as plain Markdown, for tests and scripts |
| `refs.bib` | Bibliography used by both notebooks |

Run them on JupyterHub:

```bash
pip install academicflow
cd examples
jupyter lab
```

## Deliberate mistakes in the sample paper

The sample paper is written badly on purpose, so every checker has something to find.
Use this table as the answer key when you test your module.

| Section | Mistake | Expected issue |
| --- | --- | --- |
| abstract | About 240 words: over the Nature limit (200 words) | style: abstract-length |
| abstract | Contains a citation `[@vaswani2017]` | style: citation-in-abstract |
| abstract | Informal phrases: *a lot of*, *get stuck* | style: informal-word |
| introduction | Informal words: *a lot of*, *get*, *basically*, *stuff*, *really*, *obviously* | style: informal-word / hedge |
| introduction | Contractions: *don't*, *it's* | style: contraction |
| introduction | Repeated word: *the the* | style: repeated-word |
| introduction | `NLP` used before it is defined | style: acronym-undefined |
| introduction | Misspelled citation key `[@vaswani2071]` (should be `vaswani2017`) | cite: cite-missing-key |
| introduction + methods + results | *data set* / *dataset* / *data-set* | style: term-inconsistency |
| introduction + methods | `LLM` defined twice | style: acronym-redefined |
| methods | Present tense: *We use*, *We propose* | style: tense (methods: past) |
| methods | Second sentence is over 60 words | style: long-sentence |
| results | *The style checker found* repeated 3 times | style: repeated-phrase |
| conclusion | Informal words: *pretty*, *big* | style: informal-word |

If you add a rule, add a matching mistake to the sample paper (in `sample_draft.md`
and in both notebooks) and a row to this table, so the demo shows it.
