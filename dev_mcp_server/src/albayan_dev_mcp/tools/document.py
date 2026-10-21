from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from albayan_dev_mcp.document import (
    DOCUMENT_OPERATIONS,
    DocumentDiagnosticClient,
    compare_document_reports,
)
from albayan_dev_mcp.settings import Settings
from albayan_dev_mcp.trace import TraceSource

Operation = Literal[
    "diagnose_contract", "normalize", "outline", "references",
    "reference_index", "export", "diff", "apply_command",
    "diagnose_math_object", "project_math_object_english",
]


def register_document_tools(
    server: MCPServer,
    *,
    settings: Settings,
    trace_source: TraceSource | None = None,
) -> None:
    def client() -> DocumentDiagnosticClient:
        return DocumentDiagnosticClient(settings, trace_source=trace_source)

    @server.tool(
        name="dev_document_contract_snapshot",
        title="Inspect real development document worker contract",
        description=(
            "Read the authenticated, stateless BuTeX worker operation map and reported runtime "
            "provenance through the DEV_MODE-gated Al-Bayan diagnostic endpoint. Runtime env "
            "identifiers are advisory, not independently verified build attestations."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_document_contract_snapshot(
        trace_id: Annotated[
            str | None, Field(description="Optional correlation identifier for the diagnostic only."),
        ] = None,
    ) -> dict[str, Any]:
        report = await client().inspect(operation="diagnose_contract", payload={}, trace_id=trace_id)
        if report.get("status") == "passed":
            contract = report.get("data")
            if isinstance(contract, dict):
                report["provenance_verified"] = False
                report["human_action"] = (
                    "Attest the running worker commit/package digest against CI and both migration branches "
                    "before treating this as a compatible baseline."
                )
        return report

    @server.tool(
        name="dev_document_inspect",
        title="Inspect a stateless document operation",
        description=(
            "Run one bounded synthetic fixture through the real authenticated BuTeX worker via "
            "the DEV_MODE-gated Al-Bayan backend. This does not save a document or change article state. "
            "No arbitrary target URL, worker method or database mutation is available."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_document_inspect(
        operation: Annotated[Operation, Field(description="Allowlisted stateless worker operation.")],
        payload: Annotated[
            dict[str, Any],
            Field(description="Bounded synthetic document/command/math fixture body, maximum 128 KiB."),
        ],
        trace_id: Annotated[
            str | None, Field(description="Optional validated diagnostic correlation identifier."),
        ] = None,
    ) -> dict[str, Any]:
        return await client().inspect(operation=operation, payload=payload, trace_id=trace_id)

    @server.tool(
        name="dev_document_compare",
        title="Compare captured document baseline and candidate outputs",
        description=(
            "Compare two previously captured successful document operation reports with exact "
            "JSON semantics; report bounded differences, no silent normalization. This does not "
            "check out source branches or compare Burhan model tiers. Build provenance must be "
            "independently attested."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False),
    )
    async def dev_document_compare(
        baseline: Annotated[dict[str, Any], Field(description="Prior successful baseline diagnostic report.")],
        candidate: Annotated[dict[str, Any], Field(description="Prior successful candidate diagnostic report.")],
    ) -> dict[str, Any]:
        return compare_document_reports(baseline, candidate)
