import { afterEach, describe, expect, it, vi } from "vitest";
import { CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE } from "./agent-token-config";
import { isAgentKeyUiEnabled, isDevMode } from "./dev-mode";
import { MCP_CLIENT_GUIDES, MCP_SERVER_URL } from "./mcp-client-guides";
import { isMcpEnabled } from "./mcp-enabled";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("MCP feature flag matrix", () => {
  it("keeps public MCP on while advanced key UI is off", () => {
    vi.stubEnv("NEXT_PUBLIC_MCP_ENABLED", "true");
    vi.stubEnv("NEXT_PUBLIC_DEV_MODE", "false");

    expect(isMcpEnabled()).toBe(true);
    expect(isDevMode()).toBe(false);
    expect(isAgentKeyUiEnabled()).toBe(false);
  });

  it("shows advanced key UI only when both flags are on", () => {
    vi.stubEnv("NEXT_PUBLIC_MCP_ENABLED", "true");
    vi.stubEnv("NEXT_PUBLIC_DEV_MODE", "true");

    expect(isMcpEnabled()).toBe(true);
    expect(isDevMode()).toBe(true);
    expect(isAgentKeyUiEnabled()).toBe(true);
  });

  it("keeps all MCP surfaces off when the MCP flag is off", () => {
    vi.stubEnv("NEXT_PUBLIC_MCP_ENABLED", "false");
    vi.stubEnv("NEXT_PUBLIC_DEV_MODE", "true");

    expect(isMcpEnabled()).toBe(false);
    expect(isAgentKeyUiEnabled()).toBe(false);
  });
});

describe("remote MCP client configurations", () => {
  it("uses valid client-specific JSON without local credentials", () => {
    const snippets = Object.fromEntries(
      MCP_CLIENT_GUIDES.filter((guide) => guide.configSnippet).map((guide) => [
        guide.id,
        JSON.parse(guide.configSnippet!),
      ]),
    );

    expect(snippets.cursor.mcpServers.albayan.url).toBe(MCP_SERVER_URL);
    expect(snippets.antigravity.mcpServers.albayan.serverUrl).toBe(
      MCP_SERVER_URL,
    );
    expect(snippets.opencode.mcp.servers.albayan).toEqual({
      type: "remote",
      url: MCP_SERVER_URL,
    });

    for (const snippet of MCP_CLIENT_GUIDES.map(
      (guide) => guide.configSnippet ?? "",
    )) {
      expect(snippet).not.toContain("ALBAYAN_API_URL");
      expect(snippet).not.toContain("ALBAYAN_AGENT_TOKEN");
    }
  });

  it("uses the hosted MCP endpoint for Cursor personal keys", () => {
    const snippet = JSON.parse(CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE);

    expect(snippet.mcpServers.albayan).toEqual({
      url: MCP_SERVER_URL,
      headers: {
        Authorization: "Bearer ${env:ALBAYAN_AGENT_TOKEN}",
      },
    });
    expect(CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE).not.toContain(
      "ALBAYAN_API_URL",
    );
    expect(CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE).not.toContain(
      "api.albayan-journal.org",
    );
    expect(CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE).not.toContain('"command"');
    expect(CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE).not.toContain('"args"');
  });
});
