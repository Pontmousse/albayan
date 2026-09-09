# BuTeX document editor legacy-removal and rename audit

## Purpose

This report inventories the work required to remove the legacy BuTeX React
document editor first, and only then promote the current editor from
`ButexDocumentEditor2` to `ButexDocumentEditor`.

This is a refactor plan, not an implementation. No editor source was deleted or
renamed while producing this audit.

## Refactor rule: temporary breakage is allowed

The work should be performed in the phases below, in order. During this
refactor it is explicitly acceptable for BuTeX, its demos, Al-Bayan, imports,
builds, type checks, or tests to be temporarily broken between phase commits.
Do not add compatibility aliases merely to keep every intermediate commit
green.

Temporary breakage does not make an intermediate package publishable. Do not
publish BuTeX, deploy its document worker, or merge the Al-Bayan dependency
bump until the final verification phase is green.

The required order is intentional:

1. Delete the legacy React editor and free its canonical names.
2. Rename/promote the current React editor into those names.
3. Publish the breaking BuTeX release.
4. Migrate Al-Bayan to that release.

## Audit boundary and repository snapshot

The audit follows the two repositories that participate in the integration:

- `../butex` is the BuTeX source repository. It contains both editor
  implementations.
- The current Al-Bayan repository consumes the published BuTeX package from
  `frontend/` and also documents the worker/MCP contracts.

The inspected working trees were clean at the time of the audit.

- Al-Bayan: commit `53efd52`.
- BuTeX: commit `ffbf1ff` on `main`.

There is version drift that must be resolved before implementation:

- `../butex/package.json` says `6.1.1`.
- Al-Bayan's `frontend/package.json` requests `^6.1.5`, and
  `frontend/package-lock.json` locks `6.1.5`.
- Al-Bayan's installed, untracked `frontend/node_modules` copy reports `6.1.2`.

The source audit below uses the adjacent BuTeX repository plus the tracked
Al-Bayan consumer code. Before editing, synchronize the intended BuTeX source
branch/tag with the `6.1.5` API that Al-Bayan actually locks, then rerun the
residual searches in this report. Do not treat the local `node_modules` copy as
source of truth.

## The naming boundary

### Names that should be promoted

The final public React editor surface should be unversioned:

- Package subpath: `@drghaliasri/butex/react-document2` becomes
  `@drghaliasri/butex/react-document`.
- Component: `ButexDocumentEditor2` becomes `ButexDocumentEditor`.
- Component types: `ButexDocumentEditor2Props` and
  `ButexDocumentEditor2Ref` become `ButexDocumentEditorProps` and
  `ButexDocumentEditorRef`.
- Editor initialization surface: `Document2InitialState` and
  `resolveInitialDocument2` become `DocumentInitialState` and
  `resolveInitialDocument`.
- Style surface: `DOCUMENT2_WIDGET_CSS` and
  `injectBuTeXDocument2Styles` become `DOCUMENT_WIDGET_CSS` and
  `injectBuTeXDocumentStyles`.
- React source paths: `src/react-document2/` and
  `src/react-document2-entry.ts` become `src/react-document/` and
  `src/react-document-entry.ts`.
- Editor source filenames: `ButexDocumentEditor2.tsx` and
  `documentWidgetCss2.ts` become `ButexDocumentEditor.tsx` and
  `documentWidgetCss.ts`.
- DOM/CSS surface: `.butex-document2-widget*`,
  `--butex-document2-*`, and `butex-document2-widget-styles` become their
  unversioned `.butex-document-widget*`, `--butex-document-*`, and
  `butex-document-widget-styles` forms.
- Demo surface: `demo/document-editor-app2` and its local
  `document2-demo-*` names become `demo/document-editor-app` and
  `document-demo-*`.

`ResolveDocument2ImageUrl` is exported from the React preview surface and
should be reviewed with the same naming pass; `ResolveDocumentImageUrl` is the
consistent final name. Internal UI-only `document2Messages` and
`Document2Messages` should likewise become `documentMessages` and
`DocumentMessages` because they describe the promoted editor rather than the
underlying AST version.

### Names that should remain versioned in this refactor

Do not mechanically remove every `2` in the repository. The following names
belong to the current headless document model and remote worker contract, not
to the duplicate React editor:

- `src/document2/` and the `@drghaliasri/butex/document2` package subpath.
- `Document2Json`, `Document2Node`, the `*2` AST node types, and functions such
  as `fromDocumentJson2`, `toDocumentJson2`, `document2Latex`,
  `document2Preview`, and `applyDocument2Command`.
- `src/document2-cli/`, the `butex-document2` executable, and
  `serve:document2`.
