"use client";

import {
  ArrowLeftRight,
  ArrowUpLeft,
  Plus,
  Sigma,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import { useNumerals } from "@/components/numeral-provider";
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
import {
  UserFacingError,
  userFacingErrorMessage,
} from "@/lib/user-facing-errors";

type GetToken = () => Promise<string | null>;
type EditableEquationMappingRow = EquationMappingRow & { id: string };

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
  const { formatDigits } = useNumerals();
  const [rows, setRows] = useState<EditableEquationMappingRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const nextRowId = useRef(0);
  const listRef = useRef<HTMLDivElement>(null);

  const createEditableRow = useCallback(
    (row: EquationMappingRow = { english: "", arabic: "" }) => ({
      ...row,
      id: `equation-mapping-${nextRowId.current++}`,
    }),
    [],
  );

  const load = useCallback(async () => {
    setError(null);
    setSaved(false);
    setRows(null);
    try {
      const response = await getEquationMappings(getToken, articleId);
      setRows(equationMappingRows(response.mappings).map(createEditableRow));
    } catch (err) {
      setRows([]);
      setError(userFacingErrorMessage(err, "تعذّر تحميل رموز المقال."));
    }
  }, [articleId, createEditableRow, getToken]);

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
    const row = createEditableRow();
    setRows((current) => [...(current ?? []), row]);
    requestAnimationFrame(() => {
      document.getElementById(`${row.id}-original`)?.focus();
      listRef.current?.scrollTo({
        top: listRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }

  function removeRow(index: number) {
    setSaved(false);
    setRows((current) =>
      (current ?? []).filter((_, rowIndex) => rowIndex !== index),
    );
  }

  async function save() {
    if (rows === null) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const mappings = equationMappingsFromRows(rows);
      const response = await putEquationMappings(getToken, articleId, mappings);
      setRows(equationMappingRows(response.mappings).map(createEditableRow));
      setSaved(true);
    } catch (err) {
      setError(
        err instanceof UserFacingError
          ? userFacingErrorMessage(err, "تعذّر حفظ رموز المقال.")
          : userFacingErrorMessage(
              err,
              "تعذّر حفظ رموز المقال. حاول مجدداً.",
            ),
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
      panelClassName="!p-0 flex h-[min(94dvh,56rem)] max-h-[94dvh] flex-col overflow-hidden sm:h-[min(86dvh,52rem)] sm:max-w-5xl"
    >
      <header className="flex shrink-0 items-start justify-between gap-4 border-b border-[var(--journal-border)] bg-white/80 px-5 py-4 sm:px-6 sm:py-5">
        <div className="min-w-0">
          <p className="text-xs font-semibold text-[var(--journal-accent-strong)]">
            اصطلاحات المقال
          </p>
          <h2
            id="equation-mappings-title"
            className="mt-1 text-xl font-bold text-slate-900"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            رموز المعادلات
          </h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            احفظ المقابل العربي للرموز المستخدمة في هذا المقال.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="إغلاق"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[var(--journal-border)] bg-white text-slate-500 transition hover:border-[var(--journal-accent)] hover:bg-[var(--journal-accent-soft)] hover:text-[var(--journal-accent-strong)]"
        >
          <X aria-hidden className="h-4 w-4" />
        </button>
      </header>

      <div className="grid min-h-0 flex-1 grid-rows-[auto_minmax(0,1fr)] lg:grid-cols-[18rem_minmax(0,1fr)] lg:grid-rows-1">
        <aside className="shrink-0 border-b border-[var(--journal-border)] bg-gradient-to-b from-[var(--journal-accent-soft)]/75 to-white px-5 py-4 lg:border-b-0 lg:border-l lg:px-6 lg:py-6">
          <div className="flex items-start gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[var(--journal-accent-strong)] text-white shadow-sm">
              <Sigma aria-hidden className="h-5 w-5" />
            </span>
            <div>
              <h3 className="font-bold text-slate-900">اصطلاحات واضحة</h3>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                عيّن لكل رمز أصلي مقابله العربي؛ لتساعد نماذج الذكاء
                الاصطناعي على فهم معادلاتك العربية بدقة أكبر.
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-xl border border-emerald-200/80 bg-emerald-50/80 p-3.5 text-sm leading-6 text-emerald-950">
            <div className="flex items-start gap-2.5">
              <Sparkles
                aria-hidden
                className="mt-1 h-4 w-4 shrink-0 text-emerald-700"
              />
              <p>
                مساهمتك اليوم تساعد، بإذن الله، على بناء نماذج مستقبلية أفضل فهماً
                للمعادلات العربية، خدمةً لمجتمع الباحثين والعلماء الناطقين بالعربية.
              </p>
            </div>
          </div>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            تسري التغييرات على التحويلات القادمة فقط؛ وتبقى المعادلات الحالية كما هي.
          </p>

          <Link
            href="/wukala"
            className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white px-3.5 py-3 text-sm font-semibold text-[var(--journal-accent-strong)] shadow-sm transition hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md"
          >
            <span>تعرّف إلى وكلاء البيان</span>
            <ArrowUpLeft aria-hidden className="h-4 w-4 shrink-0" />
          </Link>

          <div className="mt-5 hidden border-t border-[var(--journal-border)] pt-4 lg:block">
            <p className="text-xs font-semibold text-slate-500">عدد الرموز</p>
            <p className="mt-1 text-2xl font-bold text-[var(--journal-accent-strong)]">
              {rows === null ? "—" : formatDigits(String(rows.length))}
            </p>
          </div>
        </aside>

        <section className="flex min-h-0 min-w-0 flex-col bg-white/45">
          <div className="flex shrink-0 items-center justify-between gap-3 border-b border-[var(--journal-border)] px-4 py-3 sm:px-5">
            <div>
              <h3 className="text-sm font-bold text-slate-800">قائمة الرموز</h3>
              <p className="mt-0.5 text-xs text-slate-500">
                {rows === null
                  ? "جارٍ التحميل…"
                  : rows.length === 0
                    ? "لا توجد رموز مضافة"
                    : `${formatDigits(String(rows.length))} ${rows.length === 1 ? "رمز" : "رموز"}`}
              </p>
            </div>
            <button
              type="button"
              onClick={addRow}
              disabled={rows === null}
              className="inline-flex min-h-10 shrink-0 items-center gap-2 rounded-lg bg-[var(--journal-accent-strong)] px-3.5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
            >
              <Plus aria-hidden className="h-4 w-4" />
              <span className="hidden sm:inline">إضافة رمز</span>
              <span className="sm:hidden">إضافة</span>
            </button>
          </div>

          {error ? (
            <p
              className="mx-4 mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 sm:mx-5"
              role="alert"
            >
              {error}
            </p>
          ) : null}
          {saved ? (
            <p
              className="mx-4 mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800 sm:mx-5"
              role="status"
            >
              حُفظت رموز المقال.
            </p>
          ) : null}

          <div
            ref={listRef}
            className="equation-mappings-scrollbar min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain px-4 py-4 sm:px-5"
          >
            {rows === null ? (
              <div className="space-y-3" aria-label="جارٍ تحميل الرموز">
                <div className="h-24 animate-pulse rounded-xl bg-slate-100" />
                <div className="h-24 animate-pulse rounded-xl bg-slate-100" />
                <div className="h-24 animate-pulse rounded-xl bg-slate-100" />
              </div>
            ) : rows.length === 0 ? (
              <div className="flex min-h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--journal-border)] bg-white/80 p-6 text-center">
                <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]">
                  <Sigma aria-hidden className="h-7 w-7" />
                </span>
                <p className="mt-4 font-semibold text-slate-800">
                  ابدأ بإضافة أول رمز
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  مثال: الرمز x يقابله س.
                </p>
                <button
                  type="button"
                  onClick={addRow}
                  className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--journal-accent-strong)] px-4 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                >
                  <Plus aria-hidden className="h-4 w-4" />
                  إضافة رمز
                </button>
              </div>
            ) : (
              rows.map((row, index) => (
                <div
                  key={row.id}
                  className="mapping-row-enter group rounded-xl border border-[var(--journal-border)] bg-white p-3 shadow-sm transition hover:border-[var(--journal-accent)] hover:shadow-md sm:p-4"
                >
                  <div className="grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)_auto_minmax(0,1fr)_auto] sm:items-end">
                    <span
                      aria-hidden
                      className="hidden h-7 w-7 self-center place-items-center rounded-full bg-slate-100 text-xs font-bold text-slate-500 sm:grid"
                    >
                      {formatDigits(String(index + 1))}
                    </span>
                    <label className="block min-w-0">
                      <span className="mb-1 block text-xs font-semibold text-slate-500">
                        الرمز الأصلي
                      </span>
                      <div className="flex gap-2">
                        <input
                          id={`${row.id}-original`}
                          dir="ltr"
                          value={row.english}
                          onChange={(event) =>
                            updateRow(index, { english: event.target.value })
                          }
                          maxLength={128}
                          placeholder="x"
                          aria-label={`الرمز الأصلي ${index + 1}`}
                          className="min-h-10 min-w-0 flex-1 rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 font-mono text-sm text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
                        />
                        <CopyButton
                          value={row.english.trim()}
                          ariaLabel="نسخ الرمز الأصلي"
                          className="h-10 w-10 rounded-lg"
                        />
                      </div>
                    </label>

                    <ArrowLeftRight
                      aria-hidden
                      className="mb-2 hidden h-4 w-4 text-slate-400 sm:block"
                    />

                    <label className="block min-w-0">
                      <span className="mb-1 block text-xs font-semibold text-slate-500">
                        المقابل العربي
                      </span>
                      <div className="flex gap-2">
                        <input
                          dir="rtl"
                          value={row.arabic}
                          onChange={(event) =>
                            updateRow(index, { arabic: event.target.value })
                          }
                          maxLength={128}
                          placeholder="س"
                          aria-label={`المقابل العربي ${index + 1}`}
                          className="min-h-10 min-w-0 flex-1 rounded-lg border border-[var(--journal-border)] bg-slate-50 px-3 text-lg text-slate-900 outline-none transition focus:border-[var(--journal-accent)] focus:bg-white focus:ring-2 focus:ring-[var(--journal-accent-soft)]"
                        />
                        <CopyButton
                          value={row.arabic.trim()}
                          ariaLabel="نسخ الرمز العربي"
                          className="h-10 w-10 rounded-lg"
                        />
                      </div>
                    </label>

                    <button
                      type="button"
                      onClick={() => removeRow(index)}
                      aria-label={`حذف الرمز ${formatDigits(String(index + 1))}`}
                      title="حذف الرمز"
                      className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 transition hover:border-red-300 hover:bg-red-100 sm:w-10 sm:px-0"
                    >
                      <Trash2 aria-hidden className="h-4 w-4" />
                      <span className="sm:hidden">حذف</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>

      <footer className="flex shrink-0 flex-col-reverse gap-2 border-t border-[var(--journal-border)] bg-white/90 px-5 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        {rows !== null && rows.length > 0 ? (
          <button
            type="button"
            onClick={() => {
              setRows([]);
              setSaved(false);
            }}
            className="min-h-10 rounded-lg px-3 text-sm font-semibold text-red-700 transition hover:bg-red-50"
          >
            مسح جميع الرموز
          </button>
        ) : (
          <span />
        )}
        <div className="flex flex-col-reverse gap-2 sm:flex-row">
          <button
            type="button"
            onClick={onClose}
            className="min-h-10 rounded-lg border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-900"
          >
            إغلاق
          </button>
          <button
            type="button"
            onClick={() => void save()}
            disabled={saving || rows === null}
            className="min-h-10 rounded-lg bg-[var(--journal-accent-strong)] px-5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          >
            {saving ? "جارٍ الحفظ…" : "حفظ الرموز"}
          </button>
        </div>
      </footer>
    </AnimatedOverlay>
  );
}
