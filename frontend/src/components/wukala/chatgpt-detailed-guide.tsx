"use client";

import { useState } from "react";
import { MCP_SERVER_URL } from "@/lib/mcp-client-guides";
import { useOpenTransition } from "@/hooks/use-open-transition";

/* بيانات الدليل التفصيلي هنا (لا في mcp-client-guides.ts) عمداً:
   الأدلة الأساسية خالية من مسميات إنجليزية، بينما هذا القسم المتقدم
   المطويّ يسمّي عناصر واجهة ChatGPT كما تظهر فعلاً (OAuth, DCR...). */

export const CHATGPT_CONNECTOR_NAME = "البيان";
export const CHATGPT_CONNECTOR_DESCRIPTION =
  "مساعدة في العمل العلمي بمجلة البيان: قراءة المخطوطات، صياغة المسودات، ومساندة المراجعة والتحرير — دون تقديم المقال أو اتخاذ قرارات نهائية.";

const ACCORDION_EXIT_MS = 280;

type ChatGptDetailedStep = {
  text: string;
  /** قيمة تُعرض مع زر نسخ */
  copyValue?: string;
  copyLabel?: string;
};

type ChatGptDetailedSection = {
  title: string;
  steps: ChatGptDetailedStep[];
};

const CHATGPT_DETAILED_GUIDE: ChatGptDetailedSection[] = [
  {
    title: "أولاً — تفعيل وضع المطوّر (مرة واحدة)",
    steps: [
      {
        text: "افتح chatgpt.com من متصفح الحاسوب. وضع المطوّر لا يُفعَّل من تطبيق الجوال.",
      },
      { text: "اضغط صورتك أو اسمك في أسفل الشريط، ثم اختر «الإعدادات»." },
      { text: "افتح «التطبيقات والموصلات» (Apps & Connectors)." },
      {
        text: "انزل إلى «الإعدادات المتقدمة» وفعّل «وضع المطوّر» (Developer mode).",
      },
    ],
  },
  {
    title: "ثانياً — إنشاء الموصل",
    steps: [
      { text: "ارجع إلى «الموصلات» واضغط زر «إنشاء» (Create)." },
      {
        text: "في خانة الاسم الصق:",
        copyValue: CHATGPT_CONNECTOR_NAME,
        copyLabel: "نسخ الاسم",
      },
      {
        text: "في خانة الوصف الصق:",
        copyValue: CHATGPT_CONNECTOR_DESCRIPTION,
        copyLabel: "نسخ الوصف",
      },
      {
        text: "في خانة عنوان خادم MCP الصق:",
        copyValue: MCP_SERVER_URL,
        copyLabel: "نسخ العنوان",
      },
      { text: "في خيار المصادقة اترك OAuth كما هو (الافتراضي)." },
    ],
  },
  {
    title: "ثالثاً — التحقق والاعتماد",
    steps: [
      {
        text: "(اختياري) افتح «إعدادات OAuth المتقدمة» وتأكد أنها تعرض النطاقات openid وprofile وemail وأن التسجيل التلقائي للعميل (DCR) ظاهر — هذه تصل تلقائياً من خادمنا.",
      },
      { text: "علّم خانة الإقرار ثم اضغط «إنشاء»." },
      {
        text: "يُفتح تبويب جديد بصفحة تفويض باسم البيان: سجّل دخول التطبيق إن طُلب منك، ثم اضغط «السماح».",
      },
      {
        text: "عد إلى ChatGPT — الموصل جاهز. جرّب: «استخدم أداة البيان وأعطني ملفي الشخصي» أو «اعرض مقالاتي».",
      },
    ],
  },
];

function CopyValue({ step }: { step: ChatGptDetailedStep }) {
  const [copied, setCopied] = useState(false);

  if (!step.copyValue) return null;

  async function handleCopy() {
    if (!step.copyValue) return;
    try {
      await navigator.clipboard.writeText(step.copyValue);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <span className="mt-1.5 flex flex-wrap items-center gap-2">
      <code
        dir="auto"
        className="min-w-0 break-all rounded-md bg-slate-100 px-2.5 py-1.5 text-start text-xs text-slate-800"
      >
        {step.copyValue}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        className="shrink-0 rounded-md border border-[var(--journal-border)] bg-white px-2.5 py-1 text-xs font-semibold text-[var(--journal-accent-strong)] transition hover:border-[var(--journal-accent)]"
      >
        {copied ? "تم النسخ" : step.copyLabel ?? "نسخ"}
      </button>
    </span>
  );
}

/** دليل ChatGPT التفصيلي — مطويّ افتراضياً حتى لا يُثقل الصفحة على غير المتقدمين. */
export function ChatGptDetailedGuide() {
  const [open, setOpen] = useState(false);
  const { mounted, visible } = useOpenTransition(open, ACCORDION_EXIT_MS);

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-[var(--journal-border)] bg-white/80">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-start"
      >
        <span>
          <span className="block text-sm font-bold text-slate-900">
            الدليل التفصيلي خطوة بخطوة
          </span>
          <span className="mt-0.5 block text-xs text-slate-600">
            كل خطوات ChatGPT من تفعيل وضع المطوّر حتى «السماح» — مع أزرار نسخ
          </span>
        </span>
        <span
          aria-hidden
          className={`shrink-0 text-slate-500 transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none ${
            open ? "rotate-90" : ""
          }`}
        >
          ‹
        </span>
      </button>

      {mounted ? (
        <div
          className="accordion-panel motion-reduce:transition-none"
          data-visible={visible ? "true" : "false"}
        >
          <div className="accordion-panel-inner">
            <ol
              className="accordion-stagger space-y-5 border-t border-[var(--journal-border)] px-4 py-4"
              data-visible={visible ? "true" : "false"}
            >
              {CHATGPT_DETAILED_GUIDE.map((section) => (
                <li key={section.title}>
                  <h4 className="text-sm font-bold text-[var(--journal-accent-strong)]">
                    {section.title}
                  </h4>
                  <ol className="mt-2 list-decimal space-y-2.5 ps-5 text-sm leading-6 text-slate-700">
                    {section.steps.map((step) => (
                      <li key={step.text}>
                        {step.text}
                        <CopyValue step={step} />
                      </li>
                    ))}
                  </ol>
                </li>
              ))}
            </ol>
          </div>
        </div>
      ) : null}
    </div>
  );
}
