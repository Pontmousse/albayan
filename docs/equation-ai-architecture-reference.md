# AI Equation Architecture Reference

Status: design reference

This document summarizes the target equation architecture agreed across the five Al Bayan issues below. It is a reference for implementation work; the issue acceptance criteria remain authoritative for task-level details.

- [#99 — `get_draft_equations` compact Arabic-journal projection](https://github.com/Pontmousse/albayan/issues/99)
- [#109 — persist article-level Burhan variable mappings](https://github.com/Pontmousse/albayan/issues/109)
- [#110 — author math through existing inline-token commands](https://github.com/Pontmousse/albayan/issues/110)
- [#111 — Arabic mathematical-notation / variable-mappings editor UI](https://github.com/Pontmousse/albayan/issues/111)
- [#112 — slim `get_draft_blocks` and omit recursive equation JSON](https://github.com/Pontmousse/albayan/issues/112)

The reverse-conversion dependency lives in Burhan: [`burhan3.0#1`](https://gitlab.com/drghaliasri/burhan3.0/-/work_items/1).

## Product principle

Al Bayan is an Arabic journal. The author-facing mathematical experience remains Arabic-first, including notation and rendered equations.

Canonical English LaTeX is used only as an interoperability representation for today's general-purpose AI models. It is not the journal's user-facing mathematical language and it is not a second source of truth.

## Sources of truth

There are two deliberately small, distinct kinds of state:

1. **The current immutable Document2 draft** is authoritative for actual document content and equations. Equations remain normal Document2 math tokens inside inline fields; there is no separate equation block or equation persistence model.
2. **The article-level variable-mapping dictionary** is authoritative for the article's current Latin-to-Arabic notation choices, for example `m -> م` or `E -> ط`.

Do not persist duplicate English equation JSON, original AI LaTeX, per-equation provenance, or a second equation store.

## Read path for AI

The MCP read surface is intentionally split by purpose.

### `get_draft_outline`

Use for lightweight navigation through the document.

### `get_draft_blocks`

Use for prose, document structure, and stable targeting identities.

The AI-facing projection must preserve the information needed to understand and target blocks, fields, lists, tables, captions, and inline tokens, but it must omit recursive equation AST payloads such as `math_objects`, `caption_math_objects`, and equivalent nested structured-math collections.

The canonical Document2 draft is not changed or weakened. The context reduction happens at the AI/MCP read boundary.

### `get_draft_equations`

Use for equation-specific inspection and targeting.

The tool live-projects the **current** Document2 math tokens rather than reading a duplicated equation store. Its compact response includes:

- current revision identity;
- explicit Arabic-document context;
- an indication that surfaced LaTeX is canonical English interoperability LaTeX;
- the article-wide variable mappings once at the top level;
- stable `block_id`, `field_id`, and `token_id` identities;
- minimal container/location data when needed;
- canonical English LaTeX;
- inline/display state, label, and structured/editable state when relevant.

It does not return recursive Arabic or English `MathObject` JSON.

For an Arabic structured equation, Albayan calls Burhan's reverse projection with the current article mappings to derive canonical English MathObject/LaTeX. For an English-side structured equation, it renders canonical English LaTeX directly. Raw/unstructured math remains explicit and must not be presented as losslessly reversible structured math.

Because this is a live projection, a human edit to the current equation naturally appears on the next read.

## Write path for AI

Do not add equation-specific MCP CRUD tools.

The AI continues to use the existing `apply_draft_command` path and the generic Document2 inline-token operations:

- `insert_inline_token`
- `replace_inline_token`
- `remove_inline_token`

For a math insertion or replacement, the AI-facing command supplies ordinary LaTeX rather than recursive `MathObject` JSON. Conceptually:

```json
{
  "op": "replace_inline_token",
  "field_id": "field_8",
  "token_id": "math_17",
  "token": {
    "kind": "math",
    "latex": "\\frac{d}{dx}f(x)=3x^2",
    "display": true
  }
}
```

Albayan then:

1. loads the article's current variable mappings;
2. normalizes and validates the requested math form;
3. calls the trusted Burhan parsing/conversion path instead of asking the model to construct an AST;
4. builds a complete delimited source plus the matching structured BuTeX MathObject;
5. validates that token against the strict Document2 schema;
6. passes the expanded existing inline-token command through the normal draft-command/worker flow;
7. persists any newly discovered mappings only with the successful draft mutation.

The lower-level Document2 worker contract remains strict. Revision conflicts, `base_revision`, command idempotency, target validation, and canonical draft validation stay in the existing draft-command flow.

Removal remains the ordinary `remove_inline_token` operation and does not require Burhan conversion.

## Article-level variable mappings

Persist one small mapping dictionary on the existing article model, preferably a JSON column such as `equation_mappings`, defaulting to `{}`.

The mapping dictionary is:

- scoped to the article, not to individual equations;
- reused for forward and reverse Burhan operations;
- stable as new variables are introduced;
- explicitly editable by the human author;
- surfaced only where it is useful: `get_draft_equations` and the notation UI.

Do not create a new table unless a concrete later requirement makes the single-column design unsafe.

When an AI equation mutation discovers new mappings, mapping persistence and the draft mutation must be consistent: a failed equation mutation must not leave new mappings committed.

## Author-facing Arabic notation UI

The article editor should expose a compact Arabic-first mathematical-notation panel where an author can inspect and edit the article's current variable mappings.

A mapping-only edit changes the notation dictionary, **not** the existing Document2 equations. There is deliberately no automatic bulk-propagation engine.

If an author changes a preference after equations already exist, those equations may temporarily contain the older Arabic symbol. The author can ask the AI to revise the affected equations explicitly through the normal inline-token workflow.

`get_draft_equations` and Burhan reverse projection must therefore tolerate a temporary mapping/equation mismatch with explicit warning/fallback behavior. They must not crash and must not fabricate an exact reverse mapping.

## End-to-end flow

```text
Human author / general-purpose AI
            |
            | Arabic prose + simple equation intent
            v
        Al Bayan MCP
            |
   +--------+-------------------------+
   |                                  |
read                                  write
   |                                  |
get_draft_blocks                apply_draft_command
(prose/structure/IDs)                 |
   |                           inline-token command
   |                           with ordinary LaTeX
   |
get_draft_equations                    |
(equations + mappings)                 v
   |                              Albayan backend
   |                                  |
   |                         load article mappings
   |                                  |
   |                                  v
   +----------------------------->   Burhan
                                      |
                          parse / forward convert
                          reverse project on reads
                                      |
                                      v
                            strict MathObject token
                                      |
                                      v
                            Document2 draft worker
                                      |
                                      v
                        immutable current revision
                                      |
                                      v
                                  BuTeX render
                                      |
                                      v
                               Arabic article UI
```

## Important boundaries

Keep the design small:

- no `EquationBlock`;
- no equation-specific add/replace/remove MCP tools;
- no recursive equation JSON in AI read responses;
- no AI construction of recursive MathObjects;
- no duplicate English equation store;
- no per-equation provenance or source-history system;
- no automatic rewrite of existing equations after a mapping-only edit;
- no weakening of canonical Document2 storage or worker validation.

## Dependency and implementation order

A practical order is:

1. **#109** — article-level mapping persistence and service helpers;
2. **Burhan reverse projection** — Arabic MathObject + mappings to canonical English MathObject/LaTeX;
3. **#99** — compact `get_draft_equations` read projection;
4. **#110** — simple-LaTeX normalization into the existing inline-token mutation path;
5. **#111** — author-facing notation/mapping panel;
6. **#112** — slim `get_draft_blocks` so equation-heavy drafts no longer duplicate recursive equation context to the model.

#99 and #112 should ultimately be treated as a paired MCP read-contract change: equations belong in the dedicated compact equation projection, while block reads remain focused on prose, structure, and stable targeting.

## Long-term compatibility

This design intentionally does not make English LaTeX part of the product identity. It keeps English LaTeX as a replaceable AI interoperability layer while preserving structured Arabic math, author-controlled notation, and BuTeX rendering as the durable system boundaries. That leaves room for a future Arabic-native mathematical model or Arabic alias language without requiring a new document model.