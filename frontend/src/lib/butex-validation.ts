import { fromDocumentJson2, type Document2Node } from "@drghaliasri/butex/document2";

function hasEmptyImageBlock(blocks: unknown): boolean {
  if (!Array.isArray(blocks)) return false;

  for (const block of blocks) {
    if (!block || typeof block !== "object") continue;
    const candidate = block as Record<string, unknown>;

    if (
      (candidate.kind === "image" || candidate.command === "\\includegraphics") &&
      ![candidate.assetId, candidate.asset_id, candidate.value, candidate.src].some(
        (value) => typeof value === "string" && value.trim().length > 0,
      )
    ) {
      return true;
    }

    if (Array.isArray(candidate.items)) {
      for (const item of candidate.items) {
        if (
          item &&
          typeof item === "object" &&
          hasEmptyImageBlock((item as { blocks?: unknown }).blocks)
        ) {
          return true;
        }
      }
    }
  }

  return false;
}

/**
 * Temporary host-side validation until BuTeX exposes the validation contract in
 * docs/butex-document-validation-contract.md.
 */
export function isButexDocumentValid(documentJson: unknown): boolean {
  if (!documentJson || typeof documentJson !== "object") return false;

  try {
    const record = documentJson as Record<string, unknown>;
    const node =
      record.nodeType === "DocumentObject"
        ? (documentJson as Document2Node)
        : fromDocumentJson2(documentJson);

    return node.diagnostics.length === 0 && !hasEmptyImageBlock(node.blocks);
  } catch {
    return false;
  }
}
