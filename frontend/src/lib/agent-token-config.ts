export const ALLOWED_AGENT_SCOPES = [
  "profile:read",
  "articles:read",
  "articles:session:write",
  "reviews:read",
  "reviews:draft:write",
  "editor:read",
] as const;

export type AgentScope = (typeof ALLOWED_AGENT_SCOPES)[number];

export const AGENT_SCOPE_LABELS: Record<AgentScope, string> = {
  "profile:read": "قراءة الملف الشخصي",
  "articles:read": "قراءة المقالات",
  "articles:session:write": "كتابة مسودة الجلسة",
  "reviews:read": "قراءة تعيينات المراجعة",
  "reviews:draft:write": "مسودة ملاحظات المراجعة",
  "editor:read": "قراءة مقالات التحرير",
};

export const DEFAULT_AGENT_SCOPES: AgentScope[] = [
  "profile:read",
  "articles:read",
  "articles:session:write",
];

export const MAX_AGENT_TOKENS = 5;

export const CURSOR_MCP_EXAMPLE = `{
  "mcpServers": {
    "albayan": {
      "command": "python",
      "args": ["-m", "albayan_mcp"],
      "env": {
        "ALBAYAN_API_URL": "https://api.albayan-journal.org",
        "ALBAYAN_AGENT_TOKEN": "alb_ضع_مفتاحك_هنا"
      }
    }
  }
}`;
