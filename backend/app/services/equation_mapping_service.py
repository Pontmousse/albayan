from collections import Counter
from collections.abc import Mapping

from app.models.article import Article


class EquationMappingConflict(ValueError):
    def __init__(self, english: str, current_arabic: str, incoming_arabic: str) -> None:
        self.english = english
        self.current_arabic = current_arabic
        self.incoming_arabic = incoming_arabic
        super().__init__(
            f"Equation mapping conflict for {english!r}: "
            f"{current_arabic!r} != {incoming_arabic!r}"
        )


def _validated_copy(mappings: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for english, arabic in mappings.items():
        if not isinstance(english, str) or not english.strip():
            raise ValueError("Equation mapping keys must be non-empty strings")
        if not isinstance(arabic, str) or not arabic.strip():
            raise ValueError("Equation mapping values must be non-empty strings")
        result[english] = arabic
    return result


def get_equation_mappings(article: Article) -> dict[str, str]:
    """Return a defensive copy of the article's current English -> Arabic mappings."""
    raw = article.equation_mappings
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("Article equation mappings must be a JSON object")
    return _validated_copy(raw)


def replace_equation_mappings(
    article: Article, mappings: Mapping[str, str]
) -> dict[str, str]:
    """Replace the article mapping dictionary without committing the transaction."""
    next_mappings = _validated_copy(mappings)
    article.equation_mappings = next_mappings
    return dict(next_mappings)


def merge_equation_mappings(
    article: Article, discovered: Mapping[str, str]
) -> dict[str, str]:
    """Add newly discovered mappings while keeping existing assignments stable."""
    current = get_equation_mappings(article)
    incoming = _validated_copy(discovered)

    for english, arabic in incoming.items():
        existing = current.get(english)
        if existing is not None and existing != arabic:
            raise EquationMappingConflict(english, existing, arabic)

    merged = {**current, **incoming}
    article.equation_mappings = merged
    return dict(merged)


def invert_unique_equation_mappings(
    mappings: Mapping[str, str],
) -> tuple[dict[str, str], set[str]]:
    """Build a temporary Arabic -> English mapping, omitting ambiguous values."""
    normalized = _validated_copy(mappings)
    counts = Counter(normalized.values())
    ambiguous = {arabic for arabic, count in counts.items() if count > 1}
    reverse = {
        arabic: english
        for english, arabic in normalized.items()
        if arabic not in ambiguous
    }
    return reverse, ambiguous
