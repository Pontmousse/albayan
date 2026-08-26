"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatGptDetailedGuide } from "@/components/wukala/chatgpt-detailed-guide";
import {
  CURSOR_MCP_STDIO_SNIPPET,
  MCP_CLIENT_GUIDES,
  MCP_SERVER_URL,
  type McpClientId,
} from "@/lib/mcp-client-guides";

function ClientIcon({
  name,
  iconSrc,
  accentClass,
  size = "lg",
}: {
  name: string;
  iconSrc?: string;
  accentClass: string;
  size?: "sm" | "lg";
}) {
  const box =
    size === "sm"
      ? "h-8 w-8 rounded-lg text-sm"
      : "h-14 w-14 rounded-2xl text-lg shadow-md";

  if (iconSrc) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={iconSrc}
        alt=""
        className={`${box} object-contain`}
      />
    );
  }

  return (
    <div
      className={`flex items-center justify-center bg-gradient-to-br font-bold text-white ${box} ${accentClass}`}
      aria-hidden
    >
      {name.charAt(0)}
    </div>
  );
}

export function McpClientCarousel() {
  const [activeId, setActiveId] = useState<McpClientId>("cursor");
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeIndex = MCP_CLIENT_GUIDES.findIndex((g) => g.id === activeId);

  const scrollToIndex = useCallback((index: number) => {
    const el = scrollRef.current;
    if (!el) return;
    const child = el.children[index] as HTMLElement | undefined;
    child?.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest",
    });
    setActiveId(MCP_CLIENT_GUIDES[index]?.id ?? "cursor");
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const onScroll = () => {
      const container = scrollRef.current;
      if (!container) return;
      const center = container.getBoundingClientRect().left + container.offsetWidth / 2;
      let closest = 0;
      let minDist = Infinity;
      Array.from(container.children).forEach((child, i) => {
        const rect = (child as HTMLElement).getBoundingClientRect();
        const childCenter = rect.left + rect.width / 2;
        const dist = Math.abs(center - childCenter);
        if (dist < minDist) {
          minDist = dist;
          closest = i;
        }
      });
      const guide = MCP_CLIENT_GUIDES[closest];
      if (guide) setActiveId(guide.id);
    };

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  const active = MCP_CLIENT_GUIDES[activeIndex] ?? MCP_CLIENT_GUIDES[0];

  return (
    <section className="mt-10" aria-labelledby="mcp-setup-heading">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2
            id="mcp-setup-heading"
            className="text-xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            اختر برنامجك واتبع الخطوات
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            اسحب البطاقات أو اضغط اسم البرنامج أعلاه
          </p>
        </div>
        <p className="text-xs text-slate-500">
          الأيقونات الرسمية تُضاف قريباً
        </p>
      </div>

      {/* تبويبات — حاسوب */}
      <div
        className="mt-5 flex gap-2 overflow-x-auto nav-scroll pb-1"
        role="tablist"
        aria-label="اختيار عميل الذكاء الاصطناعي"
      >
        {MCP_CLIENT_GUIDES.map((guide, index) => {
          const selected = guide.id === activeId;
          return (
            <button
              key={guide.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => scrollToIndex(index)}
              className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition ${
                selected
                  ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white shadow-sm"
                  : "border-[var(--journal-border)] bg-white/80 text-slate-700 hover:border-[var(--journal-accent)]/50"
              }`}
            >
              <ClientIcon
                name={guide.name}
                iconSrc={guide.iconSrc}
                accentClass={guide.accentClass}
                size="sm"
              />
              <span>{guide.name}</span>
            </button>
          );
        })}
      </div>

      {/* بطاقات قابلة للسحب */}
      <div className="relative mt-4">
        <div
          ref={scrollRef}
          className="flex snap-x snap-mandatory gap-4 overflow-x-auto nav-scroll scroll-smooth pb-2"
          style={{ scrollPaddingInline: "0.5rem" }}
        >
          {MCP_CLIENT_GUIDES.map((guide) => (
            <article
              key={guide.id}
              className="w-[min(92%,100%)] shrink-0 snap-center snap-always rounded-2xl border border-[var(--journal-border)] bg-gradient-to-b from-white to-[var(--journal-accent-soft)]/40 p-5 shadow-sm sm:min-w-full sm:w-full"
              role="tabpanel"
              aria-labelledby={`tab-${guide.id}`}
            >
              <div className="flex items-start gap-4">
                <ClientIcon
                  name={guide.name}
                  iconSrc={guide.iconSrc}
                  accentClass={guide.accentClass}
                />
                <div className="min-w-0 flex-1">
                  <h3
                    id={`tab-${guide.id}`}
                    className="text-lg font-bold text-slate-900"
                  >
                    {guide.name}
                  </h3>
                  <p className="mt-0.5 text-sm text-slate-600">{guide.tagline}</p>
                  <span className="mt-2 inline-block rounded-full bg-white/90 px-2.5 py-0.5 text-xs font-medium text-[var(--journal-accent-strong)] ring-1 ring-[var(--journal-border)]">
                    {guide.authLabel}
                  </span>
                </div>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-[var(--journal-border)] bg-white/90 p-4">
                  <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                    <span aria-hidden>🖥</span> على الحاسوب
                  </p>
                  <ol className="mt-3 list-decimal space-y-2 ps-4 text-sm leading-6 text-slate-700">
                    {guide.desktopSteps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </div>
                <div className="rounded-xl border border-[var(--journal-border)] bg-white/90 p-4">
                  <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-slate-500">
                    <span aria-hidden>📱</span> على الجوال
                  </p>
                  <ol className="mt-3 list-decimal space-y-2 ps-4 text-sm leading-6 text-slate-700">
                    {guide.mobileSteps.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </div>
              </div>

              {guide.notes.length > 0 && (
                <ul className="mt-4 space-y-1.5 rounded-lg border border-amber-200/80 bg-amber-50/60 px-3 py-2.5 text-sm text-amber-950/90">
                  {guide.notes.map((note) => (
                    <li key={note} className="flex gap-2">
                      <span className="text-amber-600" aria-hidden>
                        •
                      </span>
                      <span>{note}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ))}
        </div>

        {/* مؤشرات */}
        <div className="mt-3 flex items-center justify-center gap-2">
          {MCP_CLIENT_GUIDES.map((guide, index) => (
            <button
              key={guide.id}
              type="button"
              aria-label={`${guide.name}`}
              onClick={() => scrollToIndex(index)}
              className={`h-2 rounded-full transition-all ${
                guide.id === activeId
                  ? "w-6 bg-[var(--journal-accent)]"
                  : "w-2 bg-slate-300 hover:bg-slate-400"
              }`}
            />
          ))}
        </div>

        {/* أسهم — شاشات أوسع */}
        <div className="pointer-events-none absolute inset-y-0 start-0 end-0 hidden items-center justify-between sm:flex">
          <button
            type="button"
            aria-label="السابق"
            className="pointer-events-auto ms-1 flex h-9 w-9 items-center justify-center rounded-full border border-[var(--journal-border)] bg-white/95 text-slate-700 shadow-sm transition hover:bg-white disabled:opacity-40"
            disabled={activeIndex <= 0}
            onClick={() => scrollToIndex(activeIndex - 1)}
          >
            ‹
          </button>
          <button
            type="button"
            aria-label="التالي"
            className="pointer-events-auto me-1 flex h-9 w-9 items-center justify-center rounded-full border border-[var(--journal-border)] bg-white/95 text-slate-700 shadow-sm transition hover:bg-white disabled:opacity-40"
            disabled={activeIndex >= MCP_CLIENT_GUIDES.length - 1}
            onClick={() => scrollToIndex(activeIndex + 1)}
          >
            ›
          </button>
        </div>
      </div>

      <div key={active.id} className="panel-crossfade">
        {active.id === "cursor" && (
          <div className="mt-6">
            <h3 className="text-sm font-bold text-slate-900">
              مثال ملف الربط في Cursor
            </h3>
            <p className="mt-1 text-xs text-slate-600">
              استبدل <code className="rounded bg-slate-100 px-1">alb_…</code> بمفتاح
              الربط بعد إنشائه.
            </p>
            <pre
              dir="ltr"
              className="mt-2 overflow-x-auto rounded-lg border border-[var(--journal-border)] bg-slate-950 p-4 text-start text-xs leading-6 text-emerald-100"
            >
              {CURSOR_MCP_STDIO_SNIPPET}
            </pre>
          </div>
        )}

        {(active.id === "chatgpt" || active.id === "claude") && (
          <div className="mt-6 rounded-xl border border-[var(--journal-border)] bg-white/80 p-4">
            <p className="text-sm font-semibold text-slate-800">عنوان الخادم</p>
            <p
              dir="ltr"
              className="mt-2 break-all rounded-md bg-slate-100 px-3 py-2 text-start text-sm font-mono text-slate-800"
            >
              {MCP_SERVER_URL}
            </p>
            <p className="mt-2 text-xs leading-5 text-slate-600">
              هذا العنوان هو صلة الوصل. سجّل الدخول إلى التطبيق عندما يُطلب منك —
              دون نسخ مفتاح ربط.
            </p>
          </div>
        )}

        {active.id === "chatgpt" && <ChatGptDetailedGuide />}
      </div>
    </section>
  );
}