- Worker routes under `/v1/document2/*` and the health-service value
  `butex-document2`.

Those are a separate, much larger public-API and service migration. Renaming
them is not required to make the current React editor canonical. Keeping them
stable also means this refactor does not require a stored-document or database
migration: persisted documents already use the generic wire root
`node_type: "DocumentObject"`, and Al-Bayan stores/returns the JSON rather than
persisting the TypeScript type name.

### Do not delete the whole legacy `src/document/` layer yet

Removing the legacy React editor does not make all of `src/document/` safely
deletable. The current `document2` implementation still imports shared code
from it:

- `src/document2/mathBridge.ts` imports
  `src/document/mathEditorAdapter.ts` and `src/document/types.ts`.
- `src/document2/exportJson.ts`, `inlineJsonCommands.ts`, `exportLatex.ts`, and
  `importJson.ts` import `src/document/mathObject.ts`.

The dependencies beneath those files include shared equation/normalization
code. If removal of the old headless `@drghaliasri/butex/document` API is also
desired, first extract the shared modules to a neutral directory and give that
work its own migration plan. It must not be folded blindly into the React
editor deletion.

## Phase 0 — synchronize and freeze the target contract

Before deleting anything:

- Synchronize `../butex` to the source revision corresponding to the intended
  published starting version (at least the `6.1.5` surface locked by
  Al-Bayan).
- Confirm the final mapping in “Names that should be promoted.”
- Decide that there will be no deprecated `react-document2` or
  `ButexDocumentEditor2` alias in the final release. Temporary breakage already
  makes that compatibility shim unnecessary unless another consumer is found.
- Run repository-wide searches again after synchronization so files introduced
  after `ffbf1ff` are added to the lists below.
- Record a baseline `npm run build`, `npm run typecheck`, and `npm test` result
  in BuTeX. This is diagnostic only; it is not a requirement that every later
  intermediate phase stay green.

## Phase 1 — delete the legacy editor in `../butex`

### `src/`

Delete the old React implementation and entrypoint:

- `src/react-document/ButexDocumentEditor.tsx`
- `src/react-document/documentWidgetCss.ts`
- `src/react-document-entry.ts`

Do not delete `src/document/` in this phase for the dependency reasons above.

### Package/build surface

Edit these files to remove the old React bundle temporarily:

- `package.json`: remove the existing `./react-document` export. The same key
  will be recreated for the promoted editor in Phase 2.
- `tsup.config.ts`: remove the current `react-document` entry. Phase 2 will
  recreate it with the promoted source.

This intentionally leaves only `react-document2` available between the two
phases.

### Legacy tests

Delete `test/document_entrypoints.test.tsx`; it tests the old component,
legacy CSS injection, and the old entrypoint. Do not delete similarly named
equation-editor tests such as `test/gui_v1_editor.test.ts`: “v1” there refers to
the equation-editor protocol, not the legacy document editor.

The legacy headless tests `test/document_ast.test.ts` and
`test/document_editing.test.ts` should remain as long as `src/document/` and
the `./document` export remain.

### Legacy demo

Delete the ten tracked files under `demo/document-editor-app/` so the directory
name can be reused by the promoted demo:

- `.gitignore`
- `README.md`
- `copy-global.mjs`
- `index.html`
- `package-lock.json`
- `package.json`
- `src/main.tsx`
- `src/page.css`
- `tsconfig.json`
- `vite.config.ts`

`demo/document.html` points at the canonical demo. It may be temporarily
deleted or left broken in this phase, but it must be reviewed/recreated in
Phase 2 so it describes the promoted editor rather than the removed one.

### Legacy documentation and contributor guidance

Review these even though some do not contain the string `Editor2`:

- `AGENTS.md` currently declares the legacy `src/document/` model and old
  editor behavior as the repository's document-editor rules. Rewrite its
  “Document editor” section for the promoted implementation.
- `README.md` contains separate legacy and v2 React-widget sections. Remove the
  legacy section and rewrite the current section as the sole document editor.
- `docs/document-editor-plan.md` is the old editor plan and is referenced by
  `AGENTS.md`. Replace it with current canonical constraints, or mark it
  explicitly as superseded historical material and point to the current plan.
- `docs/document-editor-rewrite-report.md` documents the failed experiment
  conceptually. Retain it only as clearly labelled history, or remove it with
  the implementation; do not leave it looking like the active design.

## Phase 2 — promote the current editor in `../butex`

### `src/react-document2/` to `src/react-document/`

Move all 21 tracked files in the current editor directory. Two basenames also
change; the others keep their basename under the new directory.

