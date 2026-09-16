export type McpClientId =
  | "cursor"
  | "chatgpt"
  | "claude"
  | "antigravity"
  | "opencode"
  | "other";

export type McpClientProvider = {
  id: McpClientId;
  name: string;
  iconSrc: string;
};

export const MCP_CLIENT_PROVIDERS = {
  cursor: {
    id: "cursor",
    name: "Cursor",
    iconSrc: "/wukala/cursor.png",
  },
  chatgpt: {
    id: "chatgpt",
    name: "ChatGPT",
    iconSrc: "/wukala/chatgpt.png",
  },
  claude: {
    id: "claude",
    name: "Claude",
    iconSrc: "/wukala/claude.png",
  },
  antigravity: {
    id: "antigravity",
    name: "Antigravity",
    iconSrc: "/wukala/antigravity.png",
  },
  opencode: {
    id: "opencode",
    name: "OpenCode",
    iconSrc: "/wukala/opencode.png",
  },
  other: {
    id: "other",
    name: "برامج أخرى",
    iconSrc: "/wukala/others.png",
  },
} as const satisfies Record<McpClientId, McpClientProvider>;

export type McpOAuthClientMetadata = {
  applicationName?: string | null;
  applicationUrl?: string | null;
  redirectDomain?: string | null;
  redirectUri?: string | null;
};

type KnownMcpClientId = Exclude<McpClientId, "other">;

type ProviderMatcher = {
  names: readonly string[];
  hostSuffixes: readonly string[];
};

const MCP_OAUTH_PROVIDER_MATCHERS: Record<KnownMcpClientId, ProviderMatcher> = {
  cursor: {
    names: ["cursor", "cursor ai"],
    hostSuffixes: ["cursor.com", "cursor.sh"],
  },
  chatgpt: {
    names: ["chatgpt", "openai", "openai chatgpt"],
    hostSuffixes: ["chatgpt.com", "openai.com"],
  },
  claude: {
    names: ["claude", "claude ai", "anthropic"],
    hostSuffixes: ["claude.ai", "anthropic.com"],
  },
  antigravity: {
    names: ["antigravity", "google antigravity"],
    // A bare google.com hostname is intentionally not enough to classify a client.
    hostSuffixes: [],
  },
  opencode: {
    names: ["opencode", "open code"],
    hostSuffixes: ["opencode.ai"],
  },
};

const KNOWN_MCP_CLIENT_IDS = [
  "cursor",
  "chatgpt",
  "claude",
  "antigravity",
  "opencode",
] as const satisfies readonly KnownMcpClientId[];

function normalizeClientName(value: string | null | undefined): string {
  return (value ?? "")
    .normalize("NFKC")
    .trim()
    .toLowerCase()
    .replace(/[._-]+/g, " ")
    .replace(/\s+/g, " ");
}

function hostnameFromValue(value: string | null | undefined): string | null {
  const normalized = value?.trim();
  if (!normalized) return null;

  try {
    const url = normalized.includes("://")
      ? new URL(normalized)
      : new URL(`https://${normalized}`);
    return url.hostname.toLowerCase().replace(/\.$/, "");
  } catch {
    return null;
  }
}

function hostMatchesSuffix(hostname: string, suffix: string): boolean {
  return hostname === suffix || hostname.endsWith(`.${suffix}`);
}

/**
 * Conservatively identifies one of Al-Bayan's reviewed MCP clients from OAuth
 * application metadata. Dynamic OAuth client IDs are deliberately ignored.
 */
export function identifyMcpClient(
  metadata: McpOAuthClientMetadata,
): KnownMcpClientId | null {
  const normalizedName = normalizeClientName(metadata.applicationName);
  const hostnames = [
    hostnameFromValue(metadata.applicationUrl),
    hostnameFromValue(metadata.redirectDomain),
    hostnameFromValue(metadata.redirectUri),
  ].filter((value): value is string => Boolean(value));

  for (const id of KNOWN_MCP_CLIENT_IDS) {
    const matcher = MCP_OAUTH_PROVIDER_MATCHERS[id];

    if (normalizedName && matcher.names.includes(normalizedName)) {
      return id;
    }

    if (
      matcher.hostSuffixes.some((suffix) =>
        hostnames.some((hostname) => hostMatchesSuffix(hostname, suffix)),
      )
    ) {
      return id;
    }
  }

  return null;
}
