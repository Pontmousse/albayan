from __future__ import annotations

import hashlib
import json
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


def test_coverage_manifest_has_145_distinct_namespaced_cases() -> None:
    path = _ROOT / "docs" / "development" / "document-migration-coverage-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["case_count"] == 145
    assert len(manifest["cases"]) == 145
    namespaced = [item["case_id"] for item in manifest["cases"]]
    assert len(set(namespaced)) == 145
    assert {"v1:MTH-01", "addendumA:MTH-01"} <= set(namespaced)
    assert manifest["local_id_collisions"] == [
        "MTH-01", "MTH-02", "MTH-03", "MTH-04", "MTH-05", "MTH-06"
    ]
    assert all(item["observed_status"] == "not_run" for item in manifest["cases"])
    for namespace, (spec_file, (_, count)) in {
        "v1": ("document-migration-frozen-acceptance-v1.md", _FROZEN["document-migration-frozen-acceptance-v1.md"]),
        "addendumA": ("document-migration-frozen-acceptance-addendum-a.md", _FROZEN["document-migration-frozen-acceptance-addendum-a.md"]),
    }.items():
        raw = (_ROOT / "docs" / "proposals" / spec_file).read_bytes()
        ids = re.findall(rb"^\| ([A-Z]+-\d{2}) \|", raw, re.MULTILINE)
        expected = {namespace + ":" + name.decode() for name in ids}
        assert len(expected) == count
        assert expected == {name for name in namespaced if name.startswith(namespace + ":")}
