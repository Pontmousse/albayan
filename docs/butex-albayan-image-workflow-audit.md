# BuTeX × Al-Bayan Image Workflow — Three-Phase Implementation Plan

## Scope

This document is intentionally limited to one interaction:

**uploading article images in Al-Bayan, then inserting, selecting, replacing, or removing those images from BuTeX image blocks inside the article editor.**

It does not cover general document editing, equations, citations, other media types, backend storage design beyond what is necessary for this workflow, or unrelated UI cleanup.

The implementation is divided into three phases so the core workflow can be fixed first, reliability can be verified second, and lower-priority UX polish can be handled last.

## Current architecture

The existing separation of responsibilities is correct and should remain:

| Responsibility | Owner |
|---|---|
| Upload image bytes to article storage / S3 | Al-Bayan |
| List article image assets | Al-Bayan |
| Resolve an `assetId` into a browser-loadable preview URL | Al-Bayan |
| Own the image / figure block inside the document | BuTeX |
| Insert an empty image block from the editor toolbar | BuTeX |
| Select or replace the asset attached to an existing image block | BuTeX UI, using host-provided asset inventory |
| Caption / label / figure metadata | BuTeX |
| Document undo / redo for image-block changes | BuTeX |

BuTeX already exposes the host integration needed for asset selection, including `listImageAssets`, `onRequestImagePick`, `updateImageBlockAsset`, `resolveImageUrl`, and the built-in image-block UI.

The expected implementation should therefore be **primarily an Al-Bayan host integration change**, not a BuTeX package redesign.

## Product decisions that apply to all phases

### Empty image blocks remain intentional warning / invalid-document states

No change is requested here.

The BuTeX toolbar image button may continue to insert an **empty image block**.

The document may continue to be considered incomplete or invalid while an image block has no selected asset.

The intended flow is:

1. author clicks **إدراج صورة** in BuTeX;
2. an empty figure block appears;
3. the block says **لا صورة محددة**;
4. the author selects an uploaded article image from inside that block;
5. the warning or invalid state disappears once an asset is selected.

Do **not** silently remove empty figures or automatically treat them as valid.

### `صور المقال` is upload / inventory only

The Al-Bayan page-level **صور المقال** panel should only:

- upload images to the article's S3/storage inventory;
- list all uploaded article image assets;
- show thumbnails/previews;
- refresh the inventory;
- later, if desired, support asset management such as deleting unused uploads.

It should **not insert an image block into the BuTeX document**.

It should also **not replace an image in an existing BuTeX block**.

There should be only one document-editing workflow for figures: **inside BuTeX**.

### Storage ownership does not move into BuTeX

BuTeX should not upload image bytes or communicate directly with S3.

Al-Bayan remains responsible for upload, storage, article asset inventory, and URL resolution.

---

# Phase 1 — High priority: establish the correct end-to-end workflow

## Goal

Make the existing BuTeX image-block workflow functional in Al-Bayan and remove the competing page-level insertion workflow.

This phase is the required functional fix.

## 1. Connect BuTeX to the article asset inventory

This is the primary issue.

BuTeX can already render an empty image block with:

- **لا صورة محددة**;
- **اختيار صورة**;
- a built-in asset `<select>` when `listImageAssets` is supplied;
- **تغيير** for a filled image block;
- **إزالة**;
- thumbnail preview through `resolveImageUrl`.

Al-Bayan currently supplies `resolveImageUrl`, but does not supply BuTeX with the article asset inventory.

### Required change

Al-Bayan should provide `listImageAssets` to `ButexDocumentEditor2`.

The callback should:

1. call Al-Bayan's existing article-assets API;
2. return the article image assets as BuTeX `ImageAssetRef[]`;
3. use the existing `asset_id` as `assetId`;
4. optionally provide a friendly `label` when one is available;
5. optionally ensure or prefetch thumbnails before or while the list is used.

Conceptual mapping:

```ts
listImageAssets={async () => {
  const { assets } = await listArticleAssets(getToken, articleId);

  return assets.map((asset) => ({
    assetId: asset.asset_id,
    value: asset.asset_id,
    label: asset.asset_id.replace(/^assets\//, ""),
  }));
}}
```

The exact implementation can be adapted to the existing Al-Bayan image resolver/cache.

## 2. Remove document insertion from `صور المقال`

