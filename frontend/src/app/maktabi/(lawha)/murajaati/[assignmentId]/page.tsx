"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { DocumentFrozenPreview } from "@/components/dashboard/document-frozen-preview";
import { CardsSkeleton, RowsSkeleton } from "@/components/dashboard/skeleton";
import { StatusBadge } from "@/components/dashboard/status-badge";
import { buttonClassName } from "@/lib/auth-ui";
import { formatDate } from "@/lib/format-date";
import {
  fetchAssignmentAssetBlob,
  getAssignment,
  getAssignmentDocument,
  RECOMMENDATION_LABELS,
  saveReviewDraft,
  submitReview,
  type AssignmentDetail,
  type ReviewRecommendation,
} from "@/lib/api/reviews";

const RECOMMENDATIONS = Object.keys(
  RECOMMENDATION_LABELS,
) as ReviewRecommendation[];

export default function MurajaatiDetailPage() {
  const { getToken } = useAuth();
  const params = useParams<{ assignmentId: string }>();
  const router = useRouter();
  const assignmentId = params.assignmentId;

  const [assignment, setAssignment] = useState<AssignmentDetail | null>(null);
  const [documentJson, setDocumentJson] = useState<unknown>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [commentsAuthor, setCommentsAuthor] = useState("");
  const [commentsEditor, setCommentsEditor] = useState("");
  const [recommendation, setRecommendation] =
    useState<ReviewRecommendation | null>(null);
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formOk, setFormOk] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getAssignment(getToken, assignmentId);
      setAssignment(data);
      setCommentsAuthor(data.review?.comments_to_author ?? "");
      setCommentsEditor(data.review?.comments_to_editor ?? "");
      setRecommendation(data.review?.recommendation ?? null);
      try {
        const doc = await getAssignmentDocument(getToken, assignmentId);
        setDocumentJson(doc.document);
      } catch {
        setDocumentJson(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر تحميل التعيين.");
    }
  }, [getToken, assignmentId]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitted =
    assignment?.assignment_status === "completed" ||
    assignment?.review?.status === "submitted";

  async function handleSaveDraft() {
    setSaving(true);
    setFormError(null);
    setFormOk(null);
    try {
      await saveReviewDraft(getToken, assignmentId, {
        comments_to_author: commentsAuthor || null,
        comments_to_editor: commentsEditor || null,
        recommendation,
      });
      setFormOk("حُفظت المسودة.");
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "تعذّر حفظ المسودة.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    if (!recommendation) {
      setFormError("اختر توصية قبل التسليم.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    setFormOk(null);
    try {
      await saveReviewDraft(getToken, assignmentId, {
        comments_to_author: commentsAuthor || null,
        comments_to_editor: commentsEditor || null,
        recommendation,
      });
      await submitReview(getToken, assignmentId);
      setFormOk("سُلِّمت المراجعة بنجاح.");
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "تعذّر تسليم المراجعة.");
    } finally {
      setSubmitting(false);
    }
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
          onClick={() => router.push("/maktabi/murajaati")}
          className="text-sm font-medium text-[var(--journal-accent)] underline-offset-4 hover:underline"
        >
          العودة إلى مراجعاتي
        </button>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="space-y-6">
        <CardsSkeleton count={1} />
        <RowsSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <Link
          href="/maktabi/murajaati"
          className="text-xs font-medium text-slate-500 underline-offset-4 hover:text-[var(--journal-accent)] hover:underline"
        >
          → مراجعاتي
        </Link>
        <div className="mt-2">
          <h1
            className="text-2xl font-bold leading-relaxed text-slate-900 sm:text-3xl"
            style={{ fontFamily: "var(--font-display-ar), serif" }}
          >
            {assignment.article_title}
          </h1>
          <p className="mt-2 flex flex-wrap items-center gap-2.5 text-sm text-slate-500">
            <StatusBadge status={assignment.version_status} />
            <span>الإصدار v{assignment.version_number}</span>
            <span aria-hidden>·</span>
            <span>دُعيت في {formatDate(assignment.invited_at)}</span>
          </p>
        </div>
      </div>

      {assignment.article_abstract ? (
        <section className="rounded-xl border border-amber-200 bg-white/80 p-5 shadow-sm">
          <h2 className="text-sm font-bold text-[var(--journal-accent)]">الملخص</h2>
          <p className="mt-2 text-sm leading-7 text-slate-700">
            {assignment.article_abstract}
          </p>
        </section>
      ) : null}

      <section>
        <h2
          className="text-lg font-bold text-[var(--journal-accent)]"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          معاينة المخطوطة
        </h2>
        <div className="mt-3">
          <DocumentFrozenPreview
            documentJson={documentJson ?? null}
            articleId={assignmentId}
            getToken={getToken}
            fetchAssetBlob={fetchAssignmentAssetBlob}
          />
        </div>
      </section>

      <section className="rounded-xl border border-amber-200 bg-white/80 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-[var(--journal-accent)]">
          تقرير المراجعة
        </h2>

        {submitted ? (
          <p className="mt-3 text-sm text-emerald-800">
            سُلِّمت هذه المراجعة
            {assignment.review?.submitted_at
              ? ` في ${formatDate(assignment.review.submitted_at)}`
              : ""}
            .
          </p>
        ) : null}

        <div className="mt-4 space-y-4">
          <label className="block space-y-1.5">
            <span className="text-xs font-semibold text-slate-600">
              ملاحظات للمؤلف
            </span>
            <textarea
              value={commentsAuthor}
              onChange={(e) => setCommentsAuthor(e.target.value)}
              disabled={submitted}
              rows={5}
              className="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)] disabled:bg-slate-50"
            />
          </label>

          <label className="block space-y-1.5">
            <span className="text-xs font-semibold text-slate-600">
              ملاحظات للمحرر (خاصة)
            </span>
            <textarea
              value={commentsEditor}
              onChange={(e) => setCommentsEditor(e.target.value)}
              disabled={submitted}
              rows={4}
              className="w-full rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-[var(--journal-accent)] disabled:bg-slate-50"
            />
          </label>

          <fieldset className="space-y-2" disabled={submitted}>
            <legend className="text-xs font-semibold text-slate-600">
              التوصية
            </legend>
            <div className="flex flex-wrap gap-2">
              {RECOMMENDATIONS.map((value) => {
                const active = recommendation === value;
                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setRecommendation(value)}
                    className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
                      active
                        ? "border-[var(--journal-accent)] bg-[var(--journal-accent)] text-white"
                        : "border-amber-200 bg-white text-slate-600 hover:border-[var(--journal-accent)]"
                    }`}
                  >
                    {RECOMMENDATION_LABELS[value]}
                  </button>
                );
              })}
            </div>
          </fieldset>

          {formError ? (
            <p
              className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
              role="alert"
            >
              {formError}
            </p>
          ) : null}
          {formOk ? (
            <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              {formOk}
            </p>
          ) : null}

          {!submitted ? (
            <div className="flex flex-wrap gap-2.5">
              <button
                type="button"
                onClick={() => void handleSaveDraft()}
                disabled={saving || submitting}
                className="rounded-md border border-[var(--journal-gold)] bg-white px-5 py-2.5 text-sm font-semibold text-[var(--journal-gold)] transition hover:bg-[var(--journal-accent-soft)] disabled:opacity-60"
              >
                {saving ? "جارٍ الحفظ..." : "حفظ المسودة"}
              </button>
              <button
                type="button"
                onClick={() => void handleSubmit()}
                disabled={saving || submitting}
                className={buttonClassName}
              >
                {submitting ? "جارٍ التسليم..." : "تسليم المراجعة"}
              </button>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
