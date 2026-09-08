"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { McpConnectionGuide } from "@/components/wukala/mcp-connection-guide";
import {
  MCP_CLIENT_GUIDES,
  type McpClientGuide,
  type McpClientId,
} from "@/lib/mcp-client-guides";

function ClientIcon({
  id,
  name,
  iconSrc,
  accentClass,
  size = "lg",
}: {
  id: McpClientId;
  name: string;
  iconSrc?: string;
  accentClass: string;
  size?: "sm" | "lg";
}) {
  const box =
    size === "sm"
      ? "h-8 w-8 rounded-lg text-sm"
      : "h-14 w-14 rounded-2xl text-lg shadow-sm";

  const iconTheme: Record<McpClientId, { surface: string; image: string }> = {
    cursor: {
      surface: "border-stone-300/80 bg-gradient-to-br from-white to-stone-200",
      image: size === "sm" ? "h-[21px] w-[21px]" : "h-9 w-9",
    },
    chatgpt: {
      surface: "border-emerald-200/90 bg-gradient-to-br from-emerald-50 to-teal-100",
      image: size === "sm" ? "h-7 w-10" : "h-12 w-16",
    },
    claude: {
      surface: "border-orange-200/90 bg-gradient-to-br from-orange-50 to-amber-100",
      image: size === "sm" ? "h-[22px] w-[22px]" : "h-[38px] w-[38px]",
    },
    antigravity: {
      surface: "border-sky-200/90 bg-gradient-to-br from-sky-50 to-indigo-100",
      // Newer source files include more transparent padding; scale them by
      // optical size so they read like Cursor, ChatGPT and Claude.
      image:
        size === "sm"
          ? "h-9 w-9 scale-[1.18]"
          : "h-[52px] w-[52px] scale-[1.18]",
    },
    opencode: {
      surface: "border-cyan-200/90 bg-gradient-to-br from-cyan-50 to-blue-100",
      image:
        size === "sm"
          ? "h-9 w-9 scale-[1.2]"
          : "h-[52px] w-[52px] scale-[1.2]",
    },
    other: {
      surface: "border-violet-200/90 bg-gradient-to-br from-violet-50 to-fuchsia-100",
      image:
        size === "sm"
          ? "h-9 w-9 scale-[1.2]"
          : "h-[52px] w-[52px] scale-[1.2]",
    },
  };
  const theme = iconTheme[id];

  if (iconSrc) {
    return (
      <span
        className={`flex shrink-0 items-center justify-center border ${box} ${theme.surface}`}
        aria-hidden
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={iconSrc}
          alt=""
          className={`${theme.image} origin-center object-contain`}
        />
      </span>
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

function ProviderSummary({
  guide,
  panelId,
  tabId,
  viewport,
  className = "",
}: {
  guide: McpClientGuide;
  panelId: string;
  tabId: string;
  viewport: "mobile" | "desktop";
  className?: string;
}) {
  const quickSteps =
    viewport === "mobile"
      ? guide.mobileSteps.slice(0, 3)
      : guide.desktopSteps.slice(0, 3);

  return (
    <article
      id={panelId}
      className={`rounded-2xl border border-[var(--journal-border)] bg-gradient-to-b from-white to-[var(--journal-accent-soft)]/40 p-5 shadow-sm ${className}`}
      role="tabpanel"
      aria-labelledby={tabId}
    >
      <div className="flex items-start gap-4">
        <ClientIcon
          id={guide.id}
          name={guide.name}
          iconSrc={guide.iconSrc}
          accentClass={guide.accentClass}
        />
        <div className="min-w-0 flex-1">
          <h3 className="text-lg font-bold text-slate-900">{guide.name}</h3>
          <p className="mt-0.5 text-sm leading-6 text-slate-600">{guide.tagline}</p>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-[var(--journal-border)] bg-white/90 p-4">
        <p className="text-xs font-bold text-slate-500">
          {viewport === "mobile" ? "على الجوال" : "الخطوات الأولى"}
        </p>
        <ol className="mt-2 list-decimal space-y-2 ps-5 text-sm leading-6 text-slate-700">
          {quickSteps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </div>
    </article>
  );
}

export function McpClientCarousel() {
  const [activeId, setActiveId] = useState<McpClientId>("cursor");
  const scrollRef = useRef<HTMLDivElement>(null);
  const activeIndex = Math.max(
    0,
    MCP_CLIENT_GUIDES.findIndex((guide) => guide.id === activeId),
  );
  const active = MCP_CLIENT_GUIDES[activeIndex] ?? MCP_CLIENT_GUIDES[0];

  const activateIndex = useCallback((index: number, scrollMobile: boolean) => {
    const guide = MCP_CLIENT_GUIDES[index];
    if (!guide) return;
    setActiveId(guide.id);

    if (!scrollMobile) return;
    const child = scrollRef.current?.children[index] as HTMLElement | undefined;
    child?.scrollIntoView({
      behavior: "smooth",
      inline: "center",
      block: "nearest",
    });
  }, []);

  function handleTabKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    index: number,
    idPrefix: "mobile" | "desktop",
    scrollMobile: boolean,
  ) {
    let nextIndex: number | null = null;

    if (event.key === "ArrowLeft") {
      nextIndex = Math.min(index + 1, MCP_CLIENT_GUIDES.length - 1);
    } else if (event.key === "ArrowRight") {
      nextIndex = Math.max(index - 1, 0);
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = MCP_CLIENT_GUIDES.length - 1;
    }

    if (nextIndex === null || nextIndex === index) return;
    event.preventDefault();
    activateIndex(nextIndex, scrollMobile);
    const nextGuide = MCP_CLIENT_GUIDES[nextIndex];
    requestAnimationFrame(() => {
      document
        .getElementById(`${idPrefix}-tab-${nextGuide.id}`)
        ?.focus();
    });
  }

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    const onScroll = () => {
      const container = scrollRef.current;
      if (!container) return;
      const center =
        container.getBoundingClientRect().left + container.offsetWidth / 2;
      let closest = 0;
      let minDist = Infinity;

      Array.from(container.children).forEach((child, index) => {
        const rect = (child as HTMLElement).getBoundingClientRect();
        const childCenter = rect.left + rect.width / 2;
        const dist = Math.abs(center - childCenter);
        if (dist < minDist) {
          minDist = dist;
          closest = index;
        }
      });

      const guide = MCP_CLIENT_GUIDES[closest];
      if (guide) setActiveId(guide.id);
    };

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  const selectedTabClass: Record<McpClientId, string> = {
    cursor:
      "border-stone-400 bg-gradient-to-br from-white to-stone-200 text-slate-900 shadow-sm ring-1 ring-stone-300/50",
    chatgpt:
      "border-emerald-400/80 bg-gradient-to-br from-emerald-50 to-teal-100 text-emerald-950 shadow-sm ring-1 ring-emerald-200/60",
    claude:
      "border-orange-300 bg-gradient-to-br from-orange-50 to-amber-100 text-orange-950 shadow-sm ring-1 ring-orange-200/60",
    antigravity:
      "border-sky-300 bg-gradient-to-br from-sky-50 to-indigo-100 text-sky-950 shadow-sm ring-1 ring-sky-200/60",
    opencode:
      "border-cyan-300 bg-gradient-to-br from-cyan-50 to-blue-100 text-cyan-950 shadow-sm ring-1 ring-cyan-200/60",
    other:
      "border-violet-300 bg-gradient-to-br from-violet-50 to-fuchsia-100 text-violet-950 shadow-sm ring-1 ring-violet-200/60",
  };

  return (
    <section className="mt-10" aria-labelledby="mcp-setup-heading">
      <div>
        <h2
          id="mcp-setup-heading"
          className="text-xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          اختر برنامجك واتبع الخطوات
        </h2>
        <p className="mt-1 text-sm leading-6 text-slate-600">
          على الجوال اسحب بين البطاقات. على الحاسوب تظهر جميع البرامج أمامك وتُبدّل اللوحة مباشرة.
        </p>
        <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2.5 text-xs leading-6 text-slate-600">
          قد تتغيّر أسماء بعض القوائم مع تحديث هذه البرامج؛ نراجع الإرشادات دورياً ونحافظ على بيانات الربط المشتركة في مكان واحد.
        </div>
      </div>

      <div
        className="nav-scroll mt-5 flex gap-2 overflow-x-auto pb-1 sm:hidden"
        role="tablist"
        aria-label="اختيار عميل الذكاء الاصطناعي"
      >
        {MCP_CLIENT_GUIDES.map((guide, index) => {
          const selected = guide.id === activeId;
          return (
            <button
              key={guide.id}
              id={`mobile-tab-${guide.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`mobile-panel-${guide.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => activateIndex(index, true)}
              onKeyDown={(event) =>
                handleTabKeyDown(event, index, "mobile", true)
              }
              className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition ${
                selected
                  ? selectedTabClass[guide.id]
                  : "border-[var(--journal-border)] bg-white/80 text-slate-700 hover:border-[var(--journal-accent)]/50"
              }`}
            >
              <ClientIcon
                id={guide.id}
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

      <div
        className="mt-5 hidden gap-2 sm:grid sm:grid-cols-3"
        role="tablist"
        aria-label="اختيار عميل الذكاء الاصطناعي"
      >
        {MCP_CLIENT_GUIDES.map((guide, index) => {
          const selected = guide.id === activeId;
          return (
            <button
              key={guide.id}
              id={`desktop-tab-${guide.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`desktop-panel-${guide.id}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => activateIndex(index, false)}
              onKeyDown={(event) =>
                handleTabKeyDown(event, index, "desktop", false)
              }
              className={`inline-flex w-full min-w-0 items-center gap-2 rounded-xl border px-3 py-2.5 text-start text-sm font-semibold transition ${
                selected
                  ? selectedTabClass[guide.id]
                  : "border-[var(--journal-border)] bg-white/80 text-slate-700 hover:border-[var(--journal-accent)]/50"
              }`}
            >
              <ClientIcon
                id={guide.id}
                name={guide.name}
                iconSrc={guide.iconSrc}
                accentClass={guide.accentClass}
                size="sm"
              />
              <span className="truncate">{guide.name}</span>
            </button>
          );
        })}
      </div>

      <div className="relative mt-4 sm:hidden">
        <div
          ref={scrollRef}
          className="nav-scroll flex snap-x snap-mandatory gap-4 overflow-x-auto scroll-smooth pb-2"
          style={{ scrollPaddingInline: "0.5rem" }}
        >
          {MCP_CLIENT_GUIDES.map((guide) => (
            <ProviderSummary
              key={guide.id}
              guide={guide}
              panelId={`mobile-panel-${guide.id}`}
              tabId={`mobile-tab-${guide.id}`}
              viewport="mobile"
              className="w-[min(92%,100%)] shrink-0 snap-center snap-always"
            />
          ))}
        </div>

        <div className="mt-3 flex items-center justify-center gap-2">
          {MCP_CLIENT_GUIDES.map((guide, index) => (
            <button
              key={guide.id}
              type="button"
              aria-label={guide.name}
              onClick={() => activateIndex(index, true)}
              className={`h-2 rounded-full transition-all ${
                guide.id === activeId
                  ? "w-6 bg-[var(--journal-accent)]"
                  : "w-2 bg-slate-300 hover:bg-slate-400"
              }`}
            />
          ))}
        </div>
      </div>

      <div key={active.id} className="panel-crossfade mt-4 hidden sm:block">
        <ProviderSummary
          guide={active}
          panelId={`desktop-panel-${active.id}`}
          tabId={`desktop-tab-${active.id}`}
          viewport="desktop"
        />
      </div>

      <div key={`connection-${active.id}`} className="panel-crossfade">
        <McpConnectionGuide guide={active} />
      </div>
    </section>
  );
}
