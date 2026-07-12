import { type VersionStatus } from "@/lib/api/articles";

const STEPS: { id: string; label: string; statuses: VersionStatus[] }[] = [
  { id: "draft", label: "مسودة", statuses: ["draft"] },
  { id: "submitted", label: "مُقدَّم", statuses: ["submitted"] },
  { id: "review", label: "قيد المراجعة", statuses: ["under_review"] },
  { id: "decision", label: "القرار", statuses: ["accepted", "rejected"] },
  { id: "published", label: "منشور", statuses: ["published"] },
];

function stepIndex(status: VersionStatus): number {
  const index = STEPS.findIndex((step) => step.statuses.includes(status));
  return index === -1 ? 0 : index;
}

export function WorkflowProgress({ status }: { status: VersionStatus }) {
  const current = stepIndex(status);
  const rejected = status === "rejected";

  return (
    <div className="nav-scroll -mx-1 overflow-x-auto px-1">
      <ol
        className="flex min-w-min items-center gap-y-2"
        aria-label="مسار المخطوطة"
      >
        {STEPS.map((step, index) => {
          const reached = index <= current;
          const isCurrent = index === current;
          return (
            <li key={step.id} className="flex shrink-0 items-center">
              {index > 0 ? (
                <span
                  aria-hidden
                  className={`mx-1 h-0.5 w-3 rounded-full transition-colors duration-300 sm:mx-1.5 sm:w-6 ${
                    reached
                      ? "bg-[var(--journal-accent)]"
                      : "bg-[var(--journal-border)]"
                  }`}
                />
              ) : null}
              <span
                className={`flex items-center gap-1.5 rounded-full border px-2 py-1 text-[11px] font-semibold transition-colors duration-300 sm:px-2.5 sm:text-xs ${
                  isCurrent
                    ? rejected
                      ? "border-rose-300 bg-rose-50 text-rose-700"
                      : "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white"
                    : reached
                      ? "border-[var(--journal-accent)] bg-[var(--journal-accent-soft)] text-[var(--journal-accent-strong)]"
                      : "border-[var(--journal-border)] bg-white/60 text-slate-400"
                }`}
                aria-current={isCurrent ? "step" : undefined}
              >
                {step.id === "decision" && rejected ? "مرفوض" : step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
