# AI Equation Architecture Reference

Status: target architecture reference

This document records the intended end-to-end contract for AI-authored equations. It is deliberately cross-repository: Al-Bayan orchestrates and persists, Burhan translates, and BuTeX imports/edits/renders/reconstructs structured mathematics.

Relevant work:

- Al-Bayan #170 — store Burhan Arabic MathObject directly in Document2
- BuTeX #19 — verify Arabic MathObject import -> English export round trip
- BuTeX #20 — graceful support for imported standard LaTeX commands
- Burhan #3 — emit Arabic LaTeX macros as structured command nodes
- Burhan #4 — reverse command-valued mappings such as `d -> \\ad`

## Product principle

Al-Bayan is an Arabic journal. The author-facing mathematical experience is Arabic-first.

Canonical English LaTeX exists as the interoperability language between a general-purpose AI and the journal. It is not a second stored equation representation and it is not the authoring language exposed by the BuTeX toolbar.

## Sources of truth

There are only two durable sources of mathematical state:

1. **The current Document2 draft**. Each equation is stored as the normal structured math token inside the article's existing Document2 `document.json` in S3. There is no separate equation store and no duplicate English equation JSON.
2. **The article-level variable-mapping dictionary** in the Al-Bayan database. It stores mappings such as `x -> س` and is reused for both forward and reverse conversion.

Al-Bayan should not become a mathematical AST transformation layer. It should orchestrate services, validate the normal Document2 contract, persist the Document2 result, and persist mappings consistently with the successful draft mutation.

## AI write path

The AI never constructs recursive MathObject JSON.

It discovers the supported authoring contract through the normal MCP math-capabilities surface and produces canonical/interoperable English LaTeX. It then uses the existing `apply_draft_command` flow with the normal inline-token operations (`insert_inline_token` or `replace_inline_token`).

Conceptually:

```text
AI
  |
  | canonical English LaTeX
  v
normal Al-Bayan MCP
  |
  | apply_draft_command / inline math token
  v
Al-Bayan backend
  |
  | load current article variable mappings (possibly {})
  v
Burhan /convert
  |
  | canonical English LaTeX + current mappings
  v
Burhan structured conversion
  |
  | arabic_json + resolved/new mappings
  v
Al-Bayan backend
  |
  | use Burhan arabic_json as the equation MathObject
  | no local English->Arabic AST projection/rewrite
  v
normal Document2 command / schema checks
  |
  v
article Document2 document.json in S3
  |
  v
BuTeX
  |
  v
Arabic article/editor rendering
```

### Forward-conversion rules

1. Al-Bayan loads the article's current mapping dictionary and sends it to Burhan with the canonical English LaTeX.
2. Burhan owns mathematical parsing and translation. Its returned `arabic_json` must already be structurally correct (for example `\\ad` is a command node, not text hidden inside a CharObject).
3. Al-Bayan feeds that returned Arabic MathObject into the normal Document2 path **as is**, apart from the ordinary Document2/token metadata and schema checks required by the document system.
4. Al-Bayan must not rebuild the Arabic tree by starting from `english_json` and substituting mapped strings into CharObjects. The historical `_editor_math_object()` projection is not part of the target architecture.
5. Newly discovered mappings are merged into the article mapping dictionary only if the corresponding draft mutation succeeds.
6. The equation is persisted only once: as its normal MathObject inside the article's Document2 `document.json`.

If Burhan cannot return a valid structured MathObject at all, the mutation should fail cleanly rather than inventing another representation. Graceful fallback applies to valid imported standard commands inside a structured equation; it is not a license to persist arbitrary malformed output.

## BuTeX import/render behavior

BuTeX receives the stored Arabic MathObject and uses its existing Arabic structured import path (`fromMathObjectJson(..., "arabic")`) to construct the editor tree and render/edit the equation.

The preferred result is fully Arabic mathematical notation. However, a valid structured equation may occasionally still contain standard LaTeX commands because Burhan passed one through or because an older/imported equation contains them.

Those commands should be treated as **compatibility fallback content**:

- import them instead of rejecting the entire equation;
- render them normally (`α`, `γ`, `∂`, etc.);
- preserve scripts/structure and save/reopen behavior;
- keep them selectable/deletable/replacable;
- preserve/export them if the user leaves them untouched;
- show a non-blocking warning that standard/non-Arabic notation remains and should be reviewed/replaced with the Arabic-oriented equivalent when appropriate.

This warning is intentionally **not** a hard editor error.

Standard-command compatibility must also remain separate from authoring affordances. The Arabic-oriented toolbar must **not** gain buttons, palette entries, or insertion actions for Greek/standard-English LaTeX merely because those commands are accepted on import.

```text
import/render/save compatibility: YES
toolbar authoring of fallback commands: NO
```

