# Dev MCP Phase 4: investigation and regression workflows

Phase 4 turns the Phase 1 service boundary, Phase 2 trace IDs, and Phase 3 equation diagnostics into repeatable, bounded developer investigations. It does **not** grant repository writes, shell access, deployments, database access, production credentials, or automatic merge authority.

## Recommended agent protocol

```text
dev_capabilities
  -> choose the smallest relevant named suite
  -> dev_run_regression_suite
  -> inspect trace IDs / specialized diagnostics when needed
  -> use Playwright separately only for browser-dependent questions
  -> apply/review a code change outside Dev MCP
  -> rerun the suite
  -> dev_investigation_report
```

Agents must not assign ownership from a final symptom alone. `likely_owning_service` is derived from the first observable failing stage and is explicitly a debugging hint, not proof of root cause.

## Tools

### `dev_capabilities`

Reports configuration state and planning hints without pretending that configuration equals live reachability. Use `dev_health` when a real network reachability check is needed.

It reports configured services, equation-diagnostic readiness, supported Burhan tiers, named suites, trace lookup support, headless BuTeX availability through the Al-Bayan diagnostic path, and whether browser observation has been explicitly declared available.

`browser_observation` is only a hint for a **separate Playwright MCP**. The Dev MCP does not launch, proxy, or authenticate Playwright.

### `dev_regression_suites`

Lists the registered suites and CI policy. The initial registry contains:

| Suite | Purpose | Mandatory live CI? |
|---|---|---|
| `equations-smoke` | Small representative pipeline smoke set | No |
| `equations-adjacency` | `dx`, `df`, `kx`, coefficient/matrix adjacency regressions | No |
| `equations-common-scientific` | Common operators, derivatives, typography and environments | No |
| `document2-roundtrip` | Document2 insertion, BuTeX reopen and reverse conversion probes | No |
| `burhan-tier-comparison` | Heuristic/cheap/medium comparison on a bounded subset | No; nondeterministic/provider-backed |

Suite registration/schema tests are offline and mandatory. Live development-service execution is explicitly opt-in. LLM-backed output is diagnostic evidence, not a brittle mandatory merge oracle.

### `dev_run_regression_suite`

Runs a named suite through existing Phase 3 diagnostics. It does not duplicate Burhan parsing, Al-Bayan projection, Document2 logic, or BuTeX editor import.

A run returns:

- stable `schema_version` and `run_id`;
- suite/domain/configuration metadata;
- start/end timestamps and bounded duration;
- trace IDs;
- stage matrix per fixture;
- first observable failing stage;
- likely owning service plus uncertainty basis;
- blockers and missing observations;
- exact human actions;
- bounded rows (`DEV_MCP_REPORT_MAX_ROWS`).

Browser validation is optional by default and does not make a deterministic/headless run partial merely because Playwright was not used. Required headless stages becoming unavailable do produce a partial result.

### `dev_investigation_report`

Produces the stable evidence-oriented report format. It can optionally run a second Burhan tier and return a compact stage-level comparison without dumping entire payloads.

Representative fields:

```json
{
  "schema_version": 1,
  "investigation_id": "...",
  "problem_reproduced": true,
  "configuration": {
    "baseline_model_tier": "heuristic",
    "candidate_model_tier": "medium"
  },
  "trace_ids": ["..."],
  "first_failing_stage": "headless_butex_validation",
  "likely_owning_service": "butex",
  "ownership_basis": "Derived from the first observable failing stage; not proof of root cause.",
  "regression_status": "failed",
  "missing_observations": [],
  "blockers": [],
  "human_actions": []
}
```

## Status semantics

- `passed`: all required currently observable stages passed.
- `failed`: at least one required observed stage returned an actual failure.
- `partial`: useful evidence exists, but a required observation is unavailable or only some fixtures/configurations were blocked.
- `blocked`: no meaningful requested suite execution could proceed.

A browser-only gap is not automatically a blocker. If `require_browser=true`, an investigation remains partial until external browser evidence is supplied.

## Browser evidence

Use the Playwright MCP separately when the question depends on deployed UI, MathJax rendering, reopen/edit behavior, console errors, or browser-network behavior. `dev_investigation_report` accepts only a short caller-supplied browser observation (`passed`, `failed`, `blocked`, or `not_checked`) and an optional bounded note. That evidence is labeled as external and is never confused with deterministic headless evidence.

## Comparison support

For ordinary fixture suites, `compare_model_tier` runs the same controlled suite under a second supported Burhan tier and compares compact per-fixture status/stage changes. It does not perform git checkout or deployment. The compared states must already be observable through the configured development services.

`burhan-tier-comparison` is a dedicated suite that runs `heuristic`, `cheap`, and `medium` for a small regression subset. Cheap/medium may consume configured provider budget.

## Security and privacy

Phase 4 keeps the existing security boundary:

- remote Dev MCP requires Clerk OAuth plus server-fetched `public_metadata.developer == true`;
- specialized equation POSTs remain fixed to the authenticated Al-Bayan dev diagnostic endpoint;
- no arbitrary POST, URL, shell, database, repository-write or deployment tool is added;
- reports are bounded and passed through the existing diagnostic sanitizer;
- tokens, cookies, authorization headers and full sensitive bodies are not intentionally retained;
- diagnostic runs are returned to the caller and are not persisted as production article state.

## Extending with another diagnostic domain

A future domain such as compile/assets/document import should follow the same pattern:

1. implement or reuse a narrow specialized diagnostic client;
2. register fixtures/suites with stable metadata;
3. return stage-level evidence and trace IDs;
4. use the common report status/blocker/human-action semantics;
5. keep live suites opt-in unless they are truly deterministic and self-contained;
6. keep external/browser observation separate when applicable.

This permits future tools such as `dev_compile_inspect`, `dev_document_roundtrip`, or `dev_assets_validate` without expanding the generic HTTP escape hatch or duplicating service internals.
