# Developer MCP Phase 2 tracing architecture

Issue: #152

This note documents the small changes outside `dev_mcp_server/` that support cross-service correlation. The tracing layer is development-oriented observability infrastructure; it does not create a second business-logic path and it does not authorize requests.

## Correlation convention

The shared transport header is:

```text
X-Trace-Id
```

A trace ID is a bounded opaque correlation identifier. The Dev MCP generates one when a diagnostic request does not supply one. The Albayan backend validates an incoming value before preserving it; invalid or missing values are replaced with a fresh UUID. The backend echoes the accepted ID on the response.

The header is deliberately unrelated to Clerk, agent tokens, API keys, or other authorization state.

## Albayan backend changes

`app.core.tracing.TraceContextMiddleware` establishes request-scoped trace context and emits structured log events containing only bounded metadata such as service, stage, status, duration, method/path, and HTTP status. It does not log request or response bodies.

The CORS configuration exposes `X-Trace-Id`, which makes correlation visible to development browser tooling without giving the browser any additional privilege.

## Burhan boundary

`app.services.burhan_client` adds the current `X-Trace-Id` to trusted Burhan requests and emits start/completion/failure metadata around the conversion boundary. `burhan_reverse_client` uses the same `_burhan_headers()` helper, so reverse conversion inherits propagation automatically.

This records what Albayan observed at the Burhan boundary. It does **not** claim to expose Burhan's internal parser/model stages. Service-side Burhan instrumentation can later emit the same ID into a centralized development trace source.

## Document2 / BuTeX worker boundary

`app.services.butex_worker_client` sends `X-Trace-Id` to the configured worker and reuses the trace ID as `X-Request-ID` when request context exists. It emits bounded start/completion/failure metadata around each worker request without logging the document payload.

This records the Albayan-to-worker boundary only. Browser/editor-internal BuTeX observations remain a Phase 3 / Playwright MCP concern.

## Trace source boundary

The Phase 2 Dev MCP defines a small trace-source protocol. The initial implementation is a bounded process-local in-memory source covering Dev MCP events. It is intentionally non-persistent and explicitly reports downstream service events as missing.

This avoids coupling the tool contract to Railway or any one vendor before the development environment is finalized. A future adapter may aggregate Railway logs, OpenTelemetry, Loki, Datadog, or another structured backend while preserving the same MCP tools:

- `dev_get_trace`
- `dev_list_recent_traces`

## Playwright MCP

Playwright MCP remains a separate observation plane:

```text
Dev MCP        -> internal APIs, structured diagnostics, traces
Playwright MCP -> real browser/UI/render/network observations
```

Where a browser-triggered request reaches Albayan, the response `X-Trace-Id` can be used to correlate browser evidence with backend evidence. The Dev MCP does not proxy Playwright.

## Security and privacy

- no production log source is added;
- no database, shell, deployment, or secret-retrieval capability is added;
- trace IDs never authorize access;
- trace outputs do not include full request/response bodies;
- secret-bearing headers are not recorded;
- Dev MCP retention is bounded and process-local;
- remote Dev MCP authentication remains Clerk OAuth plus server-side `public_metadata.developer == true` authorization.
