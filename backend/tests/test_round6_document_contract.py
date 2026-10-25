"""Round 6 candidate contract: canonical names, unchanged operation strings."""
import re
from pathlib import Path

from app.schemas.document import DocumentContractModel, DocumentCommand
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_COMMAND_OPS = frozenset({
    "insert_text_block", "replace_text_block", "remove_block", "move_block",
    "insert_figure", "update_figure", "update_float_meta",
    "insert_bibliography", "update_document_meta",
    "insert_reference", "update_reference", "remove_reference", "move_reference",
    "insert_inline_token", "replace_inline_token", "remove_inline_token",
    "insert_list", "insert_list_item", "replace_list_item", "remove_list_item",
    "move_list_item", "insert_table", "replace_table_cell", "insert_table_row",
    "remove_table_row", "move_table_row", "insert_table_column",
    "remove_table_column", "move_table_column",
})


def test_public_typed_document_command_union_preserves_exact_operations():
    backend = (ROOT / "backend/app/schemas/document.py").read_text()
    mcp = (ROOT / "mcp_server/src/albayan_mcp/schemas/document.py").read_text()
    pattern = r'op:\\s*Literal\\[\"([^\"]+)\"\\]'
    for source in [backend, mcp]:
        assert set(re.findall(pattern, source)) == EXPECTED_COMMAND_OPS
        assert "Document2ContractModel" not in source
        assert 'node_type: Literal["MathObject"]' in source
        assert "extra=\"forbid\"" in source
        assert "strict=True" in source
    assert DocumentContractModel.model_config["strict"] is True
    assert TypeAdapter(DocumentCommand).json_schema()["discriminator"]["propertyName"] == "op"


def test_normal_mcp_tool_descriptions_expose_canonical_vocabulary():
    files = [
        "mcp_server/src/albayan_mcp/tools/drafts.py",
        "mcp_server/src/albayan_mcp/tools/articles.py",
        "mcp_server/src/albayan_mcp/tools/equations.py",
        "mcp_server/src/albayan_mcp/server.py",
    ]
    for file in files:
        assert "Document2" not in (ROOT / file).read_text(), file

    dev_suite = (ROOT / "dev_mcp_server/src/albayan_dev_mcp/investigation.py").read_text()
    backend_diag = (ROOT / "backend/app/services/equation_diagnostic_service.py").read_text()
    assert '"document-roundtrip"' in dev_suite
    assert '"document_command"' in dev_suite
    assert '"document_command"' in backend_diag
    assert "document2-roundtrip" not in dev_suite
    assert "document2_command" not in backend_diag


def test_old_python_document_schema_modules_and_registry_are_retired():
    for path in (
        "backend/app/schemas/document2.py",
        "mcp_server/src/albayan_mcp/schemas/document2.py",
        "backend/app/document2_registry.py",
    ):
        assert not (ROOT / path).exists(), path
