# Al-Bayan Developer MCP

`dev_mcp_server/` is a **developer-only MCP connector** for trusted coding/debugging agents working on Al-Bayan. It is deliberately separate from `mcp_server/`, which is the product-facing authoring connector.

Phase 1 provides a safe foundation for runtime fact-gathering. Later phases add cross-service traces, equation-pipeline diagnostics, fixtures, and regression workflows.

## Purpose

The development MCP exists so an agent can inspect the development environment directly instead of relying on copied logs, screenshots, or guesses from source code.

It must also fail usefully. If an agent lacks a URL, credential, endpoint, trace source, or diagnostic adapter, the tool should return an explicit blocker and a `human_action` explaining what the developer needs to provide.

Example:

```json
{
  "ok": false,
  "blocked": true,
  "reason": "missing_configuration",
  "missing": ["BURHAN_DEV_URL"],
  "human_action": "Configure BURHAN_DEV_URL for the development MCP connector."
}
```

The agent should surface that information to the human rather than guessing or asking for production access.

## Security boundary

This server is for trusted development use only.

Phase 1 intentionally does **not** provide:

- shell execution;
- direct database access;
- arbitrary URL fetching;
- production credentials;
- deployment controls;
- destructive/admin mutations;
- unrestricted POST requests.

The generic HTTP tool can target only the explicitly configured Albayan, Burhan, and BuTeX development origins, does not follow redirects, accepts only `GET`, `HEAD`, and `OPTIONS`, bounds response size, and redacts common secret fields.

Specialized later-phase tools may perform controlled POST requests internally when that is necessary to run a diagnostic (for example Burhan conversion), but those operations should remain narrow and purpose-specific.

## Install

From this directory:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
```

Configure only development service URLs/tokens in `.env`.

## Run

stdio (recommended for a local coding agent):

```bash
albayan-dev-mcp --transport stdio
```

Streamable HTTP:

```bash
albayan-dev-mcp --transport streamable-http --host 127.0.0.1 --port 8083
```

Do not expose the streamable HTTP listener publicly without adding an explicit trusted-developer authentication layer.

## Configuration

| Variable | Purpose |
|---|---|
| `ALBAYAN_DEV_URL` | Explicit Albayan development service origin |
| `BURHAN_DEV_URL` | Explicit Burhan development service origin |
| `BUTEX_DEV_URL` | Explicit BuTeX development service origin, if one exists |
| `*_DEV_TOKEN` | Optional bearer token for the matching service |
| `DEV_MCP_REQUEST_TIMEOUT_SECONDS` | Request timeout, default 10 seconds |
| `DEV_MCP_MAX_RESPONSE_BYTES` | Maximum returned response body, default 256 KiB |
| `DEV_MCP_HOST` / `DEV_MCP_PORT` | HTTP transport bind settings |

Service URLs must be HTTP(S) **origins** only, with no embedded credentials, path prefix, query, or fragment.

A missing service URL does not prevent startup. `dev_health` reports it as a blocker so the human can configure only the capabilities needed for the investigation.

## Phase 1 tools

### `dev_health`

Checks `albayan`, `burhan`, and `butex` configuration/reachability.

Any HTTP response means the service is network-reachable; a root `404` can therefore still be reported as reachable. The tool is not asserting application health beyond connectivity in Phase 1.

### `dev_http_request`

Performs a constrained read-only request against one configured service.

Inputs:

- `service`: `albayan`, `burhan`, or `butex`;
- `path`: path on that configured origin, e.g. `/health`;
- `method`: `GET`, `HEAD`, or `OPTIONS`;
- `query`: optional non-secret query parameters.

It rejects absolute/arbitrary URLs and protocol-relative paths. Redirects are not followed or exposed as alternate targets.

Use this as an escape hatch for simple inspection when no specialized diagnostic tool exists. Prefer specialized tools once they are available.

## Human escalation contract

For developer-agent workflows, **being blocked is an expected structured outcome**.

Tools should distinguish at least:

- missing configuration;
- service unreachable;
- timeout;
- unsupported/unexposed diagnostic capability;
- missing permission/authentication;
- unavailable trace/log backend.

When a missing capability prevents investigation, return the smallest actionable request to the human developer. Examples:

- `Configure BURHAN_DEV_URL`;
- `Provide a development-only Burhan credential capable of the requested model tier`;
- `Expose a BuTeX headless editor-import diagnostic`;
- `Configure the development trace backend`.

Do not recommend production credentials as a shortcut.

## Tests

```bash
pytest
```

Tests are designed to run without live development or production services. Live integration suites belong in later phases and must be opt-in.

## Roadmap

- **Phase 1 — #151:** standalone server, safe service access, actionable blockers.
- **Phase 2 — #152:** trace/correlation IDs and structured trace inspection.
- **Phase 3 — #153:** equation pipeline inspection, fixtures, Burhan tier comparisons, BuTeX diagnostics.
- **Phase 4 — #154:** regression suites, capability discovery, automated investigation reports, CI integration.

## Adding future diagnostics

Keep the server general. New domains should reuse the same configuration, redaction, blocker, and tracing conventions rather than exposing raw internals ad hoc. Future tool families may include `dev.document.*`, `dev.compile.*`, `dev.assets.*`, and `dev.performance.*`.
