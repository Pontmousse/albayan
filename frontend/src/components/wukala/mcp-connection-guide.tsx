"use client";

import { useState } from "react";
import { CopyButton } from "@/components/ui/copy-button";
import { WukalaCtaButton } from "@/components/wukala/wukala-cta-button";
import { useOpenTransition } from "@/hooks/use-open-transition";
import {
  CURSOR_MCP_STDIO_SNIPPET,
  MCP_SERVER_URL,
  type McpClientGuide,
  type McpClientId,
} from "@/lib/mcp-client-guides";

export const MCP_CONNECTION_NAME = "البيان";
export const MCP_CONNECTION_DESCRIPTION =
  "مساعدة في العمل العلمي بمجلة البيان: قراءة المخطوطات، صياغة المسودات، ومساندة المراجعة والتحرير — دون تقديم المقال أو اتخاذ قرارات نهائية.";

const ACCORDION_EXIT_MS = 280;

type DetailedSection = {
  title: string;
  steps: string[];
};

const DETAILED_GUIDE_OVERRIDES: Partial<
  Record<McpClientId, DetailedSection[]>
> = {
  chatgpt: [
    {
      title: "أولاً — تفعيل وضع المطوّر (مرة واحدة)",
      steps: [
        "افتح chatgpt.com من متصفح الحاسوب. وضع المطوّر لا يُفعَّل من تطبيق الجوال.",
        "اضغط صورتك أو اسمك في أسفل الشريط، ثم اختر «الإعدادات».",
        "افتح «التطبيقات والموصلات» (Apps & Connectors).",
        "انزل إلى «الإعدادات المتقدمة» وفعّل «وضع المطوّر» (Developer mode).",
      ],
    },
    {
      title: "ثانياً — إنشاء الموصل",
      steps: [
        "ارجع إلى «الموصلات» واضغط زر «إنشاء» (Create).",
        "استخدم اسم الاتصال والوصف وعنوان خادم MCP من صندوق «بيانات الربط» أعلاه؛ لكل قيمة زر نسخ مستقل.",
        "في خيار المصادقة اترك OAuth كما هو (الافتراضي).",
      ],
    },
    {
      title: "ثالثاً — التحقق والاعتماد",
      steps: [
        "(اختياري) افتح «إعدادات OAuth المتقدمة» وتأكد أنها تعرض النطاقات openid وprofile وemail وأن التسجيل التلقائي للعميل (DCR) ظاهر — هذه تصل تلقائياً من خادمنا.",
        "علّم خانة الإقرار ثم اضغط «إنشاء».",
        "يُفتح تبويب جديد بصفحة تفويض باسم البيان: سجّل دخول التطبيق إن طُلب منك، ثم اضغط «السماح».",
        "عد إلى ChatGPT — الموصل جاهز. جرّب: «استخدم أداة البيان وأعطني ملفي الشخصي» أو «اعرض مقالاتي».",
      ],
    },
  ],
};

function ConnectionValue({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-emerald-200/80 bg-white/90 p-3.5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-bold text-emerald-950">{label}</p>
          {hint ? (
            <p className="mt-0.5 text-[11px] leading-5 text-slate-500">{hint}</p>
          ) : null}
          <code
            dir="auto"
            className="mt-2 block break-all rounded-md bg-slate-100 px-2.5 py-2 text-start text-xs leading-5 text-slate-800"
          >
            {value}
          </code>
        </div>
        <CopyButton value={value} ariaLabel={`نسخ ${label}`} />
      </div>
    </div>
  );
}

function getDetailedSections(guide: McpClientGuide): DetailedSection[] {
  const override = DETAILED_GUIDE_OVERRIDES[guide.id];
  const sections = override
    ? [...override]
    : [
        { title: "على الحاسوب", steps: guide.desktopSteps },
        { title: "على الجوال", steps: guide.mobileSteps },
      ];

  if (override && guide.mobileSteps.length > 0) {
    sections.push({ title: "على الجوال", steps: guide.mobileSteps });
  }

  return sections;
}

