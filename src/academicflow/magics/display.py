"""HTML helpers for the magics. Inline CSS only, readable in light and dark JupyterLab themes."""
from __future__ import annotations

import html
from collections.abc import Iterable
from typing import Any

_COLORS = {"error": "#e5484d", "warning": "#f5a524", "info": "#3b82f6"}
_ORDER = ("error", "warning", "info")


def esc(value: Any) -> str:
    """HTML-escape any value."""
    return html.escape(str(value), quote=True)


def severity_counts(issues: Iterable[Any]) -> dict[str, int]:
    """Count issues per severity (always returns the three standard keys)."""
    counts = {"error": 0, "warning": 0, "info": 0}
    for issue in issues:
        sev = getattr(issue, "severity", "warning")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _counts_text(counts: dict[str, int]) -> str:
    parts = []
    for sev in _ORDER:
        n = counts.get(sev, 0)
        if n:
            parts.append(f'<span style="color:{_COLORS[sev]};font-weight:600">{n} {sev}</span>')
    return ", ".join(parts) if parts else "no issues"


def message(text: str, kind: str = "info") -> str:
    """A small coloured message box. ``kind`` is ``info``, ``warning`` or ``error``."""
    color = _COLORS.get(kind, _COLORS["info"])
    return (
        f'<div style="border-left:4px solid {color};background:{color}22;'
        f'padding:6px 10px;margin:4px 0;border-radius:3px">{esc(text)}</div>'
    )


def error_html(text: str) -> str:
    """Short red error message (used instead of a traceback)."""
    return (
        '<div style="border-left:4px solid #e5484d;background:#e5484d22;color:#e5484d;'
        f'padding:6px 10px;margin:4px 0;border-radius:3px"><b>academicflow:</b> {esc(text)}</div>'
    )


def _issue_item(issue: Any, text: str | None) -> str:
    sev = getattr(issue, "severity", "warning")
    color = _COLORS.get(sev, _COLORS["warning"])
    snippet = ""
    start, end = getattr(issue, "start", 0), getattr(issue, "end", 0)
    if text and end > start:
        frag = text[start:end]
        if len(frag) > 80:
            frag = frag[:77] + "..."
        snippet = (
            f' <code style="background:{color}22;padding:0 3px;border-radius:2px">'
            f"{esc(frag)}</code>"
        )
    suggestion = getattr(issue, "suggestion", None)
    hint = f'<div style="opacity:.8">&#8594; {esc(suggestion)}</div>' if suggestion else ""
    return (
        f'<li style="margin:4px 0;padding-left:6px;border-left:3px solid {color};list-style:none">'
        f'<span style="color:{color};font-weight:600;font-size:.85em">{esc(sev.upper())}</span> '
        f'<span style="opacity:.7;font-size:.85em">{esc(getattr(issue, "rule", ""))}</span>'
        f"{snippet}<div>{esc(getattr(issue, 'message', ''))}</div>{hint}</li>"
    )


def issue_panel(
    issues: list[Any], text: str | None = None, title: str = "Style issues", open_: bool = False
) -> str:
    """Collapsible ``<details>`` panel listing issues.

    Args:
        issues: ``Issue`` objects.
        text: The checked text, used to show the flagged snippet.
        title: Summary label.
        open_: Whether the panel starts expanded.

    Returns:
        HTML string.
    """
    if not issues:
        return message(f"{title}: no issues found.", "info")
    items = "".join(_issue_item(i, text) for i in issues)
    return (
        f'<details{" open" if open_ else ""} style="margin:6px 0">'
        f'<summary style="cursor:pointer">{esc(title)}: '
        f"{_counts_text(severity_counts(issues))}</summary>"
        f'<ul style="margin:4px 0;padding-left:8px">{items}</ul></details>'
    )


def grouped_issue_panel(groups: list[tuple[str, list[Any], str | None]]) -> str:
    """Issues grouped by section, with severity counts per group and in total.

    Args:
        groups: ``(label, issues, text)`` triples; ``text`` may be ``None``.

    Returns:
        HTML string, or an "all clear" message when there are no issues.
    """
    all_issues = [i for _, issues, _ in groups for i in issues]
    if not all_issues:
        return message("No issues found.", "info")
    head = (
        f'<div style="margin:4px 0;font-weight:600">{len(all_issues)} issues: '
        f"{_counts_text(severity_counts(all_issues))}</div>"
    )
    blocks = [
        issue_panel(issues, text, title=label, open_=True)
        for label, issues, text in groups
        if issues
    ]
    return head + "".join(blocks)


def keyword_chips(keywords: list[tuple[str, float]]) -> str:
    """Render keywords as small chips."""
    if not keywords:
        return ""
    chips = "".join(
        f'<span style="display:inline-block;margin:2px 4px 2px 0;padding:1px 8px;'
        f'border:1px solid #8884;border-radius:10px" title="score {score:.2f}">{esc(word)}</span>'
        for word, score in keywords
    )
    return f'<div style="margin:6px 0"><b>Top keywords</b><div>{chips}</div></div>'


def stats_table(stats: Any, title: str = "Text statistics") -> str:
    """HTML table for a ``TextStats`` object."""
    rows = [
        ("Words", f"{stats.word_count:,}"),
        ("Sentences", f"{stats.sentence_count:,}"),
        ("Reading time", f"{stats.reading_time_min:.1f} min"),
        ("Flesch reading ease", f"{stats.flesch_reading_ease:.1f}"),
        ("Flesch-Kincaid grade", f"{stats.flesch_kincaid_grade:.1f}"),
        ("Avg. sentence length", f"{stats.avg_sentence_length:.1f} words"),
        ("Passive sentences", f"{stats.passive_ratio * 100:.0f}%"),
    ]
    body = "".join(
        f'<tr><td style="padding:2px 14px 2px 0;opacity:.8">{esc(k)}</td>'
        f'<td style="padding:2px 0;font-weight:600">{esc(v)}</td></tr>'
        for k, v in rows
    )
    return (
        f'<div style="margin:6px 0"><b>{esc(title)}</b>'
        f'<table style="border-collapse:collapse;margin-top:4px">{body}</table></div>'
    )


def highlight_passive(text: str, issues: list[Any]) -> str:
    """Return ``text`` as HTML with each passive-voice span wrapped in ``<mark>``."""
    spans = sorted(
        (i.start, i.end) for i in issues if getattr(i, "end", 0) > getattr(i, "start", 0)
    )
    out, pos = [], 0
    for start, end in spans:
        if start < pos:
            continue
        out.append(esc(text[pos:start]))
        out.append(
            '<mark style="background:#f5a52455;color:inherit;border-radius:2px">'
            f"{esc(text[start:end])}</mark>"
        )
        pos = end
    out.append(esc(text[pos:]))
    return (
        '<div style="white-space:pre-wrap;margin:4px 0;padding:6px 10px;border:1px solid #8884;'
        f'border-radius:3px">{"".join(out)}</div>'
    )
