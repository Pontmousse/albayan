import {
  fromDocumentJson2,
  document2Latex,
  type Document2Node,
} from "@drghaliasri/butex/document2";
import { normalizeAssetKey } from "@/lib/butex-images";

/** يطابق json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False) في بايثون. */
function canonicalize(value: unknown): unknown {
  if (value === null || typeof value !== "object") {
    return value;
  }
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  const obj = value as Record<string, unknown>;
  const out: Record<string, unknown> = {};
  for (const key of Object.keys(obj).sort()) {
    out[key] = canonicalize(obj[key]);
  }
  return out;
}

/** SHA-256 hex لـ JSON المعياري — يطابق hash_document في الخلفية. */
export async function hashDocument(documentJson: unknown): Promise<string> {
  const canonical = JSON.stringify(canonicalize(documentJson));
  const data = new TextEncoder().encode(canonical);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

const LATEX_EXPORT_OPTIONS = { twocolumn: true } as const;

export function exportDocumentLatex(documentJson: unknown): string {
  // قد يُخزَّن كـ Document2Node (nodeType) أو كـ wire JSON (node_type)
  if (
    documentJson &&
    typeof documentJson === "object" &&
    (documentJson as { nodeType?: string }).nodeType === "DocumentObject" &&
    Array.isArray((documentJson as { blocks?: unknown }).blocks)
  ) {
    return document2Latex(documentJson as Document2Node, LATEX_EXPORT_OPTIONS);
  }
  return document2Latex(fromDocumentJson2(documentJson), LATEX_EXPORT_OPTIONS);
}

export function collectAssetKeys(documentJson: unknown): string[] {
  const keys = new Set<string>();

  function visitBlocks(blocks: unknown) {
    if (!Array.isArray(blocks)) return;
    for (const block of blocks) {
      if (!block || typeof block !== "object") continue;
      const b = block as Record<string, unknown>;
      if (b.kind === "image" || b.command === "\\includegraphics") {
        for (const candidate of [b.assetId, b.asset_id, b.value, b.src]) {
          if (typeof candidate === "string") {
            const key = normalizeAssetKey(candidate);
            if (key) keys.add(key);
          }
        }
      }
      if (b.kind === "list" && Array.isArray(b.items)) {
        for (const item of b.items) {
          if (item && typeof item === "object") {
            visitBlocks((item as { blocks?: unknown }).blocks);
          }
        }
      }
    }
  }

  if (documentJson && typeof documentJson === "object") {
    visitBlocks((documentJson as { blocks?: unknown }).blocks);
  }
  return [...keys].sort();
}
