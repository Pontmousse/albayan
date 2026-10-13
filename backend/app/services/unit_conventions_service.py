"""Article-owned unit conventions; never copy or store Burhan's global catalogue."""

from __future__ import annotations

from typing import Any, Mapping

from app.models.article import Article
from app.schemas.unit_conventions import UnitConventions


def validated_unit_conventions(value: Any) -> dict[str, Any]:
    """Return a deep JSON-safe, typed copy (including empty defaults)."""
    return UnitConventions.model_validate(value).model_dump(mode="json")


def get_unit_conventions(article: Article) -> dict[str, Any]:
    # Existing/in-memory articles may not have been assigned this field yet.
    return validated_unit_conventions(article.unit_conventions or {})


def replace_unit_conventions(
    article: Article, conventions: Mapping[str, Any]
) -> dict[str, Any]:
    result = validated_unit_conventions(dict(conventions))
    article.unit_conventions = result
    return validated_unit_conventions(result)
