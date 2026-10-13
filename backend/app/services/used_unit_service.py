"""Structured used-unit inventory and revision-safe convention application.

Unit identity is only an exact canonical source_latex on a structured command
node. Arabic display strings and bare variables are never scanned as units.
"""

from __future__ import annotations

import re
import uuid
from collections import Counter
from copy import deepcopy
from typing import Any, Mapping

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.actor import Actor
from app.models.enums import DraftRevisionReason
from app.services import (
    article_draft_service,
    burhan_client,
    butex_worker_client,
    equation_mapping_service,
    equation_projection_service,
    unit_conventions_service,
    burhan_reverse_client,
)

_UNIT_SOURCE = re.compile(r"\\mathsf\{([A-Za-z][A-Za-z0-9]*)\}\Z")


def _walk_unit_tokens(node: Any):
    """Walk structured AST only; no raw LaTeX/Arabic-text regex scanning."""
    if isinstance(node, dict):
        if node.get("node_type") == "CommandObject":
            source = node.get("source_latex")
            match = _UNIT_SOURCE.fullmatch(source) if isinstance(source, str) else None
            if match:
                yield match.group(1)
        for child in node.values():
            if isinstance(child, (dict, list)):
                yield from _walk_unit_tokens(child)
    elif isinstance(node, list):
        for child in node:
            yield from _walk_unit_tokens(child)


