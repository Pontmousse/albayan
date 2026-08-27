# BuTeX Document Editor v2 — Host Figure / Asset Contract (v1)

**Audience:** `@drghaliasri/butex` maintainers  
**Consumer:** Al-Bayan (`ButexDocumentEditor2` on `/maktabi/maqalati/[id]/tahrir`)  
**Scope:** Figure UI + insert/update APIs. Not MCP, not session undo, not equation editor.

## 1. Separation of concerns

| Responsibility | Owner |
|----------------|--------|
| Upload bytes, list inventory, delete orphans | **Host** (S3; no DB table) |
| Document figure node (`\includegraphics`, caption, label) | **BuTeX** |
| `assetId`/`value` → browser URL | **Host** via `resolveImageUrl` |
| Empty-figure chrome + pick affordance | **BuTeX** default, **host-overridable** |

BuTeX must not upload files or call S3.  
BuTeX must not use a raw path textarea as the primary author UX.

## 2. Wire format (`Document2Json` image block)

```json
{
  "command": "\\includegraphics",
  "asset_id": "assets/<uuid>.jpg",
  "value": "assets/<uuid>.jpg",
  "options": { "width": "0.8\\columnwidth" },
  "caption_enabled": false,
  "caption": "",
  "label_enabled": false,
  "label": "",
  "centered": true
}
```

- `asset_id` — stable host key (Al-Bayan S3 path under version prefix).
- `value` — LaTeX `\includegraphics{...}` argument; usually equals `asset_id`.
- Empty figure: no `asset_id`, `value === ""`.
- Create/update APIs must set **both** live `assetId` and wire `asset_id`, not `value` alone.

## 3. Existing APIs (keep)

```ts
resolveImageUrl?: (ref: { assetId?: string; value: string }) => string;

type ButexDocumentEditor2Ref = {
  insertImageBlock(srcOrAsset?: string | ImageAssetRef): void;
  updateImageBlockValue(blockId: string, value: string): void;
  getDocumentJson(): Document2Json;
};
```

`insertImageBlock` remains focus-aware (insert after focused block).

## 4. New types

```ts
type ImageAssetRef = {
  assetId: string;
  value?: string;
  label?: string;
  thumbUrl?: string;
};
```

## 5. New props

```ts
onRequestImagePick?: (ctx: {
  blockId: string;
  current: ImageAssetRef | null;
}) => Promise<ImageAssetRef | null> | ImageAssetRef | null;

listImageAssets?: () => Promise<ImageAssetRef[]> | ImageAssetRef[];

renderImageBlockEditor?: (ctx: {
  blockId: string;
  assetId?: string;
  value: string;
  resolvedUrl: string;
  uiLocale: 'ar' | 'en';
  onSelectAsset: (ref: ImageAssetRef) => void;
  onClearAsset: () => void;
  defaultUi: React.ReactNode;
}) => React.ReactNode;
```

Select priority: `onRequestImagePick` → built-in list from `listImageAssets` → disabled select (not path textarea).

## 6. Default figure editor UI

**Empty:** dashed empty float, **«لا صورة محددة»**, button **«اختيار صورة»**.  
**Filled:** thumbnail via `resolveImageUrl`, **«تغيير»** / **«إزالة»**.  
**Toolbar figure:** inserts empty block after focus; does not open file picker.

Path textarea may remain as collapsed advanced/dev only.

## 7. Imperative API

```ts
insertImageBlock({ assetId: 'assets/x.jpg' })
insertImageBlock('')  // empty figure
insertImageBlock('assets/x.jpg')  // backward compatible

updateImageBlockAsset(blockId, { assetId, value? })  // NEW
```

All must push document undo snapshots.

## 8. Al-Bayan host (implemented)

- `GET /api/v1/articles/{id}/assets` — S3 list under `assets/` (no migration).
- `POST /api/v1/articles/{id}/assets` — upload.
- `GET /api/v1/articles/{id}/assets/{filename}` — preview bytes.
- Editor: **صور المقال** panel — upload to inventory, **إدراج في المستند** calls `insertImageBlock(asset_id)`.
- After BuTeX ships contract: wire `onRequestImagePick` → same panel for empty in-editor figures.

## 9. Acceptance tests (package)

1. Toolbar insert → empty state + select (ar).  
2. `onRequestImagePick` → `assetId`+`value` on block; preview uses `resolveImageUrl`.  
3. `toDocumentJson2` / `fromDocumentJson2` round-trip `asset_id`.  
4. `insertImageBlock({ assetId })` matches focus insert location.  
5. Clear returns empty state without dropping caption meta.
