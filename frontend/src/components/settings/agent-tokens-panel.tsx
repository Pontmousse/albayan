"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import {
  AGENT_SCOPE_LABELS,
  ALLOWED_AGENT_SCOPES,
  DEFAULT_AGENT_SCOPES,
  MAX_AGENT_TOKENS,
  type AgentScope,
} from "@/lib/agent-token-config";
import {
  createAgentToken,
  deleteAgentToken,
  listAgentTokens,
  updateAgentToken,
  type AgentTokenSummary,
} from "@/lib/api/agent-tokens";
import { buttonClassName, cardClassName, inputClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

type ModalMode = "closed" | "create" | "edit" | "reveal";

export function AgentTokensPanel() {
  const { getToken } = useAuth();
  const [tokens, setTokens] = useState<AgentTokenSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalMode>("closed");
  const [label, setLabel] = useState("");
  const [scopes, setScopes] = useState<AgentScope[]>([...DEFAULT_AGENT_SCOPES]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [revealedToken, setRevealedToken] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AgentTokenSummary | null>(
    null,
  );
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const rows = await listAgentTokens(getToken);
      setTokens(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل المفاتيح.");
      setTokens([]);
    }
  }, [getToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const atLimit = (tokens?.length ?? 0) >= MAX_AGENT_TOKENS;

  function openCreate() {
    setLabel("");
    setScopes([...DEFAULT_AGENT_SCOPES]);
    setEditingId(null);
    setRevealedToken(null);
    setModal("create");
  }

  function openEdit(token: AgentTokenSummary) {
    setLabel(token.label);
    setEditingId(token.id);
    setModal("edit");
  }

  function closeModal() {
    setModal("closed");
    setRevealedToken(null);
    setCopied(false);
  }

  function toggleScope(scope: AgentScope) {
    setScopes((prev) =>
      prev.includes(scope)
        ? prev.filter((s) => s !== scope)
        : [...prev, scope],
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!label.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (modal === "edit" && editingId) {
        await updateAgentToken(getToken, editingId, { label: label.trim() });
        closeModal();
        await load();
      } else if (modal === "create") {
        if (scopes.length === 0) {
          setError("اختر صلاحية واحدة على الأقل.");
          setSaving(false);
          return;
        }
        const created = await createAgentToken(getToken, {
          label: label.trim(),
          scopes,
        });
        setRevealedToken(created.token);
        setModal("reveal");
        await load();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر حفظ المفتاح.");
    } finally {
      setSaving(false);
    }
  }

  async function handleCopy() {
    if (!revealedToken) return;
    try {
      await navigator.clipboard.writeText(revealedToken);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  async function confirmDelete() {
    if (!deleteTarget) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteAgentToken(getToken, deleteTarget.id);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر حذف المفتاح.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/al-idayat"
          className="text-sm font-medium text-[var(--journal-accent)] hover:underline"
        >
          → العودة إلى الإعدادات
        </Link>
        <button
          type="button"
          onClick={openCreate}
          disabled={atLimit}
          className={buttonClassName}
        >
          مفتاح جديد
        </button>
      </div>

      {atLimit ? (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          بلغت الحد الأقصى ({MAX_AGENT_TOKENS} مفاتيح). احذف مفتاحاً قديماً لإنشاء
          آخر.
        </p>
      ) : null}

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {tokens === null ? (
        <RowsSkeleton count={2} />
      ) : tokens.length === 0 ? (
        <>
          <EmptyState
            title="لا مفاتيح بعد"
            description="أنشئ مفتاحاً لربط Cursor أو Claude Desktop بمنصة البيان."
          />
          <div className="mt-4 text-center">
            <button type="button" onClick={openCreate} className={buttonClassName}>
              مفتاح جديد
            </button>
          </div>
        </>
      ) : (
        <ul className="space-y-3">
          {tokens.map((token) => (
            <li key={token.id} className={cardClassName}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    {token.label}
                  </h2>
                  <p className="mt-1 text-xs text-slate-500">
                    أُنشئ {formatDate(token.created_at)}
                    {token.last_used_at
                      ? ` · آخر استخدام ${formatDate(token.last_used_at)}`
                      : " · لم يُستخدم بعد"}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {token.scopes.map((scope) => (
                      <span
                        key={scope}
                        className="rounded-full bg-[var(--journal-accent-soft)] px-2 py-0.5 text-[10px] font-semibold text-[var(--journal-accent-strong)]"
                      >
                        {AGENT_SCOPE_LABELS[scope as AgentScope] ?? scope}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => openEdit(token)}
                    className="min-h-9 rounded-md border border-[var(--journal-border)] bg-white px-3 text-xs font-semibold text-slate-700 hover:border-[var(--journal-accent)]"
                  >
                    تعديل الاسم
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteTarget(token)}
                    className="min-h-9 rounded-md border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 hover:bg-red-100"
                  >
                    حذف
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {(modal === "create" || modal === "edit") && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
          role="dialog"
          aria-modal="true"
        >
          <button
            type="button"
            aria-label="إغلاق"
            onClick={closeModal}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
          />
          <form
            onSubmit={handleSubmit}
            className="relative w-full max-w-md rounded-t-2xl border border-[var(--journal-border)] bg-[var(--journal-paper)] p-5 shadow-xl sm:rounded-2xl sm:p-6"
          >
            <h2
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              {modal === "edit" ? "تعديل اسم المفتاح" : "مفتاح وكيل جديد"}
            </h2>
            <div className="mt-4 space-y-4">
              <div>
                <label
                  htmlFor="token-label"
                  className="mb-1 block text-sm font-medium text-slate-700"
                >
                  اسم المفتاح
                </label>
                <input
                  id="token-label"
                  type="text"
                  required
                  maxLength={100}
                  value={label}
                  onChange={(e) => setLabel(e.target.value)}
                  placeholder="مثال: Cursor على جهازي"
                  className={inputClassName}
                />
              </div>
              {modal === "create" ? (
                <fieldset>
                  <legend className="text-sm font-medium text-slate-700">
                    الصلاحيات
                  </legend>
                  <ul className="mt-2 space-y-2">
                    {ALLOWED_AGENT_SCOPES.map((scope) => (
                      <li key={scope}>
                        <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
                          <input
                            type="checkbox"
                            checked={scopes.includes(scope)}
                            onChange={() => toggleScope(scope)}
                            className="rounded border-[var(--journal-border)] text-[var(--journal-accent)]"
                          />
                          {AGENT_SCOPE_LABELS[scope]}
                        </label>
                      </li>
                    ))}
                  </ul>
                </fieldset>
              ) : null}
            </div>
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeModal}
                className="min-h-11 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600"
              >
                إلغاء
              </button>
              <button type="submit" disabled={saving} className={buttonClassName}>
                {saving ? "جارٍ الحفظ…" : modal === "edit" ? "حفظ" : "إنشاء"}
              </button>
            </div>
          </form>
        </div>
      )}

      {modal === "reveal" && revealedToken ? (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
          role="dialog"
          aria-modal="true"
        >
          <button
            type="button"
            aria-label="إغلاق"
            onClick={closeModal}
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
          />
          <div className="relative w-full max-w-md rounded-t-2xl border border-emerald-300 bg-white p-5 shadow-xl sm:rounded-2xl sm:p-6">
            <h2
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              انسخ مفتاحك الآن
            </h2>
            <p className="mt-2 text-sm text-amber-800">
              لن نعرض هذا المفتاح مرة أخرى. احفظه في مكان آمن.
            </p>
            <pre
              dir="ltr"
              className="mt-4 overflow-x-auto rounded-lg border border-[var(--journal-border)] bg-slate-950 p-3 text-start text-xs text-emerald-100"
            >
              {revealedToken}
            </pre>
            <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={handleCopy}
                className={buttonClassName}
              >
                {copied ? "تم النسخ" : "نسخ المفتاح"}
              </button>
              <button
                type="button"
                onClick={closeModal}
                className="min-h-11 rounded-md border border-[var(--journal-border)] bg-white px-4 text-sm font-medium text-slate-600"
              >
                تمّ
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        open={deleteTarget !== null}
        title="حذف مفتاح الوكيل؟"
        description={
          deleteTarget
            ? `سيتوقف الوكيل عن العمل بهذا المفتاح («${deleteTarget.label}»). لا يمكن التراجع.`
            : ""
        }
        confirmLabel="حذف"
        submitting={deleting}
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
