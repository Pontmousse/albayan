"use client";

import Image from "next/image";
import { useState } from "react";
import { CopyButton } from "@/components/ui/copy-button";
import { WukalaCtaButton } from "@/components/wukala/wukala-cta-button";
import { useOpenTransition } from "@/hooks/use-open-transition";
import { CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE } from "@/lib/agent-token-config";
import { isDevMode } from "@/lib/dev-mode";
import {
  MCP_SERVER_URL,
  type McpClientGuide,
  type McpClientId,
} from "@/lib/mcp-client-guides";

export const MCP_CONNECTION_NAME = "مجلة البيان";
export const MCP_CONNECTION_DESCRIPTION =
  "مساعد مجلة البيان للبحث والكتابة والمراجعة والتحرير، يسهّل العمل على المقالات والاستفادة من أدوات المجلة مباشرة من مساعدك الذكي.";
export const MCP_CONNECTION_ICON_PATH = "/connector_icon.png";

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
        "املأ الحقول من صندوق «بيانات الربط» أعلاه بالترتيب: الاسم «مجلة البيان»، ثم الوصف، ثم عنوان خادم MCP.",
        "إذا ظهر حقل للأيقونة، حمّل أيقونة الموصل من صندوق «بيانات الربط» وأضفها؛ هي مُهيّأة لحدود الرفع الصغيرة مثل 10 كيلوبايت.",
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

function ConnectorIconDownload() {
  return (
    <div className="rounded-xl border border-emerald-200/80 bg-white/90 p-3.5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl border border-emerald-100 bg-white p-1.5 shadow-sm">
            <Image
              src={MCP_CONNECTION_ICON_PATH}
              alt="أيقونة مجلة البيان للموصل"
              width={48}
              height={48}
              className="h-full w-full object-contain"
            />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs font-bold text-emerald-950">أيقونة الموصل</p>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800 ring-1 ring-emerald-200">
                اختياري
              </span>
            </div>
            <p className="mt-1 text-[11px] leading-5 text-slate-500">
              حمّل شعار مجلة البيان المضغوط إذا كان برنامجك يدعم أيقونة مخصصة
              للموصل. الملف أقل من 10 كيلوبايت.
            </p>
          </div>
        </div>
        <a
          href={MCP_CONNECTION_ICON_PATH}
          download="albayan-connector-icon.png"
          className="inline-flex shrink-0 items-center justify-center rounded-lg bg-emerald-700 px-3.5 py-2 text-xs font-bold text-white transition hover:bg-emerald-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 focus-visible:ring-offset-2"
        >
          تحميل الأيقونة
        </a>
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
  const showAdvancedManualSetup =
    isDevMode() && (guide.id === "cursor" || guide.id === "other");

  return (
    <div className="mt-5 space-y-4">
      <section className="rounded-2xl border-2 border-emerald-300/80 bg-gradient-to-b from-emerald-50/80 to-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-emerald-700">ابدأ من هنا</p>
            <h3 className="mt-1 text-lg font-bold text-slate-900">بيانات الربط</h3>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              ابدأ بالاسم ثم الوصف وعنوان الخادم، وحمّل الأيقونة إذا كان برنامجك
              يدعمها.
            </p>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-emerald-900 ring-1 ring-emerald-200">
            {guide.authLabel}
          </span>
        </div>

        <div className="mt-4 grid gap-3">
          <ConnectionValue
            label="اسم الاتصال"
            value={MCP_CONNECTION_NAME}
            hint="ابدأ بهذا الاسم إذا طلب برنامجك اسماً للاتصال."
          />
          <ConnectionValue
            label="وصف الاتصال"
            value={MCP_CONNECTION_DESCRIPTION}
            hint="وصف مختصر لما يتيحه مساعد مجلة البيان."
          />
          <ConnectionValue label="عنوان خادم MCP" value={MCP_SERVER_URL} />
          <ConnectorIconDownload />
        </div>

        {guide.configSnippet ? (
          <div className="mt-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-bold text-slate-900">
                مثال الربط البعيد في {guide.name}
              </p>
              <CopyButton
                value={guide.configSnippet}
                ariaLabel={`نسخ مثال الربط في ${guide.name}`}
              />
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              لا تضف مفتاحاً شخصياً إلى هذا الإعداد المعتاد.
            </p>
            <pre
              dir="ltr"
              className="mt-2 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 text-start text-xs leading-6 text-emerald-100"
            >
              {guide.configSnippet}
            </pre>
          </div>
        ) : null}

        <p className="mt-4 border-t border-emerald-200/80 pt-3 text-xs leading-5 text-slate-600">
          عند فتح صفحة التفويض، سجّل دخولك هناك مباشرة؛ لا تنسخ كلمة مرورك إلى
          برنامج الوكيل.
        </p>
      </section>

      <DetailedInstructions guide={guide} />

      {showAdvancedManualSetup ? (
        <section className="rounded-2xl border border-[var(--journal-border)] bg-slate-50/80 p-5">
          <p className="text-xs font-bold text-slate-500">
            متقدم — وضع التطوير
          </p>
          <h3 className="mt-1 text-base font-bold text-slate-900">
            ربط بعيد بمفتاح شخصي
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            هذا مسار متقدم للأتمتة غير التفاعلية. استخدم خادم البيان البعيد
            نفسه، وأرسل مفتاحك كترويسة Bearer. يبقى تسجيل دخول التطبيق أعلاه
            هو المسار الموصى به للاستخدام المعتاد.
          </p>
          <WukalaCtaButton
            className="mt-4 w-full sm:w-auto"
            label="إدارة المفاتيح المتقدمة"
          />
          {guide.id === "cursor" ? (
            <div className="mt-5">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-bold text-slate-900">
                  مثال Cursor بمفتاح شخصي
                </p>
                <CopyButton
                  value={CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE}
                  ariaLabel="نسخ مثال Cursor بمفتاح شخصي"
                />
              </div>
              <p className="mt-1 text-xs leading-5 text-slate-600">
                احفظ مفتاحك في متغير البيئة
                <code className="mx-1 rounded bg-slate-100 px-1">
                  ALBAYAN_AGENT_TOKEN
                </code>
                قبل تشغيل Cursor. لا تضع قيمة المفتاح نفسها في ملف الإعداد.
              </p>
              <pre
                dir="ltr"
                className="mt-2 overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 text-start text-xs leading-6 text-emerald-100"
              >
                {CURSOR_REMOTE_AGENT_KEY_MCP_EXAMPLE}
              </pre>
            </div>
          ) : (
            <p className="mt-5 text-sm leading-6 text-slate-600">
              أضف ترويسة Authorization بقيمة Bearer ثم مفتاحك عبر آلية الأسرار
              التي يدعمها برنامجك. راجع وثائق البرنامج لصيغة الإعداد الدقيقة،
              ولا تضع المفتاح في ملف تشاركه مع الآخرين.
            </p>
          )}
        </section>
      ) : null}
    </div>
  );
}
