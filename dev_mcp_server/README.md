# Al-Bayan Developer MCP

`dev_mcp_server/` is a **developer-only MCP connector** for trusted coding/debugging agents working on Al-Bayan. It is deliberately separate from `mcp_server/`, which is the product-facing authoring connector.

Phase 1 provides a safe foundation for runtime fact-gathering. Phase 2 adds correlation IDs and structured trace inspection without coupling the server to one hosted logging vendor. Later phases add equation-pipeline diagnostics, fixtures, and regression workflows.

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

Remote Streamable HTTP access is authenticated with Clerk OAuth and then independently authorized by Clerk user metadata. A valid Clerk user is admitted only when:

```text
public_metadata.developer == true
```

The developer flag is read server-side from the Clerk Users API after the bearer token is authenticated. It is not trusted from an unverified request field or from client-supplied MCP arguments. Ordinary Al-Bayan users therefore cannot use the developer MCP merely because they can sign in to Al-Bayan. Other metadata such as `role: "admin"` can remain independent.

Streamable HTTP fails closed when `CLERK_ISSUER_URL`, `CLERK_SECRET_KEY`, or `DEV_MCP_RESOURCE_URL` is missing. Local stdio remains available without remote OAuth because it is a local process boundary.

The developer MCP intentionally does **not** provide:

- shell execution;
- direct database access;
- arbitrary URL fetching;
- production credentials;
- deployment controls;
- destructive/admin mutations;
- unrestricted POST requests.

The generic HTTP tool can target only the explicitly configured Albayan, Burhan, and BuTeX development origins, does not follow redirects, accepts only `GET`, `HEAD`, and `OPTIONS`, bounds response size, and redacts common secret fields.

Downstream service credentials such as `BURHAN_DEV_TOKEN` and `BUTEX_DEV_TOKEN` remain server-side environment variables on the developer MCP. The remote ChatGPT/MCP client never needs to know them.

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

Remote/Streamable HTTP:

```bash
albayan-dev-mcp --transport streamable-http --host 0.0.0.0 --port 8083
```

Before starting Streamable HTTP, configure Clerk authentication and set the connecting developer's Clerk user public metadata to:

```json
{"developer": true}
```

This can coexist with other metadata, for example:

```json
{
  "role": "admin",
  "developer": true
}
```

## Configuration

| Variable | Purpose |
|---|---|
| `ALBAYAN_DEV_URL` | Explicit Albayan development service origin |
| `BURHAN_DEV_URL` | Explicit Burhan development service origin |
| `BUTEX_DEV_URL` | Explicit BuTeX development service origin, if one exists |
| `*_DEV_TOKEN` | Optional server-side bearer token for the matching service |
| `CLERK_ISSUER_URL` | Clerk OAuth issuer used for remote MCP discovery/authentication |
| `CLERK_SECRET_KEY` | Server-only Clerk key used to authenticate the bearer and read user public metadata |
| `DEV_MCP_RESOURCE_URL` | Public resource URL of this developer MCP, e.g. `https://dev-mcp.example/mcp` |
| `DEV_MCP_REQUEST_TIMEOUT_SECONDS` | Request timeout, default 10 seconds |
| `DEV_MCP_MAX_RESPONSE_BYTES` | Maximum returned response body, default 256 KiB |
| `DEV_MCP_TRACE_MAX_TRACES` | Maximum process-local traces retained, default 200 |
| `DEV_MCP_TRACE_MAX_EVENTS_PER_TRACE` | Maximum process-local events retained per trace, default 50 |
| `DEV_MCP_HOST` / `DEV_MCP_PORT` | HTTP transport bind settings |

Service URLs must be HTTP(S) **origins** only, with no embedded credentials, path prefix, query, or fragment.

A missing downstream service URL does not prevent startup. `dev_health` reports it as a blocker so the human can configure only the capabilities needed for the investigation. In contrast, missing Clerk settings prevent remote Streamable HTTP startup because remote access must never fall back to anonymous mode.

## Developer tools

### `dev_health`

Checks `albayan`, `burhan`, and `butex` configuration/reachability.

Any HTTP response means the service is network-reachable; a root `404` can therefore still be reported as reachable. The tool is not asserting application health beyond connectivity.

### `dev_http_request`

Performs a constrained read-only request against one configured service.

Inputs:

