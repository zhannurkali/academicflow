"""Single-text and section-aware academic style rules."""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache
from importlib import resources
from typing import Any

import yaml

from academicflow.core import split_sentences, tokenize
from academicflow.style.profiles import load_profile
from academicflow.types import Issue

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
_CITATION_RE = re.compile(r"\[@[^\]]+\]")

# Function signatures stay deliberately small and deterministic. The profile is
# passed as a mapping so a profile is loaded only once per call to check().
RuleFunction = Callable[[str, dict[str, Any]], list[Issue]]


@lru_cache(maxsize=1)
def _informal_words() -> dict[str, str]:
    """Load the bundled informal-to-formal replacement dictionary."""
    raw = (
        resources.files("academicflow.style")
        .joinpath("data", "informal.yaml")
        .read_text(encoding="utf-8")
    )
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError("style/data/informal.yaml must contain a YAML mapping.")
    return {str(word): str(replacement) for word, replacement in data.items()}


def _word_count(text: str) -> int:
    """Count tokens with the shared core tokenizer, tolerating empty input."""
    if not text.strip():
        return 0
    return len(tokenize(text))


def _sentence_spans(text: str) -> list[tuple[int, int]]:
    """Use the shared core sentence splitter and fall back to a local regex if needed."""
    if not text.strip():
        return []
    try:
        spans = split_sentences(text)
    except (AttributeError, TypeError, ValueError):
        spans = []
    valid = [(start, end) for start, end in spans if 0 <= start < end <= len(text)]
    if valid:
        return valid
    # This fallback is mainly for partially implemented teammate stubs.
    return [(match.start(), match.end()) for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text)
            if match.group().strip()]


def normalize_section_name(section: str | None) -> str | None:
    """Normalise numbered headings and common section-name synonyms."""
    if section is None:
        return None
    value = section.strip().lower()
    value = re.sub(r"^\s*\d+(?:\.\d+)*[.)]?\s*", "", value)
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" :.-")
    synonyms = {
        "summary": "abstract",
        "methodology": "methods",
        "materials and methods": "methods",
        "material and methods": "methods",
        "materials methods": "methods",
        "experimental methods": "methods",
        "results and findings": "results",
        "concluding remarks": "conclusion",
        "conclusions": "conclusion",
    }
    return synonyms.get(value, value)


def _issue(
    rule: str,
    message: str,
    start: int,
    end: int,
    *,
    severity: str = "warning",
    suggestion: str | None = None,
    section: str | None = None,
) -> Issue:
    """Create an Issue while keeping the call sites concise."""
    return Issue(
        rule=rule,
        message=message,
        severity=severity,
        start=start,
        end=end,
        suggestion=suggestion,
        section=section,
    )


def _informal_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag informal words and phrases using exact, case-insensitive offsets."""
    del profile
    issues: list[Issue] = []
    terms = _informal_words()
    alternatives = sorted(terms, key=lambda item: (-len(item), item.lower()))
    if not alternatives:
        return issues
    pattern = re.compile(
        r"(?<!\w)(?:" + "|".join(re.escape(term) for term in alternatives) + r")(?!\w)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        found = match.group(0)
        replacement = next(
            (value for key, value in terms.items() if key.casefold() == found.casefold()),
            "Use a more precise academic expression.",
        )
        issues.append(
            _issue(
                "informal-word",
                f"Informal expression {found!r} may be unsuitable for academic writing.",
                match.start(),
                match.end(),
                suggestion=replacement,
            )
        )
    return issues


_CONTRACTION_EXPANSIONS = {
    "aren't": "are not", "can't": "cannot", "couldn't": "could not",
    "didn't": "did not", "doesn't": "does not", "don't": "do not",
    "hadn't": "had not", "hasn't": "has not", "haven't": "have not",
    "isn't": "is not", "mustn't": "must not", "shouldn't": "should not",
    "wasn't": "was not", "weren't": "were not", "won't": "will not",
    "wouldn't": "would not", "it's": "it is / it has", "they're": "they are",
    "we're": "we are", "you're": "you are", "I've": "I have", "we've": "we have",
    "they've": "they have", "I'll": "I will", "we'll": "we will",
}
_CONTRACTION_RE = re.compile(
    r"\b(?:[A-Za-z]+n['’]t|"
    r"(?:I|we|you|they|he|she|it|that|there|who|what|where|when|how)['’](?:s|re|ve|ll|d|m))\b",
    re.IGNORECASE,
)


def _contraction_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag contractions when the selected venue profile disallows them."""
    if profile.get("allow_contractions", False):
        return []
    issues: list[Issue] = []
    for match in _CONTRACTION_RE.finditer(text):
        found = match.group(0)
        key = found.replace("’", "'").lower()
        suggestion = _CONTRACTION_EXPANSIONS.get(key, "Write the full form instead.")
        issues.append(
            _issue(
                "contraction",
                f"Contraction {found!r} is discouraged by this profile.",
                match.start(),
                match.end(),
                suggestion=suggestion,
            )
        )
    return issues