- `ButexDocumentEditor2.tsx` becomes `ButexDocumentEditor.tsx`.
- `documentWidgetCss2.ts` becomes `documentWidgetCss.ts`.
- Move unchanged basenames: `ArticleMetaPanel.tsx`, `BlockEditor.tsx`,
  `CiteChip.tsx`, `CitePickerPopover.tsx`, `DocumentInsertToolbar.tsx`,
  `DocumentPreview.tsx`, `EquationDrawer.tsx`, `InlineField.tsx`,
  `LabelsPanel.tsx`, `MathChip.tsx`, `MathIsland.tsx`, `RefChip.tsx`,
  `RefPickerPopover.tsx`, `ReferencesPanel.tsx`, `TableInsertPopover.tsx`,
  `editorFocus.ts`, `imageAssets.ts`, `index.ts`, and `uiMessages.ts`.

Inside this directory:

- Apply the public symbol mapping from the naming-boundary section.
- Update imports/re-exports in `index.ts`.
- Update the component's named `forwardRef` function and its `displayName`.
- Update all local paths that name `ButexDocumentEditor2.tsx` or
  `documentWidgetCss2.ts`.
- Rename editor-specific UI names such as `document2Messages` only where they
  refer to the React editor. Keep model-oriented `Document2*` types, variables,
  guards, diagnostics, transforms, and imports unchanged.

### CSS contract

The class/custom-property rename is a real public breaking change, not an
internal cleanup. Apply it consistently across:

- `ArticleMetaPanel.tsx`
- `BlockEditor.tsx`
- `ButexDocumentEditor.tsx` after its rename
- `CiteChip.tsx`
- `CitePickerPopover.tsx`
- `DocumentInsertToolbar.tsx`
- `DocumentPreview.tsx`
- `EquationDrawer.tsx`
- `InlineField.tsx`
- `LabelsPanel.tsx`
- `MathChip.tsx`
- `MathIsland.tsx`
- `RefChip.tsx`
- `RefPickerPopover.tsx`
- `ReferencesPanel.tsx`
- `TableInsertPopover.tsx`
- `documentWidgetCss.ts` after its rename

The style injection ID must also change. Otherwise a page containing cached or
manually injected old CSS can suppress the new stylesheet because the injector
mistakes the old ID for the canonical stylesheet.

### Entrypoint, exports, and build

- Rename `src/react-document2-entry.ts` to
  `src/react-document-entry.ts` and update every export.
- In `package.json`, remove `./react-document2` and point
  `./react-document` at `dist/react-document.{d.ts,mjs,js}`.
- Update the root `package-lock.json` when the major package version changes;
  its root package version must agree with `package.json`.
- In `tsup.config.ts`, replace the `react-document2` build entry with
  `react-document: src/react-document-entry.ts`.
- Run a clean build. Generated `dist/react-document2*` files and source maps
  must not appear in the package tarball; do not hand-edit `dist/`.

This removal and public rename requires a major semver release. With the
currently observed 6.x line, the natural target is `7.0.0`.

### Current-editor tests

The following tests contain direct component names, paths, exported helper
names, CSS selectors, style IDs, or demo-path assertions and must be updated:

- `test/document2_entrypoints.test.tsx`: rename to the now-free
  `test/document_entrypoints.test.tsx`, then update imports, filesystem-path
  assertions, public symbols, package/tsup assertions, CSS selectors, style ID,
  and demo path.
- `test/document2_imperative_image.test.tsx`: update the entrypoint, component,
  ref type, and suite name. Renaming the file to
  `document_imperative_image.test.tsx` is recommended because it tests the
  editor API rather than only the v2 AST.
- `test/document2_provenance.test.tsx`: update the entrypoint and component.
  Rename the file only if its primary subject is the editor rather than the
  `Document2Json` provenance contract.
- `test/document2_article_meta.test.ts`: update the direct import of
  `resolveInitialDocument2` from the editor source. Keep the filename because
  most of the file tests `Document2` metadata.
- `test/document2_references_panel.test.ts`: update moved React source paths,
  UI-message naming if changed, CSS filename, and CSS selector expectations.

The remaining `test/document2_*.test.*` files exercise the headless model or
CLI and should not be renamed merely because the React editor becomes
canonical.

### Demo promotion

After the legacy demo directory is gone, rename the ten tracked files under
`demo/document-editor-app2/` into `demo/document-editor-app/`.

Within the promoted demo, update:

- `README.md`: heading, commands, and React import path.
- `package.json` and `package-lock.json`: change the local demo package name
  from `butex-document-editor-v2-demo` to an unversioned name.
