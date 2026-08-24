import type { Metadata } from "next";
import Link from "next/link";
import { tutorialVideos, type TutorialVideo } from "@/lib/tutorials";

export const metadata: Metadata = {
  title: "فيديوهات تعليمية | البيان",
  description:
    "شروح قصيرة تعرّف الباحث بمنصة مجلة البيان: الحساب، مكتبي، وكتابة المخطوطة.",
};

const EPISODE_LABELS = ["الحلقة الأولى", "الحلقة الثانية"] as const;

function TutorialCard({
  video,
  index,
}: {
  video: TutorialVideo;
  index: number;
}) {
  const episodeLabel = EPISODE_LABELS[index] ?? `الحلقة ${index + 1}`;
  return (
    <article className="overflow-hidden rounded-2xl border border-[var(--journal-border)] bg-white/80 shadow-sm">
      {video.src ? (
        <video
          className="aspect-video w-full bg-slate-900"
          controls
          playsInline
          preload="metadata"
        >
          <source src={video.src} />
        </video>
      ) : (
        <div
          className="flex aspect-video flex-col items-center justify-center bg-[linear-gradient(180deg,var(--journal-accent-soft)_0%,#f7f1e6_100%)] px-6 text-center"
          aria-label={`${video.title} — قريبًا`}
        >
          <p
            className="text-lg font-bold text-[var(--journal-accent)] sm:text-xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            قريبًا
          </p>
          <p className="mt-2 max-w-sm text-sm leading-7 text-slate-600">
            يُنشر هذا الشرح عند اكتمال تسجيله، في نحو ثلاثين ثانية.
          </p>
        </div>
      )}
      <div className="space-y-2 px-5 py-5 sm:px-6">
        <p className="text-xs font-semibold text-[var(--journal-accent)]">
          {episodeLabel}
        </p>
        <h2
          className="text-lg font-bold text-slate-900 sm:text-xl"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          {video.title}
        </h2>
        <p className="text-sm leading-8 text-slate-600 sm:text-[0.95rem]">
          {video.description}
        </p>
      </div>
    </article>
  );
}

export default function TutorialsPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:px-6 lg:py-12">
        <p className="text-xs font-semibold text-[var(--journal-accent)]">
          للمؤلفين والمراجعين
        </p>
        <h1
          className="mt-2 text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          فيديوهات تعليمية
        </h1>
        <p className="mt-3 text-sm leading-8 text-slate-600 sm:text-base">
          شروح وجيزة تُعين الباحث على معرفة منصة «البيان»: من إنشاء الحساب إلى
          الشروع في المخطوطة من «مكتبي». نبدأ بحلقتين، ونُلحق بهما بقية الشروح
          تباعًا إن شاء الله.
        </p>

        <div className="mt-8 space-y-6">
          {tutorialVideos.map((video, index) => (
            <TutorialCard key={video.id} video={video} index={index} />
          ))}
        </div>

        <p className="mt-10 rounded-xl border border-[var(--journal-border)] bg-white/70 p-4 text-sm leading-7 text-slate-700">
          للتقديم بعد المشاهدة، راجع{" "}
          <Link
            href="/irshadat-al-mualifin"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            إرشادات المؤلفين
          </Link>
          {" و"}<Link
            href="/siyasat-an-nashr"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            سياسة النشر
          </Link>
          {". إن كان لك حساب، فباب العمل هو "}
          <Link
            href="/maktabi"
            className="font-semibold text-[var(--journal-accent)] hover:underline"
          >
            مكتبي
          </Link>
          {"."}
        </p>
      </main>
    </div>
  );
}
