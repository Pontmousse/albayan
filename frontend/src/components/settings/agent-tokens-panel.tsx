"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import { AnimatedOverlay } from "@/components/ui/animated-overlay";
import {
  ALLOWED_AGENT_SCOPES,
  MAX_AGENT_TOKENS,
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
  const [surface, setSurface] = useState<"create" | "edit" | "reveal">("create");
  const [label, setLabel] = useState("");
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
    setEditingId(null);
    setRevealedToken(null);
    setSurface("create");
    setModal("create");
  }

  function openEdit(token: AgentTokenSummary) {
    setLabel(token.label);
    setEditingId(token.id);
    setSurface("edit");
    setModal("edit");
  }

  function closeModal() {
    setModal("closed");
    setRevealedToken(null);
    setCopied(false);
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
        const created = await createAgentToken(getToken, {
          label: label.trim(),
          scopes: [...ALLOWED_AGENT_SCOPES],
        });
        setRevealedToken(created.token);
        setSurface("reveal");
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
          العودة إلى الإعدادات
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

      <AnimatedOverlay
        open={modal !== "closed"}
        onClose={closeModal}
        labelledBy="token-modal-title"
        panelClassName={
          surface === "reveal" ? "border-emerald-300 bg-white" : ""
        }
      >
        {surface === "reveal" && revealedToken ? (
          <>
            <h2
              id="token-modal-title"
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
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <h2
              id="token-modal-title"
              className="text-xl font-bold text-slate-900"
              style={{ fontFamily: "var(--font-display-ar), serif" }}
            >
              {surface === "edit" ? "تعديل اسم المفتاح" : "مفتاح وكيل جديد"}
            </h2>
            <div className="mt-4">
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
              {surface === "create" ? (
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  المفتاح يتيح للوكيل المساعدة في القراءة والصياغة؛ التقديم
                  والقرارات تبقى من المنصة.
                </p>
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
                {saving ? "جارٍ الحفظ…" : surface === "edit" ? "حفظ" : "إنشاء"}
              </button>
            </div>
          </form>
        )}
      </AnimatedOverlay>

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
