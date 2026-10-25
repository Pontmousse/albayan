"""Round 3 guard: Al-Bayan must not depend on the retired first-generation BuTeX editor."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_active_document2_consumers_do_not_import_retired_package_entrypoints():
    editor = (ROOT / "frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx").read_text()
    preview = (ROOT / "frontend/src/components/dashboard/document-frozen-preview.tsx").read_text()
    worker = (ROOT / "backend/app/services/butex_worker_client.py").read_text()
    mcp_schema = ROOT / "mcp_server/src/albayan_mcp/schemas/document2.py"

    assert '@drghaliasri/butex/document2' in editor
    assert '@drghaliasri/butex/react-document2' in editor
    assert '@drghaliasri/butex/document2' in preview
    assert '@drghaliasri/butex/react-document2-preview' in preview
    for name in ('@drghaliasri/butex/document"', "@drghaliasri/butex/document'",
                 '@drghaliasri/butex/react-document"', "@drghaliasri/butex/react-document'"):
        assert name not in editor
        assert name not in preview

    for endpoint in (
        "/v1/document2/normalize",
        "/v1/document2/outline",
        "/v1/document2/references",
        "/v1/document2/reference-index",
        "/v1/document2/export",
        "/v1/document2/diff",
        "/v1/document2/commands",
        "/v1/document2/math-object/english",
    ):
        assert endpoint in worker
    assert mcp_schema.is_file()
