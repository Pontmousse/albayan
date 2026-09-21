import pytest

from app.models.article import Article
from app.services.equation_mapping_service import (
    EquationMappingConflict,
    get_equation_mappings,
    invert_unique_equation_mappings,
    merge_equation_mappings,
    replace_equation_mappings,
)


def _article(mappings=None) -> Article:
    article = Article()
    article.equation_mappings = mappings
    return article


def test_missing_mapping_state_behaves_as_empty_dict() -> None:
    article = _article(None)

    assert get_equation_mappings(article) == {}


def test_replace_mappings_stores_defensive_copy() -> None:
    article = _article({})
    supplied = {"x": "س"}

    result = replace_equation_mappings(article, supplied)
    supplied["x"] = "ص"
    result["x"] = "ع"

    assert get_equation_mappings(article) == {"x": "س"}


def test_merge_adds_new_variables_without_changing_existing_assignments() -> None:
    article = _article({"x": "س"})

    merged = merge_equation_mappings(article, {"x": "س", "y": "ص"})

    assert merged == {"x": "س", "y": "ص"}
    assert get_equation_mappings(article) == {"x": "س", "y": "ص"}


def test_merge_rejects_conflicting_existing_assignment_atomically() -> None:
    article = _article({"x": "س"})

    with pytest.raises(EquationMappingConflict) as exc_info:
        merge_equation_mappings(article, {"x": "ص", "y": "ع"})

    assert exc_info.value.english == "x"
    assert get_equation_mappings(article) == {"x": "س"}


def test_invert_unique_mappings_returns_reverse_dictionary() -> None:
    reverse, ambiguous = invert_unique_equation_mappings({"x": "س", "y": "ص"})

    assert reverse == {"س": "x", "ص": "y"}
    assert ambiguous == set()


def test_invert_unique_mappings_omits_ambiguous_arabic_values() -> None:
    reverse, ambiguous = invert_unique_equation_mappings(
        {"x": "س", "X": "س", "y": "ص"}
    )

    assert reverse == {"ص": "y"}
    assert ambiguous == {"س"}


@pytest.mark.parametrize(
    "mappings",
    [
        {"": "س"},
        {"x": ""},
        {" ": "س"},
        {"x": " "},
        {1: "س"},
        {"x": 1},
    ],
)
def test_mapping_helpers_reject_invalid_entries(mappings) -> None:
    article = _article({})

    with pytest.raises(ValueError):
        replace_equation_mappings(article, mappings)
