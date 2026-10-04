"""Keep canonical-v2 writes dormant until converter and editor retention are ready."""

from typing import Any

from fastapi import HTTPException


def reject_dormant_math_authoring(value: Any) -> None:
    """Reject reserved wire fields before an older consumer can discard them.

    Scan structured payloads only: LaTeX/text strings are never interpreted here.
    Presence (including an invalid/null value) matters for untyped document saves.
    This is deliberately a hard guard, not an activation environment switch.
    """
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            if {"authoring_profile", "canonical_atom", "canonical_command"}.intersection(item):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "math_authoring_profile_unavailable",
                        "message": "صيغة تأليف المعادلة المطلوبة غير متاحة حاليًا.",
                    },
                )
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
