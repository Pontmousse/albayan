# Equation architecture reference

This document summarizes the agreed Al-Bayan equation design captured in GitHub issues #99, #109, #110, #111, and #112. It is a reference for implementation; the linked issues remain the detailed acceptance criteria.

## Design goals

Al-Bayan is an Arabic mathematical journal. Authors work with Arabic mathematical notation, while current general-purpose AI models receive canonical English LaTeX as a compact interoperability representation.

Keep the architecture small:

- the current BuTeX Document2 math token is the source of truth for each equation;
- equations remain inline-field math tokens, not a new `EquationBlock`;
- persist one article-level Latin-to-Arabic variable mapping dictionary;
- do not persist duplicate English equation JSON, original LaTeX, provenance, or per-equation mapping/history records;
- do not expose recursive BuTeX `MathObject` JSON to the AI when a compact representation is sufficient;
- do not introduce equation-specific CRUD tools when existing inline-token commands already provide the right targeting model.

## Source of truth and persistence

The canonical Document2 draft remains authoritative for equation content. Each structured equation lives in its existing inline field and keeps the normal stable block, field, and token identities.

Albayan adds only one small piece of durable equation state: an article-level Burhan variable mapping dictionary, conceptually:

```json
{
  "E": "ط",
  "m": "م",
  "c": "س"
}
```

The intended implementation is a JSON column on the existing article record. It is the article's current notation vocabulary and is shared by human and AI equation workflows.

Existing mappings remain stable when Burhan discovers new variables unless the author explicitly edits them. Restoring an older draft does not require rolling the mapping dictionary backward.

## Reading equations through MCP

`get_draft_equations(article_id)` is the dedicated AI-facing equation read surface.

It is a live projection of the current draft, not another equation store. For each structured math token:

1. read the current Document2 MathObject;
2. if it is already English-side, render canonical English LaTeX;
3. if it is Arabic-side, use Burhan's reverse projection together with the article mappings;
4. return a compact targetable record.

The response should include the current revision identity, explicit Arabic-document context, `equation_representation: "canonical_english_latex"`, the current variable mappings once at the top level, and compact equation records containing stable targeting IDs, canonical LaTeX, display/inline state, label, and editability where relevant.

It must not expose recursive English or Arabic MathObject JSON, provenance-style state, duplicated source strings, or automatically attach surrounding paragraph/section context.

Raw/unstructured math stays explicit and must not be presented as if it had a reversible structured representation.

If a human has changed a notation mapping while an older equation still contains the previous Arabic symbol, reverse projection should degrade with a compact warning/fallback instead of crashing or inventing an exact mapping.

## Keeping `get_draft_blocks` compact

`get_draft_blocks` remains the AI's prose, structure, and targeting view. It should preserve useful content, block order, stable block/field/token IDs, and list/table/caption structure, but recursively omit heavy equation AST payloads such as `math_objects`, `caption_math_objects`, and equivalent nested structured-math collections.

The intended MCP separation is:

```text
get_draft_outline
  -> lightweight navigation

get_draft_blocks
  -> prose/content structure + stable targeting IDs

get_draft_equations
  -> equations + equation targeting IDs + article variable mappings
```

Canonical Document2 storage and lower-level BuTeX validation remain unchanged.

## Editing equations through MCP

Do not add `add_equation`, `replace_equation`, or `remove_equation` MCP tools.

Use the existing generic Document2 inline-token operations:

- `insert_inline_token`
- `replace_inline_token`
- `remove_inline_token`

For insertion/replacement, the AI supplies ordinary LaTeX in a compact math-token input rather than recursive `MathObject` JSON. Albayan then:

1. loads the article mappings;
2. normalizes delimiters and inline/display intent;
3. calls trusted Burhan parsing/conversion endpoints;
4. obtains the complete source and BuTeX-compatible structured MathObject;
5. validates that generated token against the strict Albayan/Document2 schema;
6. passes the expanded existing inline-token command into the normal draft-command/worker flow;
7. persists newly discovered mappings only together with a successful draft mutation.

The lower-level BuTeX worker contract remains strict. Revision conflicts, `base_revision`, command idempotency, stable target validation, and canonical document validation continue to use the existing draft-command machinery.

Removing an equation needs no Burhan conversion and remains a normal `remove_inline_token`.

A standalone display equation is still a math token in an inline field; this design does not create an EquationBlock.

## Human notation controls

The article editor gets a small Arabic-first mathematical notation panel backed by the same article mapping dictionary.

Authors can inspect and edit Latin-to-Arabic variable choices. The UI should support the smallest safe add/edit/remove-or-reset workflow and normal validation/loading/error feedback.

Changing a mapping does **not** automatically rewrite existing equations. It changes the article's current notation preference for future Burhan/AI work. Existing equations remain untouched until the author or AI explicitly revises them.

This avoids bulk propagation machinery, per-equation notation state, and hidden document mutations.

## Atomicity and failure behavior

AI equation insertion/replacement must not leave mappings or drafts half-updated:

- a failed Burhan call changes neither draft nor mappings;
- a failed Document2 mutation does not persist newly discovered mappings;
- generated source delimiters and MathObject mode/closing delimiters must agree;
- mapping conflicts and unsupported/invalid LaTeX should produce small stable errors;
- Burhan timeout/unavailability or incompatible responses should not leak arbitrary upstream payloads.

A standalone human mapping edit intentionally changes only the mapping dictionary and does not create a hidden draft revision or rewrite equations.

## Component responsibilities

| Component | Responsibility |
| --- | --- |
| BuTeX / Document2 | Canonical equation AST/token model, stable inline identities, strict mutation and validation primitives |
| Burhan | Deterministic LaTeX parsing/conversion and Arabic-to-canonical-English reverse projection |
| Albayan backend | Article mapping persistence, Burhan orchestration, validation, atomic integration with draft mutations |
| Albayan MCP | Compact equation discovery and normal-LaTeX authoring over existing inline-token commands |
| Article editor | Arabic-first human control of the shared notation mapping dictionary |

## Explicit non-goals

- no EquationBlock;
- no equation-specific MCP CRUD tools;
- no duplicate English/Arabic MathObject persistence;
- no original-English-LaTeX archive;
- no provenance/state machine;
- no per-equation mapping records;
- no automatic bulk propagation after a mapping edit;
- no recursive equation ASTs in normal AI read surfaces.

## Issue map

- #99 — compact live `get_draft_equations` projection.
- #109 — article-level Burhan variable mapping persistence.
- #110 — normal-LaTeX math authoring through existing inline-token commands.
- #111 — Arabic mathematical notation / mappings panel for authors.
- #112 — slim `get_draft_blocks` so recursive equation MathObject JSON is not sent to the AI.

Together these issues define one workflow: Document2 owns canonical equations, Burhan translates at the boundary, Albayan stores only the shared notation vocabulary, and both human and AI interfaces stay compact.
