"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import {
  toEasternNumeral,
  tutorialEpisodeLabel,
  type TutorialLesson,
} from "@/lib/tutorials";

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function LessonAwaitingPanel({ title }: { title: string }) {
  return (
    <div
      className="relative flex aspect-video flex-col items-center justify-center overflow-hidden bg-[linear-gradient(165deg,var(--journal-accent-soft)_0%,#fbf8f1_48%,#eef5f0_100%)] px-6 text-center"
      aria-label={`${title} — يُستكمل عند تمام التسجيل`}
    >
      <div
        className="pointer-events-none absolute inset-x-8 top-6 h-px bg-gradient-to-l from-transparent via-[var(--journal-gold)]/70 to-transparent sm:inset-x-16"
        aria-hidden
      />
      <p
        className="text-2xl text-[var(--journal-gold)] sm:text-3xl"
        aria-hidden
      >
        ۞
      </p>
      <p
        className="mt-3 text-lg font-bold text-[var(--journal-accent)] sm:text-2xl"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        يُستكمل هذا الدرس عند تمامه
      </p>
      <p className="mt-2 max-w-md text-sm leading-8 text-slate-600 sm:text-[0.95rem]">
        شرح وجيز، في نحو ثلاثين ثانية، يُدرج في موضعه من هذه الصفحة حين يكتمل
        تسجيله.
      </p>
      <div
        className="pointer-events-none absolute inset-x-8 bottom-6 h-px bg-gradient-to-l from-transparent via-[var(--journal-gold)]/70 to-transparent sm:inset-x-16"
        aria-hidden
      />
    </div>
  );
}

function LessonStage({
  lesson,
  index,
}: {
  lesson: TutorialLesson;
  index: number;
}) {
  return (
    <article className="flex h-full flex-col overflow-hidden rounded-2xl border border-[var(--journal-border)] bg-white/85 shadow-sm">
      <div className="h-1 bg-gradient-to-l from-emerald-800 via-amber-600 to-[var(--journal-accent)]" />
      {lesson.src ? (
        <video
          className="aspect-video w-full bg-slate-900"
          controls
          playsInline
          preload="metadata"
          aria-label={lesson.title}
        >
          <source src={lesson.src} />
        </video>
      ) : (
        <LessonAwaitingPanel title={lesson.title} />
      )}
      <div className="space-y-2 px-5 py-5 sm:px-7 sm:py-6">
        <p className="text-xs font-semibold tracking-wide text-[var(--journal-accent)]">
          {tutorialEpisodeLabel(index)}
        </p>
        <h2
          className="text-lg font-bold text-slate-900 sm:text-2xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          {lesson.title}
        </h2>
        <p className="text-sm leading-8 text-slate-600 sm:text-[0.95rem]">
          {lesson.description}
        </p>
      </div>
    </article>
  );
}