The page-level assets panel currently performs a document edit by inserting a new image block.

That conflicts with the intended responsibility boundary.

### Required change

Remove the current **إدراج في المستند** behavior from the page-level asset panel.

The panel should no longer call:

```ts
editorRef.current?.insertImageBlock(...)
```

Remove the related `onInsertFigure` / `handleInsertFigure` plumbing from the panel and editor page.

The panel becomes a pure **article image inventory**.

## 3. Ensure replacement updates the existing figure block

The user should never need to:

1. remove an old figure;
2. open the page-level image panel;
3. insert another figure;
4. recreate the caption or label.

Replacing an image should use BuTeX's existing asset-selection API to update the asset on the **same image block**.

The replacement workflow must **not create a second image block**.

Existing figure metadata should remain intact:

- caption;
- label;
- centered state;
- block position;
- figure identity.

The change should participate in BuTeX undo/redo.

## Phase 1 implementation locations

### Article editor page

`frontend/src/app/maktabi/maqalati/[id]/tahrir/page.tsx`

Expected changes:

- keep `resolveImageUrl`;
- add a memoized/callback-based `listImageAssets`;
- pass `listImageAssets` into `ButexDocumentEditor2`;
- remove `handleInsertFigure`;
- stop passing `onInsertFigure` into `ArticleAssetsPanel`.

Conceptually:

```tsx
<ButexDocumentEditor2
  ...
  resolveImageUrl={resolveImageUrl}
  listImageAssets={listButexImageAssets}
  onDocumentJsonChange={handleDocumentJsonChange}
/>
```

### Article assets panel

`frontend/src/components/dashboard/article-assets-panel.tsx`

Expected changes:

- remove `onInsertFigure`;
- remove **إدراج في المستند** buttons;
- keep upload;
- keep refresh;
- keep gallery thumbnails;
- keep errors/loading/empty state.

### API client

`frontend/src/lib/api/articles.ts`

The existing `listArticleAssets` and `uploadArticleAsset` APIs are sufficient for the first implementation.

No new backend endpoint should be necessary merely to connect BuTeX's selector.

### Image resolver

`frontend/src/lib/butex-images.ts`

The existing resolver and `ensureAsset` / blob cache should continue to be used.

The asset-list integration may prefetch or ensure assets for thumbnails, but should avoid unnecessary repeated network work.

## Phase 1 target user workflow

### Uploading an image

1. Author opens **صور المقال**.
2. Author clicks **رفع صورة**.
3. Al-Bayan uploads the file to article storage.
4. The image appears in the article asset gallery.
5. Nothing is inserted into the document automatically.
6. The author closes the panel and continues editing.

The panel is an **asset library**, not a document-insertion tool.

### Inserting an image into the document

1. Author places focus near the desired location.
2. Author clicks BuTeX **إدراج صورة**.
3. BuTeX inserts an empty image block after the focused block.
4. The image block shows **لا صورة محددة**.
5. The built-in image selector/dropdown lists the article images supplied by Al-Bayan.
6. Author selects an asset.
7. BuTeX updates the existing image block with that asset.
8. The preview appears.
9. Caption, label, position, and block identity remain attached to the same figure block.
10. The document becomes valid once the figure is complete.

### Replacing an image

1. Author opens an existing filled image block.
2. Author chooses **تغيير** or uses the image selector.
3. The same article asset inventory is available.
4. Author chooses another uploaded image.
5. BuTeX updates the asset on the existing block.
6. Existing figure metadata remains intact.
7. The change participates in BuTeX undo/redo.

### Removing an image from a block

BuTeX's existing **إزالة** action can remain.

Removing the selected asset from a figure should:

- clear the image asset/path;
- leave the figure block itself in place;
- preserve caption/label metadata;
- return the block to the intentional empty/warning state.

This is different from deleting the uploaded asset from S3.

## Phase 1 acceptance criteria

