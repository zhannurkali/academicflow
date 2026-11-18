"""Venue profiles (APA / IEEE / Nature presets) stored as YAML.

Owner: Member 2.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import yaml

BUILTIN_PROFILES = ("apa", "ieee", "nature")

DEFAULT_PROFILE: dict = {
    "name": "default",
    "citation_style": "apa",
    "allow_first_person": True,
    "allow_contractions": False,
    "max_sentence_words": 40,
    "abstract_max_words": 250,
    "section_rules": {},
    "preferred_spelling": "us",
    "disabled_rules": [],
}


def load_profile(name_or_path: str) -> dict:
    """Load a built-in profile by name or a custom profile from a YAML path.

    Args:
        name_or_path: ``"apa"``, ``"ieee"``, ``"nature"`` or a path to a YAML file.

    Returns:
        The profile dict merged over :data:`DEFAULT_PROFILE`.

    Raises:
        ValueError: If the name is unknown and no such file exists.

    TODO(member 2): validate keys, deep-merge section_rules.
    """
    key = name_or_path.lower()
    if key in BUILTIN_PROFILES:
        raw = resources.files("academicflow.profiles").joinpath(f"{key}.yaml").read_text("utf-8")
    elif Path(name_or_path).is_file():
        raw = Path(name_or_path).read_text("utf-8")
    else:
        raise ValueError(
            f"Unknown profile {name_or_path!r}. Use one of {BUILTIN_PROFILES} or a YAML path."
        )
    data = yaml.safe_load(raw) or {}
    return {**DEFAULT_PROFILE, **data}
