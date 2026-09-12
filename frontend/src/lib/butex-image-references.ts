/** يحوّل قيمة مسار إلى مفتاح أصل نسبي مثل assets/uuid.jpg */
export function normalizeAssetKey(raw: string | undefined | null): string | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  if (/^https?:\/\//i.test(trimmed) || trimmed.startsWith("blob:")) {
    return null;
  }
  if (trimmed.startsWith("assets/")) {
    const name = trimmed.slice("assets/".length);
    if (!name || name.includes("/") || name.includes("..")) return null;
    return `assets/${name}`;
  }
  return null;
}

/** يجمع مفاتيح الصور المستخدمة في أي موضع داخل JSON الحالي للمحرر. */
export function collectAssetKeysFromDocument(documentJson: unknown): string[] {
  const keys = new Set<string>();

  function visit(value: unknown) {
    if (Array.isArray(value)) {
      for (const item of value) visit(item);
      return;
    }
    if (!value || typeof value !== "object") return;

    const node = value as Record<string, unknown>;
    if (node.kind === "image" || node.command === "\\includegraphics") {
      for (const candidate of [
        node.assetId,
        node.asset_id,
        node.value,
        node.src,
      ]) {
        if (typeof candidate !== "string") continue;
        const key = normalizeAssetKey(candidate);
        if (key) keys.add(key);
      }
    }

    for (const child of Object.values(node)) {
      if (child && typeof child === "object") visit(child);
    }
  }

  visit(documentJson);
  return [...keys].sort();
}
