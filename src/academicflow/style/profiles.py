"""Loading, merging, and validating academic venue profiles."""

from __future__ import annotations

from copy import deepcopy
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

BUILTIN_PROFILES = ("apa", "ieee", "nature")

DEFAULT_PROFILE: dict[str, Any] = {
    "name": "default",
    "citation_style": "apa",
    "allow_first_person": True,
    "allow_contractions": False,
    "max_sentence_words": 40,
    "abstract_max_words": 250,
    "section_rules": {
        "abstract": {"forbid_citations": True},
        "methods": {"tense": "past"},
        "results": {"tense": "past"},
        "conclusion": {"forbid_citations": False},
    },
    "preferred_spelling": "us",
    "disabled_rules": [],
}

_ALLOWED_TOP_LEVEL = set(DEFAULT_PROFILE)
_ALLOWED_SECTION_KEYS = {"max_words", "forbid_citations", "tense"}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge dictionaries without mutating either input."""
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _read_profile(name_or_path: str) -> tuple[str, str]:
    """Return (source label, YAML text) for a built-in profile or a path."""
    name = name_or_path.strip()
    if not name:
        raise ValueError("Profile name or YAML path must not be empty.")

    builtin = name.lower()
    if builtin in BUILTIN_PROFILES:
        try:
            text = (
                resources.files("academicflow.profiles")
                .joinpath(f"{builtin}.yaml")
                .read_text(encoding="utf-8")
            )
        except (FileNotFoundError, ModuleNotFoundError, AttributeError) as exc:
            raise ValueError(f"Bundled profile {builtin!r} could not be loaded.") from exc
        return builtin, text

    path = Path(name).expanduser()
    if path.is_file():
        try:
            return str(path), path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Could not read profile file {str(path)!r}: {exc}") from exc

    raise ValueError(
        f"Unknown profile {name_or_path!r}. Use one of {BUILTIN_PROFILES} "
        "or provide a path to a YAML file."
    )


def _validate_profile(data: Any, source: str) -> dict[str, Any]:
    """Validate the user-supplied portion of a parsed YAML profile."""
    if not isinstance(data, dict):
        raise ValueError(f"Profile {source!r} must contain a YAML mapping at its top level.")

    unknown = sorted(set(data) - _ALLOWED_TOP_LEVEL)
    if unknown:
        raise ValueError(f"Profile {source!r} contains unknown key(s): {', '.join(unknown)}.")

    if "name" in data and (not isinstance(data["name"], str) or not data["name"].strip()):
        raise ValueError("Profile key 'name' must be a non-empty string.")
    if data.get("citation_style", "apa") not in BUILTIN_PROFILES:
        raise ValueError("'citation_style' must be one of: apa, ieee, nature.")

    for key in ("allow_first_person", "allow_contractions"):
        if key in data and not isinstance(data[key], bool):
            raise ValueError(f"Profile key {key!r} must be a boolean.")

    for key in ("max_sentence_words", "abstract_max_words"):
        value = data.get(key)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 1
        ):
            raise ValueError(f"Profile key {key!r} must be a positive integer.")

    if "preferred_spelling" in data and data["preferred_spelling"] not in ("us", "uk"):
        raise ValueError("'preferred_spelling' must be either 'us' or 'uk'.")

    disabled = data.get("disabled_rules", [])
    if not isinstance(disabled, list) or any(not isinstance(item, str) for item in disabled):
        raise ValueError("'disabled_rules' must be a list of rule-name strings.")

    section_rules = data.get("section_rules", {})
    if not isinstance(section_rules, dict):
        raise ValueError("'section_rules' must be a mapping of section names to rule settings.")
    for section, settings in section_rules.items():
        if not isinstance(section, str) or not section.strip():
            raise ValueError("Section-rule names must be non-empty strings.")
        if not isinstance(settings, dict):
            raise ValueError(f"Section rules for {section!r} must be a mapping.")
        unknown_section_keys = sorted(set(settings) - _ALLOWED_SECTION_KEYS)
        if unknown_section_keys:
            raise ValueError(
                f"Section {section!r} contains unknown key(s): "
                f"{', '.join(unknown_section_keys)}."
            )
        if "max_words" in settings:
            value = settings["max_words"]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"Section {section!r}: 'max_words' must be a positive integer.")
        if "forbid_citations" in settings and not isinstance(settings["forbid_citations"], bool):
            raise ValueError(f"Section {section!r}: 'forbid_citations' must be a boolean.")
        if "tense" in settings and settings["tense"] not in ("past", "any"):
            raise ValueError(f"Section {section!r}: 'tense' must be past or any.")

    return data


def load_profile(name_or_path: str) -> dict[str, Any]:
    """Load a built-in or custom YAML profile and merge it with defaults.

    Args:
        name_or_path: ``"apa"``, ``"ieee"``, ``"nature"`` or a filesystem path.

    Returns:
        A new dictionary containing every default and profile-specific setting.

    Raises:
        ValueError: If the profile is unknown, malformed, or contains invalid settings.
    """
    source, raw = _read_profile(name_or_path)
    try:
        parsed = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in profile {source!r}: {exc}") from exc

    validated = _validate_profile(parsed or {}, source)
    merged = _deep_merge(DEFAULT_PROFILE, validated)
    if source in BUILTIN_PROFILES and "name" not in validated:
        merged["name"] = source
    return merged
