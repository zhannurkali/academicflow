"""HTML helpers for magic output (works in light and dark themes).

Owner: Member 4.
"""

from __future__ import annotations

import html

from academicflow.types import Issue

_COLORS = {"info": "#3b82f6", "warning": "#d97706", "error": "#dc2626"}


def issues_html(issues: list[Issue], title: str = "Style issues") -> str:
    """Render issues as a collapsible panel.

    TODO(member 4): group by section, show counts per severity, nicer styling.
    """
    if not issues:
        return f"<details><summary>{html.escape(title)}: none found</summary></details>"
    rows = "".join(
        f'<li><b style="color:{_COLORS.get(i.severity, "inherit")}">{i.severity}</b> '
        f"[{html.escape(i.rule)}] {html.escape(i.message)}"
        + (f" <i>→ {html.escape(i.suggestion)}</i>" if i.suggestion else "")
        + "</li>"
        for i in issues
    )
    summary = f"{html.escape(title)} ({len(issues)})"
    return f"<details open><summary>{summary}</summary><ul>{rows}</ul></details>"
