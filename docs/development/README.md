# Development and diagnostics

Guidance for **working on Al-Bayan** rather than a description of the product architecture.

- [**Railway infrastructure and environments**](railway-infrastructure.md): actual development/production service inventory, branch mapping, domains and deployment boundaries.
- [**Playwright MCP browser testing**](playwright-mcp.md): AI-operated end-to-end UI testing against the Railway-hosted development website.
- [**Developer MCP — how to use it**](developer-mcp.md): headless diagnostics, restricted development-service access and investigation protocol.
- [**Product MCP operations**](mcp-operations.md): client onboarding, authentication boundaries and real user-agent edit verification.
- [**Math/Document2 verification**](math-verification.md): canonical LaTeX, units, agent tools, BuTeX, browser and compiler testing.
- [**MCP file transport probe**](mcp-transport-probe.md): opt-in interoperability diagnostics.
- [**Investigation workflows**](investigation-workflows.md): named suites, report interpretation, browser-evidence requirements.
- [**Equation diagnostics**](equation-diagnostics.md): stage-level conversion tests and fixtures.
- [**Tracing**](tracing.md): `X-Trace-Id` and evidence boundaries.
- [**Email deliverability**](email-deliverability.md): transactional delivery, scanner-safe links, provider boundaries.
- [**Clerk security emails**](clerk-security-email.md): six security templates, verified webhooks and rollout rules.
- [**Stripe donations**](stripe-donations.md): payment integration setup and sandbox/production safety.
- [**Developer MCP package README**](../../dev_mcp_server/README.md): concrete installation, environment variables and tool usage.
- [**Backend setup**](../../backend/README.md): Python, PostgreSQL, Alembic and local backend.
- [**Root quick start**](../../README.md): monorepo frontend/backend launch.
- [**Contributors / AI agent rules**](../../AGENTS.md).

**Where should Developer MCP live?** The reason it is separate from the user-facing MCP belongs in [architecture/mcp.md](../architecture/mcp.md). Detailed troubleshooting, operation, fixtures and trace tools belong here. These pages do not authorize using diagnostics or automated browser actions against production. [Developer MCP](developer-mcp.md) and [Playwright MCP](playwright-mcp.md) are distinct tools that agents can combine: one inspects backend/equation stages, the other observes and operates the actual development browser.
