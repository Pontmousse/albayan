"use client";

import { useAuth } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { createArticle } from "@/lib/api/articles";
import { buttonClassName, cardClassName, inputClassName } from "@/lib/auth-ui";

export default function JadidPage() {
  const { getToken } = useAuth();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const article = await createArticle(getToken, {
        title: title.trim(),
        abstract: abstract.trim() || null,
      });
      router.push(`/maktabi/maqalati/${article.id}/tahrir`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر إنشاء المقال.");
      setSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1
          className="text-3xl font-bold text-slate-900"
          style={{ fontFamily: "var(--font-display-ar), serif" }}
        >
          مقال جديد
        </h1>
        <p className="mt-1.5 text-sm text-slate-600">
          أدخل العنوان لبدء مسودتك — ستنتقل مباشرة إلى المحرر.
        </p>
      </div>

      <form onSubmit={handleSubmit} className={`${cardClassName} space-y-5`}>
        <div>
          <label htmlFor="title" className="mb-1 block text-sm font-medium text-slate-700">
            عنوان المقال <span className="text-red-600">*</span>
          </label>
          <input
            id="title"
            type="text"
            required
            maxLength={500}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="مثال: تحليل عددي لمعادلات الانتشار في الأوساط المسامية"
            className={inputClassName}
          />
        </div>

        <div>
          <label
            htmlFor="abstract"
            className="mb-1 block text-sm font-medium text-slate-700"
          >
            ملخص مختصر <span className="text-xs text-slate-400">(اختياري)</span>
          </label>
          <textarea
            id="abstract"
            rows={4}
            maxLength={5000}
            value={abstract}
            onChange={(e) => setAbstract(e.target.value)}
            placeholder="فكرة المقال في سطرين — يمكنك تعديله لاحقاً."
            className={inputClassName}
          />
        </div>

        <p className="rounded-md border border-amber-200 bg-[var(--journal-accent-soft)] px-3 py-2 text-xs leading-6 text-slate-600">
          ستُسجَّل كمؤلف مراسل لهذا المقال. يمكنك التحرير بحرية ما دامت المسودة لم
          تُقدَّم بعد.
        </p>

        {error ? (
          <p
            className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
            role="alert"
          >
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={saving || !title.trim()}
          className={`${buttonClassName} w-full`}
        >
          {saving ? "جارٍ الإنشاء…" : "إنشاء والانتقال للمحرر"}
        </button>
      </form>
    </div>
  );
}
