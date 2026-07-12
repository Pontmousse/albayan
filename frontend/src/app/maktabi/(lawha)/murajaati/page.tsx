"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useEffect, useState } from "react";
import { EmptyState } from "@/components/dashboard/empty-state";
import { RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import {
  listMyAssignments,
  type AssignmentSummary,
} from "@/lib/api/reviews";
import { formatDate } from "@/lib/format-date";

function reviewLabel(row: AssignmentSummary): string {
  if (row.assignment_status === "completed" || row.review?.status === "submitted") {
    return "مُسلَّمة";
  }
  if (row.review?.status === "draft") return "مسودة مراجعة";
  return "بانتظار المراجعة";
}

export default function MurajaatiPage() {
  const { getToken } = useAuth();
  const [rows, setRows] = useState<AssignmentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listMyAssignments(getToken)
      .then((data) => {
        if (!cancelled) setRows(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "تعذّر تحميل المراجعات.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [getToken]);

  return (
    <div className="space-y-6">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          مراجعاتي
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          المقالات المعيّنة لك للمراجعة — اقرأ المخطوطة وقدّم توصيتك.
        </p>
      </div>

      {error ? (
        <p
          className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          role="alert"
        >
          {error}
        </p>
      ) : rows === null ? (
        <RowsSkeleton count={4} />
      ) : rows.length === 0 ? (
        <EmptyState
          title="لا تعيينات مراجعة"
          description="عندما يعيّنك المحرر الإداري مراجعاً على مقال، تظهر هنا."
        />
      ) : (
        <ul className="space-y-2.5">
          {rows.map((row, index) => (
            <li
              key={row.id}
              className="stagger-item"
              style={{ "--stagger-index": index } as React.CSSProperties}
            >
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[var(--journal-border)] bg-white/80 px-4 py-3.5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--journal-accent)] hover:shadow-md">
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/maktabi/murajaati/${row.id}`}
                    className="block truncate text-sm font-semibold text-slate-800 hover:text-[var(--journal-accent-strong)]"
                  >
                    {row.article_title}
                  </Link>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>الإصدار v{row.version_number}</span>
                    <span aria-hidden>·</span>
                    <span>دُعيت في {formatDate(row.invited_at)}</span>
                    <span aria-hidden>·</span>
                    <span>{reviewLabel(row)}</span>
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <StatusBadge status={row.version_status} />
                  <Link
                    href={`/maktabi/murajaati/${row.id}`}
                    className="rounded-md border border-[var(--journal-border)] px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:border-[var(--journal-accent)] hover:text-[var(--journal-accent-strong)]"
                  >
                    فتح
                  </Link>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
