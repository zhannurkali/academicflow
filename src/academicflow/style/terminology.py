"""Cross-section checks for consistent terminology and acronym definitions."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from academicflow.style.profiles import load_profile
from academicflow.style.rules import check, normalize_section_name
from academicflow.types import Issue


@dataclass(frozen=True)
class _Occurrence:
    """A term occurrence with its local section coordinates."""
    variant: str
    start: int
    end: int
    section: str


# Variants are grouped by meaning/normalised spelling. The list intentionally
# covers common scientific vocabulary; custom vocabulary can be added here.
_HYPHENATION_GROUPS: tuple[tuple[str, ...], ...] = (
    ("dataset", "data set", "data-set"),
    ("real time", "real-time", "realtime"),
    ("state of the art", "state-of-the-art"),
    ("decision making", "decision-making"),
    ("machine learning", "machine-learning"),
    ("deep learning", "deep-learning"),
    ("long term", "long-term"),
    ("short term", "short-term"),
    ("in vitro", "in-vitro"),
    ("in vivo", "in-vivo"),
    ("cross section", "cross-section"),
    ("multi layer", "multi-layer", "multilayer"),
    ("single layer", "single-layer", "singlelayer"),
    ("high throughput", "high-throughput"),
    ("low cost", "low-cost"),
    ("open source", "open-source"),
    ("fine tuning", "fine-tuning"),
    ("pre processing", "pre-processing", "preprocessing"),
    ("post processing", "post-processing", "postprocessing"),
    ("non linear", "non-linear", "nonlinear"),
    ("linear regression", "linear-regression"),
)

# More than eighty common US/UK spelling pairs. These are consistency hints,
# not a claim that every publisher mandates one spelling in every context.
_SPELLING_PAIRS: tuple[tuple[str, str], ...] = (
    ("analyze", "analyse"), ("analyzed", "analysed"),
    ("analyzes", "analyses"), ("analyzing", "analysing"),
    ("behavior", "behaviour"), ("behavioral", "behavioural"),
    ("center", "centre"), ("centered", "centred"), ("centering", "centring"),
    ("color", "colour"), ("colored", "coloured"), ("coloring", "colouring"),
    ("colors", "colours"), ("colorful", "colourful"),
    ("defense", "defence"), ("offense", "offence"),
    ("organize", "organise"), ("organized", "organised"),
    ("organizes", "organises"), ("organizing", "organising"),
    ("organization", "organisation"), ("organizations", "organisations"),
    ("organizational", "organisational"), ("organizer", "organiser"),
    ("recognize", "recognise"), ("recognized", "recognised"),
    ("recognizes", "recognises"), ("recognizing", "recognising"),
    ("summarize", "summarise"), ("summarized", "summarised"),
    ("summarizes", "summarises"), ("summarizing", "summarising"),
    ("optimize", "optimise"), ("optimized", "optimised"),
    ("optimizes", "optimises"), ("optimizing", "optimising"),
    ("optimization", "optimisation"), ("minimize", "minimise"),
    ("minimized", "minimised"), ("minimizing", "minimising"),
    ("minimization", "minimisation"), ("maximize", "maximise"),
    ("maximized", "maximised"), ("maximizing", "maximising"),
    ("standardize", "standardise"), ("standardized", "standardised"),
    ("standardizing", "standardising"), ("characterize", "characterise"),
    ("characterized", "characterised"), ("characterizing", "characterising"),
    ("specialize", "specialise"), ("specialized", "specialised"),
    ("specializing", "specialising"), ("catalyze", "catalyse"),
    ("catalyzed", "catalysed"), ("paralyze", "paralyse"),
    ("paralyzed", "paralysed"), ("modeling", "modelling"),
    ("modeled", "modelled"), ("modeler", "modeller"),
    ("traveling", "travelling"), ("traveled", "travelled"),
    ("traveler", "traveller"), ("labeled", "labelled"),
    ("labeling", "labelling"), ("canceling", "cancelling"),
    ("canceled", "cancelled"), ("counselor", "counsellor"),
    ("counseling", "counselling"), ("enrollment", "enrolment"),
    ("fulfill", "fulfil"), ("skillful", "skilful"),
    ("favor", "favour"), ("favored", "favoured"),
    ("favorite", "favourite"), ("honor", "honour"),
    ("honored", "honoured"), ("honoring", "honouring"),
    ("honorable", "honourable"), ("labor", "labour"),
    ("laborer", "labourer"), ("neighbor", "neighbour"),
    ("neighborhood", "neighbourhood"), ("neighboring", "neighbouring"),
    ("rumor", "rumour"), ("rumored", "rumoured"),
    ("gray", "grey"), ("grayer", "greyer"), ("grayest", "greyest"),
    ("theater", "theatre"), ("theaters", "theatres"),
    ("meter", "metre"), ("meters", "metres"),
    ("liter", "litre"), ("liters", "litres"),
    ("fiber", "fibre"), ("fibers", "fibres"), ("specter", "spectre"),
    ("pediatric", "paediatric"), ("pediatrics", "paediatrics"),
    ("pediatrician", "paediatrician"), ("estrogen", "oestrogen"),
    ("anemia", "anaemia"), ("leukemia", "leukaemia"),
    ("diarrhea", "diarrhoea"), ("hemoglobin", "haemoglobin"),
    ("fetus", "foetus"), ("orthopedic", "orthopaedic"),
    ("orthopedics", "orthopaedics"), ("gynecology", "gynaecology"),
    ("encyclopedia", "encyclopaedia"), ("maneuver", "manoeuvre"),
    ("jewelry", "jewellery"), ("catalog", "catalogue"),
    ("dialog", "dialogue"), ("analog", "analogue"),
    ("airplane", "aeroplane"), ("aging", "ageing"),
    ("skeptical", "sceptical"), ("skeptic", "sceptic"),
)


def _compile_phrase(phrase: str) -> re.Pattern[str]:
    """Compile a phrase matcher allowing flexible whitespace between words."""
    pieces = phrase.split()
    body = r"\s+".join(re.escape(piece) for piece in pieces)
    return re.compile(r"(?<!\w)" + body + r"(?!\w)", re.IGNORECASE)


def _collect_group_occurrences(
    sections: dict[str, str], variants: Iterable[str]
) -> list[_Occurrence]:
    """Find occurrences of any explicit spelling variant in all sections."""
    found: list[_Occurrence] = []
    patterns = [(variant, _compile_phrase(variant)) for variant in variants]
    for section, text in sections.items():
        for variant, pattern in patterns:
            for match in pattern.finditer(text):
                found.append(_Occurrence(match.group(0), match.start(), match.end(), section))
    return found


def _term_group_issues(
    sections: dict[str, str],
    variants: tuple[str, ...],
    profile: dict,
    group_label: str,
) -> list[Issue]:
    """Report every occurrence of the minority form in a terminology family."""
    occurrences = _collect_group_occurrences(sections, variants)
    if len({item.variant.casefold() for item in occurrences}) < 2:
        return []

    counts = Counter(item.variant.casefold() for item in occurrences)
    # Preserve a display form for each normalised spelling.
    display_forms: dict[str, str] = {}
    for item in occurrences:
        display_forms.setdefault(item.variant.casefold(), item.variant)

    highest = max(counts.values())
    leaders = [variant for variant, count in counts.items() if count == highest]
    if len(leaders) == 1:
        preferred = leaders[0]
    else:
        spelling = profile.get("preferred_spelling", "us")
        preferred_us_uk = {
            pair[0 if spelling == "us" else 1].casefold() for pair in _SPELLING_PAIRS
        }
        preferred = next(
            (variant for variant in leaders if variant in preferred_us_uk),
            next(
                (variant.casefold() for variant in variants if variant.casefold() in leaders),
                sorted(leaders)[0],
            ),
        )

    count_text = ", ".join(
        f"{display_forms[variant]!r}: {count}"
        for variant, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    )
    issues: list[Issue] = []
    for item in occurrences:
        if item.variant.casefold() == preferred:
            continue
        issues.append(
            Issue(
                rule="term-inconsistency",
                message=(
                    f"Inconsistent form of {group_label}: {item.variant!r}. "
                    f"Document counts — {count_text}."
                ),
                severity="warning",
                start=item.start,
                end=item.end,
                suggestion=f"Use {display_forms[preferred]!r} consistently.",
                section=item.section,
            )
        )
    return issues


def _case_variant_issues(sections: dict[str, str]) -> list[Issue]:
    """Detect mid-sentence lower/title-case variants of one- to three-word terms."""
    token_re = re.compile(r"\b[A-Za-z][A-Za-z0-9-]{2,}\b")
    grouped: dict[str, list[_Occurrence]] = defaultdict(list)
    for section, text in sections.items():
        tokens = list(token_re.finditer(text))
        for index in range(len(tokens)):
            for size in (3, 2, 1):
                group = tokens[index:index + size]
                if len(group) != size:
                    continue
                separators = [
                    text[group[pos].end():group[pos + 1].start()]
                    for pos in range(size - 1)
                ]
                if any(not separator.isspace() for separator in separators):
                    continue
                words = [item.group(0) for item in group]
                # Acronyms and intentionally mixed-case names are outside this rule.
                if any(word.isupper() for word in words):
                    continue
                if all(word.islower() for word in words):
                    style = "lower"
                elif all(word[0].isupper() and word[1:].islower() for word in words):
                    prefix = text[:group[0].start()].rstrip()
                    # A capitalised phrase at the start of a sentence is not a variant.
                    if not prefix or prefix[-1] in ".!?\n":
                        continue
                    style = "title"
                else:
                    continue
                start, end = group[0].start(), group[-1].end()
                phrase = text[start:end]
                grouped[phrase.casefold()].append(
                    _Occurrence(style + ":" + phrase, start, end, section)
                )

    issues: list[Issue] = []
    reported: list[tuple[str, int, int]] = []
    def phrase_length(pair: tuple[str, list[_Occurrence]]) -> int:
        return max(len(item.variant.split()) - 1 for item in pair[1])

    for canonical, items in sorted(
        grouped.items(), key=lambda pair: (-phrase_length(pair), pair[0])
    ):
        styles = {item.variant.split(":", 1)[0] for item in items}
        if not ({"lower", "title"} <= styles):
            continue
        counts = Counter(item.variant.split(":", 1)[0] for item in items)
        preferred_style = max(("lower", "title"), key=lambda key: counts[key])
        minority = [item for item in items if item.variant.split(":", 1)[0] != preferred_style]
        variants = Counter(item.variant.split(":", 1)[1] for item in items)
        summary = ", ".join(f"{key!r}: {value}" for key, value in variants.items())
        for item in minority:
            # Avoid reporting individual words already covered by a longer term.
            if any(
                old_section == item.section and old_start <= item.start and item.end <= old_end
                for old_section, old_start, old_end in reported
            ):
                continue
            wrong_form = item.variant.split(":", 1)[1]
            preferred_form = next(
                item2.variant.split(":", 1)[1]
                for item2 in items
                if item2.variant.split(":", 1)[0] == preferred_style
            )
            reported.append((item.section, item.start, item.end))
            issues.append(
                Issue(
                    rule="term-inconsistency",
                    message=f"Capitalisation of {canonical!r} is inconsistent. Counts — {summary}.",
                    severity="warning",
                    start=item.start,
                    end=item.end,
                    suggestion=f"Use {preferred_form!r} consistently (found {wrong_form!r}).",
                    section=item.section,
                )
            )
    return issues


def _matching_long_form(candidate: str, acronym: str) -> str | None:
    """Return the longest suffix matching acronym initials, if one exists."""
    ignored = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "the", "to", "with"}
    words = re.findall(r"[A-Za-z0-9]+", candidate)
    for size in range(min(len(words), 8), 1, -1):
        suffix = words[-size:]
        while suffix and suffix[0].casefold() in ignored:
            suffix = suffix[1:]
        while suffix and suffix[-1].casefold() in ignored:
            suffix = suffix[:-1]
        initials = "".join(word[0] for word in suffix if word.casefold() not in ignored)
        if initials.upper() == acronym.upper():
            return " ".join(suffix)
    return None


_DEFINITION_RE = re.compile(
    r"\b(?P<long>(?:[A-Za-z][A-Za-z0-9-]*\s+){1,10}[A-Za-z][A-Za-z0-9-]*)\s+"
    r"\((?P<acronym>[A-Z]{2,6})\)"
)
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
_COMMON_ACRONYMS = {"US", "UK", "EU", "UN", "USA", "COVID"}


def _acronym_issues(sections: dict[str, str]) -> list[Issue]:
    """Check acronym first use, repeated definitions, and subsequent use."""
    definitions: dict[str, list[tuple[int, int, str, int, int]]] = defaultdict(list)
    uses: dict[str, list[tuple[int, int, str, int]]] = defaultdict(list)
    section_offsets: dict[str, int] = {}
    full_text_parts: list[str] = []
    cursor = 0
    for section, text in sections.items():
        section_offsets[section] = cursor
        full_text_parts.append(text)
        cursor += len(text) + 1
    full_text = "\n".join(full_text_parts)

    definition_spans: list[tuple[int, int]] = []
    for match in _DEFINITION_RE.finditer(full_text):
        acronym = match.group("acronym")
        long_form = _matching_long_form(match.group("long"), acronym)
        if long_form is None:
            continue
        definition_spans.append((match.start("acronym"), match.end("acronym")))
        definitions[acronym].append(
            (match.start(), match.end(), long_form, match.start("acronym"), match.end("acronym"))
        )

    for match in _ACRONYM_RE.finditer(full_text):
        acronym = match.group(0)
        if acronym in _COMMON_ACRONYMS:
            continue
        if any(start <= match.start() < end for start, end in definition_spans):
            continue
        uses[acronym].append((match.start(), match.end(), "", match.start()))

    issues: list[Issue] = []
    # Map concatenated-document offsets back to each source section.
    section_ranges = {
        section: (section_offsets[section], section_offsets[section] + len(text))
        for section, text in sections.items()
    }

    def locate(global_start: int) -> tuple[str, int]:
        for section, (left, right) in section_ranges.items():
            if left <= global_start <= right:
                return section, global_start - left
        last = next(reversed(sections))
        return last, max(0, len(sections[last]) - 1)

    for acronym, defs in definitions.items():
        first_start, first_end, long_form, acronym_start, acronym_end = defs[0]
        prior_uses = [item for item in uses.get(acronym, []) if item[0] < first_start]
        if prior_uses:
            global_start, global_end, _, _ = prior_uses[0]
            section, local_start = locate(global_start)
            issues.append(
                Issue(
                    rule="acronym-undefined",
                    message=f"Acronym {acronym} is used before it is defined as {long_form}.",
                    severity="warning",
                    start=local_start,
                    end=local_start + len(acronym),
                    suggestion=f"Define it at first use: {long_form} ({acronym}).",
                    section=section,
                )
            )
        for repeated in defs[1:]:
            section, local_start = locate(repeated[3])
            issues.append(
                Issue(
                    rule="acronym-redefined",
                    message=f"Acronym {acronym} is defined more than once.",
                    severity="warning",
                    start=local_start,
                    end=local_start + len(acronym),
                    suggestion="Define the acronym once and use the short form thereafter.",
                    section=section,
                )
            )
        later_uses = [item for item in uses.get(acronym, []) if item[0] > first_end]
        if len(later_uses) < 2:
            section, local_start = locate(acronym_start)
            issues.append(
                Issue(
                    rule="acronym-unused",
                    message=(
                        f"Acronym {acronym} is defined but appears only {len(later_uses)} "
                        "time(s) after its definition; the configured heuristic expects at least 2."
                    ),
                    severity="info",
                    start=local_start,
                    end=local_start + len(acronym),
                    suggestion="Remove the acronym and use the full term if it is not reused.",
                    section=section,
                )
            )

    # Acronyms with no valid long-form definition are undefined at their first use.
    for acronym, acronym_uses in uses.items():
        if acronym in definitions or not acronym_uses:
            continue
        global_start, _, _, _ = acronym_uses[0]
        section, local_start = locate(global_start)
        issues.append(
            Issue(
                rule="acronym-undefined",
                message=f"Acronym {acronym} is used without a preceding long-form definition.",
                severity="warning",
                start=local_start,
                end=local_start + len(acronym),
                suggestion=(
                    f"Define the full term before first use, for example 'Long Form ({acronym})'."
                ),
                section=section,
            )
        )

    return issues


def check_document(sections: dict[str, str], profile: str = "apa") -> list[Issue]:
    """Check every section and then run document-wide consistency checks.

    Args:
        sections: Ordered mapping of heading to raw text. Insertion order is preserved.
        profile: Built-in profile name or path to a custom YAML profile.

    Returns:
        All local and cross-section issues, ordered by section then character offset.
    """
    if not isinstance(sections, dict):
        raise TypeError("sections must be a dictionary mapping section names to text")
    settings = load_profile(profile)
    section_order = {name: index for index, name in enumerate(sections)}
    issues: list[Issue] = []

    for name, text in sections.items():
        if not isinstance(name, str) or not isinstance(text, str):
            raise TypeError("sections must map string section names to string text")
        for issue in check(text, profile, section=name):
            issue.section = name
            issues.append(issue)

    if "term-inconsistency" not in settings.get("disabled_rules", []):
        for group in _HYPHENATION_GROUPS:
            issues.extend(_term_group_issues(sections, group, settings, "/".join(group)))
        for us_form, uk_form in _SPELLING_PAIRS:
            issues.extend(
                _term_group_issues(sections, (us_form, uk_form), settings, f"{us_form}/{uk_form}")
            )
        issues.extend(_case_variant_issues(sections))

    acronym_rules_disabled = set(settings.get("disabled_rules", []))
    for issue in _acronym_issues(sections):
        if issue.rule not in acronym_rules_disabled:
            issues.append(issue)

    return sorted(
        issues,
        key=lambda item: (
            section_order.get(item.section or "", len(section_order)),
            item.start,
            item.end,
            item.rule,
        ),
    )
