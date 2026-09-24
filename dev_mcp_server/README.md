# Al-Bayan Developer MCP

`dev_mcp_server/` is a **developer-only** MCP connector for trusted coding/debugging agents working on Al-Bayan. It is deliberately separate from `mcp_server/`, which is the product-facing authoring connector.

The phases now provide:

- **Phase 1 — #151:** safe development-service access and actionable blockers;
- **Phase 2 — #152:** correlation IDs and structured trace inspection;
- **Phase 3 — #153:** equation pipeline diagnostics, fixtures, Burhan tier comparison and BuTeX headless validation;
- **Phase 4 — #154:** capability discovery, named regression suites, controlled comparisons and evidence-oriented investigation reports.

## Purpose

The development MCP lets an agent inspect and test the development environment directly instead of reasoning from copied logs, screenshots, or source code alone. Being blocked or partial is an expected result: tools should state exactly what configuration, permission, observation point, or human action is missing instead of guessing.

## Security boundary

Remote Streamable HTTP access is authenticated with Clerk OAuth and then independently authorized from server-fetched Clerk metadata. A valid caller is admitted only when:

```text
public_metadata.developer == true
```

Local stdio can run without OAuth because it is a local process boundary. Remote Streamable HTTP fails closed if `CLERK_ISSUER_URL`, `CLERK_SECRET_KEY`, or `DEV_MCP_RESOURCE_URL` is missing.

The developer MCP intentionally does **not** provide unrestricted shell execution, direct database access, arbitrary URLs, production credentials, deployment controls, repository writes, destructive/admin mutations, or unrestricted POST requests. The generic HTTP tool remains GET/HEAD/OPTIONS-only against explicitly configured development origins. Specialized POST diagnostics are narrow and fixed to reviewed development endpoints.

Secrets remain server-side. Diagnostic outputs are bounded and sanitized; tools should never intentionally return tokens, cookies, authorization headers, `.env` contents, or full sensitive payloads.

## Install and run

```bash
cd dev_mcp_server
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
```

Local stdio:

```bash
albayan-dev-mcp --transport stdio
```

Remote Streamable HTTP:

```bash
albayan-dev-mcp --transport streamable-http --host 0.0.0.0 --port 8083
```

## Configuration

| Variable | Purpose |
|---|---|
| `ALBAYAN_DEV_URL` | Explicit Al-Bayan development/feature service origin |
| `BURHAN_DEV_URL` | Explicit Burhan development service origin |
| `BUTEX_DEV_URL` | Explicit BuTeX development service origin |
| `*_DEV_TOKEN` | Optional server-side bearer token for the matching service; Phase 3/4 live equation diagnostics require `ALBAYAN_DEV_TOKEN` |
| `CLERK_ISSUER_URL` | Clerk OAuth issuer for remote MCP |
| `CLERK_SECRET_KEY` | Server-only Clerk key used to authenticate and read public metadata |
| `DEV_MCP_RESOURCE_URL` | Public resource URL of the developer MCP |
| `DEV_MCP_REQUEST_TIMEOUT_SECONDS` | Generic diagnostic timeout, default 10 s |
| `DEV_MCP_EQUATION_TIMEOUT_SECONDS` | Equation/model diagnostic timeout, default 90 s |
| `DEV_MCP_MAX_RESPONSE_BYTES` | Max returned HTTP body, default 256 KiB |
| `DEV_MCP_TRACE_MAX_TRACES` | Process-local trace retention bound |
| `DEV_MCP_TRACE_MAX_EVENTS_PER_TRACE` | Per-trace event retention bound |
| `DEV_MCP_REPORT_MAX_ROWS` | Phase 4 regression/report row bound, default 50 |
| `DEV_MCP_BROWSER_OBSERVATION_AVAILABLE` | Capability hint for a **separate** Playwright MCP; does not launch/proxy Playwright |
| `DEV_MCP_HOST` / `DEV_MCP_PORT` | HTTP transport bind settings |

Service URLs must be HTTP(S) origins only, with no embedded credentials, path prefix, query, or fragment.

## Core tools

### `dev_health`

Checks live reachability of configured `albayan`, `burhan`, and `butex` origins. Any HTTP response proves network reachability only; it does not imply application correctness.

### `dev_http_request`

Constrained read-only HTTP escape hatch for configured development services. It accepts only GET/HEAD/OPTIONS, rejects arbitrary URLs and redirects, propagates `X-Trace-Id`, bounds response size, and redacts common secrets. Prefer specialized diagnostics whenever one exists.