function DetailedInstructions({ guide }: { guide: McpClientGuide }) {
  const [open, setOpen] = useState(false);
  const { mounted, visible } = useOpenTransition(open, ACCORDION_EXIT_MS);
  const sections = getDetailedSections(guide);
  const panelId = `mcp-detailed-${guide.id}`;

  return (
    <section className="overflow-hidden rounded-2xl border-2 border-[var(--journal-border)] bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={panelId}
        className="flex w-full items-center justify-between gap-4 bg-[var(--journal-accent-soft)]/55 px-5 py-4 text-start transition hover:bg-[var(--journal-accent-soft)]"
      >
        <span>
          <span className="block text-sm font-bold text-slate-900">
            التعليمات التفصيلية لـ {guide.name}
          </span>
          <span className="mt-1 block text-xs leading-5 text-slate-600">
            افتح هذا القسم إذا احتجت أسماء القوائم والخطوات كاملة.
          </span>
        </span>
        <span
          aria-hidden
          className={`shrink-0 text-xl text-[var(--journal-accent-strong)] transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none ${
            open ? "rotate-90" : ""
          }`}
        >
          ‹
        </span>
      </button>

      {mounted ? (
        <div
          id={panelId}
          className="accordion-panel motion-reduce:transition-none"
          data-visible={visible ? "true" : "false"}
        >
          <div className="accordion-panel-inner">
            <div
              className="accordion-stagger space-y-5 border-t border-[var(--journal-border)] px-5 py-5"
              data-visible={visible ? "true" : "false"}
            >
              {sections.map((section) => (
                <section key={section.title}>
                  <h4 className="text-sm font-bold text-[var(--journal-accent-strong)]">
                    {section.title}
                  </h4>
                  <ol className="mt-2 list-decimal space-y-2.5 ps-5 text-sm leading-6 text-slate-700">
                    {section.steps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>
              ))}

              {guide.notes.length > 0 ? (
                <div className="rounded-lg border border-amber-200/80 bg-amber-50/60 px-3 py-2.5">
                  <p className="text-xs font-bold text-amber-900">ملاحظات</p>
                  <ul className="mt-1.5 list-disc space-y-1 ps-5 text-sm leading-6 text-amber-950/90">
                    {guide.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

export function McpConnectionGuide({ guide }: { guide: McpClientGuide }) {
  const usesRemoteServer = guide.id !== "cursor";
  const canUseManualKey = guide.id === "cursor" || guide.id === "other";

  return (
    <div className="mt-5 space-y-4">
      <section className="rounded-2xl border-2 border-emerald-300/80 bg-gradient-to-b from-emerald-50/80 to-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-emerald-700">ابدأ من هنا</p>
            <h3 className="mt-1 text-lg font-bold text-slate-900">بيانات الربط</h3>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              هذه القيم المشتركة هي ما تحتاجه أغلب البرامج. انسخ ما يطلبه برنامجك فقط.
            </p>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-emerald-900 ring-1 ring-emerald-200">
            {guide.authLabel}
          </span>
        </div>

        {usesRemoteServer ? (
          <div className="mt-4 grid gap-3">
            <ConnectionValue label="عنوان خادم MCP" value={MCP_SERVER_URL} />
            <div className="grid gap-3 sm:grid-cols-2">
              <ConnectionValue
                label="اسم الاتصال"
                value={MCP_CONNECTION_NAME}
                hint="استخدمه إذا طلب برنامجك اسماً للاتصال."
              />
              <ConnectionValue
                label="وصف الاتصال"
                value={MCP_CONNECTION_DESCRIPTION}
                hint="استخدمه إذا طلب برنامجك وصفاً للاتصال."
              />
            </div>
          </div>
        ) : null}

        {canUseManualKey ? (
          <div className="mt-4 rounded-xl border border-slate-200 bg-white/90 p-4">
            <p className="text-sm font-bold text-slate-900">
              {guide.id === "cursor" ? "مفتاح الربط" : "مفتاح ربط يدوي — عند الحاجة فقط"}
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              {guide.id === "cursor"
                ? "أنشئ مفتاحاً خاصاً ثم ضعه في إعداد Cursor كما في المثال أدناه."
                : "استخدم هذا المسار فقط إذا كان برنامجك لا يدعم تسجيل الدخول إلى خادم MCP البعيد."}
            </p>
            <WukalaCtaButton
              className="mt-3 w-full sm:w-auto"
              label="أنشئ مفتاحك الخاص"
            />
          </div>
        ) : null}

        {guide.id === "cursor" ? (
          <div className="mt-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-bold text-slate-900">مثال ملف الربط في Cursor</p>
              <CopyButton
                value={CURSOR_MCP_STDIO_SNIPPET}
                ariaLabel="نسخ مثال ملف الربط"
              />
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              استبدل <code className="rounded bg-slate-100 px-1">alb_…</code> بمفتاح الربط بعد إنشائه.
            </p>
            <pre
              dir="ltr"
              className="mt-2 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 text-start text-xs leading-6 text-emerald-100"
            >
              {CURSOR_MCP_STDIO_SNIPPET}
            </pre>
          </div>
        ) : null}

        <p className="mt-4 border-t border-emerald-200/80 pt-3 text-xs leading-5 text-slate-600">
          {canUseManualKey
            ? "إذا أنشأت مفتاح ربط، احتفظ به في مكان خاص ولا تضعه في محادثة أو مستودع عام."
            : "عند فتح صفحة التفويض، سجّل دخولك هناك مباشرة؛ لا تنسخ كلمة مرورك إلى برنامج الوكيل."}
        </p>
      </section>

      <DetailedInstructions guide={guide} />
    </div>
  );
}
