import {
  fromDocumentJson,
  documentLatex,
  type DocumentNode,
} from "@drghaliasri/butex/document";
import { collectAssetKeysFromDocument } from "./butex-image-references";

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
  // قد يُخزَّن كـ DocumentNode (nodeType) أو كـ wire JSON (node_type)
  if (
    documentJson &&
    typeof documentJson === "object" &&
    (documentJson as { nodeType?: string }).nodeType === "DocumentObject" &&
    Array.isArray((documentJson as { blocks?: unknown }).blocks)
  ) {
    return documentLatex(documentJson as DocumentNode, LATEX_EXPORT_OPTIONS);
  }
  return documentLatex(fromDocumentJson(documentJson), LATEX_EXPORT_OPTIONS);
}

export function collectAssetKeys(documentJson: unknown): string[] {
  return collectAssetKeysFromDocument(documentJson);
}
