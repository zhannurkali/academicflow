import pytest

from academicflow.style import check, check_document, load_profile


@pytest.mark.parametrize("name", ["apa", "ieee", "nature"])
def test_builtin_profiles_load(name):
    profile = load_profile(name)
    assert profile["citation_style"] == name


def test_unknown_profile_raises():
    with pytest.raises(ValueError):
        load_profile("no-such-profile")


def test_check_returns_list():
    assert isinstance(check("Some text."), list)
    assert isinstance(check_document({"intro": "Some text."}), list)
