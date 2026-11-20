"""Tests for Member 2's academic style checker and venue profiles."""

from __future__ import annotations

import pytest

from academicflow.style import check, check_document, load_profile
from academicflow.style.rules import normalize_section_name
from academicflow.style.terminology import _matching_long_form


def rule_ids(issues):
    return {issue.rule for issue in issues}


@pytest.mark.parametrize("name", ["apa", "ieee", "nature"])
def test_builtin_profiles_load(name):
    profile = load_profile(name)
    assert profile["name"] == name
    assert profile["citation_style"] == name
    assert profile["section_rules"]["abstract"]["forbid_citations"] is True
    assert profile["section_rules"]["methods"]["tense"] == "past"


def test_unknown_profile_raises_value_error():
    with pytest.raises(ValueError, match="Unknown profile"):
        load_profile("no-such-profile")


def test_custom_profile_deep_merges_defaults(tmp_path):
    path = tmp_path / "custom.yaml"
    path.write_text(
        "name: custom\npreferred_spelling: uk\nsection_rules:\n  abstract:\n    max_words: 120\n",
        encoding="utf-8",
    )
    profile = load_profile(str(path))
    assert profile["preferred_spelling"] == "uk"
    assert profile["max_sentence_words"] == 40
    assert profile["section_rules"]["abstract"] == {
        "max_words": 120,
        "forbid_citations": True,
    }
    assert profile["section_rules"]["methods"]["tense"] == "past"


def test_custom_profile_abstract_max_words_overrides_default(tmp_path):
    path = tmp_path / "short-abstract.yaml"
    path.write_text("abstract_max_words: 3\n", encoding="utf-8")
    profile = load_profile(str(path))
    assert profile["abstract_max_words"] == 3
    assert "abstract-length" in rule_ids(
        check("Four words are enough here.", str(path), section="abstract")
    )