_FIRST_PERSON_RE = re.compile(r"\b(?:I|we|our|us)\b", re.IGNORECASE)


def _first_person_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag first-person pronouns only when the profile disallows them."""
    if profile.get("allow_first_person", True):
        return []
    issues: list[Issue] = []
    for match in _FIRST_PERSON_RE.finditer(text):
        found = match.group(0)
        # Avoid treating the conventional country abbreviation US as a pronoun.
        if found == "US":
            continue
        issues.append(
            _issue(
                "first-person",
                f"First-person pronoun {found!r} is discouraged by this profile.",
                match.start(),
                match.end(),
                severity="info",
                suggestion=(
                    "Consider an objective construction that keeps the scientific agent clear."
                ),
            )
        )
    return issues


def _long_sentence_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag sentences exceeding the profile's configured word limit."""
    limit = int(profile.get("max_sentence_words", 40))
    issues: list[Issue] = []
    for start, end in _sentence_spans(text):
        sentence = text[start:end]
        count = _word_count(sentence)
        if count > limit:
            issues.append(
                _issue(
                    "long-sentence",
                    f"Sentence contains {count} words; the profile limit is {limit}.",
                    start,
                    end,
                    suggestion=(
                        "Consider splitting this sentence into two or more shorter sentences."
                    ),
                )
            )
    return issues


_REPEATED_WORD_RE = re.compile(
    r"\b(?P<first>[A-Za-z][A-Za-z0-9'-]*)\s+"
    r"(?P<second>[A-Za-z][A-Za-z0-9'-]*)\b",
    re.IGNORECASE,
)


def _repeated_word_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag adjacent duplicated words such as 'the the'."""
    del profile
    issues: list[Issue] = []
    for match in _REPEATED_WORD_RE.finditer(text):
        first = match.group("first")
        second = match.group("second")
        if first.casefold() != second.casefold():
            continue
        # Highlight the second occurrence, not the first correct use.
        second_start = match.start("second")
        second_end = match.end("second")
        issues.append(
            _issue(
                "repeated-word",
                f"Repeated word {first!r} appears twice consecutively.",
                second_start,
                second_end,
                suggestion="Delete the duplicated word.",
            )
        )
    return issues


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by",
    "for", "from", "had", "has", "have", "he", "her", "hers", "him", "his", "i",
    "in", "into", "is", "it", "its", "me", "my", "of", "on", "or", "our", "ours",
    "she", "that", "the", "their", "them", "there", "these", "they", "this", "those",
    "to", "us", "was", "we", "were", "will", "with", "you", "your",
}


def _repeated_phrase_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag repeated 3–5-word phrases after their second occurrence."""
    del profile
    tokens = list(_WORD_RE.finditer(text))
    occurrences: dict[tuple[str, ...], list[tuple[int, int]]] = {}
    for size in (5, 4, 3):
        for index in range(0, len(tokens) - size + 1):
            group = tokens[index:index + size]
            phrase = tuple(item.group(0).casefold() for item in group)
            if all(word in _STOPWORDS for word in phrase):
                continue
            # Do not build n-grams across sentence boundaries or blank lines.
            between = text[group[0].end():group[-1].start()]
            if re.search(r"[.!?\n]", between):
                continue
            occurrences.setdefault(phrase, []).append((group[0].start(), group[-1].end()))

    issues: list[Issue] = []
    # Longest phrases are considered first. Suppress a shorter repeated n-gram
    # when it is fully contained in an already reported repeated longer phrase.
    reported_spans: list[tuple[int, int]] = []
    for phrase, spans in sorted(
        occurrences.items(), key=lambda item: (-len(item[0]), item[0])
    ):
        if len(spans) < 3:
            continue
        display = " ".join(phrase)
        for start, end in spans[2:]:
            if any(left <= start and end <= right for left, right in reported_spans):
                continue
            reported_spans.append((start, end))
            issues.append(
                _issue(
                    "repeated-phrase",
                    f"Phrase {display!r} appears {len(spans)} times in this text.",
                    start,
                    end,
                    suggestion="Rephrase one or more occurrences to improve variety.",
                )
            )
    return issues


_WEASEL_TERMS = (
    "it is well known", "it is obvious", "needless to say", "clearly", "obviously",
    "very", "really", "extremely", "quite", "rather", "somewhat", "perhaps",
    "possibly", "probably", "interestingly", "surprisingly", "undoubtedly",
)
_WEASEL_RE = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(term) for term in _WEASEL_TERMS) + r")(?!\w)",
    re.IGNORECASE,
)


