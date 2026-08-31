"use client";

import { useAuth } from "@clerk/nextjs";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import {
  createAppInvitation,
  listAdminUsers,
  listAppInvitations,
  revokeAppInvitation,
  type AdminUserListItem,
  type AppInvitationRead,
} from "@/lib/api/admin";
import { buttonClassName, inputClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";

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

function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

function invitationStatusLabel(status: string): string {
  return INVITATION_STATUS_LABELS[status] ?? status;
}

export default function AdminUsersPage() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AdminUserListItem[] | null>(null);
  const [invitations, setInvitations] = useState<AppInvitationRead[] | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [invitationError, setInvitationError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  async function refreshInvitations() {
    const data = await listAppInvitations(getToken);
    setInvitations(data);
  }

  useEffect(() => {
    let cancelled = false;
    Promise.all([listAdminUsers(getToken), listAppInvitations(getToken)])
      .then(([usersData, invitationData]) => {
        if (!cancelled) {
          setRows(usersData);
          setInvitations(invitationData);
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
    if (!normalizedEmail) {
      setInvitationError("يرجى إدخال البريد الإلكتروني.");
      return;
    }

    setSending(true);
    setInvitationError(null);
    setSuccess(null);

    try {
      const response = await createAppInvitation(getToken, normalizedEmail);
      setEmail("");
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
          className="mt-4 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end"
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
                    <p className="break-all text-sm font-semibold text-slate-800">
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
                      <button
                        type="button"
                        className="rounded-md border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 transition hover:bg-red-50 disabled:opacity-60"
                        disabled={revokingId === invitation.id}
                        onClick={() => handleRevoke(invitation.id)}
                      >
                        {revokingId === invitation.id ? "جارٍ الإلغاء…" : "إلغاء"}
                      </button>
                    ) : null}
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
                      <p className="truncate text-sm font-semibold text-slate-800">
                        {row.full_name || "بدون اسم"}
                      </p>
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