- `service`: `albayan`, `burhan`, or `butex`;
- `path`: path on that configured origin, e.g. `/health`;
- `method`: `GET`, `HEAD`, or `OPTIONS`;
- `query`: optional non-secret query parameters;
- `trace_id`: optional existing correlation ID; omit it to generate one.

Every request carries `X-Trace-Id`. The returned result includes the trace ID and reports whether a downstream response echoed the same ID when that response header is available. The trace ID is observability metadata only and never authorizes access.

It rejects absolute/arbitrary URLs and protocol-relative paths. Redirects are not followed or exposed as alternate targets.

Use this as an escape hatch for simple inspection when no specialized diagnostic tool exists. Prefer specialized tools once they are available.

### `dev_get_trace`

Returns the ordered events currently available for one `trace_id`.

The Phase-2 default source is a bounded **in-memory source in the Dev MCP process**. It records the Dev MCP request and response boundary without logging full bodies, tokens, cookies, or authorization headers. Because it is not a centralized log backend, results explicitly report `partial: true` and identify downstream service events as a missing observation point.

### `dev_list_recent_traces`

Returns bounded summaries for recent traces from the configured trace source. It does not return request or response bodies.

## Phase 2 trace lifecycle

The transport convention is:

```text
X-Trace-Id: <safe correlation identifier>
```

A typical development flow is:

```text
Dev MCP generates/accepts trace_id
  -> sends X-Trace-Id to Albayan dev
  -> Albayan validates/preserves the ID
  -> Albayan echoes X-Trace-Id to the caller
  -> Albayan propagates it to Burhan and the Document2/BuTeX worker where those clients are used
  -> services/log adapters may emit structured events keyed by the same ID
```

The Albayan backend installs request-scoped trace context and emits bounded structured metadata (`service`, `stage`, `status`, `duration_ms`, method/path/status where relevant). It never logs full request/response bodies as part of this tracing layer. Burhan and BuTeX/Document2 client calls receive the correlation header. Their own internal service-side instrumentation remains a separate observation point.

The current Dev MCP trace source abstraction is intentionally vendor-neutral. The in-memory adapter is enough for deterministic local/unit behavior and for correlating the Dev MCP boundary now. A later development-environment adapter may read Railway logs, OpenTelemetry, Loki, Datadog, or another structured source without changing the MCP tool contract.

### Current observable stages

- Dev MCP diagnostic request start/completion/blocker;
- target service HTTP status and duration as observed by Dev MCP;
- Albayan inbound request start/completion in backend structured logs;
- Albayan -> Burhan conversion boundary in backend structured logs;
- Albayan -> Document2/BuTeX worker boundary in backend structured logs;
- correlation ID propagated in the relevant HTTP headers.

### Known gaps until Railway/log aggregation is configured

- `dev_get_trace` cannot yet aggregate Albayan, Burhan, and BuTeX process logs into one response;
- Burhan internal parser/model stages are not exposed by this generic Phase-2 layer;
- BuTeX browser/editor-only stages belong to Phase 3 / Playwright-assisted diagnostics;
- the in-memory Dev MCP source is lost on process restart and is not intended as durable audit storage.

These gaps are returned/documented as missing observations rather than guessed. Playwright MCP remains a separate browser observation plane; it is not proxied through the Dev MCP. Where browser-triggered backend requests expose `X-Trace-Id`, an agent can correlate browser evidence with backend evidence without making the trace ID an authorization mechanism.

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
- `Set public_metadata.developer=true on the authorized Clerk developer account`;
- `Expose a BuTeX headless editor-import diagnostic`;
- `Configure the development trace backend`.

Do not recommend production credentials as a shortcut.

## Tests

```bash
pytest
```

Tests are designed to run without live development or production services. Live integration suites are opt-in and can be configured later when the Railway development environment exists.

## Roadmap

- **Phase 1 — #151:** standalone server, safe service access, actionable blockers.
- **Phase 2 — #152:** trace/correlation IDs and structured trace inspection.
- **Phase 3 — #153:** equation pipeline inspection, fixtures, Burhan tier comparisons, BuTeX diagnostics.
- **Phase 4 — #154:** regression suites, capability discovery, automated investigation reports, CI integration.

## Adding future diagnostics

Keep the server general. New domains should reuse the same configuration, redaction, blocker, authentication, and tracing conventions rather than exposing raw internals ad hoc. Future tool families may include `dev.document.*`, `dev.compile.*`, `dev.assets.*`, and `dev.performance.*`.
