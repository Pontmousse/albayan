/** بيانات أدلة ربط MCP لكل عميل — الأيقونات تُضاف لاحقاً عبر iconSrc */

export type McpClientId = "cursor" | "chatgpt" | "claude";

export type McpClientGuide = {
  id: McpClientId;
  name: string;
  tagline: string;
  /** مسار الأيقونة المستقبلي، مثال: /icons/mcp/cursor.svg */
  iconSrc?: string;
  /** لون مؤقت حتى تُضاف الأيقونة */
  accentClass: string;
  authLabel: string;
  desktopSteps: string[];
  mobileSteps: string[];
  notes: string[];
  configSnippet?: string;
};

export const MCP_SERVER_URL =
  process.env.NEXT_PUBLIC_MCP_SERVER_URL ?? "https://mcp.albayan-journal.org/mcp";

export const MCP_API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "https://api.albayan-journal.org";

export const MCP_CLIENT_GUIDES: McpClientGuide[] = [
  {
    id: "cursor",
    name: "Cursor",
    tagline: "للمطورين — اتصال محلي عبر stdio",
    accentClass: "from-slate-700 to-slate-900",
    authLabel: "مفتاح وكيل (alb_…)",
    desktopSteps: [
      "أنشئ مفتاحاً من «أنشئ مفتاحك الخاص» أدناه (يُعرض مرة واحدة).",
      "ثبّت الخادم: من مجلد mcp_server نفّذ pip install -e .",
      "في Cursor: الإعدادات ← MCP ← أضف خادماً جديداً (stdio).",
      "عيّن ALBAYAN_API_URL و ALBAYAN_AGENT_TOKEN في env كما في المثال.",
      "أعد تشغيل Cursor، ثم جرّب: «ما هو ملفي في البيان؟»",
    ],
    mobileSteps: [
      "تطبيق Cursor على الجوال محدود لدعم MCP حالياً.",
      "يُفضّل الربط من حاسوبك؛ المفتاح نفسه يعمل على أي جهاز مُعدّ.",
    ],
    notes: [
      "الأنسب للتجربة والتطوير — لا حاجة لنشر خادم MCP للاستخدام المحلي.",
      "احفظ المفتاح في مكان آمن؛ لا تشاركه علناً.",
    ],
  },
  {
    id: "chatgpt",
    name: "ChatGPT",
    tagline: "للمستخدمين — اتصال عن بُعد (Streamable HTTP)",
    accentClass: "from-emerald-600 to-teal-800",
    authLabel: "تسجيل دخول Clerk (OAuth)",
    desktopSteps: [
      "من ChatGPT: الإعدادات ← التطبيقات / Connectors ← إضافة MCP.",
      "أدخل عنوان الخادم:",
      MCP_SERVER_URL,
      "عند الطلب سجّل دخولك بحساب البيان ووافق على الصلاحيات.",
      "اسأل: «استخدم أداة البيان وأعطني ملفي الشخصي».",
    ],
    mobileSteps: [
      "من تطبيق ChatGPT على الجوال: نفس المسار (Connectors) إن وُجد.",
      "أكمل تسجيل الدخول في المتصفح إن فُتح رابط OAuth.",
      "يتطلب اتصال إنترنت — لا مفتاح يدوي.",
    ],
    notes: [
      "لا تنسخ مفتاح alb_ — المصادقة عبر حسابك.",
      "صلاحيات المرحلة الأولى: قراءة الملف والمقالات فقط.",
    ],
  },
  {
    id: "claude",
    name: "Claude",
    tagline: "Desktop أو Claude.ai — OAuth عن بُعد",
    accentClass: "from-amber-700 to-orange-900",
    authLabel: "تسجيل دخول Clerk (OAuth)",
    desktopSteps: [
      "Claude Desktop: الإعدادات ← Developer ← Edit Config (mcpServers).",
      "أو من claude.ai: الإعدادات ← Integrations / MCP.",
      "أضف خادماً بعنوان URL:",
      MCP_SERVER_URL,
      "سجّل دخول Clerk عند الطلب، ثم جرّب أداة get_my_profile.",
    ],
    mobileSteps: [
      "تطبيق Claude على الجوال يدعم MCP تدريجياً — راجع إصدار التطبيق.",
      "إن لم يظهر الخيار، استخدم المتصفح أو الحاسوب.",
    ],
    notes: [
      "للحاسوب يمكن أيضاً stdio + مفتاح alb_ (كـ Cursor) للمطورين.",
      "التقديم والحفظ يبقيان يدوياً من منصة البيان.",
    ],
  },
];

export const CURSOR_MCP_STDIO_SNIPPET = `{
  "mcpServers": {
    "albayan": {
      "command": "python",
      "args": ["-m", "albayan_mcp"],
      "env": {
        "ALBAYAN_API_URL": "${MCP_API_URL}",
        "ALBAYAN_AGENT_TOKEN": "alb_ضع_مفتاحك_هنا"
      }
    }
  }
}`;
