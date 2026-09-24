# Dev MCP equation diagnostics (Phase 3)

Issue #153 adds a developer-only, non-persistent diagnostic path for the AI-assisted equation pipeline. It is intentionally separate from the public authoring MCP.

## Pipeline under inspection

```text
canonical English/interoperability LaTeX
  -> Al-Bayan dev diagnostic endpoint
  -> Burhan /convert
  -> Al-Bayan editor-shaped MathObject projection
  -> real Document2 worker commands
  -> BuTeX fromMathObjectJson + mathObjectToEditorSession
  -> optional Burhan /convert-to-english
```

Browser validation is a separate observation plane:

```text
Playwright MCP -> deployed Al-Bayan browser/editor/MathJax UI
```

The Dev MCP never proxies Playwright and never treats a missing browser observation as a failure of the deterministic headless pipeline.

## Tools

- `dev_equation_inspect`: inspect one equation with one Burhan tier.
- `dev_equation_compare_model_tiers`: run `heuristic`, `cheap`, and `medium` for the same input and return bounded structural differences.
- `dev_equation_run_fixture`: execute one named fixture.
- `dev_equation_run_suite`: execute a bounded fixture set and return a compact stage matrix.

`cheap` and `medium` can consume the configured Burhan model-provider budget. The suite defaults to `heuristic` for deterministic low-cost regression work.

## Stage semantics

Every stage reports `available`, `ok`, and `authoritative` separately.

- `canonical_input`: exact input plus the delimiter form selected by the real backend conversion path.
- `burhan_conversion`: Burhan request metadata, English structured representation, Arabic structured representation, Arabic LaTeX, mappings, warnings, resolved model, and request duration. This data comes from the same `/convert` request used to build the Document2 math token.
- `albayan_projection`: the real strict Al-Bayan `DocumentMathObjectJson` projection and resulting math token.
- `document2_command`: an in-memory empty document is normalized, a paragraph is inserted, then the real `insert_inline_token` command is applied through the configured Document2/BuTeX worker. No article, database, or object-storage state is persisted.
- `headless_butex_validation`: the BuTeX worker calls the existing `fromMathObjectJson()` and `mathObjectToEditorSession()` implementation. It does not contain a second parser or a diagnostic-only editor model.
- `reverse_conversion`: the stored editor-shaped MathObject and the observed mappings are sent to the real Burhan `/convert-to-english` endpoint using the selected tier.
- `browser_validation`: always reported as unavailable by this tool. Use Playwright MCP for real browser/editor/render/network evidence.

An unavailable stage is not fabricated. The report includes `reason` and `human_action` describing the smallest missing capability.

## Headless BuTeX adapter

Phase 3 adds one thin, token-protected worker endpoint:

```text
POST /v1/document2/diagnostics/math-object
```

It returns a worker envelope containing `math_diagnostic`. The nested result is either an editable result with English/Arabic editor-session renderings or a structured support failure such as:

```json
{
  "ok": false,
  "stage": "mathObjectToEditorSession",
  "editable": false,
  "error": "..."
}
```

The adapter reuses BuTeX internals directly. Parsing failures are classified at `fromMathObjectJson`; editor-support failures are classified at `mathObjectToEditorSession`.

## Fixture corpus

Fixtures live in `dev_mcp_server/src/albayan_dev_mcp/fixtures/equations.json`. They are machine-readable inputs with metadata:

- `id`
- `source`
- `display`
- `tags`
- `support_class`
- `known_failure`

The corpus includes basic operators/scripts, Greek symbols, large operators, integrals, partial derivatives, typography commands, text/operatorname forms, cases, accents, norms, spacing commands, and adjacency-sensitive expressions such as `dx`, `df`, `kx`, `k x`, `Ax`, `xA`, `abc`, and `\\frac{df}{dx}`.

Fixtures deliberately avoid golden snapshots of the entire Burhan/BuTeX AST. `known_failure` is documentation only; observed runtime evidence always wins.

## Model-tier comparison

The comparison tool runs the real pipeline for `heuristic`, `cheap`, and `medium` under one shared trace ID. It reports per-tier stage status plus mappings, warnings, reverse LaTeX, Burhan timing, headless BuTeX outcome, and a bounded generic JSON structural diff against the heuristic baseline. The diff utility compares JSON only; it is not an equation parser.

## Configuration and security

The backend route is registered but returns `404` unless `DEV_MODE=true`. It also requires normal Al-Bayan authentication (`ActorDep`). The Dev MCP therefore needs:

- `ALBAYAN_DEV_URL`
- `ALBAYAN_DEV_TOKEN`

The feature deployment must have its normal trusted Burhan and BuTeX worker configuration. The Dev MCP never receives `BUTEX_WORKER_TOKEN`, `BURHAN_API_KEY`, database credentials, or provider secrets.

Remote Dev MCP access retains the Phase 1 Clerk boundary: the server verifies the caller and requires server-fetched `public_metadata.developer == true`.

Diagnostics are read-only with respect to Al-Bayan product state. They may call external model tiers and therefore can consume provider budget.

## Trace linkage

The Dev MCP sends the Phase 2 `X-Trace-Id` to the backend. The backend preserves it and propagates it to Burhan and the BuTeX/Document2 worker. The headless worker log entry also includes the incoming trace ID. A centralized trace source can be attached later without changing the equation tool contracts.

## Feature-branch workflow

A permanent Railway development environment is not required by the implementation. `ALBAYAN_DEV_URL` means the explicitly configured safe target for the diagnostic run; during feature development it can point at a temporary/local/feature deployment. The diagnostic tools must never silently fall back to production credentials or an arbitrary URL.
