"""Style checker: informal language, repetition, terminology consistency, section rules.

Owner: Member 2.
"""

from __future__ import annotations

from academicflow.style.profiles import load_profile
from academicflow.style.rules import check
from academicflow.style.terminology import check_document

__all__ = ["load_profile", "check", "check_document"]
