# academicflow: Writing Scientific Papers Inside Jupyter Notebooks

## Abstract

Writing a scientific paper is hard, and a lot of students get stuck on style instead of content. In this paper we present academicflow, a tool that helps researchers write, check and format papers inside Jupyter notebooks [@vaswani2017]. The tool combines text analysis, a style checker, a citation manager, an abstract generator and an export module in one package. Students can write each section of their paper in a notebook cell and get immediate feedback on readability, informal language and terminology. Citations are written with a short key and are formatted automatically in APA, IEEE or Nature style. When the draft is ready, the whole paper can be exported to Word or LaTeX with one command. We evaluated the tool on twenty student drafts from an academic writing course. The style checker found on average fourteen issues per draft, and most of them were inconsistent terminology and informal words. After one revision, students fixed eighty percent of the flagged issues. Export to Word kept every citation and reference in all drafts. The abstract generator produced summaries that students rated as useful starting points for their own abstracts. These results suggest that integrating writing support directly into the notebook reduces context switching and helps students learn the conventions of academic writing. We release academicflow as an open-source Python package on PyPI so that other courses and research groups can use and extend it in their own teaching and research.

## Introduction

Students in data science spend a lot of time in Jupyter notebooks, but they still write their papers in separate tools. NLP tools for grammar checking are widely available, but they don't understand the conventions of academic writing. Natural language processing (NLP) has changed how we analyse text [@lecun2015], and large language models (LLM) can now write fluent paragraphs [@vaswani2071]. However, it's obviously not enough to get fluent text; a paper must also follow the style of the the target venue. Basically, students need a tool that checks their stuff where they already work. In this work we collected a data set of twenty student drafts and built a really simple pipeline around it.

## Methods

We use a modular design with five components. The style checker uses rules that depend on the section of the paper, so that the same sentence can be acceptable in the introduction but not in the methods, and it compares every section with every other section of the paper to find terms that are written in more than one way across the whole document. Citations are parsed from BibTeX files with pybtex. We propose an abstract generator based on TextRank, and an optional large language model (LLM) backend. The dataset was split into ten drafts for development and ten drafts for evaluation.

## Results

The style checker found on average fourteen issues per draft. The style checker found that terminology inconsistencies were the most common problem in the data-set. The style checker found fewer informal words in drafts written by senior students. After one revision, students fixed eighty percent of the flagged issues. Export to Word preserved all citations in every draft [@lecun2015].

## Conclusion

In conclusion, academicflow is a pretty big step towards writing support inside notebooks. Section-aware checks catch problems that generic linters miss, and integrated citations reduce errors. Future work will add more venue profiles and evaluate the tool with a larger group of students.
