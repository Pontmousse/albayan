/** بيانات الموصلات الخاصة ببيئة التطوير، دون أسرار أو مفاتيح. */
export const DEV_MCP_SERVERS = [
  {
    id: "dev",
    name: "البيان — مساعد التطوير",
    label: "التطوير والتشخيص",
    description:
      "مساعد تطوير البيان لتشخيص الأعطال، وتتبع الطلبات بين الخدمات، وفحص تحويل المعادلات وتشغيل اختبارات التحقق في بيئة التطوير.",
    url:
      process.env.NEXT_PUBLIC_DEV_MCP_SERVER_URL?.trim() ||
      "https://devmcp.dev.albayan-journal.org/mcp",
    iconPath: "/wukala/albayan-mcp-dev-icon.png",
    filename: "albayan-mcp-dev-icon.png",
    authHint: "اختر OAuth، ثم سجّل الدخول بحساب مخوّل للتطوير.",
    theme: "border-sky-200 bg-gradient-to-b from-sky-50/80 to-white",
  },
  {
    id: "playwright",
    name: "البيان — مساعد المتصفح",
    label: "المتصفح · Playwright",
    description:
      "مساعد البيان لاختبار تجربة الاستخدام عبر Playwright؛ يتصفح الصفحات، ويتفاعل مع عناصرها، ويلتقط صور الشاشة للتحقق من الواجهات ورصد مشكلات العرض.",
    url:
      process.env.NEXT_PUBLIC_PLAYWRIGHT_MCP_SERVER_URL?.trim() ||
      "https://playwright-mcp.dev.albayan-journal.org/mcp",
    iconPath: "/wukala/albayan-mcp-playwright-icon.png",
    filename: "albayan-mcp-playwright-icon.png",
    authHint: "اختر «بلا مصادقة» لهذا الموصل؛ تسجيل دخول الموقع داخل المتصفح خطوة مستقلة.",
    theme: "border-violet-200 bg-gradient-to-b from-violet-50/80 to-white",
  },
  {
    id: "authoring-dev",
    name: "البيان - بيئة التطوير",
    label: "الربط العادي · بيئة التطوير",
    description:
      "مساعد مجلة البيان للبحث والكتابة والمراجعة والتحرير، يسهّل العمل على المقالات والاستفادة من أدوات المجلة مباشرة من مساعدك الذكي.",
    url: "https://mcp.dev.albayan-journal.org/mcp",
    iconPath: "/connector_icon.png",
    filename: "albayan-connector-icon.png",
    authHint: "اختر OAuth، ثم سجّل الدخول بحسابك في مجلة البيان.",
    theme: "border-emerald-200 bg-gradient-to-b from-emerald-50/80 to-white",
  },
] as const;