def used_unit_counts(document: Mapping[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for candidate in equation_projection_service._iter_blocks(document.get("blocks")):
        math = candidate.get("math_object")
        if isinstance(math, dict) and math.get("node_type") == "MathObject":
            counts.update(_walk_unit_tokens(math))
    return counts


def _effective_display(
    token: str, conventions: Mapping[str, Any], registry: Mapping[str, Any]
) -> tuple[str, str, str]:
    custom = conventions.get("custom_units", {}).get(token)
    if custom is not None:
        return custom["display"], "article_custom", "custom"
    overridden = conventions.get("overrides", {}).get(token)
    if overridden is not None:
        return overridden, "article_override", "registry"
    entry = registry.get("units", {}).get(token)
    if entry is not None:
        return entry["default_display"], "registry_default", "registry"
    return token, "unknown", "unknown"


def inventory(
    document: Mapping[str, Any],
    conventions: Mapping[str, Any],
    registry: Mapping[str, Any],
    *,
    revision_number: int,
) -> dict[str, Any]:
    counts = used_unit_counts(document)
    rows = []
    for token, count in sorted(counts.items()):
        entry = registry.get("units", {}).get(token)
        display, source, status = _effective_display(token, conventions, registry)
        rows.append({
            "token": token,
            "usage_count": count,
            "status": status,
            "display": display,
            "source": source,
            "name": entry.get("name_en") if entry else None,
            "name_ar": entry.get("name_ar") if entry else None,
            "default_display": entry.get("default_display") if entry else None,
            "alternatives": list(entry.get("alternatives", [])) if entry else [],
        })
    return {
        "revision_number": revision_number,
        "unit_conventions": unit_conventions_service.validated_unit_conventions(conventions),
        "used_units": rows,
    }


def get_inventory(db: Session, article_id: uuid.UUID, actor: Actor) -> dict[str, Any]:
    article = article_draft_service.assert_author(db, article_id, actor)
    revision = article_draft_service.get_current_revision(db, article)
    return inventory(
        article_draft_service.read_document(revision),
        unit_conventions_service.get_unit_conventions(article),
        unit_conventions_service.get_unit_registry(),
        revision_number=revision.revision_number,
    )


def _changed_units(
    counts: Counter[str],
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> set[str]:
    return {
        token for token in counts
        if _effective_display(token, before, registry)[0]
        != _effective_display(token, after, registry)[0]
    }


def _rewrite_affected_equations(
    document: dict[str, Any],
    changed: set[str],
    mappings: Mapping[str, str],
    conventions: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, str], list[str]]:
    if not changed:
        return document, dict(mappings), []

    result = deepcopy(document)
    updated_mappings = dict(mappings)
    reverse, _ = equation_mapping_service.invert_unique_equation_mappings(mappings)
    updated_ids: list[str] = []

    # Each affected *token* is replaced through the normal Document2 worker,
    # so inline sidecars, source, math_object and offsets stay consistent.
    for candidate in equation_projection_service._iter_blocks(document.get("blocks")):
        math = candidate.get("math_object")
        if not isinstance(math, dict) or not changed.intersection(_walk_unit_tokens(math)):
            continue
        english_ast = butex_worker_client.project_math_object_to_english(math)
        canonical, warnings = burhan_reverse_client.project_math_object_to_canonical_latex(
            english_ast, variable_mapping=reverse
        )
        if warnings:
            # Rewriting an equation with unresolved or ambiguous variables risks
            # altering the author's work. Fail closed instead.
            raise HTTPException(
                status_code=409,
                detail={"code": "unit_rewrite_unsafe",
                        "message": "تعذّر تحديث إحدى المعادلات دون التأثير على رموز أخرى؛ راجع المعادلة أولاً."},
            )
        display = equation_projection_service._math_object_display(math, candidate.get("source", ""))
        label = equation_projection_service._label(math)
        strict, discovered = burhan_client.convert_canonical_latex_to_math_object(
            canonical,
            display=display,
            label=label,
            mappings=updated_mappings,
            unit_conventions=conventions,
        )
        try:
            updated_mappings = equation_mapping_service.merged_equation_mappings(
                updated_mappings, discovered
            )
        except equation_mapping_service.EquationMappingConflict as exc:
            raise article_draft_service._mapping_conflict() from exc
        result = butex_worker_client.apply_document_command(
            result,
            {"op": "replace_inline_token", "field_id": candidate["field_id"],
             "token_id": candidate["token_id"], "token": strict},
        )
        updated_ids.append(candidate["block_id"])
    return result, updated_mappings, sorted(set(updated_ids))


def apply_conventions(
    db: Session, article_id: uuid.UUID, actor: Actor,
    *, base_revision: int, conventions: Mapping[str, Any],
) -> dict[str, Any]:
    article = article_draft_service.assert_editable_author(db, article_id, actor)
    current = article_draft_service.get_current_revision(db, article)
    if base_revision != current.revision_number:
        raise article_draft_service._conflict(current.revision_number)

    before = unit_conventions_service.get_unit_conventions(article)
    after = unit_conventions_service.validated_unit_conventions(conventions)
    registry = unit_conventions_service.get_unit_registry()
    unit_conventions_service.validate_registry_membership(after, registry)
    document = article_draft_service.read_document(current)
    counts = used_unit_counts(document)

    # Prevent silent loss of the definition for still-used custom identities.
    removed = before["custom_units"].keys() - after["custom_units"].keys()
    if any(token in counts for token in removed):
        raise HTTPException(
            status_code=409,
            detail={"code": "used_custom_unit",
                    "message": "لا يمكن حذف وحدة مخصصة مستخدمة في المعادلات؛ عدّل المعادلات أولاً."},
        )

    if after == before:
        return {
            **article_draft_service.revision_response(current, document),
            "affected_block_ids": [],
            "used_units": inventory(document, before, registry,
                                    revision_number=current.revision_number)["used_units"],
        }

    changed = _changed_units(counts, before, after, registry)
    mappings = equation_mapping_service.get_equation_mappings(article)
    updated_document, updated_mappings, affected = _rewrite_affected_equations(
        document, changed, mappings, after
    )
    revision, canonical, affected = article_draft_service.create_revision(
        db,
        article_id=article_id,
        actor=actor,
        base_revision=base_revision,
        document=updated_document,
        reason=DraftRevisionReason.UNIT_CONVENTIONS,
        force_revision=True,
        affected_block_ids=affected,
        expected_equation_mappings=mappings,
        equation_mappings=updated_mappings,
        expected_unit_conventions=before,
        updated_unit_conventions=after,
    )
    return {
        **article_draft_service.revision_response(revision, canonical),
        "affected_block_ids": affected,
        "used_units": inventory(canonical, after, registry,
                                revision_number=revision.revision_number)["used_units"],
    }
