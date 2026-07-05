import { STATUS_LABELS, type VersionStatus } from "@/lib/api/articles";

const STATUS_STYLES: Record<VersionStatus, string> = {
  draft: "border-slate-300 bg-slate-50 text-slate-700",
  submitted: "border-emerald-200 bg-emerald-50 text-emerald-800",
  under_review: "border-amber-300 bg-amber-50 text-amber-800",
  accepted: "border-emerald-300 bg-emerald-100 text-emerald-900",
  rejected: "border-rose-200 bg-rose-50 text-rose-700",
  published: "border-[var(--journal-gold)] bg-[var(--journal-accent-soft)] text-[var(--journal-gold)]",
};

export function StatusBadge({ status }: { status: VersionStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${STATUS_STYLES[status]}`}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}
