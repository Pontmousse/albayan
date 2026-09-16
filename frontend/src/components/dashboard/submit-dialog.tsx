"use client";

import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import { buttonClassName } from "@/lib/auth-ui";

export function SubmitDialog({
  open,
  submitting,
  onConfirm,
  onCancel,
  resubmission = false,
}: {
  open: boolean;
  submitting: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  resubmission?: boolean;
}) {
  return (
    <AnimatedOverlay
      open={open}
      onClose={onCancel}
      labelledBy="submit-dialog-title"
    >
      <h2
        id="submit-dialog-title"
        className="text-xl font-bold text-slate-900"
        style={{ fontFamily: "var(--font-display-ar), serif" }}
      >
        {resubmission ? "إعادة تقديم المقال" : "تقديم المقال للمجلة"}
      </h2>
      <p className="mt-3 text-sm leading-7 text-slate-600">
        {resubmission
          ? "ستُنشأ نسخة رسمية جديدة مستقلة، وستبقى جميع النسخ السابقة وتقاريرها محفوظة. "
          : "بعد التقديم تنتقل المخطوطة إلى هيئة التحرير "}
        <strong className="text-slate-800">
          ولن تتمكن من تعديل المحتوى بعد التقديم
        </strong>
        . هل أنت متأكد؟
      </p>
      <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:flex-wrap sm:justify-end sm:gap-3">
        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)] disabled:opacity-60"
        >
          إلغاء
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={submitting}
          className={buttonClassName}
        >
          {submitting
            ? "جارٍ التقديم…"
            : resubmission
              ? "تأكيد إعادة التقديم"
              : "تأكيد التقديم"}
        </button>
      </div>
    </AnimatedOverlay>
  );
}