The user can delete a fallback command and replace it using the existing Arabic-oriented BuTeX controls.

## AI read path (`get_draft_equations`)

`get_draft_equations` live-projects equations from the current Document2 draft. It must not read a duplicated equation store.

The reverse path is:

```text
article Document2 document.json
  |
  | stored Arabic MathObject
  v
BuTeX structured import
  |
  | reconstruct/export English-side structured MathObject
  v
Al-Bayan backend
  |
  | English-side MathObject + article variable mappings
  v
Burhan /convert-to-english
  |
  | reverse mapped Arabic values/macros and canonicalize
  v
canonical English LaTeX
  |
  v
get_draft_equations
  |
  v
AI
```

### Reverse-conversion rules

1. The current stored Document2 equation is authoritative.
2. BuTeX owns the structural reconstruction from the stored Arabic editor representation to its English/canonical-side structured MathObject. Al-Bayan should not reproduce BuTeX's editor semantics in Python.
3. Al-Bayan sends that English-side MathObject plus the article's mapping dictionary to Burhan `/convert-to-english`.
4. Burhan performs the final cleanup/canonicalization. This includes reversing mapped values even when the Arabic-side value is itself a command with no Arabic Unicode, for example `d -> \\ad`.
5. `get_draft_equations` returns canonical English interoperability LaTeX to the AI together with targeting identity and the article mappings; it does not expose internal Arabic/BuTeX macros as the canonical AI representation.
6. Because this projection is live, human edits in BuTeX are naturally reflected the next time the AI fetches equations.

## MCP read surfaces

### `get_draft_outline`

Lightweight navigation.

### `get_draft_blocks`

Prose, document structure, and stable targeting identities. It should not duplicate recursive equation AST payloads.

### `get_draft_equations`

Equation-specific inspection and targeting. Its compact response should include current revision identity, Arabic-document context, article mappings, stable block/field/token IDs, canonical English LaTeX, inline/display state, label, and relevant warnings/editability state.

Recursive Arabic/English MathObject JSON is an internal service boundary, not the normal AI-facing payload.

## Article-level variable mappings

Mappings are scoped to the article and stored once in the existing Al-Bayan database model. The same dictionary participates in both directions:

```text
AI English LaTeX + mappings -> Burhan /convert -> Arabic MathObject
Arabic document -> BuTeX English reconstruction + mappings -> Burhan /convert-to-english -> AI English LaTeX
```

A mapping-only edit does not automatically rewrite existing Document2 equations. Temporary mapping/equation mismatches must therefore produce explicit warnings/fallback behavior rather than crashes or fabricated exact mappings.

## Responsibility boundaries

| Component | Responsibility |
| --- | --- |
| AI / normal MCP | discover allowed math syntax; author canonical English LaTeX; receive canonical English LaTeX on reads |
| Al-Bayan | orchestration, article mapping persistence, normal Document2 persistence/validation, MCP projection |
| Burhan `/convert` | canonical English LaTeX -> structurally correct Arabic MathObject JSON + mappings |
| BuTeX | import/edit/render stored Arabic structured math; reconstruct/export English-side structured math |
| Burhan `/convert-to-english` | final reverse mapping and canonical English LaTeX cleanup |
| Document2 | the single document/equation persistence model |

## Important boundaries

Keep the architecture small:

- no `EquationBlock`;
- no equation-specific MCP CRUD API;
- no AI construction of recursive MathObjects;
- no duplicate English equation store;
- no separate Arabic equation store;
- no Al-Bayan-specific mathematical AST rewrite layer;
- no per-equation provenance/source-history system unless a later product requirement explicitly needs one;
- no automatic rewrite of all equations after a mapping-only edit;
- no weakening of normal Document2 validation;
- no standard/English fallback-command buttons in the Arabic BuTeX toolbar.

## Verification requirement

A change is not complete merely because an internal converter test passes. Verify the complete development path:

```text
normal MCP canonical LaTeX insertion
-> Al-Bayan backend
-> Burhan Arabic JSON
-> Document2 storage
-> BuTeX browser render/edit
-> BuTeX English reconstruction
-> Burhan reverse conversion
-> normal MCP get_draft_equations
-> canonical English LaTeX
```

The final user-facing verification must use the normal Al-Bayan MCP; Dev MCP and browser diagnostics are supporting evidence, not substitutes for the product path.

## Canonical-v2 reader preparation

[The phase 1 contract](math-authoring-contract-v2.md) defines additive host/MCP
reader fields and the cross-repository delivery gates. New-profile mutations are
currently disabled. Live capability discovery remains v1; the existing producer
and reverse path remain unchanged. The contract records the historical projection
discrepancy and requires an explicit producer decision before phase 6 activation.
