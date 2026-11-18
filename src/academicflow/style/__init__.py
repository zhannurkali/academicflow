"""Style checker: venue profiles, section-aware rules, and document consistency."""

from __future__ import annotations

from academicflow.style.profiles import load_profile
from academicflow.style.rules import check
from academicflow.style.terminology import check_document

__all__ = ["load_profile", "check", "check_document"]
