"use client";

import { useAuth } from "@clerk/nextjs";
import Image from "next/image";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import { GenderIconSelector } from "@/components/gender-icon-selector";
import {
  createAppInvitation,
  listAccountDeletionRequests,
  listAdminUsers,
  listAppInvitations,
  resendAppInvitation,
  revokeAppInvitation,
  updateAccountDeletionRequest,
  type AccountDeletionRequestAdminRead,
  type AccountDeletionRequestStatus,
  type AdminUserListItem,
  type AppInvitationRead,
} from "@/lib/api/admin";
import { buttonClassName, inputClassName } from "@/lib/auth-ui";
import { useNumerals } from "@/components/numeral-provider";
import type { UserGender } from "@/lib/api";

const ROLE_LABELS: Record<string, string> = {
  author: "مؤلف",
  reviewer: "مراجع",
  editor: "محرر",
  admin: "مدير",
};

const INVITATION_STATUS_LABELS: Record<string, string> = {
  pending: "معلّقة",
  accepted: "مقبولة",
  expired: "منتهية",
  revoked: "ملغاة",
};

const DELETION_STATUS_LABELS: Record<AccountDeletionRequestStatus, string> = {
  pending: "بانتظار المراجعة",
  approved: "مقبول",
  rejected: "مرفوض",
  completed: "مكتمل",
};

function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? "دور غير معروف";
}

function invitationStatusLabel(status: string): string {
  return INVITATION_STATUS_LABELS[status] ?? "حالة غير معروفة";
}

