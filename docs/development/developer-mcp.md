# Working with Developer MCP

[← Development index](README.md) · [Current MCP architecture](../architecture/mcp.md)

Al-Bayan has a **user-facing authoring MCP**, a **developer diagnostics MCP**, and a **separate Railway-hosted Playwright MCP** for real browser interaction. Use **`mcp_server/`** for supported article authoring; **`dev_mcp_server/`** for traceable, bounded service diagnostics; and [Playwright MCP](playwright-mcp.md) to drive the actual development UI. Neither diagnostic surface is an alternative authoring API.

## Getting started

1. Follow [`dev_mcp_server/README.md`](../../dev_mcp_server/README.md) for installation, authentication and configuration. Its `.env.example` documents available settings; never paste credentials into documentation or commit them.
2. Point the dev connector to **development services**, not production. Its remote mode is restricted to authorized developers, and its generic HTTP tool is restricted to configured allowed methods/origins.
3. Call `dev_capabilities` first. A capability flag shows configuration, not that the target service is reachable; use `dev_health` when network reachability matters.
4. Run the **smallest relevant diagnostic** (for example `dev_equation_inspect`, `dev_run_regression_suite`, or a bounded trace lookup).
5. Keep the observed stages and `X-Trace-Id`; distinguish source-code expectation, actual service response, and rendered browser behavior.
6. When browser behavior matters, use **[Playwright MCP](playwright-mcp.md)** to navigate, interact with and inspect <https://dev.albayan-journal.org>. Confirm development API origins and report production redirection as a configuration defect. The AI agent can perform the browser interactions directly; it need not ask a human to manually reproduce them.
7. After any fix, verify through the **normal user-facing MCP** as well. A Dev MCP diagnostic pass is not proof that a normal client can author successfully.

## Diagnostic sequence for equations

```text
Canonical interoperable LaTeX
  -> normal MCP typed command/schema
  -> FastAPI / Document2 orchestration
  -> Burhan parser + structured Arabic MathObject
  -> persisted Document2 JSON
  -> BuTeX import/editor + MathJax/browser output
  -> optional XeLaTeX compiled output
```

For read-only diagnosis, prefer [equation diagnostic tooling](equation-diagnostics.md) and [investigation workflows](investigation-workflows.md), then check browser rendering independently. The first observable failing stage is **not** automatically the component responsible for root cause.

## Security and scope

Developer MCP is intentionally not a general shell, deployment, database, repo-write or production administration interface. It must not weaken authentication, expose secrets, or substitute developer-only behavior for supported normal-MCP behavior.

Additional reference: [tracing](tracing.md) · [Playwright browser-testing workflow](playwright-mcp.md) · [Railway environment inventory](railway-infrastructure.md) · [Developer MCP source](../../dev_mcp_server/src/albayan_dev_mcp/).

**Observed nuance (2026-10-19):** live `dev_capabilities` returned `browser_observation: false`, while Railway independently listed a successful, development-only Playwright MCP deployment. The flag is an optional Developer MCP capability hint; it does not launch, authenticate or attest to the separate browser MCP. Confirm that the agent can connect to Playwright and inspect the browser independently before claiming browser validation.