def _weasel_rule(text: str, profile: dict[str, Any]) -> list[Issue]:
    """Flag vague emphasis and hedging expressions as low-severity advice."""
    del profile
    return [
        _issue(
            "weasel-word",
            f"Potentially vague or emphatic expression {match.group(0)!r}.",
            match.start(),
            match.end(),
            severity="info",
            suggestion="Replace it with a measurable result or a more precise statement.",
        )
        for match in _WEASEL_RE.finditer(text)
    ]


def _section_rules(text: str, profile: dict[str, Any], section: str | None) -> list[Issue]:
    """Apply rules configured for a normalised section name."""
    normalised = normalize_section_name(section)
    if normalised is None:
        return []
    settings: dict[str, Any] = {}
    all_settings = profile.get("section_rules", {})
    for key, value in all_settings.items():
        if normalize_section_name(str(key)) == normalised and isinstance(value, dict):
            settings.update(value)

    issues: list[Issue] = []
    if normalised == "abstract":
        limit = int(settings.get("max_words", profile.get("abstract_max_words", 250)))
        count = _word_count(text)
        if count > limit:
            issues.append(
                _issue(
                    "abstract-length",
                    f"Abstract contains {count} words; the configured maximum is {limit}.",
                    0,
                    len(text),
                    suggestion=f"Reduce the abstract to {limit} words or fewer.",
                )
            )
        if settings.get("forbid_citations", False):
            for match in _CITATION_RE.finditer(text):
                issues.append(
                    _issue(
                        "citation-in-abstract",
                        "The selected profile discourages citations in the abstract.",
                        match.start(),
                        match.end(),
                        suggestion=(
                            "Move the citation to the main text or remove it if unnecessary."
                        ),
                    )
                )

    tense = settings.get("tense")
    if tense == "past":
        # Conservative lexical heuristics: common reporting verbs after explicit
        # subjects, plus common present-tense passive constructions.
        present_active = re.compile(
            r"\b(?:we|i|the study|this study|the experiment|the model|our method|our model|"
            r"the algorithm|the dataset|the data|the results|the findings|the samples|"
            r"the measurements|these results|this approach|our approach)\s+"
            r"(?:currently\s+)?(?:use|uses|propose|proposes|measure|measures|calculate|"
            r"calculates|collect|collects|analyze|analyzes|analyse|analyses|show|shows|"
            r"indicate|indicates|demonstrate|demonstrates|report|reports|find|finds|"
            r"suggest|suggests|include|includes|consist|consists|contain|contains|"
            r"represent|represents|employ|employs|apply|applies|obtain|obtains|"
            r"derive|derives|compute|computes|evaluate|evaluates|compare|compares)\b",
            re.IGNORECASE,
        )
        present_passive = re.compile(
            r"\b(?:is|are|am)\s+(?:being\s+)?(?:measured|calculated|collected|analysed|"
            r"analyzed|recorded|estimated|selected|used|applied|defined|determined|"
            r"obtained|performed|conducted|compared|observed|computed|evaluated|"
            r"reported|presented|shown|found|given)\b",
            re.IGNORECASE,
        )
        for start, end in _sentence_spans(text):
            sentence = text[start:end]
            match = present_active.search(sentence) or present_passive.search(sentence)
            if match:
                issues.append(
                    _issue(
                        "tense-inconsistency",
                        (
                            f"This {normalised} sentence appears to use present tense, "
                            "while the profile specifies past tense."
                        ),
                        start + match.start(),
                        start + match.end(),
                        severity="info",
                        suggestion="Check whether past tense is more appropriate for this section.",
                    )
                )

    return issues


RULES: dict[str, RuleFunction] = {
    "informal-word": _informal_rule,
    "contraction": _contraction_rule,
    "first-person": _first_person_rule,
    "long-sentence": _long_sentence_rule,
    "repeated-word": _repeated_word_rule,
    "repeated-phrase": _repeated_phrase_rule,
    "weasel-word": _weasel_rule,
}


def check(text: str, profile: str = "apa", section: str | None = None) -> list[Issue]:
    """Check one text block against a venue profile.

    Args:
        text: The text to inspect.
        profile: Built-in profile name or path to a custom YAML profile.
        section: Optional heading; enables section-specific checks when recognised.

    Returns:
        Issues sorted by character offset. Offsets refer to the original input text.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not text:
        return []

    settings = load_profile(profile)
    disabled = set(settings.get("disabled_rules", []))
    issues: list[Issue] = []
    for name, function in RULES.items():
        if name not in disabled:
            issues.extend(function(text, settings))
    for issue in _section_rules(text, settings, section):
        if issue.rule not in disabled:
            issues.append(issue)

    for issue in issues:
        issue.section = section
    return sorted(issues, key=lambda item: (item.start, item.end, item.rule))
