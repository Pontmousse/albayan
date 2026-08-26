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
    tagline: "برنامج على الحاسوب — تربطه بمفتاح ربط من حسابك",
    accentClass: "from-slate-700 to-slate-900",
    authLabel: "مفتاح ربط (يبدأ بـ alb_…)",
    desktopSteps: [
      "من هذه الصفحة اضغط «أنشئ مفتاحك الخاص». إن لم تكن داخل حسابك سيُطلب منك تسجيل دخول التطبيق أولاً.",
      "انسخ مفتاح الربط فور ظهوره (يُعرض مرة واحدة فقط).",
      "افتح برنامج Cursor على الحاسوب.",
      "من Cursor: إعدادات ← MCP ← أضف خادماً جديداً، واختر الربط من الجهاز.",
      "ضع مفتاح الربط في خانة ALBAYAN_AGENT_TOKEN كما في مثال ملف الربط أدناه.",
      "أعد تشغيل Cursor، ثم اكتب: «ما هو ملفي في مجلة البيان؟»",
    ],
    mobileSteps: [
      "تطبيق Cursor على الجوال لا يدعم هذا الربط بشكل كامل حالياً.",
      "أكمل الخطوات من الحاسوب. مفتاح الربط نفسه يعمل على أي جهاز تُعدّه لاحقاً.",
    ],
    notes: [
      "هذا المسار يناسب من يستخدم Cursor على حاسوبه.",
      "احفظ مفتاح الربط في مكان خاص؛ لا تنشره ولا ترسله لأحد.",
    ],
  },
  {
    id: "chatgpt",
    name: "ChatGPT",
    tagline: "من متصفح الحاسوب — تربطه بتسجيل دخول التطبيق",
    accentClass: "from-emerald-600 to-teal-800",
    authLabel: "تسجيل دخول التطبيق",
    desktopSteps: [
      "افتح ChatGPT من متصفح الحاسوب وفعّل «وضع المطوّر» مرة واحدة (الطريقة في الدليل التفصيلي أدناه).",
      "من الإعدادات افتح الموصلات واضغط «إنشاء».",
      "الصق الاسم والوصف وعنوان الخادم — تجدها مع أزرار نسخ في الدليل التفصيلي.",
      "وافق على الإقرار ثم اضغط «إنشاء» — تُفتح صفحة تفويض: سجّل دخول التطبيق واضغط «السماح».",
      "ارجع إلى المحادثة واسأل: «استخدم أداة البيان وأعطني ملفي الشخصي».",
    ],
    mobileSteps: [
      "تفعيل وضع المطوّر وإنشاء الموصل لا يتمّان من تطبيق الجوال.",
      "أنشئ الموصل مرة واحدة من متصفح الحاسوب، وبعدها يعمل في تطبيق الجوال أيضاً.",
    ],
    notes: [
      "لا تحتاج إلى نسخ مفتاح ربط يدوياً — يكفي تسجيل دخول التطبيق.",
      "الوكيل يساعد المؤلفين والمراجعين والمحررين في القراءة والصياغة؛ التقديم والقرارات تبقى من منصة البيان.",
    ],
  },
  {
    id: "claude",
    name: "Claude",
    tagline: "من claude.ai أو تطبيق الحاسوب — تربطه بتسجيل دخول التطبيق",
    accentClass: "from-amber-700 to-orange-900",
    authLabel: "تسجيل دخول التطبيق",
    desktopSteps: [
      "من موقع claude.ai: إعدادات ← التكاملات ← أضف خادم MCP.",
      "أو من تطبيق Claude على الحاسوب: إعدادات ← للمطوّرين ← تعديل ملف الإعداد، ثم أضف الخادم.",
      "الصق عنوان الخادم الظاهر في الصندوق أدناه.",
      "عندما يُطلب منك: سجّل الدخول إلى التطبيق ووافق على الصلاحيات.",
      "اسأل: «اعرض ملفي في مجلة البيان».",
    ],
    mobileSteps: [
      "افتح تطبيق Claude على الجوال.",
      "إن ظهر خيار الربط أو التكاملات: الصق عنوان الخادم نفسه.",
      "إن لم يظهر الخيار في إصدار تطبيقك، أكمل الربط من المتصفح أو من الحاسوب.",
    ],
    notes: [
      "التقديم والحفظ يبقيان يدوياً من منصة البيان.",
      "إن كنت تستخدم Cursor أصلاً يمكنك بدل ذلك إنشاء مفتاح ربط واستخدامه هناك.",
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
