import { describe, expect, it } from "vitest";
import { identifyMcpClient } from "./mcp-client-providers";
import { resolveOAuthClientLogo } from "./oauth-consent";

describe("identifyMcpClient", () => {
  it("recognizes ChatGPT and OpenAI metadata", () => {
    expect(identifyMcpClient({ applicationName: "ChatGPT" })).toBe("chatgpt");
    expect(
      identifyMcpClient({ redirectUri: "https://auth.openai.com/oauth/callback" }),
    ).toBe("chatgpt");
  });

  it("recognizes Claude and Anthropic metadata", () => {
    expect(identifyMcpClient({ applicationName: "Anthropic" })).toBe("claude");
    expect(
      identifyMcpClient({ applicationUrl: "https://claude.ai/settings/connectors" }),
    ).toBe("claude");
  });

  it("recognizes Cursor metadata", () => {
    expect(identifyMcpClient({ applicationName: "Cursor" })).toBe("cursor");
    expect(identifyMcpClient({ redirectDomain: "auth.cursor.com" })).toBe("cursor");
  });

  it("recognizes Google Antigravity by its explicit client name", () => {
    expect(
      identifyMcpClient({
        applicationName: "Google Antigravity",
        applicationUrl: "https://accounts.google.com/",
      }),
    ).toBe("antigravity");
  });

  it("recognizes OpenCode metadata", () => {
    expect(
      identifyMcpClient({ redirectUri: "https://opencode.ai/oauth/callback" }),
    ).toBe("opencode");
  });

  it("does not classify broad lookalikes or generic Google hosts", () => {
    expect(identifyMcpClient({ applicationName: "ChatGPT Helper" })).toBeNull();
    expect(identifyMcpClient({ redirectDomain: "accounts.google.com" })).toBeNull();
  });
});

describe("resolveOAuthClientLogo", () => {
  it("prefers reviewed local artwork for a known provider", () => {
    expect(
      resolveOAuthClientLogo(
        { applicationName: "ChatGPT" },
        "https://example.com/unreviewed-logo.png",
      ),
    ).toEqual({
      src: "/wukala/chatgpt.png",
      providerId: "chatgpt",
      isRemote: false,
    });
  });

  it("uses a safe Clerk-provided logo for an unknown application", () => {
    expect(
      resolveOAuthClientLogo(
        { applicationName: "Research Assistant" },
        "https://example.com/research-assistant.png",
      ),
    ).toEqual({
      src: "https://example.com/research-assistant.png",
      providerId: null,
      isRemote: true,
    });
  });

  it("uses the generic local artwork when no safe remote logo exists", () => {
    expect(
      resolveOAuthClientLogo(
        { applicationName: "Research Assistant" },
        "javascript:alert(1)",
      ),
    ).toEqual({
      src: "/wukala/others.png",
      providerId: "other",
      isRemote: false,
    });
  });
});
