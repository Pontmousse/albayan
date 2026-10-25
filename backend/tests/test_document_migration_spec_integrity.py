"""Immutable owner-approved Round 0 acceptance oracle fingerprints.

This is intentionally independent from focused equation/document regression suites.
"""
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN_SHA256 = {
    "document-migration-frozen-acceptance-v1.md":
        "6457a3d1abe43ba4cde16bd9b287d097978671db5ba3657c28099b1c6e26ca8e",
    "document-migration-frozen-acceptance-addendum-a.md":
        "dd96dae156fd2d026ca75ca390bb8c63104bdb938ecea7b6b0359dfbe905591e",
}


def test_frozen_migration_acceptance_documents_are_byte_identical_to_approved_hashes():
    for file_name, expected in FROZEN_SHA256.items():
        path = ROOT / "docs/proposals" / file_name
        assert path.is_file(), f"Missing frozen acceptance oracle: {file_name}"
        assert sha256(path.read_bytes()).hexdigest() == expected, (
            f"Forbidden mutation of frozen acceptance oracle: {file_name}"
        )