def test_custom_profile_rejects_unknown_key(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("name: bad\nmade_up_key: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown key"):
        load_profile(str(path))


def test_custom_profile_rejects_invalid_yaml(tmp_path):
    path = tmp_path / "invalid.yaml"
    path.write_text("name: [unterminated\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_profile(str(path))


def test_custom_profile_rejects_invalid_section_settings(tmp_path):
    path = tmp_path / "bad-section.yaml"
    path.write_text("section_rules:\n  abstract:\n    max_words: 0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="positive integer"):
        load_profile(str(path))


def test_empty_text_is_safe():
    assert check("") == []
    assert check_document({}) == []


def test_informal_word_positive_and_negative():
    issues = check("The results are a lot of big.")
    informal = [issue for issue in issues if issue.rule == "informal-word"]
    assert len(informal) == 2
    assert informal[0].suggestion
    assert check("The results are substantial.") == []


def test_informal_word_has_exact_offsets():
    text = "A result is pretty large."
    issue = next(issue for issue in check(text) if issue.rule == "informal-word")
    assert text[issue.start:issue.end] == "pretty"


def test_contraction_respects_profile():
    assert "contraction" in rule_ids(check("We don't agree.", profile="apa"))
    assert "contraction" not in rule_ids(check("We do not agree.", profile="apa"))


def test_first_person_is_profile_dependent():
    assert "first-person" not in rule_ids(check("We measured the samples.", profile="apa"))
    assert "first-person" in rule_ids(check("We measured the samples.", profile="nature"))
    assert "first-person" not in rule_ids(check("The US sample was included.", profile="nature"))


def test_long_sentence_positive_and_negative():
    long_text = " ".join(["The model uses a validated procedure"] * 9) + "."
    assert "long-sentence" in rule_ids(check(long_text, profile="ieee"))
    assert "long-sentence" not in rule_ids(check("The model was validated."))


def test_repeated_word_positive_and_negative():
    text = "The the samples were measured."
    issue = next(issue for issue in check(text) if issue.rule == "repeated-word")
    assert text[issue.start:issue.end].lower() == "the"
    assert "repeated-word" not in rule_ids(check("The samples were measured."))


def test_repeated_phrase_after_third_occurrence():
    text = (
        "The proposed model for classification was tested. "
        "The proposed model for classification was evaluated. "
        "The proposed model for classification was validated."
    )
    issues = [issue for issue in check(text) if issue.rule == "repeated-phrase"]
    assert issues
    assert all(issue.start > text.find("The proposed model") for issue in issues)
    assert "repeated-phrase" not in rule_ids(check("A model classifies the samples."))


def test_weasel_word_positive_and_negative():
    issues = check("The result is obviously important.")
    weasel = next(issue for issue in issues if issue.rule == "weasel-word")
    assert weasel.severity == "info"
    assert "weasel-word" not in rule_ids(check("The result increased by 12%."))


def test_section_name_normalisation():
    assert normalize_section_name("2. Methods") == "methods"
    assert normalize_section_name("Materials and Methods") == "methods"
    assert normalize_section_name("methodology") == "methods"
    assert normalize_section_name("Discussion") == "discussion"


def test_abstract_word_limit_and_citation_rule():
    abstract = " ".join(["evidence"] * 205) + " [@smith2020]"
    issues = check(abstract, profile="nature", section="Abstract")
    assert "abstract-length" in rule_ids(issues)
    citation_issue = next(issue for issue in issues if issue.rule == "citation-in-abstract")
    assert abstract[citation_issue.start:citation_issue.end] == "[@smith2020]"
    short = check("A short abstract without a citation.", section="abstract")
    assert "abstract-length" not in rule_ids(short)


def test_section_tense_rule_positive_and_negative():
    assert "tense-inconsistency" in rule_ids(
        check("We use the proposed protocol.", section="2. Methods")
    )
    assert "tense-inconsistency" not in rule_ids(
        check("We used the proposed protocol.", section="Methods")
    )


def test_section_rules_can_be_disabled(tmp_path):
    path = tmp_path / "no-abstract-limit.yaml"
    path.write_text(
        "name: custom\nabstract_max_words: 1\ndisabled_rules: [abstract-length]\n",
        encoding="utf-8",
    )
    assert "abstract-length" not in rule_ids(check("Several words here.", str(path), "abstract"))


def test_matching_long_form_uses_matching_suffix():
    ai_long_form = _matching_long_form("The authors used artificial intelligence", "AI")
    pca_long_form = _matching_long_form("principal component analysis", "PCA")
    assert ai_long_form == "artificial intelligence"
    assert pca_long_form == "principal component analysis"
    assert _matching_long_form("support vector machine", "XYZ") is None


def test_term_inconsistency_data_set_variants_across_sections():
    sections = {
        "Introduction": "The dataset was collected from public sources.",
        "Methods": "The data set was cleaned before analysis.",
        "Results": "The data-set contains 500 records.",
    }
    issues = [issue for issue in check_document(sections) if issue.rule == "term-inconsistency"]
    assert len(issues) >= 2
    assert {issue.section for issue in issues} >= {"Methods", "Results"}
    assert all("dataset" in (issue.suggestion or "").lower() for issue in issues)


def test_term_inconsistency_us_uk_pair():
    sections = {
        "Introduction": "We analyze the measurements.",
        "Methods": "We analyse the same measurements.",
    }
    issues = [issue for issue in check_document(sections) if issue.rule == "term-inconsistency"]
    assert any("analyse" in issue.message or "analyze" in issue.message for issue in issues)


def test_capitalisation_variant_is_detected():
    sections = {
        "Introduction": "We applied Deep Learning to the classification task.",
        "Methods": "We applied deep learning to the same task.",
    }
    issues = [issue for issue in check_document(sections) if issue.rule == "term-inconsistency"]
    assert any("capitalisation" in issue.message.lower() for issue in issues)


def test_consistent_term_does_not_trigger():
    sections = {
        "Introduction": "The dataset is public.",
        "Methods": "The dataset was filtered.",
        "Results": "The dataset contains 100 rows.",
    }
    assert "term-inconsistency" not in rule_ids(check_document(sections))


def test_acronym_used_before_definition():
    sections = {
        "Introduction": (
            "AI has changed this field. Artificial intelligence (AI) is widely studied."
        ),
        "Methods": "AI models were evaluated. AI systems were compared.",
    }
    issues = check_document(sections)
    undefined = [issue for issue in issues if issue.rule == "acronym-undefined"]
    assert undefined
    assert undefined[0].section == "Introduction"
    assert "Artificial intelligence" in undefined[0].message


def test_acronym_redefined():
    sections = {
        "Introduction": "Artificial intelligence (AI) is important. AI is useful.",
        "Methods": "Artificial intelligence (AI) was evaluated. AI was tested.",
    }
    issues = check_document(sections)
    assert "acronym-redefined" in rule_ids(issues)


def test_acronym_defined_but_not_reused():
    sections = {"Introduction": "Principal component analysis (PCA) was applied."}
    issues = check_document(sections)
    assert "acronym-unused" in rule_ids(issues)


def test_acronym_defined_and_reused_enough():
    sections = {
        "Introduction": (
            "Artificial intelligence (AI) is useful. AI is widely studied. AI has applications."
        )
    }
    assert "acronym-unused" not in rule_ids(check_document(sections))
    assert "acronym-undefined" not in rule_ids(check_document(sections))


def test_issue_sorting_and_section_assignment():
    sections = {
        "Introduction": "This is really a lot of material.",
        "Methods": "We use the method.",
    }
    issues = check_document(sections)
    assert all(issue.section in sections for issue in issues)
    indexes = [list(sections).index(issue.section) for issue in issues]
    assert indexes == sorted(indexes)


def test_public_api_returns_issue_objects():
    issues = check("This is really big.")
    assert isinstance(issues, list)
    assert all(hasattr(issue, "rule") and hasattr(issue, "start") for issue in issues)
    assert isinstance(check_document({"Intro": "A clean, concise sentence."}), list)
