# Style checker and venue profiles

`academicflow.style` reviews academic prose at three levels: individual wording,
section-specific expectations, and consistency across an entire multi-section paper.

The checks are deterministic, work offline, and do not require NLTK, spaCy, an LLM,
or any model download. They are heuristic writing aids rather than substitutes for
the target journal's current author instructions or a human editor. In particular,
verb-tense detection and acronym recognition are intentionally rule-based and can
produce false positives or miss unusual constructions.

## Quick start

```python
from academicflow.style import check, check_document, load_profile

profile = load_profile("nature")
print(profile["abstract_max_words"])  # 200

issues = check(
    "We use a lot of data in this study.",
    profile="apa",
    section="2. Methods",
)
for issue in issues:
    print(issue.rule, issue.message, issue.suggestion)

paper = {
    "Introduction": "The dataset contains public records.",
    "Methods": "The data set was filtered before analysis.",
}
for issue in check_document(paper, profile="apa"):
    print(issue.section, issue.rule, issue.start, issue.end, issue.message)
```

Each result is an `academicflow.types.Issue`. `start` is inclusive and `end` is
exclusive; both are character offsets into the original text of the reported section.

## Rules

| Rule ID | What it flags | Severity | Profile-dependent |
|---|---|---:|---|
| `informal-word` | Informal or imprecise words and phrases from the bundled YAML dictionary | warning | No |
| `contraction` | English contractions such as `don't` and `isn't` | warning | Yes: `allow_contractions` |
| `first-person` | `I`, `we`, `our`, or `us` | info | Yes: `allow_first_person` |
| `long-sentence` | Sentence exceeding `max_sentence_words` | warning | Yes |
| `repeated-word` | Adjacent duplicate words such as `the the` | warning | No |
| `repeated-phrase` | A repeated 3–5-word phrase used at least three times | warning | No |
| `weasel-word` | Vague emphasis or hedge expressions such as `obviously` and `very` | info | No |
| `abstract-length` | Abstract longer than the configured word limit | warning | Yes: `abstract_max_words` / section setting |
| `citation-in-abstract` | Pandoc-style `[@key]` citation in an abstract that forbids citations | warning | Yes |
| `tense-inconsistency` | Recognisable present-tense patterns in a section configured for past tense | info | Yes |
| `term-inconsistency` | Mixed spelling, hyphenation, spacing, or capitalisation across the document | warning | Yes: preferred spelling breaks ties |
| `acronym-undefined` | Acronym used before a matching `Long Form (LF)` definition, or never defined | warning | No |
| `acronym-redefined` | The same acronym is defined more than once | warning | No |
| `acronym-unused` | Acronym has fewer than two uses after its definition | info | No |

Rules can be disabled by their IDs using the `disabled_rules` list in a profile.

## Built-in profiles

| Setting | APA-inspired | IEEE-inspired | Nature-inspired |
|---|---:|---:|---:|
| `citation_style` | `apa` | `ieee` | `nature` |
| `allow_first_person` | true | true | false |
| `allow_contractions` | false | false | false |
| `max_sentence_words` | 40 | 35 | 35 |
| `abstract_max_words` | 250 | 250 | 200 |
| `preferred_spelling` | US | US | UK |
| Abstract citations | discouraged | discouraged | discouraged |
| Methods / Results tense | past heuristic | past heuristic | past heuristic |

These profiles are practical presets for a student project. They are not complete,
authoritative reproductions of the APA, IEEE, or Nature editorial manuals. Journals
within the same publisher can differ, and the journal's live instructions take priority.

## Section-aware checks

Section headings are case-insensitive, numbered prefixes are removed, and common
synonyms are normalised. For example:

- `2. Methods`, `Methodology`, and `Materials and Methods` become `methods`.
- `Summary` becomes `abstract`.
- `Conclusions` and `Concluding Remarks` become `conclusion`.
- `Discussion` remains distinct from `Conclusion`.

The abstract rule uses the section's `max_words` when provided, otherwise the
profile-level `abstract_max_words`. Citation checks search for the notebook citation
syntax `[@key]`. Past-tense checks use conservative lexical patterns such as
`we use` and `is measured`; they are not a full grammatical parser.

## Cross-document terminology and acronyms

`check_document` walks sections in insertion order, checks each section individually,
then checks the document-wide terminology and acronym state. It currently recognises
common space/hyphen/joined variants (including `data set`, `data-set`, and `dataset`),
more than 80 US/UK spelling pairs, and mid-sentence lower/title-case variants.

Acronym definitions are recognised in the form `Long Form (LF)`. Connecting words
such as `of`, `and`, `the`, and `for` are ignored when matching initials. Acronym
checks are deliberately simple: unusual abbreviations, pluralised acronyms, or
long forms with non-standard initials may need manual review.

## Custom profile

Create a YAML file, for example `my-journal.yaml`:

```yaml
name: my-journal
citation_style: apa
allow_first_person: false
allow_contractions: false
max_sentence_words: 32
abstract_max_words: 180
preferred_spelling: uk
disabled_rules:
  - weasel-word
section_rules:
  abstract:
    max_words: 180
    forbid_citations: true
  methods:
    tense: past
  results:
    tense: past
  discussion:
    tense: any
```

Load it by path:

```python
profile = load_profile("my-journal.yaml")
issues = check(text, profile="my-journal.yaml", section="Methods")
```

Supported top-level keys are `name`, `citation_style`, `allow_first_person`,
`allow_contractions`, `max_sentence_words`, `abstract_max_words`, `section_rules`,
`preferred_spelling`, and `disabled_rules`. Section settings support `max_words`,
`forbid_citations`, and `tense` (`past` or `any`). Missing values are
filled from the defaults; unknown or invalid values raise a descriptive `ValueError`.

## Example output

For:

```text
We use a lot of data. The dataset was really big. The the results are shown.
```

A typical APA-inspired check can report:

```text
informal-word    'a lot of' and 'big'
repeated-word    second occurrence of 'the'
weasel-word      'really'
```

Actual issue offsets always refer to the exact input string. Suggested replacements
are not applied automatically: context determines the academically appropriate wording.

## Known limitations

- Informal-word and hedge dictionaries are English-language heuristics.
- Sentence splitting and tokenisation are delegated to `academicflow.core`; their
  accuracy improves as Member 1's implementation matures.
- Passive/active voice and tense are not inferred with a complete syntactic parser.
- Cross-document spelling groups are curated, not exhaustive.
- Acronym matching is based on initials and does not understand every domain-specific
  convention.
- A single unusual capitalisation may be intentional (for example, a brand or a
  software library); review suggestions before changing a manuscript.
