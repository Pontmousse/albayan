export type McpCallQueryParams = {
  period?: "24h" | "7d" | "30d" | "90d";
  tool?: string | null;
  command?: string | null;
  status?: "success" | "error" | null;
  cursor?: string | null;
  limit?: number;
};

export function buildMcpCallsPath(params: McpCallQueryParams = {}) {
  const search = new URLSearchParams();
  search.set("period", params.period ?? "7d");
  if (params.tool) search.set("tool", params.tool);
  if (params.command) search.set("command", params.command);
  if (params.status) search.set("status", params.status);
  if (params.cursor) search.set("cursor", params.cursor);
  if (params.limit) search.set("limit", String(params.limit));
  return `/api/v1/admin/mcp/calls?${search.toString()}`;
}
