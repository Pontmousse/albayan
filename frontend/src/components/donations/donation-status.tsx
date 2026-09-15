"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import {
  formatDonationAmount,
  getDonationConfig,
  getDonationStatus,
  type DonationConfig,
  type DonationStatus,
} from "@/lib/donations";

export function DonationStatusCard() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [status, setStatus] = useState<DonationStatus | null>(null);
  const [config, setConfig] = useState<DonationConfig | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      setFailed(true);
      return;
    }

    let active = true;
    let timeout: ReturnType<typeof setTimeout> | null = null;
    let attempts = 0;

    void getDonationConfig().then((value) => {
      if (active) setConfig(value);
    }).catch(() => undefined);

    const load = async () => {
      try {
        const value = await getDonationStatus(sessionId);
        if (!active) return;
        setStatus(value);
        attempts += 1;
        if (value.status === "pending" && attempts < 12) {
          timeout = setTimeout(load, 1500);
        }
      } catch {
        if (active) setFailed(true);
      }
    };
    void load();

    return () => {
      active = false;
      if (timeout) clearTimeout(timeout);
    };
  }, [sessionId]);

  const amount =
    status && config
      ? formatDonationAmount(
          status.amount_minor,
          status.currency,
          config.minor_unit_divisor,
        )
      : null;

  if (failed) {
    return (
      <StatusShell title="تعذّر التحقق من المساهمة">
        <p>لم نتمكن من التحقق من هذه العملية. يمكنك العودة إلى صفحة الدعم والمحاولة مجدداً.</p>
        <ReturnLink />
      </StatusShell>
    );
  }

  if (!status || status.status === "pending") {
    return (
      <StatusShell title="جارٍ تثبيت نتيجة الدفع">
        <p>وصلتَ إلى صفحة العودة، وننتظر التأكيد الموثوق من خدمة الدفع. قد يستغرق ذلك لحظات قليلة.</p>
        <div className="mx-auto mt-5 h-2 w-36 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-[var(--journal-accent)]" />
        </div>
      </StatusShell>
    );
  }

  if (status.status === "paid") {
    return (
      <StatusShell title="جزاكم الله خيرًا">
        <p>تم استلام مساهمتكم بنجاح{amount ? ` بمقدار ${amount}` : ""}. نسأل الله أن يبارك في العلم النافع وأهله.</p>
        <p className="mt-4 text-sm text-slate-500">
          إن أضفت بريداً إلكترونياً، سيصلك تأكيد من مجلة البيان بعد معالجة الإشعار الموثوق.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl bg-[var(--journal-accent)] px-5 py-3 font-semibold text-white hover:bg-[var(--journal-accent-strong)]"
        >
          العودة إلى مجلة البيان
        </Link>
      </StatusShell>
    );
  }

  return (
    <StatusShell title={status.status === "expired" ? "انتهت جلسة الدفع" : "لم يكتمل الدفع"}>
      <p>لم تُسجّل مساهمة مكتملة لهذه العملية. لمتابعة الدعم، ابدأ عملية جديدة.</p>
      <ReturnLink />
    </StatusShell>
  );
}

function StatusShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="mx-auto max-w-xl rounded-3xl border border-[var(--journal-border)] bg-white/90 p-7 text-center shadow-sm sm:p-10">
      <h1
        className="text-3xl font-bold text-[var(--journal-accent-strong)]"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {title}
      </h1>
      <div className="mt-5 text-base leading-8 text-slate-600">{children}</div>
    </section>
  );
}

function ReturnLink() {
  return (
    <Link
      href="/daam-al-bayan"
      className="mt-6 inline-flex rounded-xl border border-[var(--journal-border)] bg-[var(--journal-paper)] px-5 py-3 font-semibold text-[var(--journal-accent-strong)] hover:border-[var(--journal-accent)]"
    >
      العودة إلى دعم البيان
    </Link>
  );
}
