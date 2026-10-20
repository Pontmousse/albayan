# Development and diagnostics

Guidance for **working on Al-Bayan** rather than a description of the product architecture.

- [**Developer MCP — how to use it**](developer-mcp.md): discovery, restricted development-service access and debugging protocol.
- [**Investigation workflows**](investigation-workflows.md): named suites, report interpretation, browser-evidence requirements.
- [**Equation diagnostics**](equation-diagnostics.md): stage-level conversion tests and fixtures.
- [**Tracing**](tracing.md): `X-Trace-Id` and evidence boundaries.
- [**Developer MCP package README**](../../dev_mcp_server/README.md): concrete installation, environment variables and tool usage.
- [**Backend setup**](../../backend/README.md): Python, PostgreSQL, Alembic and local backend.
- [**Root quick start**](../../README.md): monorepo frontend/backend launch.
- [**Contributors / AI agent rules**](../../AGENTS.md).

**Where should Developer MCP live?** The reason it is separate from the user-facing MCP belongs in [architecture/mcp.md](../architecture/mcp.md). Detailed troubleshooting, operation, fixtures and trace tools belong here. These pages do not authorize using the diagnostic connector against production.