- `vite.config.ts`: point `butex/react-document` at
  `dist/react-document.mjs`; keep the `butex/document2` alias unchanged.
- `src/main.tsx`: component import/uses, “v2”/“second editor” copy, and
  `document2-demo-*` class names. Keep `Document2Json` and
  `MathObject2Json` names.
- `src/page.css`: local demo classes and the promoted BuTeX widget selector and
  variables.
- `index.html`: remove “v2” from the title.
- `copy-global.mjs`: update the path in its usage comment after the directory
  move.
- `demo/editor-app/README.md`: replace its cross-reference to
  `document-editor-app2`.
- `demo/document.html`: make the pointer describe the promoted sole editor.

Ignored demo build output and copied vendor files may remain stale locally;
clean/rebuild them, but do not commit them as part of the rename.

### BuTeX documentation

Update current documentation to use the promoted component/path while retaining
`Document2` model terminology:

- `README.md`
- `AGENTS.md`
- `docs/book-editor-feasibility-report.md`
- `docs/book-editor-plan.md`
- `docs/superpowers/specs/2026-07-12-document2-block-selection-design.md`

For historical specs, either update references so links do not break after the
file move, or add an explicit historical-name note. A stale relative link to
`src/react-document2/ButexDocumentEditor2.tsx` is not acceptable even in a
historical report.

No editor-facing rename is required in `docs/document2-worker.md`,
`docs/fastapi-document2-worker-contract.md`, or
`src/document2-cli/README.md` while the headless/worker naming boundary remains
in force.

## Phase 3 — verify and publish BuTeX

Before publishing:

- Run `npm run build`.
- Run `npm run typecheck`.
- Run `npm test`.
- Build/run the promoted document-editor demo.
- Inspect `npm pack --dry-run` and the tarball file list.
- Smoke-test both ESM and CommonJS imports from
  `@drghaliasri/butex/react-document`.
- Confirm that importing `@drghaliasri/butex/react-document2` and requesting
  `ButexDocumentEditor2` fail intentionally.
- Confirm that `@drghaliasri/butex/document2` and `butex-document2` still work.
- Confirm no `dist/react-document2*` output is shipped.

The existing `ci/npm-publish.yml` and `ci/railway-deploy.yml` do not name the
React editor. Their `document2-cli` references remain correct because the
worker is out of scope. They need behavioral verification, not a rename.

## Phase 4 — migrate the Al-Bayan consumer

Only start this phase after the new major BuTeX version is available to the
frontend install.

### `frontend/src/app/`

- `frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`
  - Change the `ImageAssetRef` import to `react-document`.
  - Change the dynamic import subpath and selected export.
  - Rename the local dynamic component constant and JSX tag to
    `ButexDocumentEditor`.
- `frontend/src/app/globals.css`
  - Change the sticky-toolbar selector.
  - Change the theme root selector.
  - Change all host overrides from `--butex-document2-*` to
    `--butex-document-*`.
  - Update the “Document v2” comment.

### `frontend/src/components/`

- `frontend/src/components/dashboard/document-frozen-preview.tsx`
  - Change the dynamic import subpath and selected export.
  - Rename the local component constant and JSX tag.
  - Update the `ButexDocumentEditor2` comment.

`Document2Json` and `Document2Node` imports in this file remain on
`@drghaliasri/butex/document2`.

### `frontend/src/lib/`

- `frontend/src/lib/butex-image-assets.ts`: move the `ImageAssetRef` type import
  to `@drghaliasri/butex/react-document`.
- `frontend/src/lib/butex-mathjax.ts`: change the dynamic import, local module
  variable, style-injection call, and “v2” comment to the promoted names.

The following files intentionally keep their `document2` imports and types:

- `frontend/src/lib/api/articles.ts`
- `frontend/src/lib/butex-latex.ts`
- `frontend/src/lib/butex-validation.ts`
- `frontend/src/app/maktabi/(lawha)/maqalati/[id]/page.tsx`

They consume the current wire model, not the removed React editor.

### Frontend package metadata

- `frontend/package.json`: bump `@drghaliasri/butex` to the new major release.
- `frontend/package-lock.json`: regenerate through npm; do not hand-edit its
  version, tarball URL, or integrity hash.
- Remove/reinstall the ignored local package copy as needed so
  `frontend/node_modules/@drghaliasri/butex/package.json` agrees with the
  lockfile. The currently observed `6.1.2` installation is stale.

### Al-Bayan documentation

Update editor names and import paths in all eleven tracked direct consumers
found by the audit. Five are code/CSS files listed above; the six documentation
locations are:

