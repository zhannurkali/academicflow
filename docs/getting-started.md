# Getting started

## Install

```bash
pip install academicflow
```

Optional extras: `pip install "academicflow[llm]"` for LLM abstracts, `"academicflow[nlp]"` for spaCy-based analysis.

## Five-minute tour

```python
%load_ext academicflow
%acite refs.bib
```

```python
%%academic --style=apa --section=introduction
Large language models have changed NLP [@vaswani2017].
```

```python
%astats
%acheck
%aabstract
%aexport paper.docx
```