### `dev_get_trace` / `dev_list_recent_traces`

Inspect Phase 2 trace evidence. The default trace source is process-local and bounded, so cross-process/log aggregation may still be partial until a centralized adapter is configured.

## Phase 3 equation tools

### `dev_equation_inspect`

Runs one canonical English/interoperability LaTeX equation through the real development pipeline without persisting article state:

```text
canonical LaTeX
  -> Al-Bayan dev diagnostic endpoint
  -> Burhan /convert
  -> Al-Bayan editor-shaped MathObject projection
  -> Document2 worker command path
  -> BuTeX headless MathObject/editor adapter
  -> optional Burhan /convert-to-english
```

The report keeps `headless_butex_validation` distinct from `browser_validation`. Browser/UI/MathJax evidence belongs to a separate Playwright MCP.

### `dev_equation_compare_model_tiers`

Compares heuristic/cheap/medium Burhan behavior for one equation. Cheap/medium may consume configured provider budget.

### `dev_equation_run_fixture` / `dev_equation_run_suite`

Execute the reusable equation fixture corpus and return stage-level results rather than only a boolean.

## Phase 4 investigation tools

### `dev_capabilities`

Call this **before assuming runtime access**. It reports service configuration state, equation diagnostic readiness, trace support, named suite availability, supported Burhan tiers, headless BuTeX capability, and the external browser-observation hint. Configuration is not treated as reachability; use `dev_health` for that.

### `dev_regression_suites`

Discovers named suites and their CI policy. Initial suites are:

- `equations-smoke`;
- `equations-adjacency`;
- `equations-common-scientific`;
- `document2-roundtrip`;
- `burhan-tier-comparison`.

Mandatory CI validates the suite registry, report behavior, redaction and orchestration **offline**. Live development-service execution is opt-in. Nondeterministic LLM-backed results are diagnostic evidence and are not mandatory merge gates.

### `dev_run_regression_suite`

Runs a bounded named suite through the existing specialized diagnostics. Results include run ID, timestamps, trace IDs, per-fixture stage matrix, first observable failing stage, likely owning service, uncertainty basis, blockers, missing observations and exact human actions.

`likely_owning_service` is derived from the first observable failing boundary. It is a debugging hint, **not proof of root cause**.

### `dev_investigation_report`

Produces the stable Phase 4 evidence report. It can optionally compare a second supported Burhan model tier and returns compact stage changes rather than dumping complete structured payloads.

The report distinguishes:

- deterministic/headless Dev MCP evidence;
- external browser evidence;
- blocked or missing observations;
- exact human actions.

If a conclusion genuinely requires browser behavior, set `require_browser=true`, use Playwright separately, and provide only a short browser observation summary. A missing Playwright capability is not automatically a blocked headless investigation.

Full Phase 4 protocol: `docs/dev-mcp-investigation-workflows.md`.

## Recommended coding-agent workflow

```text
dev_capabilities
  -> specialized inspection / smallest relevant named suite
  -> collect trace IDs and intermediate evidence
  -> use Playwright separately only if the question is browser-dependent
  -> review/apply code change outside Dev MCP
  -> rerun the regression suite
  -> dev_investigation_report
```

When blocked, surface the exact blocker and human action. Never request production credentials as a workaround.

## Trace lifecycle

Correlation uses:

```text
X-Trace-Id: <safe correlation identifier>
```

The Dev MCP generates or accepts a safe trace ID, Al-Bayan preserves/echoes it, and Al-Bayan propagates it across Burhan and Document2/BuTeX boundaries where those clients are used. Trace IDs are observability metadata only and never authorize access.

Known gaps are reported rather than invented. The process-local default trace source is not durable audit storage and cannot by itself aggregate every service process.

## Tests and CI

```bash
pytest
```

Tests run without production services. Phase 4 adds offline coverage for suite registration/discovery, deterministic orchestration with mocked diagnostics, comparison output, partial/blocked reports, capability output, schema stability, trace linkage, report-size limits, redaction, and live-vs-offline CI policy.

Live suites must remain explicit/opt-in unless a future suite is self-contained and deterministic enough to be a stable merge gate.

## Adding future diagnostic domains

New domains should reuse the same client/config, tracing, blocker, suite and report conventions rather than expanding the generic HTTP escape hatch or reimplementing service internals. A future domain such as `dev_compile_inspect`, `dev_document_roundtrip`, or `dev_assets_validate` should provide a narrow specialized diagnostic, register bounded suites, emit trace-linked stage evidence, and use the common report semantics.
