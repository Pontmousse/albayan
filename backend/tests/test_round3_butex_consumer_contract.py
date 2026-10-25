"""Round 3 guard: Al-Bayan must not depend on the retired first-generation BuTeX editor."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_round5_canonical_consumers_do_not_import_retired_entries():
    editor = (ROOT / "frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx").read_text()
    preview = (ROOT / "frontend/src/components/dashboard/document-frozen-preview.tsx").read_text()
    worker = (ROOT / "backend/app/services/butex_worker_client.py").read_text()
    mcp_schema = ROOT / "mcp_server/src/albayan_mcp/schemas/document2.py"

    assert '@drghaliasri/butex/document"' in editor
    assert '@drghaliasri/butex/react-document"' in editor
    assert '@drghaliasri/butex/document"' in preview
    assert '@drghaliasri/butex/react-document-preview"' in preview
    for name in ("@drghaliasri/butex/document2", "@drghaliasri/butex/react-document2"):
        assert name not in editor
        assert name not in preview

    for endpoint in (
        "/v1/document/normalize",
        "/v1/document/outline",
        "/v1/document/references",
        "/v1/document/reference-index",
        "/v1/document/export",
        "/v1/document/diff",
        "/v1/document/commands",
        "/v1/document/math-object/english",
    ):
        assert endpoint in worker
    assert mcp_schema.is_file()