export default function AdminUsersPage() {
  const { formatDate } = useNumerals();
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AdminUserListItem[] | null>(null);
  const [invitations, setInvitations] = useState<AppInvitationRead[] | null>(
    null,
  );
  const [deletionRequests, setDeletionRequests] = useState<
    AccountDeletionRequestAdminRead[] | null
  >(null);
  const [error, setError] = useState<string | null>(null);
  const [invitationError, setInvitationError] = useState<string | null>(null);
  const [deletionError, setDeletionError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [email, setEmail] = useState("");
  const [invitedName, setInvitedName] = useState("");
  const [invitedGender, setInvitedGender] = useState<UserGender | null>(null);
  const [sending, setSending] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [resendingId, setResendingId] = useState<string | null>(null);
  const [updatingDeletionId, setUpdatingDeletionId] = useState<string | null>(
    null,
  );

  async function refreshInvitations() {
    const data = await listAppInvitations(getToken);
    setInvitations(data);
  }

  async function refreshDeletionRequests() {
    const data = await listAccountDeletionRequests(getToken);
    setDeletionRequests(data);
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listAdminUsers(getToken),
      listAppInvitations(getToken),
      listAccountDeletionRequests(getToken),
    ])
      .then(([usersData, invitationData, deletionRequestData]) => {
        if (!cancelled) {
          setRows(usersData);
          setInvitations(invitationData);
          setDeletionRequests(deletionRequestData);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "تعذّر تحميل المستخدمين.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    const q = query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((row) => {
      const hay =
        `${row.full_name ?? ""} ${row.email} ${row.roles.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [rows, query]);

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedName = invitedName.trim();
    if (!normalizedName || !normalizedEmail || !invitedGender) {
      setInvitationError("يرجى إكمال بيانات الدعوة.");
      return;
    }

    setSending(true);
    setInvitationError(null);
    setSuccess(null);

    try {
      const response = await createAppInvitation(getToken, {
        email: normalizedEmail,
        full_name: normalizedName,
        gender: invitedGender,
      });
      setEmail("");
      setInvitedName("");
      setInvitedGender(null);
      setSuccess(`أُرسلت الدعوة إلى ${response.invitation.email}.`);
      await refreshInvitations();
    } catch (err) {
      setInvitationError(
        err instanceof Error ? err.message : "تعذّر إرسال الدعوة.",
      );
    } finally {
      setSending(false);
    }
  }

  async function handleRevoke(invitationId: string) {
    setRevokingId(invitationId);
    setInvitationError(null);
    setSuccess(null);

    try {
      await revokeAppInvitation(getToken, invitationId);
      setSuccess("أُلغيت الدعوة.");
      await refreshInvitations();
    } catch (err) {
      setInvitationError(
        err instanceof Error ? err.message : "تعذّر إلغاء الدعوة.",
      );
    } finally {
      setRevokingId(null);
    }
  }

  async function handleResend(invitationId: string) {
    setResendingId(invitationId);
    setInvitationError(null);
    setSuccess(null);

    try {
      await resendAppInvitation(getToken, invitationId);
      setSuccess("أُعيد إرسال الدعوة.");
    } catch (err) {
      setInvitationError(
        err instanceof Error ? err.message : "تعذّرت إعادة إرسال الدعوة.",
      );
    } finally {
      setResendingId(null);
    }
  }

  async function handleDeletionStatus(
    requestId: string,
    status: AccountDeletionRequestStatus,
  ) {
    setUpdatingDeletionId(requestId);
    setDeletionError(null);
    setSuccess(null);

    try {
      await updateAccountDeletionRequest(getToken, requestId, status);
      setSuccess("حُدّثت حالة طلب حذف الحساب.");
      await refreshDeletionRequests();
    } catch (err) {
      setDeletionError(
        err instanceof Error ? err.message : "تعذّر تحديث طلب حذف الحساب.",
      );
    } finally {
      setUpdatingDeletionId(null);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          المستخدمون
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          قائمة المستخدمين المسجّلين ودعوات الانضمام إلى المنصة.
        </p>
      </div>

      <section className="rounded-xl border border-[var(--journal-border)] bg-white/80 p-4 shadow-sm sm:p-5">
        <h2
          className="text-xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          دعوة مستخدم جديد
        </h2>
        <form
          onSubmit={handleInvite}
          className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto_auto] sm:items-end"
          noValidate
        >
          <label className="block space-y-1.5">
            <span className="text-xs font-semibold text-slate-600">
              البريد الإلكتروني
            </span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="person@example.com"
              required
              className={inputClassName}
            />
          </label>
          <label className="block space-y-1.5">
            <span className="text-xs font-semibold text-slate-600">
              الاسم الكامل
            </span>
            <input
              type="text"
              value={invitedName}
              onChange={(event) => setInvitedName(event.target.value)}
              autoComplete="name"
              maxLength={200}
              required
              className={inputClassName}
            />
          </label>
          <GenderIconSelector
            value={invitedGender}
            onChange={setInvitedGender}
            name="invited-gender"
          />
          <button type="submit" className={buttonClassName} disabled={sending}>
            {sending ? "جارٍ الإرسال…" : "إرسال الدعوة"}
          </button>
        </form>
        {success ? (
          <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            {success}
          </p>
        ) : null}
        {invitationError ? (
          <p
            className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {invitationError}
          </p>
        ) : null}
      </section>

      <section className="space-y-3">
        <h2
          className="text-xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          دعوات الانضمام
        </h2>
        {invitations === null ? (
          <RowsSkeleton count={3} />
        ) : invitations.length === 0 ? (
          <EmptyState
            title="لا دعوات"
            description="لم تُنشأ دعوات انضمام بعد."
          />
        ) : (
          <ul className="space-y-2.5">
            {invitations.map((invitation) => (
              <li
                key={invitation.id}
                className="rounded-xl border border-[var(--journal-border)] bg-white/80 px-4 py-3.5 shadow-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      {invitation.gender ? (
                        <Image
                          src={`/${invitation.gender}.png`}
                          alt=""
                          width={24}
                          height={24}
                          className="size-6 object-contain"
                        />
                      ) : null}
                      <p className="text-sm font-semibold text-slate-800">
                        {invitation.full_name || "دعوة قديمة"}
                      </p>
                    </div>
                    <p className="mt-0.5 break-all text-xs text-slate-500">
                      {invitation.email}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      أُنشئت {formatDate(invitation.created_at)}
                      {invitation.expires_at
                        ? ` · تنتهي ${formatDate(invitation.expires_at)}`
                        : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-[var(--journal-border)] bg-[var(--journal-accent-soft)] px-2.5 py-0.5 text-xs font-semibold text-[var(--journal-accent-strong)]">
                      {invitationStatusLabel(invitation.status)}
                    </span>
                    {invitation.status === "pending" ? (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          className="rounded-md border border-[var(--journal-border)] bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-[var(--journal-accent)] disabled:opacity-60"
                          disabled={resendingId === invitation.id}
                          onClick={() => handleResend(invitation.id)}
                        >
                          {resendingId === invitation.id
                            ? "جارٍ الإرسال…"
                            : "إعادة إرسال"}
                        </button>
                        <button
                          type="button"
                          className="rounded-md border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-50 disabled:opacity-60"
                          disabled={revokingId === invitation.id}
                          onClick={() => handleRevoke(invitation.id)}
                        >
                          {revokingId === invitation.id
                            ? "جارٍ الإلغاء…"
                            : "إلغاء"}
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2
          className="text-xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          طلبات حذف الحساب
        </h2>
        {deletionError ? (
          <p
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {deletionError}
          </p>
        ) : null}
        {deletionRequests === null ? (
          <RowsSkeleton count={3} />
        ) : deletionRequests.length === 0 ? (
          <EmptyState
            title="لا طلبات حذف"
            description="لم يرسل المستخدمون طلبات حذف حسابات بعد."
          />
        ) : (
          <ul className="space-y-2.5">
            {deletionRequests.map((request) => (
              <li
                key={request.id}
                className="rounded-xl border border-[var(--journal-border)] bg-white/80 px-4 py-3.5 shadow-sm"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="break-all text-sm font-semibold text-slate-800">
                      {request.email_snapshot}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      طُلب في {formatDate(request.requested_at)}
                    </p>
                    {request.reason ? (
                      <p className="mt-2 text-sm leading-6 text-slate-600">
                        {request.reason}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full border border-[var(--journal-border)] bg-slate-50 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                      {DELETION_STATUS_LABELS[request.status]}
                    </span>
                    {(["approved", "rejected", "completed"] as const).map(
                      (status) => (
                        <button
                          key={status}
                          type="button"
                          className="rounded-md border border-[var(--journal-border)] bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                          disabled={
                            updatingDeletionId === request.id ||
                            request.status === status
                          }
                          onClick={() => handleDeletionStatus(request.id, status)}
                        >
                          {DELETION_STATUS_LABELS[status]}
                        </button>
                      ),
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-4">
        <label className="block max-w-md space-y-1.5">
          <span className="text-xs font-semibold text-slate-600">بحث</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="اسم أو بريد أو دور..."
            className="w-full rounded-lg border border-[var(--journal-border)] bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)]"
          />
        </label>

        {error ? (
          <p
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {error}
          </p>
        ) : rows === null ? (
          <RowsSkeleton count={6} />
        ) : rows.length === 0 ? (
          <EmptyState
            title="لا مستخدمين"
            description="لم يُسجَّل مستخدمون بعد في قاعدة البيانات."
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="لا نتائج"
            description="عدّل عبارة البحث لعرض مستخدمين."
          />
        ) : (
          <ul className="space-y-2.5">
            {filtered.map((row, index) => (
              <li
                key={row.id}
                className="stagger-item"
                style={{ "--stagger-index": index } as React.CSSProperties}
              >
                <div className="rounded-xl border border-[var(--journal-border)] bg-white/80 px-4 py-3.5 shadow-sm">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        {row.gender ? (
                          <Image
                            src={`/${row.gender}.png`}
                            alt=""
                            width={24}
                            height={24}
                            className="size-6 object-contain"
                          />
                        ) : null}
                        <p className="truncate text-sm font-semibold text-slate-800">
                          {row.full_name || "بدون اسم"}
                        </p>
                      </div>
                      <p className="mt-0.5 text-xs text-slate-500">{row.email}</p>
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(row.created_at)}
                    </span>
                  </div>
                  <p className="mt-2 flex flex-wrap gap-1.5">
                    {row.roles.length === 0 ? (
                      <span className="rounded-full border border-[var(--journal-border)] bg-white px-2.5 py-0.5 text-xs text-slate-500">
                        بدون أدوار مرتبطة
                      </span>
                    ) : (
                      row.roles.map((role) => (
                        <span
                          key={role}
                          className="rounded-full border border-[var(--journal-border)] bg-[var(--journal-accent-soft)] px-2.5 py-0.5 text-xs font-semibold text-[var(--journal-accent-strong)]"
                        >
                          {roleLabel(role)}
                        </span>
                      ))
                    )}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
