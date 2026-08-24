/** يُقرأ من NEXT_PUBLIC_MCP_ENABLED عند البناء (true/1/yes). الافتراضي: معطّل. */
export function isMcpEnabled(): boolean {
  const v = (process.env.NEXT_PUBLIC_MCP_ENABLED ?? "").trim().toLowerCase();
  return v === "true" || v === "1" || v === "yes";
}