- `docs/butex-figure-host-contract.md`
- `docs/butex-document-validation-contract.md`
- `docs/butex-albayan-image-workflow-audit.md`
- `docs/afkar-al-mashrou.md`
- `docs/superpowers/specs/2026-07-01-author-dashboard-design.md`
- `mcp_server/Documentation.md`

Keep `Document2Json`, `document2Latex`, `fromDocumentJson2`,
`applyDocument2Command`, and other model/worker names in those documents unless
they occur only as part of an old editor name or obsolete path.

### `backend/` and worker contract: no scoped rename

No backend production code or database schema needs an editor rename. In
particular, keep:

- `backend/app/services/butex_worker_client.py` calls to
  `/v1/document2/normalize`, `/outline`, and `/commands`.
- `backend/tests/test_butex_worker_client.py` route assertions.
- `docs/fastapi-document-worker-contract.md` service and route names.
- `backend/.env.example` and `backend/app/core/config.py` compiler/worker
  configuration names.

The backend does not import the React component. Changing these paths would be
an unrelated remote-service migration and would require coordinated backward
compatibility or downtime.

## Phase 5 — final Al-Bayan verification

Run from `frontend/` after installing the released package:

- `npm run lint`
- `npm run build`
- The relevant Vitest suites, especially BuTeX image and validation tests.
- A manual author flow on `/maktabi/maqalati/[id]/tahrir`: load, edit text and
  equations, insert/select an image, undo/redo, save, reload, and submit.
- A frozen article preview flow using `DocumentFrozenPreview`.
- A CSS inspection confirming the toolbar remains sticky below both Al-Bayan
  headers and the canonical style element is injected once.

Run the backend worker-client tests as a regression guard even though the
worker paths are intentionally unchanged.

## Residual-search gates

Search tracked files, excluding generated output, dependencies, and this audit
report (which intentionally records old names).

After Phase 1, the old implementation paths should be absent, except for
explicit historical documentation:

```bash
git grep -n -E 'src/react-document/|ButexDocumentEditor|butex-document-widget' -- \
  ':!docs/butex-document-editor-legacy-removal-rename-audit.md'
```

Run that gate before Phase 2, because those canonical strings are expected to
return after promotion.

After Phase 2 in BuTeX, these promoted-editor remnants should return no
unexpected hits:

```bash
git grep -n -E \
  'react-document2|ButexDocumentEditor2|ButexDocumentEditor2Props|ButexDocumentEditor2Ref|Document2InitialState|resolveInitialDocument2|DOCUMENT2_WIDGET_CSS|injectBuTeXDocument2Styles|documentWidgetCss2|butex-document2-widget|document-editor-app2|document2-demo-' -- \
  ':!docs/butex-document-editor-legacy-removal-rename-audit.md'
```

Run the equivalent search in Al-Bayan after Phase 4. Any surviving hit must be
classified as either an intentional historical mention or a missed consumer;
do not silently accept it.

Do not use a blanket `git grep 'Document2'` as a pass/fail gate. It would flag
the intentionally retained current model, tests, CLI, worker, and wire types.

## Completion criteria

The refactor is complete only when all of the following are true:

- There is one React document editor implementation in BuTeX.
- It is sourced from `src/react-document/` and published only from
  `@drghaliasri/butex/react-document`.
- Its public component, props, ref, initialization helpers, and style surface
  use the canonical unversioned names.
- The old source, old demo, old test, `react-document2` export, and generated
  `react-document2` artifacts are gone.
- Current BuTeX docs and links describe the sole editor; historical documents
  cannot be mistaken for active guidance.
- Al-Bayan imports and styles the canonical editor and uses the matching new
  major package version.
- The current `Document2` JSON/model and worker contracts still operate without
  a data or backend route migration.
- BuTeX build/typecheck/tests/demo/package smoke tests pass.
- Al-Bayan lint/build/editor/frozen-preview checks pass.

## Separate future project: removing all `Document2` naming

If the desired end state is later expanded from “one canonical React editor”
to “no `Document2` identifier anywhere,” stop and write a second migration
plan. At minimum it would cover:

- all 25 tracked files under `../butex/src/document2/`;
- all 6 tracked files under `../butex/src/document2-cli/`;
- all 16 `../butex/test/document2*` files;
- the package export, executable, npm scripts, build entries, CI publish chmod,
  demos, examples, README, worker docs, book docs, and block-selection spec;
- Al-Bayan's frontend model imports and helper names;
- Al-Bayan's backend worker client/tests and `/v1/document2/*` contract;
- MCP documentation and any deployed worker/agent integrations.

That project would be a public package, CLI, HTTP, and cross-service migration.
It is deliberately excluded from this editor cleanup.
