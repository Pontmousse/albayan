# Canonical mathematical authoring contract (phase 1/6)

**Status: reader preparation only. `canonical-v2` mutations are disabled.**
The deployed capability endpoint and normal MCP tool still advertise contract v1.
Schema acceptance is not a promise that converters, editors or browsers support v2.
Activation belongs to [Al-Bayan #187](https://github.com/Pontmousse/albayan/issues/187).
This document and [shared fixtures](fixtures/math-authoring-contract-v2.json) define
the contract for [#186](https://github.com/Pontmousse/albayan/issues/186).

## Baseline and representation ownership

Reviewed integration revisions:

| Component | Branch/revision |
| --- | --- |
| Al-Bayan | develop, `b125799425895d060521c9352cc17d7e6844a366` |
| Burhan | develop, `52f70f7a230960d385df0b1e666e3dd39b499ce0`, merged MR !18 |
| BuTeX | develop, `9287812c93fa0e34f7d269887edee60b0fe7ff1d`, package 7.2.1 |

Normal flow: English LaTeX → typed normal MCP draft command → FastAPI/Document2
→ Burhan → editor-owned structured MathObject → revision storage → BuTeX editor
and MathJax → reverse projection → Burhan English conversion →
`get_draft_equations` → canonical English LaTeX.

There is one authoritative equation tree, existing location/token IDs, labels and
revision history, plus the existing article variable-mapping dictionary. Do not
add a parallel stored equation, original-LaTeX cache, occurrence-ID registry or
article-wide semantic mode. Reverse export must use the live edited tree.

**Source discrepancy to resolve before phase 6:** current `_arabic_math_object`
validates normalized Burhan `arabic_json` and marks it Arabic/editor-owned. The
architecture reference describes that current producer. The originally requested
canonical-English skeleton with Arabic values was produced by historical
`_editor_math_object` at `5c8cffaec584ec1c226f95b73735ef8d1ac5bf6c`.
Phase 1 preserves the current producer. Future integration must explicitly decide
which producer owns structure; this contract does not authorize silently switching
between them. Bounded canonical identity can accompany either presentation tree.

MR !18 removes model-tier prescan shortcuts for ambiguous d/T/delta/number-set
letters, keeps ordinary delta, corrects N's glyph, excludes D from sets and fixes
the derivative regex. It does not solve token-global mapping or identifier
splitting. Legacy conversion behavior remains unchanged in this phase.

## Future AI syntax

The following rules become authoritative only when phase 6 advertises v2:

| Meaning | Generate | Semantics/inference |
| --- | --- | --- |
| Transpose | `A^\top` | Standard symbol; never use `A^T` for transpose |
| Ordinary single-letter variable | `T`, `d`, `R`, etc. | Variable role; translate its name without reclassifying it as a set/operator |
| Number systems | `\mathbb{N}`, `\mathbb{Z}`, `\mathbb{Q}`, `\mathbb{R}`, `\mathbb{C}`, `\mathbb{H}` | Explicit sets; H is quaternions, D is not a set |
| Total differential | Exact `\mathrm{d}` | Explicit differential; never use bare d for this meaning |
| Partial derivative | `\partial` | Intrinsic standard symbol |
| Ordinary Greek/standard symbol | `\delta`, `\Delta`, `\nabla`, etc. | Preserve standard source identity deterministically |
| Functional variation notation | `\frac{\delta F}{\delta u}` | Preserve notation; no new variation-role annotation or contextual delta rewrite |
| Atomic named variable | `\mathtt{velocity}` | One alphabetic Latin name, 2–64 characters, scripts outside |
| Unit | `\mathsf{m}` | Reuse the existing unit resolver; legacy `\unit` remains supported |
| Functions | `\sin x`, `\log x` | Distinct from named variables `\mathtt{sin}`, `\mathtt{log}` |
| Multiplication | `x\cdot y` when needed | Avoid ambiguous bare `xy`, `mc`, `mv`, `abc`, `dx`, `df` |

No new `\var`, `\transpose`, `\differential` or `\numberSet` authoring macros.
The reserved roles of `\mathtt` and `\mathsf` apply only to canonical-v2.
Legacy/imported font wrappers retain their existing behavior. Generic `\mathit`
is styling, not an alternative named-variable boundary. Read-back keeps the
standard `\mathtt`/`\mathsf` boundaries.

### Translation policy (Burhan phase 5)

* Named variables: extract the whole name through supported styling. A valid exact
  full-name mapping wins; otherwise call the selected model in every model-backed
  tier, including free. Never split or deterministically translate an unmapped
  name. Batch missing names, reuse repeats and measure latency. Heuristic mode is
  offline: unmapped named variables report model-required. Provider failure must
  not masquerade as successful heuristic translation.
* Single Latin letters: valid mapping first, then safe variable-only fallback
  tables when prescanning is enabled and mapping instructions do not override
  them, then the configured model for unresolved names. Explicit ordinary-variable
  roles cannot consult set/transpose/derivative tables. This policy does not
  require a model call for every single letter.
* Symbols, sets and differentials: deterministic structural semantics, independent
  of variable-name translation. Explicit roles outrank incompatible historical
  mappings locally; preserve the existing dictionary and stable merge behavior.
* Units: dispatch a canonical `\mathsf` boundary to the existing `\unit` resolver
  before ordinary child translation. Preserve its known-unit/model/fallback flow.
  Do not replace strings with a regex. Fix unit-versus-set precedence in phase 5
  (notably N, H, T and C); keep `\unit` compatibility.

### Styles, nesting and units

Preserve role/name and wrapper order in both `\mathtt{\mathbf{velocity}}_0` and
`\mathbf{\mathtt{velocity}}_0`, and the analogous unit forms. `\mathbf` and
`\boldsymbol` decorate appearance; they do not imply vector/variable/unit roles.
Nested math alphabets can override one another visually: do not promise identical
fonts or bold monospace. `\mathbf` is not portable bold Greek; test `\boldsymbol`.
Generic style wrappers can contain expression arguments in BuTeX phase 2.
`\mathscr` and `\bm` depend on renderer/package support and are not automatically
safe. Internal `\boldarabic`/`\italicarabic` remain compatibility/output syntax,
not canonical AI authoring commands.

The future parser rejects expressions inside named-variable boundaries, e.g.
`\mathtt{x+y}`, functions within that boundary, and conflicting roles such as
`\mathsf{\mathtt{foo}}`. Host schemas do not parse raw LaTeX semantics.

Unit factors are the 28 base names in the fixtures. Input Ω normalizes explicitly
to metadata `\Omega`; the schema does not perform translation or alias repair.
Compound units use structured products/quotients and integer powers of factors,
never an expression in an atom's `name`. Test `\mathsf{m/s^{2}}` and
`\mathsf{kg}\cdot\mathsf{m}/\mathsf{s}^{2}` before advertising compounds. Unknown
units and siunitx syntax remain outside guaranteed deterministic support.

## Wire additions

### Equation profile

Optional `authoring_profile: "canonical-v2"` exists on the compact
`DocumentMathAuthoringInlineToken` and root `DocumentMathObjectJson`. Omission
means legacy. Null, unknown versions and coercion are invalid. The profile is
equation-level and independent of model tier and discovery `contract_version`.

Future compact input (currently rejected at mutation time):

```json
{"kind":"math","latex":"A^\\top + T","display":false,"authoring_profile":"canonical-v2"}
```

### Bounded atom identity

Optional `canonical_atom` is a discriminated `{kind, name}` object with no extra
fields, opaque expression, glyph-derived reverse guess or occurrence ID.

| kind | name | Allowed nodes |
| --- | --- | --- |
| variable | ASCII `[A-Za-z]{1,64}` | CharObject, CommandObject |
| symbol | One of the 23 source commands in the fixtures | CharObject, CommandObject |
| differential | `d` | CharObject, CommandObject |
| number_set | N/Z/Q/R/C/H | CharObject, CommandObject |
| unit | One of the 28 canonical base names in the fixtures | CharObject, CommandObject |
| operator | `/` or `\backslash` | OperatorObject, CommandObject |

Chains, the root, numbers, delimiters and environments cannot carry atom identity.
Scripts carry their own identity. Annotate a whole translated named atom once,
not every Arabic character. Annotated descendants require a canonical-v2 root,
including descendants in scripts, delimiters, arguments and environment lines.
Unannotated historical AST nodes remain permissive.

The frozen symbol registry is not the full supported-LaTeX registry: an unlisted
standard command can remain structurally retained without provenance. Metadata
validation checks bounds/placement; converters and editors must ensure the source
identity still matches the mathematical atom after edits.

### Lost wrapper provenance

Preserve standard wrapper CommandObjects first. If lowering actually loses a
wrapper, optional `canonical_command` records its source command on that same
node. Allowed sources: `\mathbf`, `\boldsymbol`, `\mathrm`, `\mathit`, `\mathtt`,
`\mathsf`, `\mathbb`, `\mathcal`, `\mathfrak`, `\mathscr`.

Only lowered CommandObjects named `\text`, `\boldarabic` or `\italicarabic`, with
exactly one mandatory argument and no optional arguments, may carry this field.
Other lowered names require a contract extension. Retained identical wrappers
must not be redundantly tagged. Source values cannot contain arguments,
declarations or internal Arabic macros. No parallel style JSON is introduced.

### Lifecycle and dormant-write boundary

Display-only edits preserve identity. Name/role/symbol edits invalidate or recompute
it; deletion removes it; copy/paste/history preserve it. Removing bold keeps the
named-variable/unit boundary; removing that boundary requires reclassification.
BuTeX phase 3 owns precise editing operations and their tests.

Host and normal MCP readers accept the additive fields and capability response
versions 1/2. Live capability content stays byte-for-byte semantically v1, including
its existing pins, examples, whitelist and instructions. No active profile flag
or new safe-syntax claim is introduced.

Until phase 6, mutation fails with HTTP 422, code
`math_authoring_profile_unavailable`, before conversion, mapping merge, worker or
storage. The guard reserves the three new wire keys in structured payloads; it
never parses LaTeX/text strings. It covers compact commands, structured insert/
replace, existing documents passed to mutation, normalization for full PUT/
autosave/revision/restore, and metadata commands. Access checks, command receipt
replay and revision conflicts keep their prior ordering. Old payloads follow their
unchanged paths. There is no toggle that can activate an incomplete producer.

No migration: old equations and mappings remain valid and receive no manufactured
annotations. Before activation, deploy all compatible readers, worker/editor
retention and reverse support; only then replace the dormant guard.

## Ownership and delivery gates

1. **Al-Bayan #186:** this contract, fixtures, mirrored readers, v1/2 capability
   parsing, dormant guards and host tests. No producer or persistence replacement.
2. **[BuTeX #21](https://gitlab.com/drghaliasri/butex/-/work_items/21):** generic
   standard wrapper/symbol parsing, editable AST and rendering; nested style and
   Arabic bold compatibility. Browser/MathJax proof is required.
3. **[BuTeX #22](https://gitlab.com/drghaliasri/butex/-/work_items/22):** preserve/
   invalidate identity and wrapper provenance through editor sessions, copies,
   history, serialization and Document2 projections.
4. **[Burhan #5](https://gitlab.com/drghaliasri/burhan3.0/-/work_items/5):** live-tree
   canonical reverse conversion and legacy read-back; independent of forward roles.
5. **[Burhan #6](https://gitlab.com/drghaliasri/burhan3.0/-/work_items/6):** explicit
   structural roles, isolated identifiers, exact-name/model policy and existing
   unit resolver routing. Keep heuristic and legacy model tiers compatible.
6. **Al-Bayan #187:** resolve the producer decision, integrate profile propagation,
   preserve mappings, deploy compatible services and advertise truthful capability
   v2. Remove the guard only after the normal user-facing MCP round trip passes.

Final integration matrix must include `A^\top + T`, each explicit set alongside its
bare letter, `\delta + \epsilon`, `\frac{\delta f}{\delta x}`,
`\frac{\mathrm{d}f}{\mathrm{d}x}`, `d + \frac{\mathrm{d}f}{\mathrm{d}x}`,
`\partial f / \partial x`, all discussed identifier cases, nested wrappers and
unit/set collisions. Expected read-back preserves standard canonical roles and
named boundaries after persistence **and editing**. Normal MCP → stored Document2
→ BuTeX → reverse → `get_draft_equations` is mandatory; Dev MCP alone is not proof.

Phase 1 host fixture/guard tests prove reader readiness and safe dormancy only.
Renderer, provider latency, stale-identity invalidation, compound-unit support,
historical producer choice and full persisted round-trip remain later gates.
