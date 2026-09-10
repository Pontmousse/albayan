import { MCP_SERVER_URL } from "./mcp-client-guides";

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

/** إعداد Cursor المتقدم: المفتاح يبقى في البيئة ويُرسل إلى خادم MCP المستضاف. */
export const CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE = `{
  "mcpServers": {
    "albayan": {
      "url": "${MCP_SERVER_URL}",
      "headers": {
        "Authorization": "Bearer \${env:ALBAYAN_AGENT_TOKEN}"
      }
    }
  }
}`;
