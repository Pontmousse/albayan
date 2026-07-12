"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ConfirmDialog } from "@/components/dashboard/confirm-dialog";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { WorkflowProgress } from "@/components/dashboard/workflow-progress";
import {
  assignEditor,
  assignReviewer,
  cancelInvitation,
  getAdminArticle,
  inviteToArticle,
  INVITATION_ROLE_LABELS,
  INVITATION_STATUS_LABELS,
  listAdminUsers,
  listArticleInvitations,
  overrideDecision,
  REVIEWER_STATUS_LABELS,
  resendInvitation,
  unassignEditor,
  unassignReviewer,
  type AdminArticleDetail,
  type AdminUserListItem,
  type InvitationRead,
  type InvitationRole,
} from "@/lib/api/admin";
import type { VersionStatus } from "@/lib/api/articles";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

const OVERRIDE_STATUSES: { status: VersionStatus; label: string; confirm: boolean }[] =
  [
    { status: "submitted", label: "مُقدَّم", confirm: false },
    { status: "under_review", label: "قيد المراجعة", confirm: false },
    { status: "accepted", label: "قبول", confirm: true },
    { status: "rejected", label: "رفض", confirm: true },
    { status: "published", label: "منشور", confirm: true },
  ];

export default function AdminArticleDetailPage() {
  const { getToken } = useAuth();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const articleId = params.id;

  const [article, setArticle] = useState<AdminArticleDetail | null>(null);
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [invitations, setInvitations] = useState<InvitationRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionOk, setActionOk] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [assignRole, setAssignRole] = useState<InvitationRole>("reviewer");
  const [assignMode, setAssignMode] = useState<"user" | "email">("user");
  const [selectedUserId, setSelectedUserId] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");

  const [overrideReason, setOverrideReason] = useState("");
  const [pendingOverride, setPendingOverride] = useState<VersionStatus | null>(
    null,
  );

  const load = useCallback(async () => {
    const [detail, inviteRows, userRows] = await Promise.all([
      getAdminArticle(getToken, articleId),
      listArticleInvitations(getToken, articleId),
      listAdminUsers(getToken),
    ]);
    setArticle(detail);
    setInvitations(inviteRows);
    setUsers(userRows);
  }, [getToken, articleId]);

  useEffect(() => {
    let cancelled = false;
    load()
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل المقال.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  const userOptions = useMemo(() => {
    return [...users].sort((a, b) =>
      (a.full_name || a.email).localeCompare(b.full_name || b.email, "ar"),
    );
  }, [users]);

  async function runAction(
    label: string,
    fn: () => Promise<unknown>,
    successMessage?: (result: unknown) => string,
  ) {
    setBusy(true);
    setActionError(null);
    setActionOk(null);
    try {
      const result = await fn();
      setActionOk(successMessage ? successMessage(result) : label);
      await load();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "تعذّر تنفيذ العملية.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAssignOrInvite() {
    if (assignMode === "user") {
      if (!selectedUserId) {
        setActionError("اختر مستخدماً للتعيين.");
        return;
      }
      await runAction(
        assignRole === "reviewer" ? "تم تعيين المراجع." : "تم تعيين المحرر.",
        () =>
          assignRole === "reviewer"
            ? assignReviewer(getToken, articleId, selectedUserId)
            : assignEditor(getToken, articleId, selectedUserId),
      );
      return;
    }

    const email = inviteEmail.trim();
    if (!email) {
      setActionError("أدخل بريداً إلكترونياً للدعوة.");
      return;
    }
    await runAction(
      "أُنشئت الدعوة.",
      async () => {
        const res = await inviteToArticle(getToken, articleId, email, assignRole);
        setInviteEmail("");
        return res;
      },
      (result) => {
        const res = result as { warning?: string | null };
        if (res?.warning) {
          return `أُنشئت الدعوة — تنبيه: ${res.warning}`;
        }
        return "أُنشئت الدعوة.";
      },
    );
  }

  async function applyOverride(status: VersionStatus) {
    await runAction("تم تحديث حالة الإصدار.", () =>
      overrideDecision(getToken, articleId, status, overrideReason.trim() || null),
    );
    setPendingOverride(null);
  }

  if (error) {
    return (
      <div className="space-y-4">
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
        <button
          type="button"
          onClick={() => router.push("/admin/maqalat")}
          className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          العودة إلى المقالات
        </button>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="space-y-6">
        <CardsSkeleton count={1} />
        <RowsSkeleton />
      </div>
    );
  }

  const current = article.current_version;
  const pendingInvites = invitations.filter((i) => i.status === "pending");

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/admin/maqalat"
          className="text-xs font-medium text-slate-500 underline-offset-4 hover:text-[var(--journal-accent)] hover:underline"
        >
          → المقالات
        </Link>
        <div className="mt-2">
          <h1
            className="text-2xl font-bold leading-relaxed text-slate-900 sm:text-3xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {article.title}
          </h1>
          <p className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-slate-500">
            <StatusBadge status={current.status} />
            <span>الإصدار v{current.version_number}</span>
            <span aria-hidden>·</span>
            <span>أُنشئ في {formatDate(article.created_at)}</span>
          </p>
        </div>
      </div>

      {actionError ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {actionError}
        </p>
      ) : null}
      {actionOk ? (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
          {actionOk}
        </p>
      ) : null}

      {article.abstract ? (
        <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-[var(--journal-accent)]">الملخص</h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">{article.abstract}</p>
        </section>
      ) : null}

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">مسار المخطوطة</h2>
        <div className="mt-3">
          <WorkflowProgress status={current.status} />
        </div>
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">المؤلفون</h2>
        {article.authors.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">لا مؤلفين مرتبطين.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {article.authors.map((author) => (
              <li
                key={author.user.id}
                className="rounded-lg border border-[var(--journal-border)] bg-white px-3.5 py-2.5 text-sm"
              >
                <span className="font-semibold text-slate-800">
                  {author.user.full_name || author.user.email}
                </span>
                <span className="ms-2 text-xs text-slate-500">
                  {author.user.email}
                  {author.is_corresponding ? " · مراسل" : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">المراجعون</h2>
        {article.reviewers.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">لا مراجعين معيّنين.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {article.reviewers.map((row) => (
              <li
                key={row.user.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-3.5 py-2.5 text-sm"
              >
                <div>
                  <p className="font-semibold text-slate-800">
                    {row.user.full_name || row.user.email}
                  </p>
                  <p className="text-xs text-slate-500">
                    {row.user.email} · {REVIEWER_STATUS_LABELS[row.status]}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void runAction("أُلغي تعيين المراجع.", () =>
                      unassignReviewer(getToken, articleId, row.user.id),
                    )
                  }
                  className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
                >
                  إلغاء التعيين
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">المحررون</h2>
        {article.editors.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">لا محررين معيّنين.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {article.editors.map((row) => (
              <li
                key={row.user.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-3.5 py-2.5 text-sm"
              >
                <div>
                  <p className="font-semibold text-slate-800">
                    {row.user.full_name || row.user.email}
                  </p>
                  <p className="text-xs text-slate-500">
                    {row.user.email} · عُيِّن في {formatDate(row.assigned_at)}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void runAction("أُلغي تعيين المحرر.", () =>
                      unassignEditor(getToken, articleId, row.user.id),
                    )
                  }
                  className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
                >
                  إلغاء التعيين
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">
          تعيين أو دعوة
        </h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {(["reviewer", "editor"] as InvitationRole[]).map((role) => (
            <button
              key={role}
              type="button"
              onClick={() => setAssignRole(role)}
              className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
                assignRole === role
                  ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white"
                  : "border-[var(--journal-border)] bg-white text-slate-600"
              }`}
            >
              {INVITATION_ROLE_LABELS[role]}
            </button>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setAssignMode("user")}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
              assignMode === "user"
                ? "border-[var(--journal-gold)] bg-[var(--journal-accent-soft)] text-[var(--journal-gold)]"
                : "border-[var(--journal-border)] bg-white text-slate-600"
            }`}
          >
            مستخدم موجود
          </button>
          <button
            type="button"
            onClick={() => setAssignMode("email")}
            className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
              assignMode === "email"
                ? "border-[var(--journal-gold)] bg-[var(--journal-accent-soft)] text-[var(--journal-gold)]"
                : "border-[var(--journal-border)] bg-white text-slate-600"
            }`}
          >
            دعوة ببريد
          </button>
        </div>

        <div className="mt-4 space-y-3">
          {assignMode === "user" ? (
            <label className="block space-y-1.5">
              <span className="text-xs font-semibold text-slate-600">المستخدم</span>
              <select
                value={selectedUserId}
                onChange={(e) => setSelectedUserId(e.target.value)}
                className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
              >
                <option value="">— اختر —</option>
                {userOptions.map((u) => (
                  <option key={u.id} value={u.id}>
                    {(u.full_name || "بدون اسم") + ` <${u.email}>`}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label className="block space-y-1.5">
              <span className="text-xs font-semibold text-slate-600">
                البريد الإلكتروني
              </span>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
                placeholder="name@example.com"
              />
            </label>
          )}
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleAssignOrInvite()}
            className={buttonClassName}
          >
            {assignMode === "user" ? "تعيين" : "إرسال دعوة"}
          </button>
        </div>
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">الدعوات</h2>
        {invitations.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">لا دعوات لهذا المقال.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {invitations.map((inv) => (
              <li
                key={inv.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--journal-border)] bg-white px-3.5 py-2.5 text-sm"
              >
                <div>
                  <p className="font-semibold text-slate-800">{inv.email}</p>
                  <p className="text-xs text-slate-500">
                    {INVITATION_ROLE_LABELS[inv.role]} ·{" "}
                    {INVITATION_STATUS_LABELS[inv.status]} · تنتهي{" "}
                    {formatDate(inv.expires_at)}
                  </p>
                </div>
                {inv.status === "pending" ? (
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction("أُعيد إرسال الدعوة.", () =>
                          resendInvitation(getToken, inv.id),
                        )
                      }
                      className="rounded-md border border-[var(--journal-border)] px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] disabled:opacity-60"
                    >
                      إعادة إرسال
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void runAction("أُلغيت الدعوة.", () =>
                          cancelInvitation(getToken, inv.id),
                        )
                      }
                      className="rounded-md border border-rose-200 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-50 disabled:opacity-60"
                    >
                      إلغاء
                    </button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
        {pendingInvites.length > 0 ? (
          <p className="mt-3 text-xs text-slate-500">
            {pendingInvites.length} دعوة معلّقة.
          </p>
        ) : null}
      </section>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">
          تجاوز القرار
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          يحدّث حالة الإصدار الحالي مباشرة (مسار إداري).
        </p>
        <label className="mt-4 block space-y-1.5">
          <span className="text-xs font-semibold text-slate-600">
            سبب (اختياري — غير محفوظ حالياً في الخادم)
          </span>
          <textarea
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            rows={2}
            maxLength={2000}
            className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
          />
        </label>
        <div className="mt-4 flex flex-wrap gap-2.5">
          {OVERRIDE_STATUSES.map((item) => (
            <button
              key={item.status}
              type="button"
              disabled={busy || current.status === item.status}
              onClick={() => {
                if (item.confirm) {
                  setPendingOverride(item.status);
                } else {
                  void applyOverride(item.status);
                }
              }}
              className={
                current.status === item.status
                  ? "rounded-md border border-[var(--journal-accent)] bg-[var(--journal-accent)] px-5 py-2.5 text-sm font-semibold text-white opacity-80"
                  : buttonClassName
              }
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {pendingOverride ? (
        <ConfirmDialog
          open
          title="تأكيد تجاوز الحالة"
          description={`سيتم تغيير حالة الإصدار إلى «${
            OVERRIDE_STATUSES.find((s) => s.status === pendingOverride)?.label ??
            pendingOverride
          }».`}
          confirmLabel="تأكيد"
          submitting={busy}
          onConfirm={() => void applyOverride(pendingOverride)}
          onCancel={() => setPendingOverride(null)}
        />
      ) : null}
    </div>
  );
}
