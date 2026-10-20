# Al-Bayan product MCP

The user-facing Model Context Protocol adapter is located in this directory. It runs over Streamable HTTP for remote clients (and supports local stdio for contributors) and **delegates all article authorization and durable state to FastAPI**.

- [Current MCP architecture](../docs/architecture/mcp.md)
- [Developer and client operation guide](../docs/development/mcp-operations.md)
- [Normal MCP + equation verification](../docs/development/math-verification.md)
- [Project development environment](../docs/development/railway-infrastructure.md)
- [Historical file-transport investigation](../docs/archive/2026-mcp-file-transport-findings.md)

There is also a **separate** Developer MCP (`../dev_mcp_server/`) and a Railway-hosted Playwright MCP for development browser testing; neither is the end-user authoring API.

## Local contributor entrypoint

Configure `.env` from [`.env.example`](.env.example), install the package per [`pyproject.toml`](pyproject.toml), and use the `albayan_mcp` module's documented transport options. The remote public endpoint is `https://mcp.albayan-journal.org/mcp` and development uses `https://mcp.dev.albayan-journal.org/mcp`. Never commit live tokens or point test scripts to production.

Prior long-form implementation plans and dated deployment walkthroughs were removed from the active tree after being superseded. Git history retains them if historical reasoning is needed.
