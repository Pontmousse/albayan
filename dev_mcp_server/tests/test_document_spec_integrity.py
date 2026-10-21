from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_FROZEN = {
    "document-migration-frozen-acceptance-v1.md": (
        "6457a3d1abe43ba4cde16bd9b287d097978671db5ba3657c28099b1c6e26ca8e", 66
    ),
    "document-migration-frozen-acceptance-addendum-a.md": (
        "dd96dae156fd2d026ca75ca390bb8c63104bdb938ecea7b6b0359dfbe905591e", 79
    ),
}


@pytest.mark.parametrize("name", list(_FROZEN))
def test_immutable_acceptance_contract_matches_phase_zero_freeze(name: str) -> None:
    expected_hash, expected_cases = _FROZEN[name]
    raw = (_ROOT / "docs" / "proposals" / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_hash
    ids = re.findall(rb"^\| ([A-Z]+-\d{2}) \|", raw, re.MULTILINE)
    assert len(ids) == expected_cases
    assert len(set(ids)) == expected_cases
