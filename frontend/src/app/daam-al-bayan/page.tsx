import type { Metadata } from "next";
import Image from "next/image";
import { DonationCheckout } from "@/components/donations/donation-checkout";

export const metadata: Metadata = {
  title: "دعم البيان | مجلة البيان",
  description: "مساهمة اختيارية لدعم استمرار مجلة البيان وخدماتها العلمية المجانية.",
};

export default function SupportAlbayanPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:px-6 lg:py-14">
        <header className="mx-auto max-w-3xl text-center">
          <Image
            src="/official-logo.png"
            alt="شعار مجلة البيان"
            width={96}
            height={96}
            className="mx-auto h-20 w-20 object-contain drop-shadow-[0_12px_24px_rgba(18,63,51,0.12)]"
          />
          <p className="mt-5 text-sm font-semibold text-[var(--journal-accent)]">دعم المعرفة العربية المفتوحة</p>
          <h1
            className="mt-2 text-4xl font-bold text-slate-900 sm:text-5xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            دعم مجلة البيان
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
            إن رغبت، يمكنك المساهمة اختيارياً في تكاليف استمرار المجلة وتطوير أدواتها وخدماتها العلمية المفتوحة.
          </p>
        </header>

        <figure className="mx-auto mt-8 max-w-2xl rounded-2xl border border-[var(--journal-border)] bg-white/70 px-6 py-5 text-center shadow-sm">
          <blockquote
            className="text-2xl font-bold leading-loose text-[var(--journal-accent-strong)]"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            «رَبِّ زِدْنِي عِلْمًا»
          </blockquote>
          <figcaption className="mt-2 text-sm text-slate-500">سورة طه: ١١٤</figcaption>
        </figure>

        <div className="mx-auto mt-8 grid max-w-4xl gap-6 lg:grid-cols-[0.86fr_1.14fr] lg:items-start">
          <aside className="space-y-5">
            <section className="rounded-2xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
              <h2 className="font-bold text-[var(--journal-accent-strong)]">المساهمة لا تشتري امتيازاً</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                خدمات مجلة البيان العلمية متاحة دون مقابل، والمساهمة اختيارية ولا تؤثر بأي صورة في التقديم أو التحكيم أو القرار التحريري أو النشر.
              </p>
            </section>
            <section className="rounded-2xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
              <h2 className="font-bold text-[var(--journal-accent-strong)]">ماذا تدعم؟</h2>
              <p className="mt-3 text-sm leading-7 text-slate-600">
                تساعد المساهمات في تكاليف التشغيل والتطوير التقني واستمرار إتاحة أدوات المجلة للباحثين دون رسوم.
              </p>
            </section>
            <p className="px-1 text-xs leading-6 text-slate-500">
              هذه المساهمة ليست رسماً للنشر، ولا نعرضها بوصفها تبرعاً معفى من الضرائب أو زكاة أو إيصالاً خيرياً.
            </p>
          </aside>
          <DonationCheckout />
        </div>
      </main>
    </div>
  );
}
