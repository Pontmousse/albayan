# User-facing MCP: development and client operations

[← Development index](README.md) · [MCP system architecture](../architecture/mcp.md)

The normal `mcp_server/` is the **end-user authoring interface**, not the developer diagnostics MCP. It is a thin authenticated HTTP adapter over FastAPI; only FastAPI decides identity, scopes, manuscript ownership and whether a workflow action is human-only.

## Deployed entrypoints

| Environment | MCP endpoint | Application API |
| --- | --- | --- |
| Development | <https://mcp.dev.albayan-journal.org/mcp> | <https://api.dev.albayan-journal.org> |
| Production | <https://mcp.albayan-journal.org/mcp> | <https://api.albayan-journal.org> |

The endpoints were verified as configured Railway custom domains; **successful connection or a particular OAuth behavior must be tested separately**. See [Railway infrastructure](railway-infrastructure.md).

## Authentication/connection model

- Remote Streamable HTTP clients use the supported OAuth flow with Clerk. Where enabled, a scoped personal `alb_...` token can be sent via Bearer to the MCP service, which forwards it to FastAPI for validation.
- Local stdio is a contributor/test path rather than the default public onboarding path.
- The server's declared package version lives in [`mcp_server/pyproject.toml`](../../mcp_server/pyproject.toml); a client UI's cached tool list is **not proof** of the currently deployed server version.
- Never print raw Bearer tokens, cookies, private article content or credential-bearing URLs into logs or PR descriptions.
- To diagnose transport, check the environment-specific MCP resource metadata and OAuth challenge, then verify an authenticated tool call in the chosen client. Do not infer successful authorization from an anonymous `GET` alone.

## Authoring flow for AI agents

1. `get_my_profile` / article reads establish authorized identity and accessible manuscript.
2. `get_draft_outline`, `get_draft_blocks` and reference/equation discovery return stable document identifiers and the current revision.
3. `get_math_authoring_capabilities` and, if relevant, `get_unit_registry` constrain canonical LaTeX.
4. `apply_draft_command` sends **one** typed Document2 command with observed `base_revision` and a unique logical `command_id`.
5. On `revision_conflict`, **re-read** the draft; do not blindly replay using stale IDs or reuse the same command ID for a different payload.
6. Compile explicitly only when needed, then retrieve status/PDF through the normal tools. Final submission/review/editorial decisions remain human-only.

Actual tool registration and request schemas: [`mcp_server/src/albayan_mcp/server.py`](../../mcp_server/src/albayan_mcp/server.py), [tool modules](../../mcp_server/src/albayan_mcp/tools/) and [FastAPI actor policy](../../backend/app/core/actor.py).

## Developer verification

To validate a change: inspect the typed tool surfaced by the **normal MCP client**, exercise against a **dedicated development test draft**, inspect FastAPI revision state, and use [Playwright MCP](playwright-mcp.md) to verify the browser. Supplement with [Developer MCP](developer-mcp.md) traces. Testing internal HTTP endpoints alone does **not** verify the user-facing MCP schema or transport.

For an isolated file/transport diagnostic (not an authoring operation), see [transport probe](mcp-transport-probe.md) and [historical findings](../archive/2026-mcp-file-transport-findings.md). An experimental transport probe should not be exposed as standard product functionality.
