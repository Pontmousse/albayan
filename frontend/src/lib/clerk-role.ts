export function readClerkRole(publicMetadata: unknown): string | null {
  if (!publicMetadata || typeof publicMetadata !== "object") {
    return null;
  }

  const role = (publicMetadata as { role?: unknown }).role;
  return typeof role === "string" ? role : null;
}