export function LessonsFolio({ lessons }: { lessons: TutorialLesson[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const tablistId = useId();
  const showSwitcher = lessons.length > 1;
  const active = lessons[activeIndex] ?? lessons[0];

  const scrollToIndex = useCallback(
    (index: number, { updateHash = true }: { updateHash?: boolean } = {}) => {
      if (index < 0 || index >= lessons.length) return;
      const el = scrollRef.current;
      const child = el?.children[index] as HTMLElement | undefined;
      child?.scrollIntoView({
        behavior: prefersReducedMotion() ? "auto" : "smooth",
        inline: "center",
        block: "nearest",
      });
      setActiveIndex(index);
      const lesson = lessons[index];
      if (updateHash && lesson && typeof window !== "undefined") {
        const nextHash = `#${lesson.id}`;
        if (window.location.hash !== nextHash) {
          history.replaceState(null, "", nextHash);
        }
      }
    },
    [lessons],
  );

  useEffect(() => {
    function applyHash() {
      const id = decodeURIComponent(window.location.hash.replace(/^#/, ""));
      if (!id) return;
      const index = lessons.findIndex((lesson) => lesson.id === id);
      if (index >= 0) scrollToIndex(index, { updateHash: false });
    }
    applyHash();
    window.addEventListener("hashchange", applyHash);
    return () => window.removeEventListener("hashchange", applyHash);
  }, [lessons, scrollToIndex]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el || lessons.length < 2) return;

    const onScroll = () => {
      const container = scrollRef.current;
      if (!container) return;
      const center =
        container.getBoundingClientRect().left + container.offsetWidth / 2;
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
      setActiveIndex((current) => {
        if (current === closest) return current;
        const lesson = lessons[closest];
        if (lesson && typeof window !== "undefined") {
          const nextHash = `#${lesson.id}`;
          if (window.location.hash !== nextHash) {
            history.replaceState(null, "", nextHash);
          }
        }
        return closest;
      });
    };

    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [lessons]);

  if (lessons.length === 0 || !active) {
    return null;
  }

  return (
    <section className="mt-8" aria-labelledby={tablistId}>
      <h2 id={tablistId} className="sr-only">
        فهرس الدروس
      </h2>

      {showSwitcher ? (
        <div className="mb-4 sm:hidden">
          <label
            htmlFor="lesson-select"
            className="mb-1.5 block text-xs font-semibold text-[var(--journal-accent)]"
          >
            فهرس الدروس
          </label>
          <select
            id="lesson-select"
            className="min-h-11 w-full rounded-xl border border-[var(--journal-border)] bg-white/90 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none transition focus:border-[var(--journal-accent)]"
            value={active.id}
            onChange={(event) => {
              const index = lessons.findIndex((lesson) => lesson.id === event.target.value);
              if (index >= 0) scrollToIndex(index);
            }}
          >
            {lessons.map((lesson, index) => (
              <option key={lesson.id} value={lesson.id}>
                {toEasternNumeral(index + 1)} — {lesson.title}
              </option>
            ))}
          </select>
        </div>
      ) : null}

      <div className="lg:grid lg:grid-cols-[minmax(13rem,16rem)_minmax(0,1fr)] lg:items-start lg:gap-6">
        {showSwitcher ? (
          <nav className="mb-4 hidden sm:block lg:mb-0" aria-label="فهرس الدروس">
            <p
              className="mb-3 hidden text-sm font-semibold text-[var(--journal-accent)] lg:block"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              الفهرس
            </p>
            <div
              role="tablist"
              aria-label="اختيار الدرس"
              className="flex gap-2 overflow-x-auto nav-scroll pb-1 lg:flex-col lg:gap-1.5 lg:overflow-visible lg:pb-0"
              onKeyDown={(event) => {
                if (event.key === "ArrowLeft") {
                  event.preventDefault();
                  scrollToIndex(Math.min(lessons.length - 1, activeIndex + 1));
                } else if (event.key === "ArrowRight") {
                  event.preventDefault();
                  scrollToIndex(Math.max(0, activeIndex - 1));
                } else if (event.key === "Home") {
                  event.preventDefault();
                  scrollToIndex(0);
                } else if (event.key === "End") {
                  event.preventDefault();
                  scrollToIndex(lessons.length - 1);
                }
              }}
            >
              {lessons.map((lesson, index) => {
                const selected = index === activeIndex;
                return (
                  <button
                    key={lesson.id}
                    type="button"
                    role="tab"
                    id={`lesson-tab-${lesson.id}`}
                    aria-selected={selected}
                    aria-controls={`lesson-panel-${lesson.id}`}
                    tabIndex={selected ? 0 : -1}
                    onClick={() => scrollToIndex(index)}
                    className={`shrink-0 rounded-xl border border-s-4 ps-3.5 pe-3.5 py-2.5 text-start transition lg:w-full ${
                      selected
                        ? "border-[var(--journal-accent)] border-s-[var(--journal-accent)] bg-[var(--journal-accent-soft)] shadow-sm"
                        : "border-[var(--journal-border)] border-s-transparent bg-white/80 hover:border-[var(--journal-accent)]/50"
                    }`}
                  >
                    <span className="flex items-baseline gap-2">
                      <span
                        className={`text-sm font-bold ${
                          selected
                            ? "text-[var(--journal-gold)]"
                            : "text-[var(--journal-accent)]"
                        }`}
                        style={{ fontFamily: "var(--font-display-ar), serif" }}
                      >
                        {toEasternNumeral(index + 1)}
                      </span>
                      <span
                        className={`text-sm font-semibold leading-6 ${
                          selected ? "text-slate-900" : "text-slate-700"
                        }`}
                      >
                        {lesson.title}
                      </span>
                    </span>
                    <span className="mt-0.5 hidden text-[11px] text-slate-500 lg:block">
                      {tutorialEpisodeLabel(index)}
                      {lesson.src ? "" : " · يُستكمل"}
                    </span>
                  </button>
                );
              })}
            </div>
          </nav>
        ) : null}

        <div>
          <div
            ref={scrollRef}
            className="flex snap-x snap-mandatory overflow-x-auto nav-scroll scroll-smooth"
            style={{ scrollPaddingInline: "0.25rem" }}
          >
            {lessons.map((lesson, index) => (
              <div
                key={lesson.id}
                id={`lesson-panel-${lesson.id}`}
                role="tabpanel"
                aria-labelledby={`lesson-tab-${lesson.id}`}
                aria-hidden={index !== activeIndex}
                className="w-full min-w-full shrink-0 snap-center snap-always"
              >
                <LessonStage lesson={lesson} index={index} />
              </div>
            ))}
          </div>

          {showSwitcher ? (
            <div className="mt-4 flex items-center justify-between gap-3">
              <button
                type="button"
                className="inline-flex min-h-10 items-center rounded-full border border-[var(--journal-border)] bg-white/95 px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-[var(--journal-accent)] disabled:cursor-not-allowed disabled:opacity-40"
                disabled={activeIndex <= 0}
                onClick={() => scrollToIndex(activeIndex - 1)}
              >
                السابق
              </button>
              <p
                className="text-xs font-medium text-slate-500"
                aria-live="polite"
              >
                {toEasternNumeral(activeIndex + 1)} من {toEasternNumeral(lessons.length)}
              </p>
              <button
                type="button"
                className="inline-flex min-h-10 items-center rounded-full border border-[var(--journal-border)] bg-white/95 px-4 text-sm font-semibold text-slate-700 shadow-sm transition hover:border-[var(--journal-accent)] disabled:cursor-not-allowed disabled:opacity-40"
                disabled={activeIndex >= lessons.length - 1}
                onClick={() => scrollToIndex(activeIndex + 1)}
              >
                التالي
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
