"use client";

import Image from "next/image";
import { useRef, useState, type KeyboardEvent } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { isDevMode } from "@/lib/dev-mode";
import { DEV_MCP_SERVERS } from "@/lib/dev-mcp-servers";
import { ConnectionValue, ConnectorIconDownload } from "./mcp-connection-fields";

export function DevMcpServerCarousel() {
  const viewportRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  if (!isDevMode()) return null;

  function navigate(index: number) {
    const next = Math.max(0, Math.min(index, DEV_MCP_SERVERS.length - 1));
    const slide = viewportRef.current?.children[next] as HTMLElement | undefined;
    slide?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "instant"
        : "smooth",
      block: "nearest",
      inline: "center",
    });
    setActiveIndex(next);
  }

  function syncActiveSlide() {
    const viewport = viewportRef.current;
    if (!viewport) return;
    const bounds = viewport.getBoundingClientRect();
    const center = bounds.left + bounds.width / 2;
    let nearest = 0;
    let distance = Infinity;
    Array.from(viewport.children).forEach((slide, index) => {
      const rect = slide.getBoundingClientRect();
      const delta = Math.abs(rect.left + rect.width / 2 - center);
      if (delta < distance) {
        nearest = index;
        distance = delta;
      }
    });
    setActiveIndex(nearest);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    // Keep keyboard events in copy/download controls local to those controls.
    if (event.target !== event.currentTarget) return;
    const target = {
      ArrowLeft: activeIndex + 1,
      ArrowRight: activeIndex - 1,
      Home: 0,
      End: DEV_MCP_SERVERS.length - 1,
    }[event.key];
    if (target === undefined) return;
    event.preventDefault();
    navigate(target);
  }

  const controlClass =
    "inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-35 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600";

  return (
    <section
      className="mt-10"
      aria-labelledby="dev-mcp-heading"
      aria-roledescription="عارض بطاقات"
      dir="rtl"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-amber-700">خاص ببيئة التطوير</p>
          <h2 id="dev-mcp-heading" className="mt-1 text-xl font-bold text-slate-900">
            أدوات البيان للتطوير والاختبار
          </h2>
          <p id="dev-mcp-help" className="mt-2 text-sm leading-6 text-slate-600">
            أضف كل موصل على حدة. اسحب بين البطاقات أو استخدم الأسهم لاختيار الأداة.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className={controlClass}
            aria-label="الموصل السابق"
            aria-controls="dev-mcp-slides"
            disabled={activeIndex === 0}
            onClick={() => navigate(activeIndex - 1)}
          >
            <ChevronRight size={20} aria-hidden />
          </button>
          <button
            type="button"
            className={controlClass}
            aria-label="الموصل التالي"
            aria-controls="dev-mcp-slides"
            disabled={activeIndex === DEV_MCP_SERVERS.length - 1}
            onClick={() => navigate(activeIndex + 1)}
          >
            <ChevronLeft size={20} aria-hidden />
          </button>
        </div>
      </div>

      <div
        id="dev-mcp-slides"
        ref={viewportRef}
        tabIndex={0}
        role="group"
        aria-label="موصلات بيئة التطوير"
        aria-describedby="dev-mcp-help"
        onKeyDown={handleKeyDown}
        onScroll={syncActiveSlide}
        className="mt-5 flex snap-x snap-mandatory gap-4 overflow-x-auto rounded-2xl pb-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600"
      >
        {DEV_MCP_SERVERS.map((server) => (
          <article
            key={server.id}
            aria-labelledby={`dev-mcp-${server.id}-heading`}
            aria-roledescription="بطاقة"
            className={`w-full min-w-0 shrink-0 snap-center snap-always rounded-2xl border-2 p-4 shadow-sm sm:p-5 ${server.theme}`}
          >
            <div className="mb-5 flex items-center gap-4">
              <Image
                src={server.iconPath}
                alt=""
                width={80}
                height={80}
                className="h-20 w-20 shrink-0 object-contain"
              />
              <div>
                <p className="text-xs font-semibold text-slate-500">{server.label}</p>
                <h3 id={`dev-mcp-${server.id}-heading`} className="mt-1 text-lg font-bold text-slate-900">
                  {server.name}
                </h3>
              </div>
            </div>
            <div className="grid gap-3">
              <ConnectionValue label="اسم الاتصال" value={server.name} />
              <ConnectionValue label="وصف الاتصال" value={server.description} />
              <ConnectionValue label="عنوان خادم MCP" value={server.url} />
              <ConnectorIconDownload
                iconPath={server.iconPath}
                name={server.name}
                filename={server.filename}
              />
            </div>
            <p className="mt-4 text-xs leading-6 text-slate-600">{server.authHint}</p>
          </article>
        ))}
      </div>

      <div className="mt-2 flex flex-wrap justify-center gap-2" aria-label="اختيار موصل التطوير">
        {DEV_MCP_SERVERS.map((server, index) => (
          <button
            key={server.id}
            type="button"
            aria-pressed={activeIndex === index}
            aria-controls="dev-mcp-slides"
            onClick={() => navigate(index)}
            className={`rounded-full border px-4 py-2 text-xs font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-600 ${
              activeIndex === index
                ? "border-slate-700 bg-slate-800 text-white"
                : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            }`}
          >
            {server.label}
          </button>
        ))}
      </div>
    </section>
  );
}
