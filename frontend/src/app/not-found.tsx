import Link from "next/link";

export default function NotFound() {
  return (
    <main className="relative isolate flex flex-1 items-center justify-center overflow-hidden px-6 py-20 sm:py-28">
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,color-mix(in_srgb,var(--journal-accent-soft)_78%,transparent),transparent_52%)]"
      />

      <section className="w-full max-w-2xl text-center">
        <p
          className="text-7xl font-bold leading-none text-[var(--journal-border)] sm:text-8xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          404
        </p>

        <div className="mx-auto mt-5 h-px w-20 bg-[var(--journal-gold)]" />

        <p className="mt-7 text-xs font-semibold tracking-[0.18em] text-[var(--journal-accent)]">
          مجلة البيان
        </p>
        <h1
          className="mt-3 text-3xl font-bold text-[var(--journal-ink)] sm:text-4xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          الصفحة غير موجودة
        </h1>
        <p className="mx-auto mt-5 max-w-lg text-base leading-8 text-[var(--journal-muted)]">
          عذرًا، لم نتمكن من العثور على الصفحة التي تبحث عنها. ربما نُقلت،
          أو تغيّر عنوانها، أو لم تعد متاحة.
        </p>

        <Link
          href="/"
          className="mt-9 inline-flex min-h-11 items-center justify-center rounded-md bg-[var(--journal-accent)] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[var(--journal-accent-strong)] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--journal-accent)]"
        >
          العودة إلى الصفحة الرئيسية
        </Link>
      </section>
    </main>
  );
}
