"""Cross-section rules: terminology consistency and acronyms.

Owner: Member 2.
"""

from __future__ import annotations

from academicflow.style.rules import check
from academicflow.types import Issue


def check_document(sections: dict[str, str], profile: str = "apa") -> list[Issue]:
    """Check a whole document made of named sections.

    Args:
        sections: Ordered mapping of section name to text.
        profile: Profile name or YAML path.

    Returns:
        Issues from every section (with ``Issue.section`` set) plus cross-section issues.

    TODO(member 2): term-inconsistency, acronym-undefined/redefined/unused.
    """
    issues: list[Issue] = []
    for name, text in sections.items():
        for issue in check(text, profile, section=name):
            issue.section = name
            issues.append(issue)
    return issues