- [ ] **صور المقال** uploads images to article storage.
- [ ] **صور المقال** lists uploaded article images and previews them.
- [ ] **صور المقال** no longer contains **إدراج في المستند**.
- [ ] Opening **صور المقال** never mutates the BuTeX document.
- [ ] Clicking BuTeX **إدراج صورة** still inserts an empty image block after the current focus.
- [ ] An empty image block remains visibly incomplete and keeps the document warning/invalid state.
- [ ] The BuTeX image block can list uploaded article images.
- [ ] Selecting an image from the BuTeX block sets both `asset_id` and the image `value`.
- [ ] The selected image preview resolves correctly through Al-Bayan.
- [ ] **تغيير** replaces the asset on the same figure block.
- [ ] Replacing an image does not create an additional figure.
- [ ] Caption and label metadata survive image replacement.
- [ ] **إزالة** returns the figure to the empty state without deleting the uploaded S3 asset.
- [ ] No direct S3/upload logic is added to BuTeX.

---

# Phase 2 — Medium priority: reliability, error handling, and validation

## Goal

Once the core workflow works, verify that failures are represented correctly and that document state remains consistent through selecting, replacing, clearing, and undo/redo.

## 1. Make asset-list failures visible

BuTeX's generic `listImageAssets` fallback can treat a rejected list call similarly to an empty inventory.

For Al-Bayan, the host should avoid presenting a network/API failure as if the article genuinely has no uploaded images.

Preferred options:

- keep an Al-Bayan-level error state for the asset-list request; or
- provide a custom `renderImageBlockEditor` only if standard integration proves insufficient.

Do not redesign this prematurely. First use the standard BuTeX API from Phase 1 and evaluate the resulting UX.

## 2. Verify empty / filled document validity transitions

The existing validation behavior should remain:

- an image block with no selected asset is incomplete/invalid;
- selecting an asset clears that image-specific warning state;
- using **إزالة** returns the same figure block to the incomplete/invalid state;
- reselecting an asset makes the figure complete again.

Testing should explicitly verify this sequence.

## 3. Verify undo / redo across all image-block asset changes

Test BuTeX undo/redo for:

- first asset selection;
- replacing one asset with another;
- clearing an asset with **إزالة**;
- reselecting after removal.

Undo/redo must operate on the existing figure block and preserve figure metadata correctly.

## 4. Keep upload constraints visible

The current accepted formats are:

- JPEG;
- PNG;
- GIF;
- WebP.

The backend limit is **5 MiB**.

The **صور المقال** panel should tell the user this before upload instead of only reporting it after rejection.

Suggested copy:

> JPEG، PNG، GIF أو WebP — بحد أقصى 5 ميغابايت.

This belongs to the Al-Bayan asset panel, not BuTeX.

## 5. Verify image resolver / cache behavior

Continue using the existing Al-Bayan resolver and `ensureAsset` / blob cache.

If the asset selector triggers preview loading or thumbnail prefetching, verify that the implementation does not create unnecessary repeated requests.

This is a host integration concern; it is not a reason by itself to move storage logic into BuTeX.

## Phase 2 acceptance criteria

- [ ] Upload errors remain visible in the Al-Bayan asset panel.
- [ ] Article asset-list failures are not silently presented as a genuine empty inventory when the host can distinguish them.
- [ ] Empty figure → selected asset → removed asset → reselected asset produces the expected validity transitions.
- [ ] Undo/redo works for selecting, changing, and removing image assets.
- [ ] Caption and label metadata survive replacement and clearing.
- [ ] Image previews continue to resolve through Al-Bayan's existing resolver/cache.
- [ ] Asset-list and preview behavior avoids unnecessary repeated network work.
- [ ] Upload format and 5 MiB limits are visible before upload.

---

# Phase 3 — Low priority: UX polish and optional improvements

## Goal

Improve clarity and convenience only after the standard BuTeX integration has been proven reliable.

None of the items in this phase should block the Phase 1 functional fix.

## 1. Improve display names when possible

Al-Bayan currently stores assets under generated keys such as:

```text
assets/<uuid>.jpg
```

Those identifiers are technically correct but are not friendly labels in a dropdown.

For the first implementation, displaying the filename/UUID is acceptable.

A later improvement could preserve or expose an optional human-readable upload name and pass it as:

```ts
{
  assetId,
  value: assetId,
  label: originalFilename,
}
```

This is polish, not a blocker.

### Current Al-Bayan limitation

Al-Bayan does not currently persist the original upload filename. The upload
endpoint replaces it with a generated UUID key, and the asset-list response
exposes only that key, content type, size, and modification time. Phase 3 may
derive a clearer label from those reliable fields, but preserving an original
filename requires a separate storage/API change and is intentionally deferred.

## 2. Consider richer picker UI only if the built-in selector is insufficient

