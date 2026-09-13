# Document2 React / Headless Command Parity Audit

Status: Phase 1 audit complete; the recommended Phase 2 commands are implemented
in the published worker contract.

Baseline: BuTeX `7.0.2` (2026-09-12).

## Surfaces Compared

- React authoring in `ButexDocumentEditor2`: metadata, references, labels,
  blocks, inline content, lists, tables, and figures.
- Public `@drghaliasri/butex/document2` helpers and canonical `Document2Json`.
- `Document2Command`, `applyDocument2Command`, and the stateless worker.

**Supported** means expressible through current commands. **Host-owned** means
intentionally outside document commands. **Deferred gap** means a real parity
gap that is not part of the current complete-article workflow.

## Findings

### Top-level blocks

**Supported**

- Insert section, subsection, subsubsection, paragraph, list, table, figure, and
  bibliography blocks at stable before/after/end anchors.
- Replace a plain text block, remove a top-level block, and move one by stable ID.
- Preserve creation provenance (`metadata.source`) while editing.

**Deferred gaps**

- Raw blocks remain import/export compatibility content without authoring commands.
- Paragraph centering has a React control but no command.
- Imported nested blocks in list items round-trip, but construction and general
  movement remain top-level.

### Inline content, math, citations, and references

**Supported**

- Insert, replace, and remove text, structured math, citation, and reference
  tokens by stable field/token IDs.
- Lookup covers text blocks, list items, nested list content, and table cells.
- Text styles are bold, italic, and underline; clients can split and replace
  tokens to reproduce styled ranges.
- Math requires one complete delimited source and a matching structured
  `MathObject`; the worker does not parse equation LaTeX into an AST.
- Math labels travel in `MathObject` JSON, and citations or `ref`/`eqref` keys
  are structured token fields.

Full draft validation stays separate because Document2 permits temporarily
invalid drafts.

**Deferred gaps**

- React provides caret-offset conveniences and direct style toggles while the
  headless API works at token boundaries.
- A label-only math command would be convenience only; structured replacement
  already carries `label_enabled` and `label`.

### Lists

**Supported**

- Insert ordered or unordered top-level lists with initial items.
- Insert, replace, remove, and reorder items using stable list/item IDs.
- Recursive lookup supports imported nested lists; inline commands edit their
  structured fields.
- Lists retain at least one item.

**Deferred gaps**

- Commands cannot construct a nested block inside an item.
- List kind cannot be toggled after insertion.

### Tables

**Supported**

- Insert a non-empty rectangular table with an explicit LaTeX column spec.
- Replace plain cells and insert/remove/move rows and columns.
- Use inline commands for structured table-cell content.
- Update captions and labels through `update_float_meta`.
- Target imported nested tables by stable block ID.

The headless row/column surface is broader than the current React table UI.

### Figures

**Supported**

- Insert figures with a host asset, include value, caption, label, provenance,
  and stable anchor.
- Update or clear asset associations and include values.
- Update centering, captions, and labels through `update_float_meta`.

**Host-owned**

- Upload, storage, inventory, URL resolution, authorization, and picker UI.

**Deferred gaps**

- Empty figure placeholders and arbitrary `includegraphics` option editing are
  not part of the headless workflow.

### Metadata, references, and bibliography

**Supported**

- Patch title, authors, abstract, and partial Hijri dates.
- Insert, update, remove, and reorder references by normalized key, including
  authors, title, year, venue, URL, and Arabic/Latin field separators.
- Insert one bibliography block whose entries derive from the ordered reference
  catalog rather than a second data model.
- Use one shared namespace for reference, figure, table, and equation keys.

Removing or renaming a reference preserves citation tokens, matching editor
behavior; a later command may repair the temporarily invalid draft.

### Editor-visible behavior outside commands

**Host-owned or UI-only**

- Users, articles, permissions, sessions, revisions, idempotency, storage,
  saving, submission, and asset authorization.
- Undo/redo, selection, caret/focus, collapsed blocks, responsive UI, locale,
  preview, dialogs, clipboard actions, and validity notifications.

These do not belong in `Document2Command` or the worker.

### Derived and read-only APIs

Canonical import/export, normalization, outline, validation, preview, and LaTeX
export exist in the Document2 package. The deployed worker exposes normalization
and outline alongside command application. Future remote validation or export
should be a separate read-only worker action, not a mutation command.

## Current Host-facing Command Set

BuTeX 7.0.2 publishes 29 operations:

1. `insert_text_block`, `replace_text_block`, `remove_block`, `move_block`.
2. `insert_figure`, `update_figure`, `update_float_meta`,
   `insert_bibliography`.
3. `update_document_meta`, plus reference insert/update/remove/move.
4. Inline-token insert/replace/remove.
5. List insert and list-item insert/replace/remove/move.
6. Table insert, cell replacement, and row/column insert/remove/move.

Excluded intentionally: nested-block construction, raw authoring, paragraph
centering, arbitrary image options, UI state, persistence, revisions,
authentication, and asset storage.

## Compatibility Conclusion

The current worker covers the complete-article workflow while remaining
stateless. Albayan must mirror its union at the typed FastAPI boundary and keep
all host and session concerns outside Node.

## Upstream Source Map

- Vocabulary/errors: `src/document2/jsonCommandTypes.ts`.
- Parsing/dispatch/output: `src/document2/jsonCommands.ts`.
- Inline/list/table behavior: `src/document2/*JsonCommands.ts`.
- Editor behavior: `src/document2/commands.ts` and
  `src/react-document2/ButexDocumentEditor2.tsx`.
- Metadata/references/labels: `src/document2/types.ts`, `articleMeta.ts`,
  `citations.ts`, `labels.ts`, and `exportJson.ts`.
- Worker boundary: `src/document2-cli/execute.ts`.
