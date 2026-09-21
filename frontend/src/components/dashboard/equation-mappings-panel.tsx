"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import { CopyButton } from "@/components/ui/copy-button";
import {
  getEquationMappings,
  putEquationMappings,
} from "@/lib/api/equation-mappings";
import {
  equationMappingRows,
  equationMappingsFromRows,
  type EquationMappingRow,
} from "@/lib/equation-mappings";
import { userFacingErrorMessage } from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;

export function EquationMappingsPanel({
  open,
  articleId,
  getToken,
  onClose,
}: {
  open: boolean;
  articleId: string;
  getToken: GetToken;
  onClose: () => void;
}) {
  const [rows, setRows] = useState<EquationMappingRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    setSaved(false);
    setRows(null);
    try {
      const response = await getEquationMappings(getToken, articleId);
      setRows(equationMappingRows(response.mappings));
    } catch (err) {
      setRows([]);
      setError(userFacingErrorMessage(err, "تعذّر تحميل الرموز الرياضية."));
    }
  }, [articleId, getToken]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  function updateRow(index: number, patch: Partial<EquationMappingRow>) {
    setSaved(false);
    setRows((current) =>
      (current ?? []).map((row, rowIndex) =>
        rowIndex === index ? { ...row, ...patch } : row,
      ),
    );
  }

  function addRow() {
    setSaved(false);
    setRows((current) => [...(current ?? []), { english: "", arabic: "" }]);
  }

  function removeRow(index: number) {
    setSaved(false);
    setRows((current) => (current ?? []).filter((_, rowIndex) => rowIndex !== index));
  }

  async function save() {
    if (rows === null) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const mappings = equationMappingsFromRows(rows);
      const response = await putEquationMappings(getToken, articleId, mappings);
      setRows(equationMappingRows(response.mappings));
      setSaved(true);
    } catch (err) {
      setError(
        err instanceof Error && !("status" in err)
          ? err.message
          : userFacingErrorMessage(err, "تعذّر حفظ الرموز الرياضية."),
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <AnimatedOverlay
      open={open}
      onClose={onClose}
      labelledBy="equation-mappings-title"
      panelClassName="sm:max-w-2xl max-h-[88vh] overflow-y-auto"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-[var(--journal-accent-strong)]">
            اصطلاحات المقال
          </p>
          <h2
            id="equation-mappings-title"
            className="mt-1 text-xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            الرموز الرياضية العربية
          </h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-600">
            حدّد كيف تقابل الرموز الأصلية الرموز العربية في هذا المقال. تستخدم أدوات
            البيان هذه الخريطة عند تحويل المعادلات ومساعدة الوكيل على فهم اصطلاحاتك.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="إغلاق"
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-[var(--journal-border)] bg-white text-lg text-slate-500 hover:border-[var(--journal-accent)] hover:text-slate-800"
        >
          ×
        </button>
      </div>

      <div className="mt-5 rounded-xl border border-sky-200 bg-sky-50/70 p-4 text-sm leading-6 text-sky-950">
        <p>
          كلما كانت اصطلاحات الرموز واضحة، كان من الأسهل على أدوات الذكاء الاصطناعي
          التعامل مع الرياضيات العربية في مقالك. يمكنك أيضاً مراجعة
          {" "}
          <Link
            href="/al-idayat/wukala"
            className="font-semibold text-[var(--journal-accent-strong)] underline underline-offset-4"
          >
            إعدادات الوكلاء
          </Link>
          .
        </p>
        <p className="mt-2 text-xs text-sky-800">
          هذه الاختيارات تساعد مشروع البيان على بناء دعم أفضل للرياضيات العربية مستقبلاً.
        </p>
      </div>

      <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
        تغيير تفضيل رمز هنا لا يعيد كتابة المعادلات الموجودة تلقائياً. يطبّق التفضيل على
        أعمال Burhan والوكيل اللاحقة، ويمكنك مراجعة المعادلات القديمة وتعديلها صراحةً عند
        الحاجة.
      </div>

      {error ? (
        <p
          className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : null}
      {saved ? (
        <p
          className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
          role="status"
        >
          تم حفظ اصطلاحات الرموز.
        </p>
      ) : null}

      <div className="mt-5 space-y-3">
        {rows === null ? (
          <div className="space-y-3" aria-label="جارٍ تحميل الرموز">
            <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
            <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
          </div>
        ) : rows.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--journal-border)] bg-white p-6 text-center">
            <p className="font-semibold text-slate-800">لا توجد اصطلاحات محفوظة بعد</p>
            <p className="mt-1 text-sm text-slate-500">
              أضف أول رمز عندما تريد تثبيت اختيار عربي للمقال.
            </p>
            <button
              type="button"
              onClick={addRow}
              className="mt-4 min-h-10 rounded-md bg-[var(--journal-accent-strong)] px-4 text-sm font-semibold text-white"
            >
              إضافة رمز
            </button>
          </div>
        ) : (
          rows.map((row, index) => (
            <div
              key={`${index}-${row.english}`}
              className="rounded-xl border border-[var(--journal-border)] bg-white p-3 shadow-sm"
            >
              <div className="grid gap-3 sm:grid-cols-[1fr_auto_1fr_auto] sm:items-end">
                <label className="block min-w-0">
                  <span className="mb-1 block text-xs font-semibold text-slate-500">
                    الرمز الأصلي
                  </span>
                  <div className="flex gap-2">
                    <input
                      dir="ltr"
                      value={row.english}
                      onChange={(event) => updateRow(index, { english: event.target.value })}
                      maxLength={128}
                      placeholder="x"
                      aria-label={`الرمز الأصلي ${index + 1}`}
                      className="min-h-10 min-w-0 flex-1 rounded-md border border-[var(--journal-border)] bg-slate-50 px-3 font-mono text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white"
                    />
                    <CopyButton value={row.english.trim()} ariaLabel="نسخ الرمز الأصلي" />
                  </div>
                </label>

                <span className="hidden pb-2 text-slate-400 sm:block">←</span>

                <label className="block min-w-0">
                  <span className="mb-1 block text-xs font-semibold text-slate-500">
                    الرمز العربي
                  </span>
                  <div className="flex gap-2">
                    <input
                      dir="rtl"
                      value={row.arabic}
                      onChange={(event) => updateRow(index, { arabic: event.target.value })}
                      maxLength={128}
                      placeholder="س"
                      aria-label={`الرمز العربي ${index + 1}`}
                      className="min-h-10 min-w-0 flex-1 rounded-md border border-[var(--journal-border)] bg-slate-50 px-3 text-lg text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white"
                    />
                    <CopyButton value={row.arabic.trim()} ariaLabel="نسخ الرمز العربي" />
                  </div>
                </label>

                <button
                  type="button"
                  onClick={() => removeRow(index)}
                  className="min-h-10 rounded-md border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 hover:bg-red-100"
                >
                  حذف
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {rows !== null && rows.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={addRow}
            className="min-h-10 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-semibold text-slate-700 hover:border-[var(--journal-accent)]"
          >
            + إضافة رمز
          </button>
          <button
            type="button"
            onClick={() => {
              setRows([]);
              setSaved(false);
            }}
            className="min-h-10 rounded-md border border-red-200 bg-white px-4 text-sm font-semibold text-red-700 hover:bg-red-50"
          >
            مسح الكل
          </button>
        </div>
      ) : null}

      <div className="mt-6 flex flex-col-reverse gap-2 border-t border-[var(--journal-border)] pt-4 sm:flex-row sm:justify-end">
        <button
          type="button"
          onClick={onClose}
          className="min-h-11 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600"
        >
          إغلاق
        </button>
        <button
          type="button"
          onClick={() => void save()}
          disabled={saving || rows === null}
          className="min-h-11 rounded-md bg-[var(--journal-accent-strong)] px-5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {saving ? "جارٍ الحفظ…" : "حفظ الاصطلاحات"}
        </button>
      </div>
    </AnimatedOverlay>
  );
}
