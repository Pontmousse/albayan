# BuTeX Document Validation Contract

## Context

Al-Bayan lets authors save incomplete drafts, but it must not compile an invalid
document. In particular, a figure block with no selected image currently exports
as `\includegraphics[...]{}`, which must be treated as an editor error rather than
ignored or removed.

The host application should not duplicate BuTeX's document rules or understand
individual editor errors. BuTeX owns validation and the UI that identifies the
invalid field; the host only needs a validity boolean.

## Required package API

Export a framework-independent function from `@drghaliasri/butex/document2`:

```ts
export function isDocument2Valid(
  document: Document2Json | Document2Node,
): boolean;
```

Requirements:

- Return `false` for malformed input and for every condition that would produce
  invalid or unsafe LaTeX.
- Return `false` when a `\includegraphics` block has neither a non-empty
  `asset_id`/`assetId` nor a non-empty `value`.
- Apply the same validation recursively to blocks nested in list items.
- Treat existing parser diagnostics that prevent a reliable export as invalid.
- Do not mutate, remove, or silently ignore invalid content.
- Give identical results for equivalent wire JSON and runtime document nodes.
- Keep the function deterministic and usable in browsers and Node workers.

Add an optional React callback to `ButexDocumentEditor2Props`:

```ts
onValidityChange?: (isValid: boolean) => void;
```

Requirements:

- Invoke it after initial document resolution and whenever an edit changes
  validity.
- Avoid duplicate emissions when the boolean has not changed.
- Derive the callback from the exact same validation used by
  `isDocument2Valid`; there must not be separate rule sets.
- Preserve all existing document-change callbacks and editor behavior.

## Editor UX owned by BuTeX

BuTeX must visibly identify invalid content inside the editor even though the
public host contract is only a boolean:

- Mark each invalid block or field with the existing error colors and accessible
  error semantics.
- For an empty figure, show an Arabic message such as
  `لم تُحدّد صورة لهذه الكتلة.` and the normal image-selection action.
- Do not delete the empty figure, ignore it during export, or export
  `\includegraphics{}`.
- Existing invalid keys, equations, references, tables, and other export-blocking
  errors must contribute to the same document validity state.
- Localize messages through the package's existing `uiLocale` mechanism.

## Export invariant

LaTeX export must never silently succeed for a document for which
`isDocument2Valid(document)` is `false`. The preferred behavior is for
`document2Latex` to throw a typed validation error before producing LaTeX. At a
minimum, this invariant and the required precondition must be documented.

## Acceptance tests

The package change is complete when automated tests demonstrate that:

1. A valid empty document reports `true`.
2. A figure with a valid `asset_id` reports `true`.
3. A figure with a valid literal `value` reports `true`.
4. A figure with missing, empty, or whitespace-only image identity reports
   `false` in both JSON and runtime-node representations.
5. Invalid nested content reports `false`.
6. Parser/export-blocking diagnostics report `false`.
7. The React callback emits the initial validity and changes only when validity
   changes.
8. An empty figure is visibly marked in Arabic and English UI locales.
9. Invalid documents cannot be silently exported to LaTeX.
10. Saving and round-tripping an invalid draft preserves its content so the user
    can repair it later.

## Al-Bayan integration after release

Once a release containing this contract is available, Al-Bayan will replace its
temporary `isButexDocumentValid` compatibility helper with
`isDocument2Valid`, pass `onValidityChange` to the editor, continue allowing
draft saves, warn after an invalid draft is saved, and block compilation while
the boolean is `false`.
