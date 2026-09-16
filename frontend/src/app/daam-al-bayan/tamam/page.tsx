import type { Metadata } from "next";
import { Suspense } from "react";
import { DonationStatusCard } from "@/components/donations/donation-status";

export const metadata: Metadata = {
  title: "نتيجة المساهمة | مجلة البيان",
  robots: { index: false, follow: false },
};

export default function DonationReturnPage() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--journal-paper)]">
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-14 sm:px-6 lg:py-20">
        <Suspense
          fallback={
            <div className="mx-auto max-w-xl rounded-3xl border border-[var(--journal-border)] bg-white/90 p-8 text-center text-slate-600 shadow-sm">
              جارٍ التحقق من المساهمة…
            </div>
          }
        >
          <DonationStatusCard />
        </Suspense>
      </main>
    </div>
  );
}