BuTeX already supports host picker integration and a built-in asset selector.

Do not introduce a custom image-block editor unless integration/testing demonstrates a concrete UX limitation that cannot reasonably be handled with the documented host API.

If a richer picker is eventually justified, it should still use the same Al-Bayan-provided article asset inventory and update the current BuTeX block rather than creating another insertion workflow.

Phase 3 keeps the built-in selector because no concrete usage finding currently
shows that a custom picker is required. A richer picker should remain a separate
follow-up backed by observed inventory size or asset-identification problems.

## 3. Optional article asset management

The **صور المقال** panel may later support inventory-management features such as deleting unused uploads.

That is separate from document editing.

Deleting or managing an uploaded S3 asset must not be conflated with BuTeX's **إزالة** action, which only clears the asset from a figure block.

## 4. Optional thumbnail prefetch refinements

If testing shows useful performance gains, the host may refine prefetching/ensuring behavior for asset thumbnails.

Any such optimization should preserve the existing ownership boundary:

- Al-Bayan owns asset retrieval and browser-loadable URLs;
- BuTeX owns the figure block and document mutation.

The article inventory should lazily ensure thumbnails near the visible scroll
area instead of fetching every asset blob when the list response arrives.

## Phase 3 acceptance criteria

- [ ] Friendly labels are added only if useful metadata is available.
- [ ] Any richer picker remains a BuTeX block-level selection workflow, not a page-level insertion workflow.
- [ ] Optional asset-management features remain clearly separate from figure-block removal.
- [ ] No BuTeX package change is made unless host integration testing proves one is required.

---

# Intentional non-changes

The following current behaviors are acceptable and should remain unless testing reveals a concrete problem.

## BuTeX toolbar button

Keep the existing small image icon / **إدراج صورة** toolbar action.

It is acceptable for this button to insert an empty image block rather than immediately opening the host upload interface.

## Empty figure validation

Keep the current warning/invalid state for image blocks without an asset.

## Raw / advanced image path

BuTeX's advanced image-path editor can remain collapsed as an advanced/developer capability.

It should not become the normal author workflow.

## Storage ownership

BuTeX should not upload image bytes or communicate directly with S3.

## S3 inventory panel

Al-Bayan should retain **صور المقال** as the place to upload and inspect article assets.

The only required workflow change is that it must no longer mutate the document.

# BuTeX-side assessment

At the time of this audit, no required BuTeX change is identified.

BuTeX already provides the necessary functionality:

- empty figure blocks;
- `listImageAssets`;
- host picker support;
- `ImageAssetRef`;
- selecting an asset on an existing block;
- changing/replacing an asset;
- clearing an asset;
- `asset_id` persistence;
- thumbnail resolution;
- undo/redo;
- caption and label preservation.

The first implementation should therefore be attempted entirely in Al-Bayan.

Only open a BuTeX change if integration/testing demonstrates a package-level defect that cannot reasonably be handled by the documented host API.

# Recommended implementation order

## Phase 1 — Core workflow

1. Remove document insertion behavior from **صور المقال**.
2. Add an Al-Bayan `listImageAssets` callback for BuTeX.
3. Pass it to `ButexDocumentEditor2`.
4. Test inserting an empty figure and selecting an existing uploaded image.
5. Test replacing an image on the same block.
6. Test remove → empty warning → reselect.

## Phase 2 — Reliability and validation

7. Verify captions/labels survive replacement and clearing.
8. Verify undo/redo.
9. Verify document validity changes correctly between empty and filled figure states.
10. Verify asset-list errors are distinguishable from a true empty inventory.
11. Show upload format and size constraints before upload.
12. Verify resolver/cache behavior does not cause unnecessary repeated network work.

## Phase 3 — Polish

13. Add friendly asset labels if useful metadata becomes available.
14. Consider richer picker UI only if the built-in workflow proves insufficient.
15. Consider optional asset-management or thumbnail-prefetch refinements.
16. Only then consider a BuTeX package change if a package-level defect has actually been demonstrated.

# Final UX principle

There should be one clear mental model for authors:

> **صور المقال** manages the article's uploaded image library.  
> **BuTeX** decides where an image appears in the manuscript and which uploaded asset belongs to each figure.

Uploading an image and inserting an image are deliberately separate actions.

That separation should remain visible and consistent throughout the editor.
