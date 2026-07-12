"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import {
  listAdminUsers,
  type AdminUserListItem,
} from "@/lib/api/admin";
import { formatDate } from "@/lib/format-date";

const ROLE_LABELS: Record<string, string> = {
  author: "مؤلف",
  reviewer: "مراجع",
  editor: "محرر",
  admin: "مدير",
};

function roleLabel(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export default function AdminUsersPage() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AdminUserListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    listAdminUsers(getToken)
      .then((data) => {
        if (!cancelled) setRows(data);
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
      const hay = `${row.full_name ?? ""} ${row.email} ${row.roles.join(" ")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [rows, query]);

  return (
    <div className="space-y-6">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          المستخدمون
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          قائمة المستخدمين المسجّلين في المنصة (عرض فقط).
        </p>
      </div>

      <label className="block max-w-md space-y-1.5">
        <span className="text-xs font-semibold text-slate-600">بحث</span>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="اسم أو بريد أو دور…"
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
    </div>
  );
}
