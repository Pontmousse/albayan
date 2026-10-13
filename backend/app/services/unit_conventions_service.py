"""Article-owned unit conventions; Burhan remains the catalogue authority."""

from __future__ import annotations

from typing import Any, Mapping

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.article import Article
from app.schemas.unit_conventions import UnitConventions


def validated_unit_conventions(value: Any) -> dict[str, Any]:
    """Return a deep typed, JSON-safe copy without adding omitted custom names."""
    return UnitConventions.model_validate(value).model_dump(
        mode="json", exclude_none=True
    )


def get_unit_conventions(article: Article) -> dict[str, Any]:
    return validated_unit_conventions(article.unit_conventions or {})


def validate_registry_membership(conventions: Mapping[str, Any]) -> None:
    """Use Burhan's live registry; never replicate its unit catalogue here.

    Empty resets work even when Burhan is offline. Fail closed for nonempty
    conventions so an unknown override or shadowed custom identity is never
    persisted as article state.
    """
    overrides = conventions.get("overrides", {})
    custom_units = conventions.get("custom_units", {})
    if not overrides and not custom_units:
        return

    base = settings.burhan_url.rstrip("/")
    if not base:
        raise HTTPException(
            status_code=503,
            detail={"code": "unit_registry_unavailable", "message": "تعذّر التحقق من سجل الوحدات."},
        )
    # Shared trusted headers implement the same machine-authentication contract
    # as POST /convert, including correlation/tracing metadata.
    from app.services.burhan_client import _burhan_headers

    try:
        with httpx.Client(base_url=base, timeout=8.0, headers=_burhan_headers()) as client:
            response = client.get("/unit-registry")
            response.raise_for_status()
            body = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"code": "unit_registry_unavailable", "message": "تعذّر التحقق من سجل الوحدات."},
        ) from exc

    if not isinstance(body, dict) or not isinstance(body.get("units"), dict):
        raise HTTPException(
            status_code=503,
            detail={"code": "unit_registry_unavailable", "message": "استجابة سجل الوحدات غير صالحة."},
        )
    registered = body["units"]
    if any(token not in registered for token in overrides):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_unit_conventions", "message": "لا يمكن تخصيص وحدة غير مسجلة."},
        )
    if any(token in registered for token in custom_units):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_unit_conventions", "message": "لا يمكن استبدال وحدة مسجلة بوحدة مخصصة."},
        )


def replace_unit_conventions(
    article: Article, conventions: Mapping[str, Any]
) -> dict[str, Any]:
    result = validated_unit_conventions(dict(conventions))
    article.unit_conventions = result
    return validated_unit_conventions(result)
