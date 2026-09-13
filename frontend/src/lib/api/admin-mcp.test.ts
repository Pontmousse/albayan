import { describe, expect, it } from "vitest";
import { buildMcpCallsPath } from "./admin-mcp-query";

describe("MCP admin API query construction", () => {
  it("uses the seven-day default and omits empty filters", () => {
    expect(buildMcpCallsPath()).toBe("/api/v1/admin/mcp/calls?period=7d");
  });

  it("encodes period, filters, cursor, and limit", () => {
    const path = buildMcpCallsPath({
      period: "90d",
      tool: "apply session",
      command: "insert_text_block",
      status: "error",
      cursor: "opaque+/=",
      limit: 25,
    });
    const url = new URL(path, "http://localhost");

    expect(url.pathname).toBe("/api/v1/admin/mcp/calls");
    expect(Object.fromEntries(url.searchParams)).toEqual({
      period: "90d",
      tool: "apply session",
      command: "insert_text_block",
      status: "error",
      cursor: "opaque+/=",
      limit: "25",
    });
  });
});
