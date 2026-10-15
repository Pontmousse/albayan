# Unit conventions — normal MCP and development E2E gate (#219)

## Contract / ownership

The **normal user-facing MCP** is the acceptance path. Neither Dev MCP diagnostics
nor direct backend calls prove that the end-user tool is exposed correctly.

Discover in order:

1. `get_math_authoring_capabilities` — `unit_discovery` metadata identifies
   the canonical authoring syntax, grammar and read/apply tools.
2. `get_unit_registry` — live **Burhan-owned** catalogue proxied through
   authenticated Al-Bayan FastAPI (`GET /api/v1/math/unit-registry`);
   this is the source of defaults and alternatives, not an MCP copy.
3. `get_article_unit_context(article_id)` — current article-owned
   `unit_conventions`, used-unit counts and display sources, unknown tokens,
   plus the current `revision_number`.
4. For an authorized author's editorial changes,
   `apply_article_unit_conventions(article_id, base_revision, unit_conventions)`
   replaces the **full** conventions object, producing a new immutable revision.
   Preserve any unrelated custom units and overrides. Resolve revision
   conflicts by re-reading, not overwriting.
5. `apply_draft_command` with `{kind: "math", latex, display}` inserts
   canonical `\\mathsf{...}` through normal Document2.

The canonical identity is a **case-sensitive** token matching
`^[A-Za-z][A-Za-z0-9]*$`. Each `\\mathsf{token}` is a separate unit atom.
Bare `N` is a variable; `\\mathbb{N}` is a set; `\\mathsf{N}` is a unit.
The international token belongs in source LaTeX; never author the Arabic
display in its place. Exponents/operators are separate:
`30\\mathsf{m}/\\mathsf{s}`, `2\\mathsf{m}^2`. Burhan handles
custom definition → article override → registry default → unknown preserved +
warning. **No numerical conversion, dimensions, or LLM unit inference**.

Source of truth and trust boundaries:
- Burhan: registry `GET /unit-registry`, grammar, display validation, conversion.
- Al-Bayan: article state, authorization, immutable revision snapshot,
  Document2 canonical source, targeted current-document conversion.
- MCP: only typed, caller-authenticated FastAPI proxy tools (never a second
  catalogue, direct Burhan call, or internal Dev MCP commands).
- BuTeX: existing structured `\\unit` MathObject consumer; no implementation
  change unless browser evidence proves a fundamental incompatibility.

## Deployment preflight — MUST PASS before declaring live E2E success

Check **development only**, in this order:

- Burhan MR !31 (registry), !32 (runtime), !33 (round-trip) are merged and
  deployed in development. Verify `GET https://api.dev...Burhan.../unit-registry`
  returns the expected registry and version. Do not infer readiness from green
  GitLab CI or a branch name alone.
- Al-Bayan PR #220 (persistence), #221 (inventory/UI), and #222 (#219) are
  merged in order to `develop` and deployed in development. Apply migration
  `023_article_unit_conventions` against **development DB only**.
- Verify development frontend has Units panel and normal MCP discovery lists
  the three new unit tools. Inspect Railway deployed commit SHAs; do not
  substitute an API/docs schema or Dev MCP for the normal MCP evidence.
- Confirm browser navigation stays on `https://dev.albayan-journal.org` and
  all frontend API requests target `https://api.dev.albayan-journal.org`.
  Production redirects or API calls are configuration bugs.

## Live acceptance matrix (use a dedicated disposable dev test draft)

Record the normal MCP tool call/result, the revision ID/number, canonical
MathObject `source_latex`, Dev MCP intermediate conversion stages, and the
real **Playwright dev browser/editor** observation for each:

| Scenario | Canonical LaTeX | Expected check |
| --- | --- | --- |
| Registry default | `10\\mathsf{N}` | Registry default, not variable N; editable Arabic |
| Compound atoms | `v=30\\mathsf{m}/\\mathsf{s}` | Two units, no unit conversion or operator drift |
| Unit exponent | `A=2\\mathsf{m}^2` | Exponent outside unit; canonical reverse identity |
| Article override | `5\\mathsf{kg}` | Set `kg: كغ`, target new document display |
| Custom unit | `E=5\\mathsf{CU}` | Define `CU → وحدة معايرة`, discover through MCP, insert and edit |
| Historical/non-SI | `2\\mathsf{ha}` | Registry default from Burhan, no hard-coded alternative |
| Safe punctuation | `E=5\\mathsf{CU}` | Change CU display to `و.م`, editor keeps one unit atom |
| Unknown token | `7\\mathsf{XYZ}` | Warning, identity retained, never guessed |
| Bare variable | `N + 10\\mathsf{N}` | Only explicit atom is inventoried/translated |
| Round-trip/revision | `5\\mathsf{kg}` | A default → B override; A remains unchanged after new revision |

Required steps for **each**: discover → get article context → canonical MCP
Document2 command → verify stored source and Arabic MathObject → inspect
BuTeX rendering and editable import using Playwright on dev → reverse
conversion and verify identity. For changed conventions: verify only affected
equations change, history/rollback preserves older revision snapshot, and
new revisions reflect the intended convention. Investigate any failure by
AI input → MCP schema → FastAPI → Burhan → Document2 AST → BuTeX → browser.

**Do not close issue #219 as E2E complete based on mock tests, green CI,
headless BuTeX import, or prior deployed revisions alone.**

## Observed baseline on 2026-10-13 (before dependent merges)

- Dev MCP service health: Al-Bayan, Burhan and BuTeX endpoints reachable.
- Railway development environment: **9/9 services online**, no active warnings, recent failures or pending deployments. Development backend, normal MCP and frontend deploy commit `80de584eb0e28da87132253ffa7c8555b431a60e` on `develop` (2026-10-12). Neither #217–#219 nor the new normal MCP tools are deployed.
- Dev Burhan `GET /unit-registry`: **HTTP 404** (trace
  `98837e0f-c8a8-41d3-b077-ea7fa6fb2730`).
- GitLab Burhan MRs !31, !32 and !33: **opened/unmerged**.
- GitHub Al-Bayan PRs #220 and #221: **open draft/unmerged**.
- Existing normal MCP `get_math_authoring_capabilities` still has old unit
  description and has not yet discovered the three new tools.
- Playwright `browser_navigate` attempt to the dev domain was blocked
  by the testing tool's security check; **no real browser evidence acquired**.
- Dev MCP read-only `10\\mathsf{N}` diagnostic trace
  `b67261f5-b7e3-41aa-9da4-d9eba7379dd4`: Burhan converts to
  `\\unit{ن}` with `source_latex = \\mathsf{N}`; Document2 insertion,
  headless BuTeX editable import and reverse to `10 \\mathsf{N}` succeeded.
  This is **headless diagnostic evidence**, not deployed convention resolution
  or a browser/normal MCP insertion acceptance pass.
- Therefore live registry, override/custom, UI edit, revision and full
  round-trip cases are **not yet verified**.

After deployments, append actual trace IDs, MCP requests and redacted
responses, browser screenshots/observations, commit SHAs and per-row PASS/FAIL
here. Do not run this workflow against production.
